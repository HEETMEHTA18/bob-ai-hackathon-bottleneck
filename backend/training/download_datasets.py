"""
Dataset Download Script for GridMind AI
Downloads publicly available solar and wind datasets
"""
import os
import sys
import urllib.request
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"
RAW_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def generate_solar_dataset(n_days: int = 30) -> str:
    np.random.seed(42)
    hours = n_days * 24
    start = datetime(2024, 1, 1)
    timestamps = [start + timedelta(hours=i) for i in range(hours)]

    hour_of_day = np.array([t.hour for t in timestamps])
    day_of_year = np.array([t.timetuple().tm_yday for t in timestamps])
    solar_factor = np.clip(np.sin(np.pi * (hour_of_day - 6) / 12), 0, 1)
    seasonal = 0.7 + 0.3 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    noise = np.random.normal(0, 0.05, hours)

    ghi = 800 * solar_factor * seasonal + noise * 100
    ghi = np.clip(ghi, 0, 1200)
    dni = ghi * 0.6 * (1 + noise * 0.2)
    dhi = ghi * 0.4 * (1 + noise * 0.1)
    temp = 25 + 10 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 2, hours)
    wind_speed = 5 + 3 * np.sin(2 * np.pi * hour_of_day / 24 + 1) + np.random.normal(0, 1, hours)
    wind_speed = np.clip(wind_speed, 0, 20)
    humidity = 60 + 20 * np.sin(2 * np.pi * hour_of_day / 24 - 2) + np.random.normal(0, 5, hours)
    humidity = np.clip(humidity, 20, 100)
    cloud = np.clip(50 - ghi / 20 + np.random.normal(0, 10, hours), 0, 100)
    pressure = 1013 + np.random.normal(0, 5, hours)

    capacity_kw = 100
    generation = capacity_kw * solar_factor * seasonal * (1 - cloud / 200) + np.random.normal(0, 3, hours)
    generation = np.clip(generation, 0, capacity_kw)

    df = pd.DataFrame({
        "timestamp": [t.strftime("%Y-%m-%d %H:%M:%S") for t in timestamps],
        "ghi": ghi, "dni": dni, "dhi": dhi,
        "temperature_2m": temp, "wind_speed_10m": wind_speed,
        "relative_humidity_2m": humidity, "cloud_cover": cloud,
        "pressure_msl": pressure, "generation_kw": generation,
        "capacity_kw": capacity_kw,
    })

    path = str(RAW_DIR / "solar_generation.csv")
    df.to_csv(path, index=False)
    print(f"Generated solar dataset: {len(df)} rows -> {path}")
    return path


def generate_wind_dataset(n_days: int = 30) -> str:
    np.random.seed(123)
    hours = n_days * 24
    start = datetime(2024, 1, 1)
    timestamps = [start + timedelta(hours=i) for i in range(hours)]

    hour_of_day = np.array([t.hour for t in timestamps])
    day_of_year = np.array([t.timetuple().tm_yday for t in timestamps])

    base_wind = 8 + 4 * np.sin(2 * np.pi * day_of_year / 365)
    diurnal = 2 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
    turbulence = np.random.normal(0, 2, hours)
    wind_speed = base_wind + diurnal + turbulence
    wind_speed = np.clip(wind_speed, 0, 25)

    wind_dir = (180 + 90 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 30, hours)) % 360
    temp = 15 + 10 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 3, hours)
    pressure = 1013 + np.random.normal(0, 5, hours)

    rated_kw = 100
    cut_in, rated_speed, cut_out = 3, 12, 25
    power = np.zeros(hours)
    for i in range(hours):
        v = wind_speed[i]
        if cut_in <= v < rated_speed:
            power[i] = rated_kw * ((v - cut_in) / (rated_speed - cut_in)) ** 3
        elif rated_speed <= v <= cut_out:
            power[i] = rated_kw
    power += np.random.normal(0, 2, hours)
    power = np.clip(power, 0, rated_kw)

    df = pd.DataFrame({
        "timestamp": [t.strftime("%Y-%m-%d %H:%M:%S") for t in timestamps],
        "wind_speed": wind_speed, "wind_direction": wind_dir,
        "temperature": temp, "pressure": pressure,
        "generation_kw": power, "rated_capacity_kw": rated_kw,
    })

    path = str(RAW_DIR / "wind_generation.csv")
    df.to_csv(path, index=False)
    print(f"Generated wind dataset: {len(df)} rows -> {path}")
    return path


def download_from_kaggle():
    print("\nNote: Kaggle datasets require manual download.")
    print("1. Solar: https://www.kaggle.com/datasets/anikannal/solar-power-generation-data")
    print("2. Wind: https://www.kaggle.com/datasets/berkerzen wind-turbine-scada-dataset")
    print("Place downloaded CSVs in: data/raw/")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("GridMind AI — Dataset Preparation")
    print("=" * 60)

    print("\n[1/2] Generating synthetic solar dataset...")
    generate_solar_dataset(30)

    print("\n[2/2] Generating synthetic wind dataset...")
    generate_wind_dataset(30)

    print("\n" + "=" * 60)
    print("Datasets ready in data/raw/")
    print("=" * 60)
    download_from_kaggle()
