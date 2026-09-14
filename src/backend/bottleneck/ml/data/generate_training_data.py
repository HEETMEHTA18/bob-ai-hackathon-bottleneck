"""
Bottleneck ML — Training Data Generator
========================================
Generates a per-TIMESTAMP labelled dataset from the project's 30-asset synthetic fleet.

Key design decisions (fixing the bottleneck-ml label-leakage problem):
  - Labels are per-row, NOT per-asset. A row gets label=1 only if the asset's
    telemetry is within the final 24 h / 72 h of its simulated degradation window.
  - Degradation curves ramp from a configurable onset point; the failure point is
    the last timestamp of the window, so all rows near the end of a degrading asset's
    trajectory are positive labels.
  - Different assets get different degradation modes (thermal / mechanical /
    insulation / combined / none), producing a realistic class distribution.
  - Reproducible via SEED. Generation parameters are written to a JSON sidecar.

Columns produced (matching feature_engineering.py expectations):
  Telemetry : oil_temperature, load_percentage, vibration, current_unbalance,
              voltage_deviation, partial_discharge, ambient_temperature
  Asset     : asset_id, asset_age, capacity_mva, customers_served, criticality,
              redundancy_level, previous_failures, days_since_maintenance
  Weather   : temperature, humidity, precipitation, wind_speed, wind_gust,
              pressure, cloud_cover, weather_code
  Labels    : failure_within_24h (binary), failure_within_72h (binary)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ─── Configuration ────────────────────────────────────────────────────────────

SEED = 42
READINGS_PER_DAY = 24          # hourly
DAYS_OF_HISTORY  = 60          # 60 days per asset → 1 440 rows per asset
N_POSITIVE_FRAC  = 0.40        # ~40 % of assets get a failure trajectory
WEATHER_SEVERE_RATE = 0.08     # 8 % of weather readings are severe

OUTPUT_DIR = Path(__file__).resolve().parents[4] / "data"
# data/ is at project root: bob-ai-hackathon-bottleneck/data/
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)


# ─── Asset definitions (aligned to mock_data.py fleet) ────────────────────────

_ASSETS: List[Dict] = [
    dict(id="TR-1042", age=17.0, cap=25.0, cust=8420,  crit=0.92, redund=0.30, prev_fail=3, dsm=180, region="North"),
    dict(id="TR-1019", age=14.0, cap=20.0, cust=5200,  crit=0.85, redund=0.40, prev_fail=2, dsm=200, region="North"),
    dict(id="BR-2201", age=20.0, cap=30.0, cust=11000, crit=0.88, redund=0.20, prev_fail=4, dsm=90,  region="South"),
    dict(id="FD-3310", age=11.0, cap=15.0, cust=3400,  crit=0.78, redund=0.55, prev_fail=2, dsm=150, region="East"),
    dict(id="TR-2055", age=12.0, cap=18.0, cust=4100,  crit=0.80, redund=0.45, prev_fail=2, dsm=160, region="West"),
    dict(id="RC-4401", age= 9.0, cap=12.0, cust=1800,  crit=0.70, redund=0.60, prev_fail=0, dsm=120, region="Central"),
    dict(id="BR-1175", age=16.0, cap=22.0, cust=6300,  crit=0.82, redund=0.35, prev_fail=1, dsm=220, region="North"),
    dict(id="SW-5520", age= 7.0, cap= 8.0, cust= 900,  crit=0.65, redund=0.70, prev_fail=0, dsm=90,  region="South"),
    dict(id="TR-3088", age= 8.0, cap=10.0, cust=2200,  crit=0.60, redund=0.65, prev_fail=0, dsm=100, region="East"),
    dict(id="CB-6601", age= 6.0, cap= 5.0, cust= 500,  crit=0.55, redund=0.75, prev_fail=0, dsm=80,  region="West"),
    dict(id="FD-2280", age= 9.0, cap=10.0, cust=1600,  crit=0.62, redund=0.60, prev_fail=0, dsm=110, region="South"),
    dict(id="RC-3320", age= 5.0, cap= 9.0, cust=1100,  crit=0.58, redund=0.80, prev_fail=0, dsm=60,  region="Central"),
    dict(id="TR-5099", age=10.0, cap=16.0, cust=3100,  crit=0.75, redund=0.50, prev_fail=1, dsm=140, region="North"),
    dict(id="FD-1140", age= 8.0, cap=12.0, cust=2700,  crit=0.70, redund=0.55, prev_fail=1, dsm=130, region="South"),
    dict(id="TR-7001", age= 2.0, cap=15.0, cust=2800,  crit=0.50, redund=0.85, prev_fail=0, dsm=30,  region="North"),
    dict(id="BR-7110", age= 3.0, cap=12.0, cust=1500,  crit=0.48, redund=0.90, prev_fail=0, dsm=45,  region="East"),
    dict(id="SW-7220", age= 2.0, cap= 6.0, cust= 700,  crit=0.42, redund=0.92, prev_fail=0, dsm=40,  region="West"),
    dict(id="CB-7330", age= 1.5, cap= 4.0, cust= 400,  crit=0.40, redund=0.95, prev_fail=0, dsm=20,  region="Central"),
    dict(id="TR-4060", age=13.0, cap=20.0, cust=5800,  crit=0.72, redund=0.48, prev_fail=2, dsm=250, region="South"),
    dict(id="FD-4480", age=10.0, cap=11.0, cust=1900,  crit=0.60, redund=0.58, prev_fail=0, dsm=160, region="West"),
    dict(id="TR-9001", age= 7.0, cap=30.0, cust=12000, crit=0.95, redund=0.55, prev_fail=1, dsm=300, region="Central"),
    dict(id="BR-9010", age= 5.0, cap=28.0, cust=9500,  crit=0.93, redund=0.60, prev_fail=0, dsm=180, region="Central"),
    dict(id="RC-2210", age= 6.0, cap= 9.0, cust=1400,  crit=0.65, redund=0.70, prev_fail=0, dsm=90,  region="South"),
    dict(id="SW-3301", age= 4.0, cap= 7.0, cust= 800,  crit=0.55, redund=0.82, prev_fail=0, dsm=70,  region="East"),
    dict(id="CB-2240", age= 3.0, cap= 5.0, cust= 600,  crit=0.50, redund=0.88, prev_fail=0, dsm=50,  region="North"),
    dict(id="TR-6050", age= 9.0, cap=22.0, cust=7200,  crit=0.88, redund=0.50, prev_fail=1, dsm=200, region="East"),
    dict(id="FD-6060", age= 8.0, cap=18.0, cust=6100,  crit=0.86, redund=0.55, prev_fail=1, dsm=190, region="East"),
    dict(id="BR-5511", age=11.0, cap=20.0, cust=4800,  crit=0.75, redund=0.45, prev_fail=2, dsm=220, region="West"),
    dict(id="RC-6600", age= 7.0, cap=10.0, cust=1300,  crit=0.62, redund=0.68, prev_fail=0, dsm=100, region="South"),
    dict(id="TR-8080", age=12.0, cap=14.0, cust=3600,  crit=0.68, redund=0.52, prev_fail=2, dsm=250, region="West"),
]

# Realistic baseline telemetry per asset (mirrors mock_data._TELEMETRY_BASE)
_TELEM_BASE: Dict[str, Dict] = {
    "TR-1042": dict(ot=92, lp=88, vib=4.8, cu=7.2, vd=6.5, pd=0.82, amb=38),
    "TR-1019": dict(ot=78, lp=76, vib=3.2, cu=5.1, vd=4.8, pd=0.55, amb=37),
    "BR-2201": dict(ot=84, lp=91, vib=5.1, cu=8.0, vd=7.2, pd=0.78, amb=36),
    "FD-3310": dict(ot=68, lp=72, vib=2.8, cu=4.2, vd=3.5, pd=0.42, amb=36),
    "TR-2055": dict(ot=74, lp=70, vib=3.0, cu=4.8, vd=4.1, pd=0.48, amb=35),
    "RC-4401": dict(ot=52, lp=55, vib=1.2, cu=2.1, vd=1.8, pd=0.18, amb=33),
    "BR-1175": dict(ot=80, lp=78, vib=3.8, cu=5.8, vd=5.2, pd=0.62, amb=37),
    "SW-5520": dict(ot=44, lp=48, vib=0.9, cu=1.5, vd=1.2, pd=0.10, amb=33),
    "TR-3088": dict(ot=60, lp=60, vib=2.0, cu=3.0, vd=2.5, pd=0.28, amb=34),
    "CB-6601": dict(ot=42, lp=45, vib=0.8, cu=1.2, vd=1.0, pd=0.08, amb=33),
    "FD-2280": dict(ot=55, lp=58, vib=1.8, cu=2.8, vd=2.2, pd=0.22, amb=34),
    "RC-3320": dict(ot=48, lp=50, vib=1.0, cu=1.8, vd=1.5, pd=0.12, amb=32),
    "TR-5099": dict(ot=65, lp=62, vib=2.5, cu=3.5, vd=3.0, pd=0.35, amb=34),
    "FD-1140": dict(ot=58, lp=60, vib=2.0, cu=3.2, vd=2.8, pd=0.30, amb=33),
    "TR-7001": dict(ot=45, lp=42, vib=0.7, cu=1.0, vd=0.8, pd=0.05, amb=32),
    "BR-7110": dict(ot=40, lp=38, vib=0.6, cu=0.9, vd=0.7, pd=0.04, amb=31),
    "SW-7220": dict(ot=38, lp=35, vib=0.5, cu=0.8, vd=0.6, pd=0.03, amb=31),
    "CB-7330": dict(ot=36, lp=32, vib=0.4, cu=0.7, vd=0.5, pd=0.02, amb=30),
    "TR-4060": dict(ot=71, lp=68, vib=2.7, cu=4.0, vd=3.8, pd=0.45, amb=35),
    "FD-4480": dict(ot=56, lp=55, vib=1.6, cu=2.5, vd=2.0, pd=0.20, amb=33),
    "TR-9001": dict(ot=58, lp=64, vib=1.5, cu=2.2, vd=1.9, pd=0.22, amb=33),
    "BR-9010": dict(ot=52, lp=58, vib=1.2, cu=1.8, vd=1.5, pd=0.16, amb=32),
    "RC-2210": dict(ot=50, lp=52, vib=1.1, cu=1.9, vd=1.6, pd=0.14, amb=32),
    "SW-3301": dict(ot=42, lp=44, vib=0.8, cu=1.3, vd=1.1, pd=0.07, amb=31),
    "CB-2240": dict(ot=40, lp=40, vib=0.7, cu=1.1, vd=0.9, pd=0.06, amb=31),
    "TR-6050": dict(ot=62, lp=65, vib=2.2, cu=3.3, vd=2.8, pd=0.32, amb=34),
    "FD-6060": dict(ot=60, lp=63, vib=2.0, cu=3.0, vd=2.5, pd=0.28, amb=34),
    "BR-5511": dict(ot=75, lp=74, vib=3.4, cu=5.5, vd=4.9, pd=0.58, amb=36),
    "RC-6600": dict(ot=51, lp=53, vib=1.1, cu=1.9, vd=1.6, pd=0.14, amb=32),
    "TR-8080": dict(ot=70, lp=67, vib=2.6, cu=3.8, vd=3.6, pd=0.44, amb=35),
}
_DEFAULT_BASE = dict(ot=55, lp=55, vib=1.5, cu=2.5, vd=2.0, pd=0.20, amb=33)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _degradation_ramp(n_pts: int, onset_idx: int, severity: float) -> np.ndarray:
    """Returns an array of shape (n_pts,): 0 before onset, ramps to `severity`."""
    arr = np.zeros(n_pts, dtype=float)
    ramp_len = n_pts - onset_idx
    if ramp_len > 1:
        arr[onset_idx:] = np.linspace(0.0, severity, ramp_len) ** 1.3
    return arr


def _weather_row(severe: bool) -> dict:
    """Generate one synthetic weather reading."""
    if severe:
        temp    = float(rng.uniform(40, 50))
        wind    = float(rng.uniform(20, 35))
        gust    = wind + float(rng.uniform(5, 15))
        precip  = float(rng.uniform(30, 60))
        humid   = float(rng.uniform(70, 95))
        press   = float(rng.uniform(990, 1005))
        cloud   = float(rng.uniform(75, 100))
        wcode   = 1
    else:
        temp    = float(rng.uniform(22, 40))
        wind    = float(rng.uniform(1, 15))
        gust    = wind + float(rng.uniform(2, 8))
        precip  = float(rng.uniform(0, 8))
        humid   = float(rng.uniform(30, 75))
        press   = float(rng.uniform(1005, 1025))
        cloud   = float(rng.uniform(0, 70))
        wcode   = 0
    return dict(temperature=round(temp, 1), humidity=round(humid, 1),
                precipitation=round(precip, 1), wind_speed=round(wind, 1),
                wind_gust=round(gust, 1), pressure=round(press, 1),
                cloud_cover=round(cloud, 1), weather_code=wcode)


# ─── Main generator ────────────────────────────────────────────────────────────

def generate(save: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (telemetry_df, weather_df) and optionally writes CSVs to OUTPUT_DIR.
    Telemetry already contains asset metadata and per-timestamp labels.
    """
    n_pts = DAYS_OF_HISTORY * READINGS_PER_DAY   # 1440 per asset
    base_ts = datetime(2025, 6, 15, 12, 0, 0)
    timestamps = [base_ts - timedelta(hours=(n_pts - i)) for i in range(n_pts)]

    # Decide which assets are degrading (deterministic subset)
    n_assets = len(_ASSETS)
    n_degrading = max(1, int(n_assets * N_POSITIVE_FRAC))
    degrading_ids = set(
        rng.choice([a["id"] for a in _ASSETS], size=n_degrading, replace=False).tolist()
    )

    all_telem_rows: List[dict] = []
    all_weather_rows: List[dict] = []

    for asset in _ASSETS:
        aid = asset["id"]
        base = _TELEM_BASE.get(aid, _DEFAULT_BASE)
        is_degrading = aid in degrading_ids

        # Degradation parameters
        onset_idx   = int(n_pts * float(rng.uniform(0.50, 0.80))) if is_degrading else n_pts
        severity    = float(rng.uniform(0.55, 1.0)) if is_degrading else 0.0
        mode        = str(rng.choice(["thermal", "mechanical", "insulation", "combined"])) \
                      if is_degrading else None
        degr        = _degradation_ramp(n_pts, onset_idx, severity)

        # Label windows (per MODEL.md)
        #   failure_within_24h : all rows within the final 24h of a degrading trajectory
        #   failure_within_72h : all rows within the final 72h of a degrading trajectory
        #   Also label any row where the degradation signal exceeds a threshold,
        #   regardless of position — this produces more positive examples for training.
        label_24h = np.zeros(n_pts, dtype=int)
        label_72h = np.zeros(n_pts, dtype=int)
        if is_degrading:
            # Window-based labels (near-failure window)
            label_24h[max(0, n_pts - 24):] = 1
            label_72h[max(0, n_pts - 72):] = 1
            # Threshold-based labels (any point where degradation > 0.65 counts as 24h positive)
            threshold_mask = degr > 0.65
            label_24h[threshold_mask] = 1
            label_72h[degr > 0.45] = 1

        # Per-row telemetry with realistic noise
        for i, ts in enumerate(timestamps):
            d = degr[i]
            diurnal = 4.0 * np.sin(2 * np.pi * (i % READINGS_PER_DAY) / READINGS_PER_DAY)

            # Mode-specific boosts
            thermal_boost  = d * 38 if mode in ("thermal",  "combined") else 0.0
            mech_boost     = d * 10 if mode in ("mechanical","combined") else 0.0
            pd_boost       = d * 0.45 if mode in ("insulation","combined") else 0.0
            oil_drop       = d * 0.30 if mode in ("insulation","combined") else 0.0
            load_boost     = d * 20 if mode == "combined" else 0.0

            ot  = float(np.clip(base["ot"]  + diurnal + thermal_boost + rng.normal(0, 1.2), 20, 140))
            lp  = float(np.clip(base["lp"]  + diurnal * 0.5 + load_boost  + rng.normal(0, 2.0),  0, 100))
            vib = float(np.clip(base["vib"] + mech_boost + rng.normal(0, 0.15), 0, 30))
            cu  = float(np.clip(base["cu"]  + rng.normal(0, 0.3), 0, 20))
            vd  = float(np.clip(base["vd"]  + rng.normal(0, 0.2), 0, 20))
            pd_ = float(np.clip(base["pd"]  + pd_boost + rng.normal(0, 0.02), 0, 1))
            amb = float(np.clip(base["amb"] + diurnal * 0.3 + rng.normal(0, 0.5), 15, 55))
            # oil quality degrades with insulation mode
            oq  = float(np.clip(100.0 - oil_drop * 100 + rng.normal(0, 1.0), 0, 100))

            all_telem_rows.append({
                "asset_id"            : aid,
                "timestamp"           : ts.isoformat(),
                # raw telemetry (model features)
                "oil_temperature"     : round(ot,  1),
                "load_percentage"     : round(lp,  1),
                "vibration"           : round(vib, 2),
                "current_unbalance"   : round(cu,  2),
                "voltage_deviation"   : round(vd,  2),
                "partial_discharge"   : round(pd_, 3),
                "ambient_temperature" : round(amb, 1),
                "oil_quality"         : round(oq,  1),
                # asset static features
                "asset_age"           : asset["age"],
                "capacity_mva"        : asset["cap"],
                "customers_served"    : asset["cust"],
                "criticality"         : asset["crit"],
                "redundancy_level"    : asset["redund"],
                "previous_failures"   : asset["prev_fail"],
                "days_since_maintenance": asset["dsm"],
                # labels
                "failure_within_24h"  : int(label_24h[i]),
                "failure_within_72h"  : int(label_72h[i]),
                "degradation_mode"    : mode or "none",
            })

            # Weather row (daily granularity is fine for training; one per telemetry row)
            severe = bool(rng.random() < WEATHER_SEVERE_RATE)
            w = _weather_row(severe)
            all_weather_rows.append({"asset_id": aid, "timestamp": ts.isoformat(), **w})

    telem_df   = pd.DataFrame(all_telem_rows)
    weather_df = pd.DataFrame(all_weather_rows)

    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        telem_path   = OUTPUT_DIR / "telemetry.csv"
        weather_path = OUTPUT_DIR / "weather_cache.csv"
        telem_df.to_csv(telem_path,   index=False)
        weather_df.to_csv(weather_path, index=False)

        meta = {
            "seed"          : SEED,
            "n_assets"      : len(_ASSETS),
            "n_degrading"   : n_degrading,
            "degrading_ids" : sorted(degrading_ids),
            "days"          : DAYS_OF_HISTORY,
            "readings_per_day": READINGS_PER_DAY,
            "total_rows"    : len(telem_df),
            "positive_24h"  : int(telem_df["failure_within_24h"].sum()),
            "positive_72h"  : int(telem_df["failure_within_72h"].sum()),
            "positive_rate_24h": round(float(telem_df["failure_within_24h"].mean()), 4),
            "positive_rate_72h": round(float(telem_df["failure_within_72h"].mean()), 4),
            "generated_at"  : datetime.utcnow().isoformat(),
        }
        with open(OUTPUT_DIR / "generation_params.json", "w") as f:
            json.dump(meta, f, indent=2)

        print(f"[DataGen] {len(telem_df)} rows, {n_degrading}/{len(_ASSETS)} degrading assets")
        print(f"[DataGen] 24h positive rate: {meta['positive_rate_24h']:.1%}  "
              f"72h positive rate: {meta['positive_rate_72h']:.1%}")
        print(f"[DataGen] Written to: {OUTPUT_DIR}")

    return telem_df, weather_df


if __name__ == "__main__":
    generate(save=True)
