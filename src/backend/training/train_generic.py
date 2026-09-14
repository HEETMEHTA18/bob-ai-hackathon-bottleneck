"""
GENERIC multi-site, climate-aware training for Bottleneck SURGE.

The point of this trainer: replace the site-specialist models (trained only on
Bhadla/Jaisalmer) with models that are *generic across climate and geometry*.

Key design decisions:
  1. MULTI-SITE TRAINING — one shared point model + quantile trio trained on
     several real sites spanning very different climates (desert, coastal,
     humid highlands, cold high-altitude).
  2. SITE-CONTEXT FEATURES — latitude, |latitude|, longitude, elevation,
     surface_tilt, surface_azimuth are added as features so the model can
     *interpolate* climate/geometry, not memorise site ids.  No categorical
     site id is fed to the trees.
  3. GENUINE GENERALIZATION TEST — one whole site is held out of training
     entirely (solar: Leh; wind: Coimbatore).  Metrics on it prove whether the
     model really transfers to a climate it never saw.
  4. PHYSICS BIAS IS LEARNED — raw pvlib physics (no per-site bias multiplier)
     is used as a feature for the generic model; the trees learn the
     site-to-plant mismatch from the context features, removing the need for a
     hand-fit bias at serving time.
  5. CONFORMAL CALIBRATION (CQR) — after quantile fitting, a symmetric
     conformity margin is learned on a calibration slice and added to the
     P10/P90 bands, giving *guaranteed* ~1-alpha coverage (fixes solar's
     empirical-80%≈65% shortfall).

Outputs (never overwrite the specialist models):
  models/generic_solar/{solar_generic.json, feature_cols.json, quantile/*, calibration.json}
  models/generic_wind/{wind_generic.txt, feature_cols.json, quantile/*, calibration.json}
  models/metrics/generic_eval.json
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

from backend.forecasting.inference import (
    _build_surge_solar_features, _build_surge_wind_features,
    _apply_solar_physics, _apply_wind_physics, _enforce_monotonicity,
)
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import validate_coverage
from backend.training.tune_utils import cap, report_overfit

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR   = Path(__file__).parent.parent.parent / "data" / "raw"

CAPACITY_KW = 100.0

# Solar sites: real climate diversity.  Holdout=False → trains; True → never seen.
SOLAR_SITES = [
    {"name": "bhadla",     "lat": 27.5667, "lon": 72.0667, "elev": 210.0,
     "tilt": 26, "az": 180, "csv": "solar_generation.csv",       "holdout": False},
    {"name": "chennai",    "lat": 13.0827, "lon": 80.2700, "elev": 6.0,
     "tilt": 26, "az": 180, "csv": "solar_2024_chennai.csv",     "holdout": False},
    {"name": "bengaluru",  "lat": 12.9716, "lon": 77.5946, "elev": 920.0,
     "tilt": 20, "az": 180, "csv": "solar_2024_bengaluru.csv",   "holdout": False},
    {"name": "leh",        "lat": 34.1526, "lon": 77.5771, "elev": 3500.0,
     "tilt": 30, "az": 180, "csv": "solar_2024_leh.csv",         "holdout": True},
]

# Wind sites.  Holdout → Coimbatore (never trained on).
WIND_SITES = [
    {"name": "jaisalmer",   "lat": 26.9157, "lon": 70.9083, "elev": 225.0,
     "csv": "wind_generation.csv",            "holdout": False},
    {"name": "kanyakumari", "lat": 8.0883,   "lon": 77.5385, "elev": 0.0,
     "csv": "wind_2024_kanyakumari.csv",      "holdout": False},
    {"name": "satara",      "lat": 17.6860,  "lon": 74.0187, "elev": 700.0,
     "csv": "wind_2024_satara.csv",           "holdout": False},
    {"name": "coimbatore",  "lat": 11.0168,  "lon": 76.9558, "elev": 411.0,
     "csv": "wind_2024_coimbatore.csv",       "holdout": True},
]

SOLAR_CTX = ["latitude", "abs_latitude", "longitude", "elevation_m",
             "surface_tilt", "surface_azimuth"]
WIND_CTX = ["latitude", "abs_latitude", "longitude", "elevation_m"]

ALPHA = 0.20  # conformal target: 80% coverage


# ── Dataset loading ────────────────────────────────────────────
def _add_context(df, site, keys):
    """Add site-context features that don't already exist in the frame."""
    vals = {
        "latitude": site["lat"], "abs_latitude": abs(site["lat"]),
        "longitude": site["lon"], "elevation_m": site["elev"],
        "surface_tilt": site.get("tilt", 0.0), "surface_azimuth": site.get("az", 0.0),
    }
    for k in keys:
        if k not in df.columns:
            df[k] = vals[k]
    return df


