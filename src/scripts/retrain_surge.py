#!/usr/bin/env python3
"""
retrain_surge.py — SURGE-Inspired Training Pipeline for Bottleneck AI

Trains XGBoost models for solar and wind generation forecasting using SURGE's
exact architecture: multi-model benchmarking, quantile regression (P10/P50/P90),
physics constraints, and chronological time-series validation.

Models trained:
  1. Solar point forecast (XGBoost, 5-model benchmark)
  2. Solar quantile forecaster (P10/P50/P90 via reg:quantileerror)
  3. Wind point forecast (XGBoost, 4-model benchmark)
  4. Wind quantile forecaster (P10/P50/P90 via reg:quantileerror)

Usage:
  python3 retrain_surge.py                    # Train all models
  python3 retrain_surge.py --type solar       # Train solar only
  python3 retrain_surge.py --type wind        # Train wind only
  python3 retrain_surge.py --data path.csv    # Use custom data
"""

import os
import sys
import json
import time
import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"

# ─── SURGE Feature Columns ─────────────────────────────────────
# Solar: 21 features from SURGE/src/training/train.py
SURGE_SOLAR_FEATURES = [
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation",
    "temperature_2m", "relative_humidity_2m", "surface_pressure",
    "cloud_cover", "wind_speed_10m",
    "solar_zenith", "solar_azimuth", "solar_elevation",
    "clearsky_ghi", "clearness_index",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "day_of_year_sin", "day_of_year_cos",
    "cloud_cover_rolling_3h", "temp_rolling_3h",
]

# Wind: 16 features from SURGE/src/wind/train_wind.py
SURGE_WIND_FEATURES = [
    "wind_speed_10m", "wind_speed_100m", "wind_gusts_10m",
    "wind_dir_sin", "wind_dir_cos",
    "air_density",
    "temperature_2m", "surface_pressure",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "day_of_year_sin", "day_of_year_cos",
    "wind_speed_rolling_3h", "wind_speed_rolling_6h",
]


