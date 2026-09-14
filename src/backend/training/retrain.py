"""
Retrain the Bottleneck solar models with walk-forward evaluation and save
artifacts exactly where the inference engine expects them:

    models/solar/solar_hybrid.json        (XGBoost residual model)
    models/solar/feature_cols.json        (feature order)
    models/solar/quantile/p10.txt|p50.txt|p90.txt  (LightGBM quantile models)
    models/metrics/evaluation_report.json (walk-forward + holdout + coverage)

p50 = pvlib physics + XGBoost residual (clipped); p10/p50/p90 = LightGBM
quantile models (clipped + sorted). This mirrors inference.predict_solar.
"""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.forecasting.features import prepare_solar_features, SOLAR_FEATURE_COLS
from backend.forecasting.solar import run_physics_model
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import validate_coverage

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR = Path(__file__).parent.parent / "data"

SITE_PARAMS = {
    "name": "Bhadla Solar Park (Rajasthan, India)",
    "latitude": 27.5667,
    "longitude": 72.0667,
    "altitude": 210,
    "capacity_kw": 100,
    "surface_tilt": 26,
    "surface_azimuth": 180,
    "temp_coeff_pmax": -0.004,
}


def load_training_df(csv_path):
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = prepare_solar_features(df, SITE_PARAMS["latitude"], SITE_PARAMS["longitude"])
    df["physics_estimate_kw"] = run_physics_model(df, SITE_PARAMS)
    return df


def train_solar_csv(df):
    import xgboost as xgb

    capacity = SITE_PARAMS["capacity_kw"]
    df = df.copy()
    df["residual"] = df["generation_kw"] - df["physics_estimate_kw"]

    available_features = [c for c in SOLAR_FEATURE_COLS if c in df.columns]
    print(f"[Solar] {len(available_features)} features")

    X = df[available_features].fillna(0)
    y = df["residual"]

    split_idx = int(len(df) * 0.8)
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
        reg_alpha=0.1, reg_lambda=1.0, tree_method="hist",
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    val_pred = np.clip(
        df["physics_estimate_kw"].iloc[split_idx:] + model.predict(X_val),
        0, capacity,
    )
    holdout_metrics = evaluate(df["generation_kw"].iloc[split_idx:].values, val_pred, capacity)

    model_dir = MODELS_DIR / "solar"
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "solar_hybrid.json"))
    with open(model_dir / "feature_cols.json", "w") as f:
        json.dump(available_features, f)

    print(f"[Solar] Holdout nMAE={holdout_metrics['nMAE_%']:.2f}% R²={holdout_metrics['R2']:.4f}")
    return model, available_features, holdout_metrics


def train_quantile_models(df, feature_cols):
    import lightgbm as lgb

    capacity = SITE_PARAMS["capacity_kw"]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(0)
    y = df["generation_kw"]

    split_idx = int(len(df) * 0.8)
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    q_dir = MODELS_DIR / "solar" / "quantile"
    q_dir.mkdir(parents=True, exist_ok=True)

    models = {}
    for name, alpha in {"p10": 0.1, "p50": 0.5, "p90": 0.9}.items():
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=alpha, num_leaves=31,
            learning_rate=0.05, n_estimators=300, random_state=42,
            n_jobs=-1, verbosity=-1,
        )
        m.fit(X_train, y_train, eval_set=[(X_val, y_val)])
        m.booster_.save_model(str(q_dir / f"{name}.txt"))
        models[name] = m

    preds = np.sort(np.stack([models[n].predict(X_val) for n in ("p10", "p50", "p90")], axis=1), axis=1)
    preds = np.clip(preds, 0, capacity)
    coverage = validate_coverage(y_val.values, preds[:, 0], preds[:, 2])
    ret = {
        "coverage_80": float(coverage),
        "nMAE_p50_%": float(np.mean(np.abs(y_val.values - preds[:, 1])) / capacity * 100),
        "nMAE_p10_%": float(np.mean(np.abs(y_val.values - preds[:, 0])) / capacity * 100),
        "nMAE_p90_%": float(np.mean(np.abs(y_val.values - preds[:, 2])) / capacity * 100),
    }
    print(f"[Quantile] 80% coverage={coverage:.1%}  p50 nMAE={ret['nMAE_p50_%']:.2f}%")
    return models, ret


def walk_forward_eval(df, feature_cols, capacity):
    import xgboost as xgb

    df = df.copy()
    df["residual"] = df["generation_kw"] - df["physics_estimate_kw"]
    X = df[feature_cols].fillna(0)
    y = df["residual"]
    fold_metrics = []
    for fold, (train_idx, test_idx) in enumerate(walk_forward_split(df, n_splits=5, test_size=168)):
        model = xgb.XGBRegressor(
            objective="reg:squarederror", n_estimators=300, max_depth=6,
            learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            min_child_weight=5, tree_method="hist", random_state=fold, n_jobs=-1,
        )
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = np.clip(
            df["physics_estimate_kw"].iloc[test_idx].values + model.predict(X.iloc[test_idx]),
            0, capacity,
        )
        m = evaluate(df["generation_kw"].iloc[test_idx].values, pred, capacity)
        m["fold"] = fold + 1
        fold_metrics.append(m)
        print(f"  fold {fold+1}: nMAE={m['nMAE_%']:.2f}% R²={m['R2']:.4f}")

    avg = {
        "nMAE_%": float(np.mean([m["nMAE_%"] for m in fold_metrics])),
        "MAE": float(np.mean([m["MAE"] for m in fold_metrics])),
        "RMSE": float(np.mean([m["RMSE"] for m in fold_metrics])),
        "R2": float(np.mean([m["R2"] for m in fold_metrics])),
        "MAPE_%": float(np.mean([m["MAPE_%"] for m in fold_metrics if m["MAPE_%"] is not None])) if any(m["MAPE_%"] is not None for m in fold_metrics) else None,
        "Forecast_Reliability_Score": float(np.mean([m["Forecast_Reliability_Score"] for m in fold_metrics])),
    }
    return avg, fold_metrics


def main():
    csv_path = DATA_DIR / "raw" / "solar_generation.csv"
    if not csv_path.exists():
        sys.exit(f"Training data not found: {csv_path} (run build_dataset.py first)")

    df = load_training_df(csv_path)
    capacity = SITE_PARAMS["capacity_kw"]

    print("=" * 60)
    print(f"Training on {len(df)} hourly rows | {SITE_PARAMS['name']}")
    print("=" * 60)

    model, feature_cols, holdout = train_solar_csv(df)
    quantile_models, quantile_report = train_quantile_models(df, feature_cols)

    print("\nWalk-forward evaluation (5 x 168h):")
    wf_avg, wf_folds = walk_forward_eval(df, feature_cols, capacity)

    report = {
        "timestamp": datetime.now().isoformat(),
        "site_params": SITE_PARAMS,
        "rows": int(len(df)),
        "features": feature_cols,
        "holdout": holdout,
        "quantiles": quantile_report,
        "walk_forward": {"average": wf_avg, "folds": wf_folds},
    }
    metrics_dir = MODELS_DIR / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"  Holdout nMAE  : {holdout['nMAE_%']:.2f}%")
    print(f"  Holdout R²    : {holdout['R2']:.4f}")
    print(f"  80% coverage  : {quantile_report['coverage_80']:.1%}")
    print(f"  WF avg nMAE   : {wf_avg['nMAE_%']:.2f}%")
    print(f"  WF avg R²     : {wf_avg['R2']:.4f}")
    print(f"Report: {metrics_dir / 'evaluation_report.json'}")


if __name__ == "__main__":
    main()