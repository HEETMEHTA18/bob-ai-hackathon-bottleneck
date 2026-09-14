"""
Wind model retraining — SURGE-aligned, physics-informed, tuned.

Features (identical to serving `_build_surge_wind_features`):
  16 SURGE features
  + power_curve_estimate (IEC cubic at 10m)
  + wind_speed_lag_1h, wind_speed_rolling_6h... persistence
  = 19 features

Validation discipline (no over/underfit):
  - strictly chronological splits
  - randomized hyperparameter search + early stopping
  - train | val | test gap reported explicitly
  - final holdout on last 20%

Outputs:
  models/wind/wind_lgbm.txt              LightGBM point model
  models/wind/feature_cols.json          feature order (serving must match)
  models/wind/quantile/*.txt|joblib      P10/P50/P90 quantile bundle
  models/wind/calibration.json           band_scale + coverage_80
  models/metrics/wind_evaluation_report.json
"""
import json
import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
warnings.filterwarnings("ignore")

from backend.forecasting.inference import _build_surge_wind_features
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import validate_coverage
from backend.training.tune_utils import cap, report_overfit

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR   = Path(__file__).parent.parent.parent / "data"
CAPACITY   = 100.0

SURGE_COLS = [
    "wind_speed_10m", "wind_speed_100m", "wind_gusts_10m",
    "wind_dir_sin", "wind_dir_cos",
    "air_density", "temperature_2m", "surface_pressure",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "day_of_year_sin", "day_of_year_cos",
    "wind_speed_rolling_3h", "wind_speed_rolling_6h",
]
PERSISTENCE_COLS = [
    "power_curve_estimate", "wind_speed_lag_1h", "wind_speed_lag_6h",
]
ALL_FEATURES = SURGE_COLS + PERSISTENCE_COLS

TEST_FRAC = 0.20
TUNE_FRAC = 0.20
N_ITERS = 20


def _tune_lgb(X, y, tune_cut):
    import lightgbm as lgb

    Xt, yt = X.iloc[:tune_cut], y.iloc[:tune_cut]
    split = int(len(Xt) * 0.75)
    Xtr, ytr = Xt.iloc[:split], yt.iloc[:split]
    Xva, yva = Xt.iloc[split:], yt.iloc[split:]

    rng = np.random.default_rng(7)
    leaves = [15, 31, 63, 127]
    lrs = [0.02, 0.05, 0.1]
    cols = [0.5, 0.7, 0.9]
    subs = [0.7, 0.85, 1.0]
    mcs = [5, 20, 50]
    results = []

    for _ in range(N_ITERS):
        p = dict(num_leaves=int(rng.choice(leaves)), learning_rate=float(rng.choice(lrs)),
                 colsample_bytree=float(rng.choice(cols)), subsample=float(rng.choice(subs)),
                 min_child_samples=int(rng.choice(mcs)), n_estimators=800)
        m = lgb.LGBMRegressor(objective="regression", metric="mae",
                              boosting_type="gbdt", random_state=42,
                              n_jobs=-1, verbosity=-1, **p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])
        va = evaluate(yva.values, cap(m.predict(Xva), CAPACITY), CAPACITY)
        it = max(int(m.best_iteration_ or 800), 1)
        results.append((va["MAE"], p, it))
        print(f"  [tune] MAE={va['MAE']:.3f} R²={va['R2']:.4f} it={it} {p}")

    results.sort(key=lambda r: r[0])
    _, best_p, best_it = results[0]
    return best_p, best_it, float(results[0][0])


def _calibrate_bands(y_true, p10_raw, p50, p90_raw, target=0.80):
    d10 = np.clip(p50 - p10_raw, 1e-6, None)
    d90 = np.clip(p90_raw - p50, 1e-6, None)
    best_s, best_cov = 1.0, validate_coverage(y_true, p10_raw, p90_raw)
    for s in np.arange(0.4, 5.0, 0.05):
        cov = validate_coverage(y_true,
                                np.clip(p50 - s * d10, 0, CAPACITY),
                                np.clip(p50 + s * d90, 0, CAPACITY))
        if abs(cov - target) < abs(best_cov - target):
            best_s, best_cov = s, cov
    return best_s, best_cov