# ─── SURGE Feature Engineering ─────────────────────────────────
def surge_solar_features(df: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    """
    SURGE's exact solar feature engineering pipeline:
    1. Solar astronomical geometry (pvlib NREL SPA)
    2. Clear-sky irradiance & clearness index (Ineichen model)
    3. Cyclical temporal encodings (sin/cos)
    4. Atmospheric rolling statistics
    """
    import pvlib

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Ensure IST timezone for pvlib
    ts = df["timestamp"]
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("Asia/Kolkata")

    # 1. Solar astronomical geometry
    times = pd.DatetimeIndex(ts)
    solpos = pvlib.solarposition.get_solarposition(times, lat, lon)
    df["solar_zenith"] = np.round(np.asarray(solpos["apparent_zenith"]), 2)
    df["solar_azimuth"] = np.round(np.asarray(solpos["azimuth"]), 2)
    df["solar_elevation"] = np.round(np.maximum(0.0, 90.0 - np.asarray(solpos["apparent_zenith"])), 2)

    # 2. Clear-sky irradiance (Ineichen model)
    loc = pvlib.location.Location(lat, lon, tz="Asia/Kolkata")
    clearsky = loc.get_clearsky(times, model="ineichen")
    clearsky_ghi = np.maximum(0.0, np.asarray(clearsky["ghi"]))
    df["clearsky_ghi"] = np.round(clearsky_ghi, 2)

    # Clearness index: kt = GHI / clearsky_ghi, clipped [0, 1.2]
    valid_sun = clearsky_ghi > 10.0
    kt = np.zeros(len(df))
    ghi_col = "shortwave_radiation" if "shortwave_radiation" in df.columns else "ghi"
    if ghi_col in df.columns:
        kt[valid_sun] = np.clip(
            df[ghi_col].values[valid_sun] / clearsky_ghi[valid_sun], 0.0, 1.2
        )
    df["clearness_index"] = np.round(kt, 3)

    # 3. Cyclical temporal encodings
    hour = df["timestamp"].dt.hour
    df["hour_sin"] = np.round(np.sin(2 * np.pi * hour / 24.0), 4)
    df["hour_cos"] = np.round(np.cos(2 * np.pi * hour / 24.0), 4)

    month = df["timestamp"].dt.month
    df["month_sin"] = np.round(np.sin(2 * np.pi * month / 12.0), 4)
    df["month_cos"] = np.round(np.cos(2 * np.pi * month / 12.0), 4)

    doy = df["timestamp"].dt.dayofyear
    df["day_of_year_sin"] = np.round(np.sin(2 * np.pi * doy / 365.25), 4)
    df["day_of_year_cos"] = np.round(np.cos(2 * np.pi * doy / 365.25), 4)

    # 4. Atmospheric rolling statistics
    df["cloud_cover_rolling_3h"] = np.round(
        df["cloud_cover"].rolling(window=3, min_periods=1).mean(), 2
    ) if "cloud_cover" in df.columns else 0.0
    df["temp_rolling_3h"] = np.round(
        df["temperature_2m"].rolling(window=3, min_periods=1).mean(), 2
    ) if "temperature_2m" in df.columns else 0.0

    # Normalize column names from Bottleneck format to SURGE format
    col_map = {
        "ghi": "shortwave_radiation", "dni": "direct_normal_irradiance",
        "dhi": "diffuse_radiation", "temperature": "temperature_2m",
        "humidity": "relative_humidity_2m", "pressure": "surface_pressure",
        "wind_speed": "wind_speed_10m", "cloud_cover": "cloud_cover",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    return df


def surge_wind_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    SURGE's exact wind feature engineering pipeline.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Normalize column names
    if "temperature" in df.columns and "temperature_2m" not in df.columns:
        df["temperature_2m"] = df["temperature"]
    if "pressure" in df.columns and "surface_pressure" not in df.columns:
        df["surface_pressure"] = df["pressure"]
    if "wind_speed" in df.columns and "wind_speed_10m" not in df.columns:
        df["wind_speed_10m"] = df["wind_speed"]
    if "wind_direction" in df.columns:
        df["wind_dir_sin"] = np.sin(np.radians(df["wind_direction"]))
        df["wind_dir_cos"] = np.cos(np.radians(df["wind_direction"]))
    else:
        df["wind_dir_sin"] = 0.0
        df["wind_dir_cos"] = 0.0

    # Wind speed at 100m (log-law extrapolation)
    if "wind_speed_100m" not in df.columns:
        alpha = 0.14
        df["wind_speed_100m"] = df["wind_speed_10m"] * (100 / 10) ** alpha if "wind_speed_10m" in df.columns else 0.0
    if "wind_gusts_10m" not in df.columns:
        df["wind_gusts_10m"] = df["wind_speed_10m"] * 1.3 if "wind_speed_10m" in df.columns else 0.0

    # Air density from ideal gas law
    if "surface_pressure" in df.columns and "temperature_2m" in df.columns:
        R_specific = 287.05
        df["air_density"] = (df["surface_pressure"] * 100) / (R_specific * (df["temperature_2m"] + 273.15))
    else:
        df["air_density"] = 1.225

    # Cyclical time encodings
    hour = df["timestamp"].dt.hour
    df["hour_sin"] = np.round(np.sin(2 * np.pi * hour / 24.0), 4)
    df["hour_cos"] = np.round(np.cos(2 * np.pi * hour / 24.0), 4)

    month = df["timestamp"].dt.month
    df["month_sin"] = np.round(np.sin(2 * np.pi * month / 12.0), 4)
    df["month_cos"] = np.round(np.cos(2 * np.pi * month / 12.0), 4)

    doy = df["timestamp"].dt.dayofyear
    df["day_of_year_sin"] = np.round(np.sin(2 * np.pi * doy / 365.25), 4)
    df["day_of_year_cos"] = np.round(np.cos(2 * np.pi * doy / 365.25), 4)

    # Rolling wind speed statistics
    ws_col = "wind_speed_10m" if "wind_speed_10m" in df.columns else "wind_speed"
    if ws_col in df.columns:
        df["wind_speed_rolling_3h"] = np.round(df[ws_col].rolling(3, min_periods=1).mean(), 2)
        df["wind_speed_rolling_6h"] = np.round(df[ws_col].rolling(6, min_periods=1).mean(), 2)
    else:
        df["wind_speed_rolling_3h"] = 0.0
        df["wind_speed_rolling_6h"] = 0.0

    return df


# ─── SURGE Quantile Forecaster ─────────────────────────────────
def train_quantile_models(X_train, y_train, target_type="solar", capacity=100.0):
    """
    SURGE's exact SiteQuantileForecaster: trains P10/P50/P90 XGBoost regressors
    using reg:quantileerror (pinball loss).
    """
    from xgboost import XGBRegressor

    quantiles = [0.10, 0.50, 0.90]
    models = {}

    for q in quantiles:
        q_key = f"p{int(round(q * 100))}"
        logger.info(f"  Training {target_type.upper()} quantile {q_key} (alpha={q})...")

        model = XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=q,
            n_estimators=150,
            max_depth=5,
            learning_rate=0.07,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        models[q_key] = model

    return models


def apply_physics_constraints(preds: dict, df: pd.DataFrame, target_type: str, capacity: float) -> dict:
    """
    SURGE's physics boundary enforcement:
    - Solar: nighttime (elevation <= 0) forced to 0 MW
    - Wind: cut-in (<3 m/s) and cut-out (>=25 m/s) forced to 0 MW
    - Monotonicity: P10 <= P50 <= P90
    """
    p10 = preds["p10"].copy()
    p50 = preds["p50"].copy()
    p90 = preds["p90"].copy()

    if target_type == "solar":
        if "solar_elevation" in df.columns:
            night_mask = df["solar_elevation"].values <= 0.0
            p10[night_mask] = 0.0
            p50[night_mask] = 0.0
            p90[night_mask] = 0.0
        elif "shortwave_radiation" in df.columns:
            night_mask = df["shortwave_radiation"].values <= 1.0
            p10[night_mask] = 0.0
            p50[night_mask] = 0.0
            p90[night_mask] = 0.0
    elif target_type == "wind":
        ws_col = "wind_speed_100m" if "wind_speed_100m" in df.columns else "wind_speed_10m"
        if ws_col in df.columns:
            w = df[ws_col].values
            cut_mask = (w < 3.0) | (w >= 25.0)
            p10[cut_mask] = 0.0
            p50[cut_mask] = 0.0
            p90[cut_mask] = 0.0

    # Enforce monotonicity: P10 <= P50 <= P90
    p50 = np.maximum(p10, p50)
    p90 = np.maximum(p50, p90)

    # Clip to capacity
    p10 = np.clip(p10, 0.0, capacity)
    p50 = np.clip(p50, 0.0, capacity)
    p90 = np.clip(p90, 0.0, capacity)

    return {"p10": p10, "p50": p50, "p90": p90}


# ─── Model Evaluation ──────────────────────────────────────────
def evaluate(y_true, y_pred, capacity=100.0):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    y_pred = np.clip(y_pred, 0.0, capacity)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    nrmse = (rmse / capacity) * 100.0
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 4), "nrmse": round(nrmse, 2)}


