#!/usr/bin/env python3
"""
benchmark.py — Honest external model benchmark

Compares the deployed Bottleneck models (SURGE solar XGBoost + physics, SURGE wind
LightGBM) against standard baseline methods on the SAME out-of-sample window.

Baselines:
  persistence_1h   : forecast(t) = actual(t-1)      (classic short-horizon)
  persistence_24h  : forecast(t) = actual(t-24)     (diel pattern)
  climatology      : hour-of-day mean from training
  naive_mean       : global training mean
  physics_only     : pvlib solar model / IEC power-curve wind (no ML)
  xgb_no_physics   : XGBoost on the same features, WITHOUT physics gating

Metrics: MAE, RMSE, nMAE%, R2 (+ daytime-only for solar).
Significance: Diebold–Mariano test (loss = abs error, HAC variance) comparing
every baseline to the deployed model.  p<0.05 => the deployed model is
significantly better; p>0.95 => significantly worse.

PROCEDURE FAIRNESS: all models are evaluated on the same chronological
out-of-sample window (last `test_frac`).  Baselines that need no training use
only the training window to learn their statistics.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.forecasting.inference import (
    predict_solar, predict_wind, _build_surge_solar_features, _build_surge_wind_features,
    _add_site_context,
    _load_solar_model, _load_wind_model,
)
from backend.forecasting.solar import run_physics_model, persistence_baseline
from backend.forecasting.wind import persistence_baseline_wind
from backend.forecasting.inference import _load_solar_calibration

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
MODELS_DIR = ROOT / "models"
CAPACITY = 100.0
LAT, LON = 27.5667, 72.0667
SITE_PARAMS = {"latitude": LAT, "longitude": LON, "altitude": 210,
               "capacity_kw": CAPACITY, "surface_tilt": 26, "surface_azimuth": 180}


# ------------------------------------------------------------------ metrics
def metrics(y, p, capacity=CAPACITY, day_mask=None):
    p = np.clip(np.asarray(p), 0, capacity)
    y = np.asarray(y)
    if day_mask is not None:
        y, p = y[day_mask], p[day_mask]
    mae = float(np.mean(np.abs(y - p)))
    rmse = float(np.sqrt(np.mean((y - p) ** 2)))
    nmae = 100.0 * mae / capacity
    r2 = float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)) if np.var(y) > 0 else 0.0
    return {"MAE": mae, "RMSE": rmse, "nMAE_%": nmae, "R2": r2}


def diebold_mariano(y, p1, p2):
    """DM test: H0 equal predictive accuracy. Positive stat => model1 better."""
    e1 = np.abs(np.asarray(y) - np.asarray(p1))
    e2 = np.abs(np.asarray(y) - np.asarray(p2))
    d = e2 - e1                      # >0 when model1 (deployed) has smaller error
    T = len(d)
    mean_d = d.mean()
    # Newey-West HAC variance, lag truncation ~ T^(1/3)
    L = int(np.ceil(T ** (1.0 / 3.0)))
    w = [1.0 - l / (L + 1) for l in range(1, L + 1)]
    var = d.var(ddof=1)
    for l in range(1, L + 1):
        cov = np.cov(d[:-l], d[l:])
        var += 2.0 * w[l - 1] * cov[0, 1]
    var = max(var, 1e-12)
    stat = mean_d / np.sqrt(var / T)
    from scipy.stats import norm
    pval = 2 * (1 - norm.cdf(abs(stat)))   # two-sided
    return stat, pval


# ------------------------------------------------------------------ baselines
def persistence_1h(y_train, y_test):
    # needs t-1 actual; first value padded with last train value
    last_train = y_train[-1]
    return np.concatenate([[last_train], y_test[:-1]])


def persistence_24h(y_train, y_test):
    # t-24 actual; for first 24 h of test use the last 24 h of training
    tail = np.concatenate([y_train[-24:], y_test[:-24]])
    return tail


def climatology(y_train, h_train, h_test):
    table = {}
    for hh in range(24):
        sel = h_train == hh
        table[hh] = y_train[sel].mean() if sel.any() else 0.0
    return np.array([table[hh] for hh in h_test])


def naive_mean(y_train, n_test):
    return np.full(n_test, y_train.mean())


# ------------------------------------------------------------------ main
def run_solar():
    df = pd.read_csv(DATA_DIR / "solar_generation.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    split = int(len(df) * 0.7)
    tr, te = df.iloc[:split], df.iloc[split:]

    y_tr = tr["generation_kw"].values
    y_te = te["generation_kw"].values
    h_te = te["timestamp"].dt.hour.values
    day = (te["ghi"].values > 10.0)   # daytime mask for honest solar R2

    feats_tr = _build_surge_solar_features(tr.copy(), LAT, LON)
    feats_te = _build_surge_solar_features(te.copy(), LAT, LON)
    _add_site_context(feats_tr, LAT, LON, 210, 26, 180)
    _add_site_context(feats_te, LAT, LON, 210, 26, 180)
    model, feat_cols = _load_solar_model()

    # deployed SURGE model
    out = predict_solar(te.copy(), LAT, LON, CAPACITY)
    dep = np.array(out["p50"]) if out["p50"] is not None else (
        np.clip(model.predict(feats_te[feat_cols].fillna(0)), 0, CAPACITY))

    # XGBoost without physics gating (pure ML)
    X_te = feats_te[[c for c in feat_cols if c in feats_te.columns]].fillna(0)
    xgb_raw = np.clip(model.predict(X_te), 0, CAPACITY)

    # physics-only pvlib baseline, calibrated to serving (× physics_bias_scale)
    phys_df = te.copy()
    if "temp_air" not in phys_df.columns and "temperature_2m" in phys_df.columns:
        phys_df["temp_air"] = phys_df["temperature_2m"]
    elif "temperature_2m" not in phys_df.columns and "temp_air" in phys_df.columns:
        phys_df["temperature_2m"] = phys_df["temp_air"]
    if "wind_speed_10m" not in phys_df.columns and "wind_speed" in phys_df.columns:
        phys_df["wind_speed_10m"] = phys_df["wind_speed"]
    if "ghi" not in phys_df.columns and "shortwave_radiation" in phys_df.columns:
        phys_df["ghi"] = phys_df["shortwave_radiation"]
    if "dni" not in phys_df.columns and "direct_normal_irradiance" in phys_df.columns:
        phys_df["dni"] = phys_df["direct_normal_irradiance"]
    if "dhi" not in phys_df.columns and "diffuse_radiation" in phys_df.columns:
        phys_df["dhi"] = phys_df["diffuse_radiation"]
    phys_df["temp_air"] = phys_df["temperature_2m"]
    phys_df["wind_speed"] = phys_df["wind_speed_10m"]
    try:
        phys = np.asarray(run_physics_model(phys_df, SITE_PARAMS))
    except Exception:
        phys = np.zeros(len(te))
    bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
    phys = np.clip(phys * bias, 0, CAPACITY)

    # baselines
    p1 = persistence_1h(y_tr, y_te)
    p24 = persistence_24h(y_tr, y_te)
    clim = climatology(y_tr, tr["timestamp"].dt.hour.values, h_te)
    mean = naive_mean(y_tr, len(te))

    rows = [
        ("persistence_1h", p1), ("persistence_24h", p24), ("climatology", clim),
        ("naive_mean", mean), ("physics_only", phys), ("xgb_no_physics", xgb_raw),
        ("deployed_surge", dep),
    ]
    return build_table(rows, y_te, day, saved_report="evaluation_report.json")


def run_wind():
    df = pd.read_csv(DATA_DIR / "wind_generation.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    split = int(len(df) * 0.7)
    tr, te = df.iloc[:split], df.iloc[split:]

    y_tr = tr["generation_kw"].values
    y_te = te["generation_kw"].values

    model, feat_cols = _load_wind_model()
    out = predict_wind(te.copy(), hub_height=80, rated_capacity_kw=CAPACITY)
    dep = np.array(out["prediction"]) if "prediction" in out else np.array(out["p50"])

    feats_te = _build_surge_wind_features(te.copy())
    _add_site_context(feats_te, LAT, LON, 225, 0, 0)
    X_te = feats_te[[c for c in feat_cols if c in feats_te.columns]].fillna(0)
    xgb_raw = np.clip(model.predict(X_te), 0, CAPACITY)

    # IEC power-curve physics baseline (returns kW at rated capacity)
    from backend.forecasting.features import power_curve_estimate
    ws = te["wind_speed"].values
    phys = np.clip(np.array([power_curve_estimate(v) for v in ws]), 0, CAPACITY)

    p1 = persistence_1h(y_tr, y_te)
    p24 = persistence_24h(y_tr, y_te)
    h_tr = tr["timestamp"].dt.hour.values
    h_te = te["timestamp"].dt.hour.values
    clim = climatology(y_tr, h_tr, h_te)
    mean = naive_mean(y_tr, len(te))

    rows = [
        ("persistence_1h", p1), ("persistence_24h", p24), ("climatology", clim),
        ("naive_mean", mean), ("physics_only", phys), ("xgb_no_physics", xgb_raw),
        ("deployed_surge", dep),
    ]
    return build_table(rows, y_te, None, saved_report="wind_evaluation_report.json")


def build_table(rows, y_test, day_mask, saved_report):
    results = {}
    dep_pred = None
    for name, pred in rows:
        pred = np.asarray(pred, dtype=float)
        if pred.shape[0] != len(y_test):
            pred = pred[:len(y_test)]
        m = metrics(y_test, pred, day_mask=day_mask)
        if name == "deployed_surge":
            dep_pred = pred
            m_all = metrics(y_test, pred, day_mask=None)
        results[name] = m

    # DM test vs deployed
    dms = {}
    for name, pred in rows:
        if name == "deployed_surge":
            dms[name] = {"stat": np.nan, "p_value": np.nan}
            continue
        pred = np.asarray(pred, dtype=float)[:len(y_test)]
        stat, pval = diebold_mariano(y_test, dep_pred, pred)
        dms[name] = {"stat": round(float(stat), 3), "p_value": round(float(pval), 4)}

    report = {
        "timestamp": datetime.now().isoformat(),
        "asset": saved_report.split("_")[0],
        "capacity_kw": CAPACITY,
        "test_window": f"{len(y_test)}h (last 30%, chronological)",
        "daytime_only_note": "solar R2 reported daytime-only (ghi>10); full-window R2 shown as all_R2"
                             if day_mask is not None else None,
        "metrics_by_model": results,
        "diebold_mariano_vs_deployed": dms,
        "interpretation": (
            "DM stat > 0 with p<0.05 => deployed significantly BETTER than baseline; "
            "p>0.95 => deployed significantly WORSE; 0.05<p<0.95 => no significant difference."
        ),
    }
    save = MODELS_DIR / "metrics" / f"benchmark_{'solar' if day_mask is not None else 'wind'}.json"
    save.write_text(json.dumps(report, indent=2))

    print(f"\n{'='*72}\n  {report['asset'].upper()} — out-of-sample comparison\n{'='*72}")
    hdr = f"{'model':<20}{'MAE':>9}{'RMSE':>9}{'nMAE%':>8}{'R2':>9}   DM-stat{'DM-p':>9}"
    print(hdr)
    print("-" * len(hdr))
    for name, m in results.items():
        dm = dms[name]
        flag = ""
        if name != "deployed_surge":
            if dm["p_value"] < 0.05 and dm["stat"] > 0:
                flag = "   deployed BEST*"
            elif dm["p_value"] < 0.05:
                flag = "   baseline better*"
        print(f"{name:<20}{m['MAE']:>9.2f}{m['RMSE']:>9.2f}{m['nMAE_%']:>8.2f}{m['R2']:>9.4f}"
              f"   {dm['stat']:+7.3f}{dm['p_value']:>9.4f} {flag}")
    print("* p<0.05 (Diebold–Mariano vs deployed)")
    print(f"Saved: {save}")
    return report


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("solar", "all"):
        run_solar()
    if which in ("wind", "all"):
        run_wind()