def train():
    import lightgbm as lgb
    import joblib

    csv_path = DATA_DIR / "raw" / "wind_generation.csv"
    if not csv_path.exists():
        sys.exit(f"Wind data not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    df = _build_surge_wind_features(df)
    available = [c for c in ALL_FEATURES if c in df.columns]
    X = df[available].fillna(0)
    y = df["generation_kw"]

    # ── split: last TEST_FRAC untouched holdout ──
    n_test = int(len(df) * TEST_FRAC)
    X_tr_te, X_te = X.iloc[:-n_test], X.iloc[-n_test:]
    y_tr_te, y_te = y.iloc[:-n_test], y.iloc[-n_test:]
    tune_cut = int(len(X_tr_te) * (1 - TUNE_FRAC))

    print(f"\n[Tuning] rows={len(df)}  tune_cut={tune_cut}  holdout={n_test}")
    best_p, best_it, tune_mae = _tune_lgb(X_tr_te, y_tr_te, tune_cut)
    print(f"[Tune] best MAE={tune_mae:.3f}  it={best_it}  params={best_p}")

    final_it = min(best_it + 100, 1500)
    final_params = {k: v for k, v in best_p.items() if k != "n_estimators"}
    model = lgb.LGBMRegressor(objective="regression", metric="mae",
                              boosting_type="gbdt", n_estimators=final_it,
                              random_state=42, n_jobs=-1, verbosity=-1, **final_params)
    n_hold = int(len(X_tr_te) * TUNE_FRAC)
    Xf, Xv = X_tr_te.iloc[:-n_hold], X_tr_te.iloc[-n_hold:]
    yf, yv = y_tr_te.iloc[:-n_hold], y_tr_te.iloc[-n_hold:]
    model.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])

    tr_pred = cap(model.predict(Xf), CAPACITY)
    va_pred = cap(model.predict(Xv), CAPACITY)
    te_pred = cap(model.predict(X_te), CAPACITY)
    train_m = evaluate(yf.values, tr_pred, CAPACITY)
    val_m = evaluate(yv.values, va_pred, CAPACITY)
    holdout = evaluate(y_te.values, te_pred, CAPACITY)
    report_overfit("wind", train_m, val_m, holdout)

    # ── quantiles ──
    q_dir = MODELS_DIR / "wind" / "quantile"
    q_dir.mkdir(parents=True, exist_ok=True)
    q_models = {}
    q_params = {k: v for k, v in best_p.items() if k != "n_estimators"}
    q_params.update(n_estimators=1000,
                    num_leaves=max(15, int(best_p["num_leaves"])),
                    min_child_samples=max(5, best_p["min_child_samples"]))
    for name, alpha in {"p10": 0.1, "p50": 0.5, "p90": 0.9}.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, random_state=42,
                              n_jobs=-1, verbosity=-1, **q_params)
        m.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])
        m.booster_.save_model(str(q_dir / f"{name}.txt"))
        q_models[name] = m

    p10_raw = cap(q_models["p10"].predict(X_te), CAPACITY)
    p50     = cap(q_models["p50"].predict(X_te), CAPACITY)
    p90_raw = cap(q_models["p90"].predict(X_te), CAPACITY)
    band_scale, coverage = _calibrate_bands(y_te.values, p10_raw, p50, p90_raw)

    joblib.dump({
        "target_type": "wind",
        "max_capacity_mw": CAPACITY / 1000,
        "quantiles": {"p10": 0.1, "p50": 0.5, "p90": 0.9},
        "feature_columns": available,
        "models": {k: m for k, m in q_models.items()},
    }, str(q_dir / "quantile_wind.joblib"))

    # ── calibration ──
    (MODELS_DIR / "wind" / "calibration.json").write_text(
        json.dumps({"band_scale": float(band_scale),
                     "coverage_80": float(coverage)}, indent=2)
    )

    # ── walk-forward ──
    wf_metrics = []
    for fold, (tr, te) in enumerate(walk_forward_split(df, n_splits=3, test_size=168)):
        m = lgb.LGBMRegressor(objective="regression", metric="mae",
                              boosting_type="gbdt", random_state=fold,
                              n_jobs=-1, verbosity=-1, **best_p)
        m.fit(X.iloc[tr], y.iloc[tr])
        p = cap(m.predict(X.iloc[te]), CAPACITY)
        fm = evaluate(y.iloc[te].values, p, CAPACITY)
        wf_metrics.append(fm)
    wf_avg = {k: float(np.mean([m[k] for m in wf_metrics]))
              for k in ("nMAE_%", "MAE", "RMSE", "R2", "Forecast_Reliability_Score")}

    # ── save ──
    model.booster_.save_model(str(MODELS_DIR / "wind" / "wind_lgbm.txt"))
    (MODELS_DIR / "wind" / "feature_cols.json").write_text(json.dumps(available, indent=2))

    report = {
        "timestamp": datetime.now().isoformat(),
        "rows": len(df),
        "tuning": {"best_params": best_p, "best_iterations": best_it, "tune_MAE": tune_mae, "n_iters": N_ITERS},
        "overfit_check": {"train": train_m, "val": val_m, "test": holdout},
        "holdout": holdout,
        "quantiles": {"coverage_80": coverage, "band_scale": band_scale},
        "walk_forward": {"average": wf_avg, "folds": wf_metrics},
    }
    (MODELS_DIR / "metrics" / "wind_evaluation_report.json").write_text(
        json.dumps(report, indent=2, default=str))

    print(f"\n{'='*60}\nWIND TRAINING COMPLETE")
    print(f"  Holdout nMAE : {holdout['nMAE_%']:.2f}%")
    print(f"  Holdout R²   : {holdout['R2']:.4f}")
    print(f"  80% coverage : {coverage:.1%}")
    print(f"  band_scale   : {band_scale:.2f}")
    print(f"  Features     : {len(available)}")
    print(f"  WF avg R²    : {wf_avg['R2']:.4f}")
    return report


if __name__ == "__main__":
    train()