def quantile_coverage(y_true, p10, p90):
    inside = np.sum((y_true >= p10) & (y_true <= p90))
    return round(inside / len(y_true) * 100, 2) if len(y_true) > 0 else 0.0


# ─── Load Training Data from Bottleneck DB ───────────────────────
def load_weather_data(site_id: int = None) -> pd.DataFrame:
    """Load weather data from Bottleneck's SQLite database."""
    import sqlite3

    db_path = PROJECT_ROOT / "bottleneck.db"
    if not db_path.exists():
        # Try alternative locations
        for p in [PROJECT_ROOT / "backend" / "bottleneck.db", Path("bottleneck.db")]:
            if p.exists():
                db_path = p
                break

    if not db_path.exists():
        logger.error("No database found. Generating synthetic training data...")
        return generate_synthetic_data()

    conn = sqlite3.connect(str(db_path))

    # Get all weather data (or for specific site)
    if site_id:
        query = f"""
            SELECT w.*, s.latitude, s.longitude, s.capacity_kw, s.site_type
            FROM weather_data w
            JOIN sites s ON w.site_id = s.id
            WHERE w.site_id = {site_id}
            ORDER BY w.timestamp
        """
    else:
        query = """
            SELECT w.*, s.latitude, s.longitude, s.capacity_kw, s.site_type
            FROM weather_data w
            JOIN sites s ON w.site_id = s.id
            ORDER BY w.timestamp
        """

    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        logger.warning(f"Query failed: {e}. Trying without site_type...")
        query = query.replace("s.site_type,", "")
        df = pd.read_sql(query, conn)
    conn.close()

    if len(df) == 0:
        logger.warning("No weather data in DB. Generating synthetic training data...")
        return generate_synthetic_data()

    logger.info(f"Loaded {len(df)} weather records from DB")
    return df


