"""
Build a real training dataset for the GridMind solar forecaster.

Pipeline:
  1. Pull historical hourly weather from the Open-Meteo archive (free, no key)
     for a real Indian solar location. GHI/DNI/DHI come directly from the archive.
  2. Run the pvlib physics model to produce a physically-realistic AC generation
     "ground truth", plus a realistic plant model (soiling, clipping, partial
     cloud shading, temperature derating already inside ModelChain).
  3. Write `data/raw/solar_generation.csv` in the exact schema the training
     pipeline expects.

The generation is a pvlib-modelled reference — ideal for shipping a reproducible
baseline model and for validating the full ML pipeline against real solar
geometry + real historical irradiance. Swap in SCADA CSV later for real plant
output (same schema).
"""
import argparse
import os
import sys
import ssl
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import certifi
import numpy as np
import pandas as pd
import urllib.request
import urllib.parse
import json

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.forecasting.solar import run_physics_model

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

ARCHIVE_VARS = (
    "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,cloud_cover,"
    "surface_pressure,shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
)

DEFAULT_SITE = {
    "name": "Bhadla Solar Park (Rajasthan, India)",
    "latitude": 27.5667,
    "longitude": 72.0667,
    "altitude": 210,
    "capacity_kw": 100,
    "surface_tilt": 26,
    "surface_azimuth": 180,
    "temp_coeff_pmax": -0.004,
}


def _ssl_ctx():
    return ssl.create_default_context(cafile=certifi.where())


def _fetch_archive(latitude, longitude, start_date, end_date, base, month_limit):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ARCHIVE_VARS,
        "timezone": "Asia/Kolkata",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "GridMind-AI/2.0"})
    with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=60) as resp:
        data = json.loads(resp.read().decode())

    if "error" in data:
        raise RuntimeError(f"Open-Meteo error: {data.get('reason')}")

    hourly = data["hourly"]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "ghi": np.asarray(hourly["shortwave_radiation"], dtype=float),
        "dni": np.asarray(hourly["direct_normal_irradiance"], dtype=float),
        "dhi": np.asarray(hourly["diffuse_radiation"], dtype=float),
        "temp_air": np.asarray(hourly["temperature_2m"], dtype=float),
        "wind_speed": np.asarray(hourly["wind_speed_10m"], dtype=float),
        "wind_direction": np.asarray(hourly.get("wind_direction_10m", 180.0), dtype=float),
        "humidity": np.asarray(hourly["relative_humidity_2m"], dtype=float),
        "cloud_cover": np.asarray(hourly["cloud_cover"], dtype=float),
        "pressure": np.asarray(hourly["surface_pressure"], dtype=float),
    })
    df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
    df = df.dropna().reset_index(drop=True)
    return df


def fetch_historical_weather(latitude, longitude, start_date, end_date):
    """Fetch in one call; falls back to month-by-month for very long ranges."""
    try:
        return _fetch_archive(latitude, longitude, start_date, end_date,
                              OPEN_METEO_ARCHIVE, month_limit=None)
    except Exception as e:
        print(f"Single call failed ({e}); fetching month-by-month...")
        dfs = []
        start = pd.Timestamp(start_date, tz="Asia/Kolkata")
        end = pd.Timestamp(end_date, tz="Asia/Kolkata")
        cursor = start
        while cursor <= end:
            stop = min(cursor + pd.DateOffset(months=1) - pd.Timedelta(days=1), end)
            print(f"  {cursor.date()} -> {stop.date()}")
            dfs.append(_fetch_archive(
                latitude, longitude, cursor.strftime("%Y-%m-%d"), stop.strftime("%Y-%m-%d"),
                OPEN_METEO_ARCHIVE, month_limit=1))
            cursor = stop + pd.Timedelta(days=1)
        return pd.concat(dfs, ignore_index=True)


def generate_ground_truth(df, site_params, rng=np.random.default_rng(42)):
    """Physically-grounded 'actual generation' from pvlib + realistic plant effects."""
    df = df.copy()
    for k in ("capacity_kw", "latitude", "longitude"):
        if k not in df.columns:
            df[k] = site_params[k]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        physics_kw = run_physics_model(df, site_params)
    df["physics_kw"] = np.clip(physics_kw, 0, site_params["capacity_kw"])

    capacity = site_params["capacity_kw"]

    soiling = rng.uniform(0.97, 1.0, len(df))  # slow soiling factor
    clip = df["physics_kw"] >= (capacity * 0.985)  # inverter clipping
    partial_shade = 1.0 - 0.03 * np.clip(df["cloud_cover"] / 100.0, 0, 1)  # cloud penumbra
    plant_eff = 1.0 + rng.normal(0, 0.012, len(df))  # inverter/MPPT noise

    generation = df["physics_kw"] * soiling * partial_shade * plant_eff
    generation[clip] = capacity - rng.uniform(0, capacity * 0.01, len(clip))[clip]

    outage_mask = rng.random(len(df)) < 0.0005  # rare plant outages
    generation[outage_mask] = 0.0

    df["generation_kw"] = np.clip(generation, 0, capacity)
    df.drop(columns=["physics_kw"], inplace=True)
    return df


def build_training_dataset(site_params, start_date, end_date, out_name="solar_generation.csv"):
    df = fetch_historical_weather(
        site_params["latitude"], site_params["longitude"], start_date, end_date
    )
    df = generate_ground_truth(df, site_params)
    df["capacity_kw"] = site_params["capacity_kw"]

    out_path = RAW_DIR / out_name
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows -> {out_path}")
    print(f"Gap fill: GHI range [{df['ghi'].min():.0f}, {df['ghi'].max():.0f}] W/m², "
          f"generation range [{df['generation_kw'].min():.1f}, {df['generation_kw'].max():.1f}] kW")
    return str(out_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Build GridMind solar training dataset")
    p.add_argument("--start", default="2023-01-01", help="UTC start date (YYYY-MM-DD)")
    p.add_argument("--end", default="2024-12-31", help="UTC end date (YYYY-MM-DD)")
    p.add_argument("--lat", type=float, default=DEFAULT_SITE["latitude"])
    p.add_argument("--lon", type=float, default=DEFAULT_SITE["longitude"])
    p.add_argument("--capacity-kw", type=float, default=DEFAULT_SITE["capacity_kw"])
    p.add_argument("--altitude", type=float, default=DEFAULT_SITE["altitude"])
    p.add_argument("--tilt", type=float, default=DEFAULT_SITE["surface_tilt"])
    p.add_argument("--azimuth", type=float, default=DEFAULT_SITE["surface_azimuth"])
    p.add_argument("--out", default="solar_generation.csv",
                   help="output filename in data/raw/ (e.g. solar_2023_bhadla.csv)")
    args = p.parse_args()

    site = dict(DEFAULT_SITE)
    site.update({"latitude": args.lat, "longitude": args.lon, "capacity_kw": args.capacity_kw,
                 "altitude": args.altitude, "surface_tilt": args.tilt,
                 "surface_azimuth": args.azimuth})
    build_training_dataset(site, args.start, args.end, out_name=args.out)