def _load_solar(site) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / site["csv"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = _build_surge_solar_features(df, site["lat"], site["lon"],
                                     100.0, site["elev"], site["tilt"], site["az"])
    return _add_context(df, site, SOLAR_CTX)


def _load_wind(site) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / site["csv"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = _build_surge_wind_features(df, 100.0)
    return _add_context(df, site, WIND_CTX)


def _chronological_split(df, train_frac=0.70, val_frac=0.15):
    """Per-site chronological split: train | val | test (no shuffle)."""
    n = len(df)
    tr = df.iloc[: int(n * train_frac)].copy()
    va = df.iloc[int(n * train_frac): int(n * (train_frac + val_frac))].copy()
    te = df.iloc[int(n * (train_frac + val_frac)):].copy()
    return tr, va, te


# ── Conformal (CQR) ────────────────────────────────────────────
def conformal_margin(p10: np.ndarray, p90: np.ndarray, y: np.ndarray, alpha=ALPHA):
    """Symmetric CQR margin: E=max(q_lo-y, y-q_hi), margin=quantile(1-alpha)."""
    e = np.maximum(p10 - y, y - p90)
    n = len(e)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    k = min(k, n)
    return float(np.sort(e)[k - 1])


# ── Training ───────────────────────────────────────────────────
def _pick_point_features(df):
    """Use columns ordered as inference will: start from the SURGE columns that
    exist in the frame, then append site-context columns."""
    drop = {"timestamp", "generation_kw", "capacity_kw",
            "ghi", "dni", "dhi", "temp_air", "wind_speed",
            "humidity", "pressure", "wind_direction", "temperature",
            "rated_capacity_kw", "turbine_rated_capacity_kw"}
    return [c for c in df.columns if c not in drop]


def train_solar():
    import xgboost as xgb
    import lightgbm as lgb
    import joblib

    train_sites = [s for s in SOLAR_SITES if not s["holdout"]]
    hold_sites = [s for s in SOLAR_SITES if s["holdout"]]

    frames_tr, frames_va, frames_te = [], [], []
    for site in train_sites:
        df = _load_solar(site)
        tr, va, te = _chronological_split(df)
        print(f"[solar:{site['name']}] rows={len(df)}  "
              f"train={len(tr)} val={len(va)} test={len(te)}")
        frames_tr.append(tr); frames_va.append(va); frames_te.append(te)

    def _df(fs):  # merge feature columns
        out = pd.concat(fs, ignore_index=True)
        return out

    Xf, yf = _df(frames_tr).drop(columns=["generation_kw"]), _df(frames_tr)["generation_kw"]
    Xv, yv = _df(frames_va).drop(columns=["generation_kw"]), _df(frames_va)["generation_kw"]
    Xte, yte = _df(frames_te).drop(columns=["generation_kw"]), _df(frames_te)["generation_kw"]

    feats = _pick_point_features(Xf)
    cols = [c for c in feats if c in Xf.columns]
    Xf, Xv, Xte = Xf[cols], Xv[cols], Xte[cols]
    print(f"[solar] features={len(cols)}")

    # point model (tuned-enough XGBoost with early stopping vs val)
    params = dict(max_depth=7, learning_rate=0.03, colsample_bytree=0.8,
                  subsample=0.9, min_child_weight=8, reg_lambda=5.0,
                  n_estimators=2000, tree_method="hist", random_state=42,
                  n_jobs=-1, verbosity=0, early_stopping_rounds=80)
    model = xgb.XGBRegressor(objective="reg:squarederror", **params)
    model.fit(Xf, yf, eval_set=[(Xv, yv)], verbose=False)
    best_it = getattr(model, "best_iteration", None) or 2000

    tr_p = cap(model.predict(Xf), CAPACITY_KW)
    va_p = cap(model.predict(Xv), CAPACITY_KW)
    te_p = cap(model.predict(Xte), CAPACITY_KW)
    train_m = evaluate(yf.values, tr_p, CAPACITY_KW)
    val_m = evaluate(yv.values, va_p, CAPACITY_KW)
    holdout = evaluate(yte.values, te_p, CAPACITY_KW)
    report_overfit("generic_solar", train_m, val_m, holdout)

    # quantile trio (LightGBM, early stop vs val)
    q_models = {}
    for name, alpha in {"p10": 0.1, "p50": 0.5, "p90": 0.9}.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha,
                              num_leaves=31, learning_rate=0.05,
                              n_estimators=1000, colsample_bytree=0.8,
                              subsample=0.9, min_child_samples=30, random_state=42,
                              n_jobs=-1, verbosity=-1)
        m.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])
        q_models[name] = m

    # physics gating + monotonicity on val & test
    def _bands(X):
        p10 = cap(q_models["p10"].predict(X), CAPACITY_KW)
        p50 = cap(q_models["p50"].predict(X), CAPACITY_KW)
        p90 = cap(q_models["p90"].predict(X), CAPACITY_KW)
        return _enforce_monotonicity(p10, p50, p90)

    def _gate(asset, X, p):
        if asset == "solar":
            return _apply_solar_physics(p, X, CAPACITY_KW)
        return _apply_wind_physics(p, X, CAPACITY_KW)

    p10v, p50v, p90v = _bands(Xv)
    p10t, p50t, p90t = _bands(Xte)
    p10v, p50v, p90v = _gate("solar", Xv, p10v), _gate("solar", Xv, p50v), _gate("solar", Xv, p90v)
    p10t, p50t, p90t = _gate("solar", Xte, p10t), _gate("solar", Xte, p50t), _gate("solar", Xte, p90t)
    p10v, p50v, p90v = _enforce_monotonicity(p10v, p50v, p90v)
    p10t, p50t, p90t = _enforce_monotonicity(p10t, p50t, p90t)

    # band scaling (old) + conformal margin (new)
    best_s, best_cov = 1.0, validate_coverage(yv.values, p10v, p90v)
    for s in np.arange(0.4, 5.0, 0.05):
        cov = validate_coverage(yv.values,
                                np.clip(p50v - s * np.clip(p50v - p10v, 1e-6, None), 0, CAPACITY_KW),
                                np.clip(p50v + s * np.clip(p90v - p50v, 1e-6, None), 0, CAPACITY_KW))
        if abs(cov - 0.80) < abs(best_cov - 0.80):
            best_s, best_cov = s, cov
    d10, d90 = np.clip(p50v - p10v, 1e-6, None), np.clip(p90v - p50v, 1e-6, None)
    p10v_s = np.clip(p50v - best_s * d10, 0, CAPACITY_KW)
    p90v_s = np.clip(p50v + best_s * d90, 0, CAPACITY_KW)
    margin = conformal_margin(p10v_s, p90v_s, yv.values)

    # apply to test
    d10t, d90t = np.clip(p50t - p10t, 1e-6, None), np.clip(p90t - p50t, 1e-6, None)
    p10t_b = np.clip(p50t - best_s * d10t - margin, 0, CAPACITY_KW)
    p90t_b = np.clip(p50t + best_s * d90t + margin, 0, CAPACITY_KW)
    p10t_b, p50t, p90t_b = _enforce_monotonicity(p10t_b, p50t, p90t_b)
    coverage_test = validate_coverage(yte.values, p10t_b, p90t_b)
    wink = np.mean((p90t_b - p10t_b) + (2/0.20) * (p10t_b - yte.values) * (yte.values < p10t_b)
                   + (2/0.20) * (yte.values - p90t_b) * (yte.values > p90t_b))

    # aggregate generic test-frame bands (for JSON)
    def _f(x): return float(np.mean(x))

    # ── save ──
    out_dir = MODELS_DIR / "generic_solar"
    (out_dir / "quantile").mkdir(parents=True, exist_ok=True)
    model.save_model(str(out_dir / "solar_generic.json"))
    (out_dir / "feature_cols.json").write_text(json.dumps(cols, indent=2))
    joblib.dump({
        "target_type": "solar", "max_capacity_mw": CAPACITY_KW / 1000,
        "quantiles": {"p10": 0.1, "p50": 0.5, "p90": 0.9},
        "feature_columns": cols,
        "models": q_models,
    }, str(out_dir / "quantile" / "quantile_solar_generic.joblib"))
    (out_dir / "calibration.json").write_text(json.dumps({
        "band_scale": float(best_s), "coverage_calib": float(best_cov),
        "cqr_margin_kw": margin, "target_coverage": 0.80, "physics_bias_scale": 1.0,
    }, indent=2))

    # held-out-site (Leh) evaluation
    leh = _load_solar(hold_sites[0])
    leh_X = leh[cols]
    leh_y = leh["generation_kw"].values
    leh_p50 = cap(model.predict(leh_X), CAPACITY_KW)
    leh_metrics = evaluate(leh_y, leh_p50, CAPACITY_KW)
    lp10, lp50, lp90 = _bands(leh_X)
    lp10, lp50, lp90 = _gate("solar", leh_X, lp10), _gate("solar", leh_X, lp50), _gate("solar", leh_X, lp90)
    lp10, lp50, lp90 = _enforce_monotonicity(lp10, lp50, lp90)
    dl10, dl90 = np.clip(lp50 - lp10, 1e-6, None), np.clip(lp90 - lp50, 1e-6, None)
    lp10b = np.clip(lp50 - best_s * dl10 - margin, 0, CAPACITY_KW)
    lp90b = np.clip(lp50 + best_s * dl90 + margin, 0, CAPACITY_KW)
    leh_cov = validate_coverage(leh_y, lp10b, lp90b)
    print(f"[solar:LEH holdout-site] MAE={leh_metrics['MAE']:.3f} R²={leh_metrics['R2']:.4f} "
          f"cov80={leh_cov:.3f}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "type": "generic_multi_site_solar",
        "train_sites": [s["name"] for s in train_sites],
        "holdout_site": hold_sites[0]["name"],
        "rows": {"train": len(Xf), "val": len(Xv), "test": len(Xte),
                 "heldout_site": len(leh)},
        "features": cols,
        "overfit_check": {"train": train_m, "val": val_m, "test": holdout},
        "holdout": holdout,
        "quantiles": {"coverage_80_test": coverage_test, "winkler_80": _f(wink),
                      "band_scale": float(best_s), "cqr_margin_kw": margin,
                      "nMAE_p50_%": _f(np.abs(yte.values - p50t)) / CAPACITY_KW * 100},
        "heldout_site_metrics": leh_metrics,
        "heldout_site_coverage_80": leh_cov,
    }
    (MODELS_DIR / "metrics" / "generic_solar_eval.json").write_text(
        json.dumps(report, indent=2, default=str))
    print(f"=== SOLAR GENERIC DONE === holdout R²={holdout['R2']:.4f} "
          f"MAE={holdout['MAE']:.3f} cov80(test)={coverage_test:.3f}")
    return report