def generate_synthetic_data() -> pd.DataFrame:
    """
    Generate 6 months of synthetic training data using NREL pvlib physics,
    matching SURGE's data generation approach.
    """
    import pvlib

    logger.info("Generating synthetic training data for Delhi (28.61N, 77.21E)...")
    lat, lon = 28.6139, 77.2090
    capacity_kw = 100.0

    # Generate hourly timestamps for 6 months
    dates = pd.date_range("2025-01-01", "2025-06-30", freq="1h")
    n = len(dates)

    # Solar position
    times = dates.tz_localize("Asia/Kolkata")
    solpos = pvlib.solarposition.get_solarposition(times, lat, lon)
    zenith = solpos["apparent_zenith"].values
    elevation = np.maximum(0.0, 90.0 - zenith)

    # Clear-sky irradiance
    loc = pvlib.location.Location(lat, lon, tz="Asia/Kolkata")
    clearsky = loc.get_clearsky(times, model="ineichen")
    clearsky_ghi = np.maximum(0.0, clearsky["ghi"].values)

    # Synthetic weather with realistic variability
    np.random.seed(42)
    cloud_base = np.clip(50 + 30 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.normal(0, 15, n), 0, 100)
    ghi = np.clip(clearsky_ghi * (1 - cloud_base / 100) + np.random.normal(0, 20, n), 0, 1000)
    dni = np.clip(ghi * 0.7 + np.random.normal(0, 30, n), 0, 800)
    dhi = np.clip(ghi * 0.3 + np.random.normal(0, 15, n), 0, 400)

    # Temperature: seasonal + diurnal
    temp = 25 + 10 * np.sin(2 * np.pi * np.arange(n) / (24 * 365) - np.pi / 2) + \
           5 * np.sin(2 * np.pi * np.arange(n) / 24) + np.random.normal(0, 2, n)

    # Generate actual generation using NREL pvlib physics
    df_synth = pd.DataFrame({
        "timestamp": dates,
        "shortwave_radiation": ghi,
        "direct_normal_irradiance": dni,
        "diffuse_radiation": dhi,
        "temperature_2m": temp,
        "relative_humidity_2m": np.clip(60 + 20 * np.sin(2 * np.pi * np.arange(n) / 24) + np.random.normal(0, 10, n), 0, 100),
        "surface_pressure": 1013.25 + np.random.normal(0, 5, n),
        "cloud_cover": cloud_base,
        "wind_speed_10m": np.clip(np.random.weibull(2.0, n) * 5, 0, 25),
        "latitude": lat,
        "longitude": lon,
        "capacity_kw": capacity_kw,
    })

    # Compute actual generation via pvlib physics (same as SURGE)
    df_synth["solar_zenith"] = np.round(zenith, 2)
    df_synth["solar_elevation"] = np.round(elevation, 2)
    df_synth["actual_generation_mw"] = np.clip(
        clearsky_ghi * (capacity_kw / 1000) * (1 - cloud_base / 100) * 0.85, 0, capacity_kw
    )
    df_synth.loc[df_synth["solar_elevation"] <= 0, "actual_generation_mw"] = 0.0

    logger.info(f"Generated {n} synthetic records")
    return df_synth


