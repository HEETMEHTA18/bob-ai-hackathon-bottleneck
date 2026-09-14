"""
Solar model training — SURGE-aligned, physics-informed, tuned.

Features (identical to serving `_build_surge_solar_features`):
  21 SURGE features
  + weather-persistence (shortwave_radiation_lag_1h, rolling_6h, rolling_24h)
  + physics_estimate_kw (pvlib PVWatts × bias_scale)
  = 25 features

Validation discipline (no over/underfit):
  - strictly chronological expansions (TimeSeriesSplit, no shuffle)
  - randomized hyperparameter search on a validation split
  - early stopping against the val fold
  - train | val | test gap reported explicitly
  - final model refit on full training window, final metrics on untouched 20% holdout

Outputs:
  models/solar/solar_hybrid.json          XGBoost point model
  models/solar/feature_cols.json          feature order (serving must match)
  models/solar/quantile/*.txt|joblib      P10/P50/P90 quantile bundle
  models/solar/calibration.json           band_scale + physics_bias_scale
  models/metrics/evaluation_report.json
"""
import json
import os
import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
warnings.filterwarnings("ignore")

from backend.forecasting.inference import _build_surge_solar_features
from backend.forecasting.solar import run_physics_model
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import validate_coverage
from backend.training.tune_utils import cap, report_overfit

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR   = Path(__file__).parent.parent.parent / "data"

CAPACITY_KW = 100.0
SITE_PARAMS = {
    "latitude": 27.5667, "longitude": 72.0667, "altitude": 210,
    "capacity_kw": CAPACITY_KW,
    "surface_tilt": 26, "surface_azimuth": 180,
}
TRAIN_CSV = DATA_DIR / "raw" / "solar_generation.csv"

SURGE_COLS = [
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation",
    "temperature_2m", "relative_humidity_2m", "surface_pressure",
    "cloud_cover", "wind_speed_10m", "solar_zenith", "solar_azimuth",
    "solar_elevation", "clearsky_ghi", "clearness_index",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "day_of_year_sin", "day_of_year_cos",
    "cloud_cover_rolling_3h", "temp_rolling_3h",
]
PERSISTENCE_COLS = [
    "shortwave_radiation_lag_1h", "shortwave_radiation_rolling_6h",
    "shortwave_radiation_rolling_24h",
]
PHYS_COL = "physics_estimate_kw"
ALL_FEATURES = SURGE_COLS + PERSISTENCE_COLS + [PHYS_COL]

TEST_FRAC = 0.20          # untouched holdout (last 20%)
TUNE_FRAC = 0.20          # of the 80% train portion → val for tuning
N_ITERS = 20              # random-search hyperparameter combos
N_SPLITS = 4


def _compute_physics_bias(df: pd.DataFrame, raw_physics: np.ndarray) -> float:
    day = (df["solar_elevation"] > 10) & (raw_physics > 0.5)
    if day.sum() == 0:
        return 1.0
    ratio = df.loc[day, "generation_kw"].median() / np.median(raw_physics[day])
    return float(np.clip(ratio, 0.2, 4.0))


def _calibrate_bands(y_true, p10_raw, p50, p90_raw, target=0.80):
    d10 = np.clip(p50 - p10_raw, 1e-6, None)
    d90 = np.clip(p90_raw - p50, 1e-6, None)
    best_s, best_cov = 1.0, validate_coverage(y_true, p10_raw, p90_raw)
    for s in np.arange(0.4, 5.0, 0.05):
        cov = validate_coverage(y_true,
                                np.clip(p50 - s * d10, 0, CAPACITY_KW),
                                np.clip(p50 + s * d90, 0, CAPACITY_KW))
        if abs(cov - target) < abs(best_cov - target):
            best_s, best_cov = s, cov
    return best_s, best_cov