def train_wind():
    import lightgbm as lgb
    import joblib

    train_sites = [s for s in WIND_SITES if not s["holdout"]]
    hold_sites = [s for s in WIND_SITES if s["holdout"]]

    frames_tr, frames_va, frames_te = [], [], []
    for site in train_sites:
        df = _load_wind(site)
        tr, va, te = _chronological_split(df)
        print(f"[wind:{site['name']}] rows={len(df)}  "
              f"train={len(tr)} val={len(va)} test={len(te)}")
        frames_tr.append(tr); frames_va.append(va); frames_te.append(te)

    def _df(fs):
        return pd.concat(fs, ignore_index=True)

    Xf, yf = _df(frames_tr).drop(columns=["generation_kw"]), _df(frames_tr)["generation_kw"]
    Xv, yv = _df(frames_va).drop(columns=["generation_kw"]), _df(frames_va)["generation_kw"]
    Xte, yte = _df(frames_te).drop(columns=["generation_kw"]), _df(frames_te)["generation_kw"]

    cols = [c for c in _pick_point_features(Xf) if c in Xf.columns]
    Xf, Xv, Xte = Xf[cols], Xv[cols], Xte[cols]
    print(f"[wind] features={len(cols)}")

    params = dict(objective="regression", metric="mae", boosting_type="gbdt",
                  num_leaves=31, learning_rate=0.05, colsample_bytree=0.8,
                  subsample=0.9, min_child_samples=30, random_state=42,
                  n_estimators=2000, n_jobs=-1, verbosity=-1)
    model = lgb.LGBMRegressor(**params)
    model.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(80), lgb.log_evaluation(0)])

    tr_p = cap(model.predict(Xf), CAPACITY_KW)
    va_p = cap(model.predict(Xv), CAPACITY_KW)
    te_p = cap(model.predict(Xte), CAPACITY_KW)
    train_m = evaluate(yf.values, tr_p, CAPACITY_KW)
    val_m = evaluate(yv.values, va_p, CAPACITY_KW)
    holdout = evaluate(yte.values, te_p, CAPACITY_KW)
    report_overfit("generic_wind", train_m, val_m, holdout)

    q_models = {}
    for name, alpha in {"p10": 0.1, "p50": 0.5, "p90": 0.9}.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha,
                              num_leaves=31, learning_rate=0.05,
                              n_estimators=1000, colsample_bytree=0.8,
                              subsample=0.9, min_child_samples=30, random_state=42,
                              n_jobs=-1, verbosity=-1)
        m.fit(Xf, yf, eval_set=[(Xv, yv)],
              callbacks=[lgb.early_stopping(60), lgb.log_evaluation(0)])
        q_models[name] = m

    def _bands(X):
        p10 = cap(q_models["p10"].predict(X), CAPACITY_KW)
        p50 = cap(q_models["p50"].predict(X), CAPACITY_KW)
        p90 = cap(q_models["p90"].predict(X), CAPACITY_KW)
        return _enforce_monotonicity(p10, p50, p90)

    def _gate(X, p):
        return _apply_wind_physics(p, X, CAPACITY_KW)

    p10v, p50v, p90v = _bands(Xv)
    p10t, p50t, p90t = _bands(Xte)
    p10v, p50v, p90v = _gate(Xv, p10v), _gate(Xv, p50v), _gate(Xv, p90v)
    p10t, p50t, p90t = _gate(Xte, p10t), _gate(Xte, p50t), _gate(Xte, p90t)
    p10v, p50v, p90v = _enforce_monotonicity(p10v, p50v, p90v)
    p10t, p50t, p90t = _enforce_monotonicity(p10t, p50t, p90t)

    best_s, best_cov = 1.0, validate_coverage(yv.values, p10v, p90v)
    for s in np.arange(0.4, 5.0, 0.05):
        cov = validate_coverage(yv.values,
                                np.clip(p50v - s * np.clip(p50v - p10v, 1e-6, None), 0, CAPACITY_KW),
                                np.clip(p50v + s * np.clip(p90v - p50v, 1e-6, None), 0, CAPACITY_KW))
        if abs(cov - 0.80) < abs(best_cov - 0.80):
            best_s, best_cov = s, cov
    d10, d90 = np.clip(p50v - p10v, 1e-6, None), np.clip(p90v - p50v, 1e-6, None)
    p10v_s = np.clip(p50v - best_s * d10, 0, CAPACITY_KW)
    p90v_s = np.clip(p50v + best_s * d90, 0, CAPACITY_KW)
    margin = conformal_margin(p10v_s, p90v_s, yv.values)

    d10t, d90t = np.clip(p50t - p10t, 1e-6, None), np.clip(p90t - p50t, 1e-6, None)
    p10t_b = np.clip(p50t - best_s * d10t - margin, 0, CAPACITY_KW)
    p90t_b = np.clip(p50t + best_s * d90t + margin, 0, CAPACITY_KW)
    p10t_b, p50t, p90t_b = _enforce_monotonicity(p10t_b, p50t, p90t_b)
    coverage_test = validate_coverage(yte.values, p10t_b, p90t_b)
    wink = np.mean((p90t_b - p10t_b) + (2/0.20) * (p10t_b - yte.values) * (yte.values < p10t_b)
                   + (2/0.20) * (yte.values - p90t_b) * (yte.values > p90t_b))

    out_dir = MODELS_DIR / "generic_wind"
    (out_dir / "quantile").mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(out_dir / "wind_generic.txt"))
    (out_dir / "feature_cols.json").write_text(json.dumps(cols, indent=2))
    joblib.dump({
        "target_type": "wind", "max_capacity_mw": CAPACITY_KW / 1000,
        "quantiles": {"p10": 0.1, "p50": 0.5, "p90": 0.9},
        "feature_columns": cols,
        "models": q_models,
    }, str(out_dir / "quantile" / "quantile_wind_generic.joblib"))
    (out_dir / "calibration.json").write_text(json.dumps({
        "band_scale": float(best_s), "coverage_calib": float(best_cov),
        "cqr_margin_kw": margin, "target_coverage": 0.80,
    }, indent=2))

    hold = _load_wind(hold_sites[0])
    hold_X, hold_y = hold[cols], hold["generation_kw"].values
    hold_p50 = cap(model.predict(hold_X), CAPACITY_KW)
    hold_metrics = evaluate(hold_y, hold_p50, CAPACITY_KW)
    hp10, hp50, hp90 = _bands(hold_X)
    hp10, hp50, hp90 = _gate(hold_X, hp10), _gate(hold_X, hp50), _gate(hold_X, hp90)
    hp10, hp50, hp90 = _enforce_monotonicity(hp10, hp50, hp90)
    dh10, dh90 = np.clip(hp50 - hp10, 1e-6, None), np.clip(hp90 - hp50, 1e-6, None)
    hp10b = np.clip(hp50 - best_s * dh10 - margin, 0, CAPACITY_KW)
    hp90b = np.clip(hp50 + best_s * dh90 + margin, 0, CAPACITY_KW)
    hold_cov = validate_coverage(hold_y, hp10b, hp90b)
    print(f"[wind:{hold_sites[0]['name']} holdout-site] MAE={hold_metrics['MAE']:.3f} "
          f"R²={hold_metrics['R2']:.4f} cov80={hold_cov:.3f}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "type": "generic_multi_site_wind",
        "train_sites": [s["name"] for s in train_sites],
        "holdout_site": hold_sites[0]["name"],
        "rows": {"train": len(Xf), "val": len(Xv), "test": len(Xte),
                 "heldout_site": len(hold)},
        "features": cols,
        "overfit_check": {"train": train_m, "val": val_m, "test": holdout},
        "holdout": holdout,
        "quantiles": {"coverage_80_test": coverage_test, "winkler_80": float(wink),
                      "band_scale": float(best_s), "cqr_margin_kw": margin,
                      "nMAE_p50_%": float(np.mean(np.abs(yte.values - p50t))) / CAPACITY_KW * 100},
        "heldout_site_metrics": hold_metrics,
        "heldout_site_coverage_80": hold_cov,
    }
    (MODELS_DIR / "metrics" / "generic_wind_eval.json").write_text(
        json.dumps(report, indent=2, default=str))
    print(f"=== WIND GENERIC DONE === holdout R²={holdout['R2']:.4f} "
          f"MAE={holdout['MAE']:.3f} cov80(test)={coverage_test:.3f}")
    return report


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("solar", "all"):
        train_solar()
    if which in ("wind", "all"):
        train_wind()
    print("\nGENERIC TRAINING COMPLETE")