# ─── Solar Training Pipeline ────────────────────────────────────
def train_solar_models(data: pd.DataFrame) -> dict:
    """SURGE's full solar training pipeline."""
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
    from xgboost import XGBRegressor
    import joblib

    logger.info("=" * 60)
    logger.info("SURGE SOLAR TRAINING PIPELINE")
    logger.info("=" * 60)

    # Get site coordinates
    lat = data["latitude"].iloc[0] if "latitude" in data.columns else 28.6139
    lon = data["longitude"].iloc[0] if "longitude" in data.columns else 77.2090
    capacity = float(data["capacity_kw"].iloc[0]) if "capacity_kw" in data.columns else 100.0

    # Feature engineering
    logger.info("Running SURGE feature engineering (solar)...")
    df = surge_solar_features(data.copy(), lat, lon)

    # Ensure target column exists
    if "actual_generation_mw" not in df.columns and "generation_kw" in df.columns:
        df["actual_generation_mw"] = df["generation_kw"] / 1000.0 * capacity / 100.0
    elif "actual_generation_mw" not in df.columns:
        # Generate realistic synthetic targets using pvlib physics + noise
        logger.info("No generation data found — generating physics-based synthetic targets with noise")
        ghi = df["shortwave_radiation"].values if "shortwave_radiation" in df.columns else np.zeros(len(df))
        elev = df["solar_elevation"].values if "solar_elevation" in df.columns else np.zeros(len(df))
        temp = df["temperature_2m"].values if "temperature_2m" in df.columns else np.full(len(df), 25.0)
        cloud = df["cloud_cover"].values if "cloud_cover" in df.columns else np.full(len(df), 30.0)

        # Physics: generation = f(ghi, temperature_derating, cloud_loss, elevation)
        base = np.clip(ghi * (capacity / 1000) * 0.85, 0, capacity)
        temp_derate = 1.0 - 0.004 * np.maximum(temp - 25, 0)  # -0.4%/°C above 25°C
        cloud_loss = 1.0 - 0.6 * (cloud / 100)  # up to 60% loss at 100% cloud
        night_zero = (elev > 0).astype(float)

        target = base * temp_derate * cloud_loss * night_zero

        # Add realistic noise (±8% of capacity, correlated with weather variability)
        np.random.seed(42)
        noise = np.random.normal(0, capacity * 0.06, len(df))
        # More noise during high generation (realistic uncertainty)
        noise_scale = np.clip(target / capacity, 0.1, 1.0)
        noise = noise * noise_scale

        target = np.clip(target + noise, 0, capacity)
        df["actual_generation_mw"] = np.round(target, 3)

    # Sort chronologically
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Filter features that exist
    available_features = [f for f in SURGE_SOLAR_FEATURES if f in df.columns]
    logger.info(f"Using {len(available_features)} features: {available_features}")

    X = df[available_features].fillna(0)
    y = df["actual_generation_mw"]

    # Chronological split: 70/15/15
    n = len(df)
    train_end = int(0.70 * n)
    val_end = int(0.85 * n)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

    logger.info(f"Train: {len(X_train)}h | Val: {len(X_val)}h | Test: {len(X_test)}h")

    # 5-model benchmark (SURGE architecture)
    models = {
        "Ridge": Ridge(alpha=10.0),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1),
    }

    results = []
    best_rmse = float("inf")
    best_name = None
    best_model = None

    for name, model in models.items():
        logger.info(f"Training {name}...")
        t0 = time.time()
        model.fit(X_train, y_train)
        dt = round(time.time() - t0, 2)

        val_pred = np.clip(model.predict(X_val), 0, capacity)
        test_pred = np.clip(model.predict(X_test), 0, capacity)

        val_m = evaluate(y_val.values, val_pred, capacity)
        test_m = evaluate(y_test.values, test_pred, capacity)

        results.append({
            "model": name, "train_time_s": dt,
            "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_r2": val_m["r2"],
            "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_r2": test_m["r2"],
        })

        if test_m["rmse"] < best_rmse:
            best_rmse = test_m["rmse"]
            best_name = name
            best_model = model

    logger.info(f"\nBest model: {best_name} (Test RMSE={best_rmse})")

    # Save best model
    solar_dir = MODELS_DIR / "solar"
    solar_dir.mkdir(parents=True, exist_ok=True)

    # Save as JSON (XGBoost native format)
    if best_name == "XGBoost":
        best_model.save_model(str(solar_dir / "solar_hybrid.json"))
    else:
        import joblib
        joblib.dump(best_model, str(solar_dir / "solar_best.joblib"))

    # Save feature columns
    (solar_dir / "feature_cols.json").write_text(json.dumps(available_features, indent=2))

    # Feature importance
    fi = {}
    if hasattr(best_model, "feature_importances_"):
        imp = best_model.feature_importances_
        for i in np.argsort(imp)[::-1]:
            fi[available_features[i]] = round(float(imp[i]), 4)

    # Train quantile models (SURGE architecture)
    logger.info("Training solar quantile models (P10/P50/P90)...")
    quantile_models = train_quantile_models(X_train, y_train, "solar", capacity)

    # Evaluate quantile models
    q_preds = {}
    for q_key, q_model in quantile_models.items():
        q_preds[q_key] = np.clip(q_model.predict(X_test), 0, capacity)

    # Apply physics constraints
    q_constrained = apply_physics_constraints(
        {"p10": q_preds["p10"], "p50": q_preds["p50"], "p90": q_preds["p90"]},
        df.iloc[val_end:], "solar", capacity,
    )

    coverage = quantile_coverage(y_test.values, q_constrained["p10"], q_constrained["p90"])

    # Save quantile models as joblib
    import joblib
    joblib.dump({
        "target_type": "solar",
        "max_capacity_mw": capacity,
        "quantiles": [0.10, 0.50, 0.90],
        "feature_columns": available_features,
        "models": quantile_models,
    }, str(solar_dir / "quantile" / "quantile_solar.joblib"))

    # Save metadata
    metadata = {
        "best_model": best_name,
        "training_date": datetime.now().isoformat(),
        "plant_capacity_kw": capacity,
        "feature_columns": available_features,
        "all_model_results": results,
        "quantile_coverage_pct": coverage,
        "feature_importance": fi,
    }
    (solar_dir / "surge_metadata.json").write_text(json.dumps(metadata, indent=2))

    logger.info(f"Quantile P10-P90 coverage: {coverage}% (target ~80%)")
    logger.info(f"Saved solar models to {solar_dir}")

    return {"best_model": best_name, "results": results, "coverage": coverage}


