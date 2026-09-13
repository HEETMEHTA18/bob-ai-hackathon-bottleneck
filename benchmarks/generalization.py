#!/usr/bin/env python3
"""
generalization.py — honest out-of-distribution tests.

The deployed models were trained ONLY on real 2024 weather at Bhadla (solar) and
Jaisalmer (wind).  This script pushes them beyond that:

  in-distribution : last 30% of 2024, same sites   (baseline for contrast)
  cross-year      : ALL of 2023, same sites         (temporal generalization)
  cross-site      : ALL of 2024, DIFFERENT climate  (spatial generalization)
                      solar  -> Chennai (humid/coastal, vs desert Bhadla)
                      wind   -> Kanyakumari (coastal/monsoon, vs desert Jaisalmer)

For each case we report deployed MAE/R2 AND the physics-only + persistence_24h
baselines computed on the SAME window, so a performance drop can be judged
against "how hard is this window anyway".

No model is retrained here — this measures the shipped model as-is.
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.forecasting.inference import (
    predict_solar, predict_wind, _load_solar_calibration,
)
from backend.forecasting.solar import run_physics_model
from backend.forecasting.features import power_curve_estimate

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
MODELS_DIR = ROOT / "models"
CAP = 100.0
BHADLA = (27.5667, 72.0667)
SITE = {"latitude": BHADLA[0], "longitude": BHADLA[1], "altitude": 210,
        "capacity_kw": CAP, "surface_tilt": 26, "surface_azimuth": 180}


def metrics(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    mae = float(np.mean(np.abs(y - p)))
    r2 = float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)) if np.var(y) > 0 else 0.0
    return {"MAE": mae, "nMAE_%": mae / CAP * 100, "R2": r2}


def persistence_24h(y_tr, y_te):
    return np.concatenate([y_tr[-24:], y_te[:-24]])


def load(path):
    df = pd.read_csv(DATA_DIR / path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


# ---------------------------------------------------------------- solar
def test_solar(fname, label):
    df = load(fname)
    if label == "in-distribution":
        df = df.iloc[int(len(df) * 0.7):]
    y = df["generation_kw"].values
    day = df["ghi"].values > 10.0

    out = predict_solar(df.copy(), *BHADLA, CAP)
    p = np.clip(np.asarray(out["p50"]), 0, CAP)

    bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
    phys = np.clip(np.asarray(run_physics_model(df.copy(), SITE)) * bias, 0, CAP)

    y_tr = load("solar_generation.csv")["generation_kw"].values[:int(len(load("solar_generation.csv")) * 0.7)]
    p24 = persistence_24h(y_tr, y)

    return {
        "window": f"{len(df)}h ({label})",
        "site": fname,
        "deployed": metrics(y[day], p[day]),
        "deployed_allhours": metrics(y, p),
        "physics_only": metrics(y[day], phys[day]),
        "persistence_24h": metrics(y[day], p24[day]),
        "daytime_R2_context": "solar R2 reported daytime-only (ghi>10)",
    }


# ---------------------------------------------------------------- wind
def test_wind(fname, label):
    df = load(fname)
    if label == "in-distribution":
        df = df.iloc[int(len(df) * 0.7):]
    y = df["generation_kw"].values

    out = predict_wind(df.copy(), hub_height=80, rated_capacity_kw=CAP)
    p = np.clip(np.asarray(out["p50"]), 0, CAP)

    ws = df["wind_speed"].values
    phys = np.clip(np.array([power_curve_estimate(v) for v in ws]), 0, CAP)

    y_tr = load("wind_generation.csv")["generation_kw"].values[:int(len(load("wind_generation.csv")) * 0.7)]
    p24 = persistence_24h(y_tr, y)

    return {
        "window": f"{len(df)}h ({label})",
        "site": fname,
        "deployed": metrics(y, p),
        "physics_only": metrics(y, phys),
        "persistence_24h": metrics(y, p24),
    }


# ---------------------------------------------------------------- main
def main():
    solar_cases = [
        ("solar_generation.csv", "in-distribution (last 30% of 2024, Bhadla)"),
        ("solar_2023_bhadla.csv", "cross-year (all 2023, Bhadla)"),
        ("solar_2024_chennai.csv", "cross-site (all 2024, Chennai)"),
    ]
    wind_cases = [
        ("wind_generation.csv", "in-distribution (last 30% of 2024, Jaisalmer)"),
        ("wind_2023_jaisalmer.csv", "cross-year (all 2023, Jaisalmer)"),
        ("wind_2024_kanyakumari.csv", "cross-site (all 2024, Kanyakumari)"),
    ]

    results = {"timestamp": datetime.now().isoformat(),
               "note": "Deployed models trained on 2024 Bhadla solar + 2024 Jaisalmer wind only."}
    results["solar"] = {label: test_solar(f, label) for f, label in solar_cases}
    results["wind"] = {label: test_wind(f, label) for f, label in wind_cases}

    out = MODELS_DIR / "metrics" / "generalization.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()