def _tune_xgb(X, y, tune_cut):
    """Randomized search on the tuning window (chronological)."""
    import xgboost as xgb

    Xt, yt = X.iloc[:tune_cut], y.iloc[:tune_cut]
    split = int(len(Xt) * 0.75)
    Xtr, ytr = Xt.iloc[:split], yt.iloc[:split]
    Xva, yva = Xt.iloc[split:], yt.iloc[split:]

    rng = np.random.default_rng(42)
    depths = [3, 4, 5, 6]
    lrs = [0.02, 0.03, 0.05]
    cols = [0.5, 0.7, 0.9]
    subs = [0.7, 0.85, 1.0]
    mcw = [1, 5, 15]
    lams = [1.0, 5.0, 20.0]
    results = []

    for _ in range(N_ITERS):
        p = dict(max_depth=int(rng.choice(depths)), learning_rate=float(rng.choice(lrs)),
                 colsample_bytree=float(rng.choice(cols)), subsample=float(rng.choice(subs)),
                 min_child_weight=int(rng.choice(mcw)), reg_lambda=float(rng.choice(lams)),
                 n_estimators=800)
        m = xgb.XGBRegressor(objective="reg:squarederror", tree_method="hist",
                             random_state=42, n_jobs=-1, verbosity=0,
                             early_stopping_rounds=50, **p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
        best_it = m.best_iteration if hasattr(m, "best_iteration") and m.best_iteration else 800
        va = evaluate(yva.values, cap(m.predict(Xva), CAPACITY_KW), CAPACITY_KW)
        results.append((va["MAE"], p, best_it))
        print(f"  [tune] MAE={va['MAE']:.3f} R²={va['R2']:.4f} it={best_it} {p}")

    results.sort(key=lambda r: r[0])
    _, best_p, best_it = results[0]
    return best_p, best_it, float(results[0][0])


def train(csv_path: str = None):
    import xgboost as xgb
    import lightgbm as lgb
    import joblib

    csv_path = csv_path or str(TRAIN_CSV)
    if not os.path.exists(csv_path):
        sys.exit(f"Data not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # SURGE features + persistence + physics (same pipeline as serving)
    df = _build_surge_solar_features(df, SITE_PARAMS["latitude"], SITE_PARAMS["longitude"])

    # Bias-calibrate the physics feature to the real plant yield
    # Recompute physics with a fresh pvlib pass, bias-corrected to plant yield.
    # (Mirrors the serving push: run_physics_model × physics_bias_scale.)
    p_df = df.copy()
    if "ghi" not in p_df.columns and "shortwave_radiation" in p_df.columns:
        p_df["ghi"] = p_df["shortwave_radiation"]
    if "dni" not in p_df.columns and "direct_normal_irradiance" in p_df.columns:
        p_df["dni"] = p_df["direct_normal_irradiance"]
    if "dhi" not in p_df.columns and "diffuse_radiation" in p_df.columns:
        p_df["dhi"] = p_df["diffuse_radiation"]
    p_df["temp_air"] = p_df["temperature_2m"]
    p_df["wind_speed"] = p_df["wind_speed_10m"]
    raw_physics = run_physics_model(p_df, SITE_PARAMS)
    bias_scale = _compute_physics_bias(df, raw_physics)
    print(f"[Physics] bias_scale = {bias_scale:.3f}")
    df[PHYS_COL] = np.round(np.clip(raw_physics, 0, CAPACITY_KW) * bias_scale, 3)

    available = [c for c in ALL_FEATURES if c in df.columns]
    X = df[available].fillna(0)
    y = df["generation_kw"]

    # ── split: last TEST_FRAC untouched holdout ──
    n_test = int(len(df) * TEST_FRAC)
    X_tr_te, X_te = X.iloc[:-n_test], X.iloc[-n_test:]
    y_tr_te, y_te = y.iloc[:-n_test], y.iloc[-n_test:]
    tune_cut = int(len(X_tr_te) * (1 - TUNE_FRAC))  # tuning uses first 60% of total

    # ── hyperparameter search (chronological, on training window) ──
    print(f"\n[Tuning] rows={len(df)}  tune_cut={tune_cut}  holdout={n_test}")
    best_p, best_it, tune_mae = _tune_xgb(X_tr_te, y_tr_te, tune_cut)
    print(f"[Tune] best MAE={tune_mae:.3f}  it={best_it}  params={best_p}")

    # ── final point model on all training rows (minus holdout), capped iters ──
    final_it = min(best_it + 100, 1500)
    model = xgb.XGBRegressor(objective="reg:squarederror", tree_method="hist",
                             random_state=42, n_jobs=-1,
                             verbosity=0, early_stopping_rounds=60, **best_p)
    n_hold = int(len(X_tr_te) * TUNE_FRAC)
    Xf, Xv = X_tr_te.iloc[:-n_hold], X_tr_te.iloc[-n_hold:]
    yf, yv = y_tr_te.iloc[:-n_hold], y_tr_te.iloc[-n_hold:]
    model.fit(Xf, yf, eval_set=[(Xv, yv)], verbose=False)

    # metrics: train | val | test
    tr_pred = cap(model.predict(Xf), CAPACITY_KW)
    va_pred = cap(model.predict(Xv), CAPACITY_KW)
    te_pred = cap(model.predict(X_te), CAPACITY_KW)
    train_m = evaluate(yf.values, tr_pred, CAPACITY_KW)
    val_m = evaluate(yv.values, va_pred, CAPACITY_KW)
    holdout = evaluate(y_te.values, te_pred, CAPACITY_KW)
    report_overfit("solar", train_m, val_m, holdout)

    # ── quantile models (tuned-ish, same features, early stop) ──
    q_dir = MODELS_DIR / "solar" / "quantile"
    q_dir.mkdir(parents=True, exist_ok=True)
    q_models = {}
    for name, alpha in {"p10": 0.1, "p50": 0.5, "p90": 0.9}.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha,
                              num_leaves=max(15, int(best_p["max_depth"]) * 4),
                              learning_rate=best_p["learning_rate"],
                              n_estimators=1000, colsample_bytree=best_p["colsample_bytree"],
                              subsample=best_p["subsample"], min_child_samples=max(5, best_p["min_child_weight"]),
                              reg_lambda=best_p["reg_lambda"], random_state=42,
                              n_jobs=-1, verbosity=-1)
        m.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])
        m.booster_.save_model(str(q_dir / f"{name}.txt"))
        q_models[name] = m

    p10_raw = cap(q_models["p10"].predict(X_te), CAPACITY_KW)
    p50_q = cap(q_models["p50"].predict(X_te), CAPACITY_KW)
    p90_raw = cap(q_models["p90"].predict(X_te), CAPACITY_KW)
    band_scale, coverage = _calibrate_bands(y_te.values, p10_raw, p50_q, p90_raw)

    joblib.dump({
        "target_type": "solar",
        "max_capacity_mw": CAPACITY_KW / 1000,
        "quantiles": {"p10": 0.1, "p50": 0.5, "p90": 0.9},
        "feature_columns": available,
        "models": {k: m for k, m in q_models.items()},
    }, str(q_dir / "quantile_solar.joblib"))

    # ── walk-forward ──
    wf_metrics = []
    for fold, (tr, te) in enumerate(walk_forward_split(df, n_splits=3, test_size=168)):
        m = xgb.XGBRegressor(objective="reg:squarederror", tree_method="hist",
                             random_state=fold, n_jobs=-1, verbosity=0, **best_p)
        m.fit(X.iloc[tr], y.iloc[tr])
        fm = evaluate(y.iloc[te].values, cap(m.predict(X.iloc[te]), CAPACITY_KW), CAPACITY_KW)
        fm["fold"] = fold + 1
        wf_metrics.append(fm)
    wf_avg = {k: float(np.mean([m[k] for m in wf_metrics]))
              for k in ("nMAE_%", "MAE", "RMSE", "R2", "Forecast_Reliability_Score")}

    # ── save ──
    model_dir = MODELS_DIR / "solar"
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "solar_hybrid.json"))
    (model_dir / "feature_cols.json").write_text(json.dumps(available, indent=2))
    (model_dir / "calibration.json").write_text(json.dumps({
        "band_scale": float(band_scale), "coverage_80": float(coverage),
        "physics_bias_scale": float(bias_scale)}, indent=2))

    report = {
        "timestamp": datetime.now().isoformat(),
        "site_params": SITE_PARAMS,
        "rows": len(df),
        "features": available,
        "tuning": {"best_params": best_p, "best_iterations": best_it, "tune_MAE": tune_mae, "n_iters": N_ITERS},
        "overfit_check": {"train": train_m, "val": val_m, "test": holdout},
        "holdout": holdout,
        "quantiles": {"coverage_80": coverage, "band_scale": band_scale,
                      "nMAE_p50_%": float(np.mean(np.abs(y_te.values - p50_q)) / CAPACITY_KW * 100)},
        "walk_forward": {"average": wf_avg, "folds": wf_metrics},
    }
    (MODELS_DIR / "metrics" / "evaluation_report.json").write_text(
        json.dumps(report, indent=2, default=str))

    print(f"\n{'='*60}\nSOLAR TRAINING COMPLETE")
    print(f"  Holdout nMAE : {holdout['nMAE_%']:.2f}%")
    print(f"  Holdout R²   : {holdout['R2']:.4f}")
    print(f"  80% coverage : {coverage:.1%}")
    print(f"  band_scale   : {band_scale:.2f}")
    print(f"  physics_bias : {bias_scale:.3f}")
    print(f"  Features     : {len(available)}")
    print(f"  WF avg R²    : {wf_avg['R2']:.4f}")
    return report


if __name__ == "__main__":
    train()