# ─── Wind Training Pipeline ─────────────────────────────────────
def train_wind_models(data: pd.DataFrame) -> dict:
    """SURGE's full wind training pipeline."""
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
    from xgboost import XGBRegressor
    import joblib

    logger.info("=" * 60)
    logger.info("SURGE WIND TRAINING PIPELINE")
    logger.info("=" * 60)

    # Feature engineering
    logger.info("Running SURGE feature engineering (wind)...")
    df = surge_wind_features(data.copy())

    # Ensure target
    if "actual_generation_mw" not in df.columns and "generation_kw" in df.columns:
        capacity = float(data["capacity_kw"].iloc[0]) if "capacity_kw" in data.columns else 100.0
        df["actual_generation_mw"] = df["generation_kw"] / 1000.0 * capacity / 100.0
    elif "actual_generation_mw" not in df.columns:
        logger.info("No generation data found — generating physics-based synthetic wind targets")
        capacity = float(data["capacity_kw"].iloc[0]) if "capacity_kw" in data.columns else 100.0
        ws = df["wind_speed_10m"].values if "wind_speed_10m" in df.columns else np.zeros(len(df))
        density = df["air_density"].values if "air_density" in df.columns else np.full(len(df), 1.225)

        # IEC power curve with air density correction
        def _iec_power(v, rho):
            v_cutin, v_rated, v_cutout = 3.0, 12.0, 25.0
            rho_ref = 1.225
            # Density-corrected wind speed
            v_corr = v * (rho / rho_ref) ** (1/3)
            if v_corr < v_cutin or v_corr >= v_cutout:
                return 0.0
            if v_corr >= v_rated:
                return capacity
            # Cubic region
            return capacity * ((v_corr - v_cutin) / (v_rated - v_cutin)) ** 3

        target = np.array([_iec_power(v, r) for v, r in zip(ws, density)])

        # Add realistic turbulence noise
        np.random.seed(42)
        turbulence = np.random.normal(0, capacity * 0.08, len(df))
        gust_factor = np.clip(ws / 15, 0.2, 1.0)  # more noise at higher wind speeds
        target = np.clip(target + turbulence * gust_factor, 0, capacity)
        df["actual_generation_mw"] = np.round(target, 3)

    df = df.sort_values("timestamp").reset_index(drop=True)

    available_features = [f for f in SURGE_WIND_FEATURES if f in df.columns]
    logger.info(f"Using {len(available_features)} features")

    X = df[available_features].fillna(0)
    y = df["actual_generation_mw"]

    # Chronological split
    n = len(df)
    train_end = int(0.70 * n)
    val_end = int(0.85 * n)

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

    capacity = float(data["capacity_kw"].iloc[0]) if "capacity_kw" in data.columns else 100.0

    # 4-model benchmark (SURGE architecture)
    models = {
        "Ridge": Ridge(alpha=10.0),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=150, max_depth=8, learning_rate=0.08, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1),
    }

    results = []
    best_rmse = float("inf")
    best_name = None
    best_model = None

    for name, model in models.items():
        logger.info(f"Training {name}...")
        t0 = time.time()
        model.fit(X_train, y_train)
        dt = round(time.time() - t0, 2)

        test_pred = np.clip(model.predict(X_test), 0, capacity)
        test_m = evaluate(y_test.values, test_pred, capacity)

        results.append({
            "model": name, "train_time_s": dt,
            "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_r2": test_m["r2"],
        })

        if test_m["rmse"] < best_rmse:
            best_rmse = test_m["rmse"]
            best_name = name
            best_model = model

    logger.info(f"\nBest model: {best_name} (Test RMSE={best_rmse})")

    # Save best model
    wind_dir = MODELS_DIR / "wind"
    wind_dir.mkdir(parents=True, exist_ok=True)

    if best_name == "XGBoost":
        best_model.save_model(str(wind_dir / "wind_xgboost.json"))
    else:
        import joblib
        joblib.dump(best_model, str(wind_dir / "wind_best.joblib"))

    (wind_dir / "feature_cols.json").write_text(json.dumps(available_features, indent=2))

    # Train quantile models
    logger.info("Training wind quantile models (P10/P50/P90)...")
    quantile_models = train_quantile_models(X_train, y_train, "wind", capacity)

    # Evaluate
    q_preds = {}
    for q_key, q_model in quantile_models.items():
        q_preds[q_key] = np.clip(q_model.predict(X_test), 0, capacity)

    q_constrained = apply_physics_constraints(
        {"p10": q_preds["p10"], "p50": q_preds["p50"], "p90": q_preds["p90"]},
        df.iloc[val_end:], "wind", capacity,
    )
    coverage = quantile_coverage(y_test.values, q_constrained["p10"], q_constrained["p90"])

    import joblib
    joblib.dump({
        "target_type": "wind",
        "max_capacity_mw": capacity,
        "quantiles": [0.10, 0.50, 0.90],
        "feature_columns": available_features,
        "models": quantile_models,
    }, str(wind_dir / "quantile" / "quantile_wind.joblib"))

    metadata = {
        "best_model": best_name,
        "training_date": datetime.now().isoformat(),
        "plant_capacity_kw": capacity,
        "feature_columns": available_features,
        "all_model_results": results,
        "quantile_coverage_pct": coverage,
    }
    (wind_dir / "surge_metadata.json").write_text(json.dumps(metadata, indent=2))

    logger.info(f"Quantile P10-P90 coverage: {coverage}% (target ~80%)")
    logger.info(f"Saved wind models to {wind_dir}")

    return {"best_model": best_name, "results": results, "coverage": coverage}


# ─── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SURGE-Inspired Training Pipeline")
    parser.add_argument("--type", choices=["solar", "wind", "all"], default="all")
    parser.add_argument("--data", type=str, help="Path to CSV training data")
    parser.add_argument("--site-id", type=int, help="Site ID to train for")
    args = parser.parse_args()

    # Load data
    if args.data:
        logger.info(f"Loading data from {args.data}...")
        data = pd.read_csv(args.data)
    else:
        data = load_weather_data(args.site_id)

    results = {}
    if args.type in ("solar", "all"):
        results["solar"] = train_solar_models(data)
    if args.type in ("wind", "all"):
        results["wind"] = train_wind_models(data)

    # Print summary
    print("\n" + "=" * 60)
    print("  SURGE TRAINING COMPLETE")
    print("=" * 60)
    for asset, r in results.items():
        print(f"\n{asset.upper()}:")
        print(f"  Best model: {r['best_model']}")
        print(f"  Quantile coverage: {r['coverage']}%")
        for m in r["results"]:
            print(f"  {m['model']:25s} | RMSE={m['test_rmse']:.3f} | R²={m['test_r2']:.4f}")


if __name__ == "__main__":
    main()
