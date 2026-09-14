"""
Build a real-weather wind training dataset for Bottleneck.

Pipeline (same philosophy as build_dataset.py but for wind):
  1. Pull real hourly 10 m wind speed/direction, temperature, pressure from the
     Open-Meteo archive (ERA5 reanalysis) for a real Indian wind location.
  2. Model "actual generation" from the IEC cubic power curve (cut-in 3, rated
     12, cut-out 25 m/s) with a light turbulence noise — the standard wind-farm
     power model and the SAME curve the ML physics feature uses.
  3. Write `data/raw/wind_generation.csv` in the schema training expects.

The weather is real (measured/reanalysis); only the turbine output is modelled,
since no Indian wind-farm SCADA is publicly scrapeable here.
"""
import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.forecasting.features import power_curve_estimate

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

WIND_SITE = {
    "name": "Jaisalmer Wind Park (Rajasthan, India)",
    "latitude": 26.9157,
    "longitude": 70.9083,
    "capacity_kw": 100,
}

CUT_IN, RATED_SPEED, CUT_OUT = 3.0, 12.0, 25.0


def fetch_real_wind(latitude, longitude, start_date, end_date, base=None):
    from backend.training.build_dataset import fetch_historical_weather
    df = fetch_historical_weather(latitude, longitude, start_date, end_date)
    return df


def generate_wind_ground_truth(df, site_params, rng=np.random.default_rng(123)):
    df = df.copy()
    ws = df["wind_speed"].values
    power = np.asarray([power_curve_estimate(v, v_cutin=CUT_IN, v_rated=RATED_SPEED,
                                             v_cutout=CUT_OUT,
                                             p_rated_kw=site_params["capacity_kw"])
                        for v in ws])
    turbulence = 1.0 + rng.normal(0, 0.02, len(df))          # ±2% turbulence
    ramp = rng.normal(0, 1.0, len(df))                        # 1 kW additive noise
    generation = np.clip(power * turbulence + ramp, 0, site_params["capacity_kw"])

    outage_mask = rng.random(len(df)) < 0.0005                # rare maintenance
    generation[outage_mask] = 0.0

    df["generation_kw"] = generation
    return df


def build_wind_dataset(site_params, start_date, end_date, out_name="wind_generation.csv"):
    df = fetch_real_wind(site_params["latitude"], site_params["longitude"],
                         start_date, end_date)
    df = generate_wind_ground_truth(df, site_params)
    df["rated_capacity_kw"] = site_params["capacity_kw"]

    # keep the exact schema train_wind/_build_surge_wind_features expect
    out = pd.DataFrame({
        "timestamp": df["timestamp"],
        "wind_speed": df["wind_speed"],
        "wind_direction": df.get("wind_direction", 180.0),
        "temperature": df["temp_air"],
        "pressure": df["pressure"],
        "generation_kw": df["generation_kw"],
        "rated_capacity_kw": df["rated_capacity_kw"],
    })
    out_path = RAW_DIR / out_name
    out.to_csv(out_path, index=False)
    print(f"Wrote {len(out)} rows -> {out_path}")
    print(f"Wind speed range [{out.wind_speed.min():.1f}, {out.wind_speed.max():.1f}] m/s, "
          f"generation range [{out.generation_kw.min():.1f}, {out.generation_kw.max():.1f}] kW")
    return str(out_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build Bottleneck wind training dataset")
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--lat", type=float, default=WIND_SITE["latitude"])
    p.add_argument("--lon", type=float, default=WIND_SITE["longitude"])
    p.add_argument("--capacity-kw", type=float, default=WIND_SITE["capacity_kw"])
    p.add_argument("--out", default="wind_generation.csv",
                   help="output filename in data/raw/ (e.g. wind_2023_jaisalmer.csv)")
    args = p.parse_args()

    site = dict(WIND_SITE)
    site.update({"latitude": args.lat, "longitude": args.lon, "capacity_kw": args.capacity_kw})
    build_wind_dataset(site, args.start, args.end, out_name=args.out)