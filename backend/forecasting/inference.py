"""
ML Inference Engine — SURGE-Inspired Architecture

Loads trained XGBoost models and generates forecasts with physics constraints:
  - Solar: nighttime zero-power, clearsky index, pvlib solar position
  - Wind: cut-in/cut-out, air density correction, IEC power curves
  - Quantile: P10/P50/P90 via reg:quantileerror with monotonicity enforcement
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

MODELS_DIR = Path(__file__).parent.parent.parent / "models"

# ─── Model Cache ──────────────────────────────────────────────
_solar_model = None
_solar_features = None
_solar_quantile = None
_wind_model = None
_wind_features = None
_wind_quantile = None
_solar_calibration = None
_wind_calibration = None


def _load_solar_calibration() -> dict:
    global _solar_calibration
    if _solar_calibration is None:
        p = MODELS_DIR / "solar" / "calibration.json"
        _solar_calibration = json.loads(p.read_text()) if p.exists() else {}
    return _solar_calibration


def _load_wind_calibration() -> dict:
    global _wind_calibration
    if _wind_calibration is None:
        p = MODELS_DIR / "wind" / "calibration.json"
        _wind_calibration = json.loads(p.read_text()) if p.exists() else {}
    return _wind_calibration


def _load_solar_model():
    global _solar_model, _solar_features
    if _solar_model is None:
        import xgboost as xgb
        model_path = MODELS_DIR / "solar" / "solar_hybrid.json"
        if not model_path.exists():
            raise FileNotFoundError(f"Solar model not found: {model_path}")
        _solar_model = xgb.XGBRegressor()
        _solar_model.load_model(str(model_path))
        features_path = MODELS_DIR / "solar" / "feature_cols.json"
        _solar_features = json.loads(features_path.read_text())
    return _solar_model, _solar_features


def _load_solar_quantile():
    global _solar_quantile
    if _solar_quantile is None:
        import joblib
        q_path = MODELS_DIR / "solar" / "quantile" / "quantile_solar.joblib"
        if q_path.exists():
            _solar_quantile = joblib.load(str(q_path))
        else:
            _solar_quantile = None
    return _solar_quantile


def _load_wind_model():
    global _wind_model, _wind_features
    if _wind_model is None:
        import xgboost as xgb
        model_path = MODELS_DIR / "wind" / "wind_xgboost.json"
        if not model_path.exists():
            # Fallback to LightGBM format
            try:
                import lightgbm as lgb
                model_path = MODELS_DIR / "wind" / "wind_lgbm.txt"
                _wind_model = lgb.Booster(model_file=str(model_path))
                features_path = MODELS_DIR / "wind" / "feature_cols.json"
                _wind_features = json.loads(features_path.read_text())
                return _wind_model, _wind_features
            except Exception:
                raise FileNotFoundError(f"Wind model not found")
        _wind_model = xgb.XGBRegressor()
        _wind_model.load_model(str(model_path))
        features_path = MODELS_DIR / "wind" / "feature_cols.json"
        _wind_features = json.loads(features_path.read_text())
    return _wind_model, _wind_features


def _load_wind_quantile():
    global _wind_quantile
    if _wind_quantile is None:
        import joblib
        q_path = MODELS_DIR / "wind" / "quantile" / "quantile_wind.joblib"
        if q_path.exists():
            _wind_quantile = joblib.load(str(q_path))
        else:
            _wind_quantile = None
    return _wind_quantile


# ─── SURGE Feature Engineering (for inference) ─────────────────
def _build_surge_solar_features(df: pd.DataFrame, lat: float, lon: float,
                                capacity_kw: float = 100.0,
                                altitude: float = 210.0,
                                surface_tilt: float = 26.0,
                                surface_azimuth: float = 180.0) -> pd.DataFrame:
    """
    SURGE's exact solar feature pipeline for inference.
    Produces the same 21 features used during training.
    """
    import pvlib

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Normalize column names
    col_map = {
        "ghi": "shortwave_radiation", "dni": "direct_normal_irradiance",
        "dhi": "diffuse_radiation", "temperature": "temperature_2m",
        "humidity": "relative_humidity_2m", "pressure": "surface_pressure",
        "pressure_msl": "surface_pressure",
        "wind_speed": "wind_speed_10m", "cloud_cover": "cloud_cover",
    }
    for src, dst in col_map.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]

    # Ensure all required columns exist
    for col in ["shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation",
                "temperature_2m", "relative_humidity_2m", "surface_pressure",
                "cloud_cover", "wind_speed_10m"]:
        if col not in df.columns:
            df[col] = 0.0

    # Solar position (pvlib NREL SPA)
    ts = df["timestamp"]
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("Asia/Kolkata")
    times = pd.DatetimeIndex(ts)
    solpos = pvlib.solarposition.get_solarposition(times, lat, lon)

    df["solar_zenith"] = np.round(np.asarray(solpos["apparent_zenith"]), 2)
    df["solar_azimuth"] = np.round(np.asarray(solpos["azimuth"]), 2)
    df["solar_elevation"] = np.round(np.maximum(0.0, 90.0 - np.asarray(solpos["apparent_zenith"])), 2)

    # Clear-sky irradiance (Ineichen model)
    loc = pvlib.location.Location(lat, lon, tz="Asia/Kolkata")
    clearsky = loc.get_clearsky(times, model="ineichen")
    clearsky_ghi = np.maximum(0.0, np.asarray(clearsky["ghi"]))
    df["clearsky_ghi"] = np.round(clearsky_ghi, 2)

    # Clearness index
    valid_sun = clearsky_ghi > 10.0
    kt = np.zeros(len(df))
    kt[valid_sun] = np.clip(
        df["shortwave_radiation"].values[valid_sun] / clearsky_ghi[valid_sun], 0.0, 1.2
    )
    df["clearness_index"] = np.round(kt, 3)

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

    # Rolling statistics
    df["cloud_cover_rolling_3h"] = np.round(
        df["cloud_cover"].rolling(window=3, min_periods=1).mean(), 2
    )
    df["temp_rolling_3h"] = np.round(
        df["temperature_2m"].rolling(window=3, min_periods=1).mean(), 2
    )

    # Weather-persistence features (computable from forecast weather at serving)
    _ghi = df["shortwave_radiation"]
    df["shortwave_radiation_lag_1h"] = np.round(_ghi.shift(1).fillna(0.0), 3)
    df["shortwave_radiation_rolling_6h"] = np.round(_ghi.rolling(6, min_periods=1).mean(), 3)
    df["shortwave_radiation_rolling_24h"] = np.round(_ghi.rolling(24, min_periods=1).mean(), 3)

    # Physics-informed feature (pvlib PVWatts, bias-calibrated to real yield)
    try:
        from backend.forecasting.solar import run_physics_model
        phys_df = df.copy()
        phys_df["temp_air"] = df["temperature_2m"]
        phys_df["wind_speed"] = df.get("wind_speed_10m", 0.0)
        if "ghi" not in phys_df.columns and "shortwave_radiation" in phys_df.columns:
            phys_df["ghi"] = phys_df["shortwave_radiation"]
        if "dni" not in phys_df.columns and "direct_normal_irradiance" in phys_df.columns:
            phys_df["dni"] = phys_df["direct_normal_irradiance"]
        if "dhi" not in phys_df.columns and "diffuse_radiation" in phys_df.columns:
            phys_df["dhi"] = phys_df["diffuse_radiation"]
        if "temp_air" not in phys_df.columns and "temperature_2m" in phys_df.columns:
            phys_df = phys_df.rename(columns={"temperature_2m": "temp_air"})
        sp = {
            "latitude": lat, "longitude": lon,
            "altitude": altitude, "capacity_kw": capacity_kw,
            "surface_tilt": surface_tilt, "surface_azimuth": surface_azimuth,
        }
        bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
        physics_kw = run_physics_model(phys_df, sp) * bias
        df["physics_estimate_kw"] = np.round(physics_kw.astype(float), 3)
    except Exception:
        df["physics_estimate_kw"] = 0.0

    return df


def _build_surge_wind_features(df: pd.DataFrame,
                               rated_capacity_kw: float = 100.0) -> pd.DataFrame:
    """SURGE's exact wind feature pipeline for inference."""
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Normalize column names
    if "temperature" in df.columns and "temperature_2m" not in df.columns:
        df["temperature_2m"] = df["temperature"]
    if "pressure" in df.columns and "surface_pressure" not in df.columns:
        df["surface_pressure"] = df["pressure"]
    if "wind_speed" in df.columns and "wind_speed_10m" not in df.columns:
        df["wind_speed_10m"] = df["wind_speed"]

    for col in ["temperature_2m", "surface_pressure", "wind_speed_10m"]:
        if col not in df.columns:
            df[col] = 0.0

    # Wind direction decomposition
    if "wind_direction" in df.columns:
        df["wind_dir_sin"] = np.sin(np.radians(df["wind_direction"]))
        df["wind_dir_cos"] = np.cos(np.radians(df["wind_direction"]))
    else:
        df["wind_dir_sin"] = 0.0
        df["wind_dir_cos"] = 0.0

    # 100m wind speed
    if "wind_speed_100m" not in df.columns:
        alpha = 0.14
        df["wind_speed_100m"] = df["wind_speed_10m"] * (100 / 10) ** alpha
    if "wind_gusts_10m" not in df.columns:
        df["wind_gusts_10m"] = df["wind_speed_10m"] * 1.3

    # Air density
    R_specific = 287.05
    df["air_density"] = (df["surface_pressure"] * 100) / (R_specific * (df["temperature_2m"] + 273.15))

    # Cyclical time
    hour = df["timestamp"].dt.hour
    df["hour_sin"] = np.round(np.sin(2 * np.pi * hour / 24.0), 4)
    df["hour_cos"] = np.round(np.cos(2 * np.pi * hour / 24.0), 4)

    month = df["timestamp"].dt.month
    df["month_sin"] = np.round(np.sin(2 * np.pi * month / 12.0), 4)
    df["month_cos"] = np.round(np.cos(2 * np.pi * month / 12.0), 4)

    doy = df["timestamp"].dt.dayofyear
    df["day_of_year_sin"] = np.round(np.sin(2 * np.pi * doy / 365.25), 4)
    df["day_of_year_cos"] = np.round(np.cos(2 * np.pi * doy / 365.25), 4)

    # Rolling stats
    df["wind_speed_rolling_3h"] = np.round(df["wind_speed_10m"].rolling(3, min_periods=1).mean(), 2)
    df["wind_speed_rolling_6h"] = np.round(df["wind_speed_10m"].rolling(6, min_periods=1).mean(), 2)

    # Physics-informed feature: IEC power curve at 10m (same formula as data generator)
    try:
        from backend.forecasting.features import power_curve_estimate
        df["power_curve_estimate"] = df["wind_speed_10m"].apply(
            lambda v: power_curve_estimate(v, v_cutin=3.0, v_rated=12.0, v_cutout=25.0,
                                           p_rated_kw=rated_capacity_kw)
        )
    except Exception:
        df["power_curve_estimate"] = 0.0

    # Weather-persistence features (computable from forecast weather at serving)
    _ws = df["wind_speed_10m"]
    df["wind_speed_lag_1h"] = np.round(_ws.shift(1).fillna(0.0), 3)
    df["wind_speed_lag_6h"] = np.round(_ws.shift(6).fillna(0.0), 3)

    return df


# ─── Physics Constraints (SURGE) ──────────────────────────────
def _apply_solar_physics(preds: np.ndarray, df: pd.DataFrame, capacity: float) -> np.ndarray:
    """SURGE solar: nighttime / no-irradiance zero-power enforcement."""
    result = preds.copy()

    night_mask = np.zeros(len(result), dtype=bool)
    if "solar_elevation" in df.columns:
        night_mask |= (df["solar_elevation"].values <= 0.0)
    if "shortwave_radiation" in df.columns:
        night_mask |= (df["shortwave_radiation"].values <= 1.0)
    result[night_mask] = 0.0

    return np.clip(result, 0.0, capacity)


def _apply_wind_physics(preds: np.ndarray, df: pd.DataFrame, capacity: float) -> np.ndarray:
    """SURGE wind: cut-in (<3 m/s) and cut-out (>=25 m/s) enforcement.

    Gate on the SAME 10 m wind speed the power-curve feature and the turbine
    model use (wind_speed_10m), NOT the extrapolated 100 m value — otherwise
    high-wind hours (10 m >= ~18 m/s) are falsely cut even though the turbine
    is still producing at rated.
    """
    result = preds.copy()

    ws_col = "wind_speed_10m" if "wind_speed_10m" in df.columns else "wind_speed"
    if ws_col in df.columns:
        w = df[ws_col].values
        cut_mask = (w < 3.0) | (w >= 25.0)
        result[cut_mask] = 0.0

    return np.clip(result, 0.0, capacity)


def _enforce_monotonicity(p10: np.ndarray, p50: np.ndarray, p90: np.ndarray) -> tuple:
    """Ensure p10 <= p50 <= p90 element-wise."""
    p10 = np.minimum(p10, p50)
    p90 = np.maximum(p90, p50)
    return p10, p50, p90


def _add_site_context(df: pd.DataFrame, lat: float, lon: float,
                     elevation: float, surface_tilt: float, surface_azimuth: float) -> pd.DataFrame:
    """Append site-context features used by the generic multi-site models.

    These continuously-valued columns are what let the model interpolate across
    climates and plant geometry instead of memorising a site id."""
    ctx = {
        "latitude": lat, "abs_latitude": abs(lat), "longitude": lon,
        "elevation_m": elevation, "surface_tilt": surface_tilt,
        "surface_azimuth": surface_azimuth,
    }
    for k, v in ctx.items():
        if k not in df.columns:
            df[k] = v
    return df


def _apply_calibrated_bands(p10: np.ndarray, p50: np.ndarray, p90: np.ndarray,
                            calibration: dict, capacity: float = 100.0) -> tuple:
    """Scale deviation bands around p50 then widen by the conformal CQR margin."""
    band_scale = calibration.get("band_scale", 1.0)
    margin = calibration.get("cqr_margin_kw", 0.0)
    d10 = np.clip(p50 - p10, 1e-6, None)
    d90 = np.clip(p90 - p50, 1e-6, None)
    p10 = np.clip(p50 - band_scale * d10 - margin, 0, capacity)
    p90 = np.clip(p50 + band_scale * d90 + margin, 0, capacity)
    return _enforce_monotonicity(p10, p50, p90)


# ─── Predictions ───────────────────────────────────────────────
def predict_solar(weather_df: pd.DataFrame, latitude: float, longitude: float,
                  capacity_kw: float = 100,
                  altitude: float = 210.0, surface_tilt: float = 26.0,
                  surface_azimuth: float = 180.0) -> dict:
    """
    SURGE-inspired solar prediction with XGBoost + physics constraints.

    Capacity handling: features (incl. physics_estimate_kw) are ALWAYS built at
    the model's trained 100 kW scale, and point + quantile outputs are scaled
    linearly by capacity_kw/100 afterwards.  This matters for hybrid sites where
    capacity_kw < 100 (feature-scale-capacity mismatches otherwise inflate bias).
    """
    model, feature_cols = _load_solar_model()

    # Build SURGE features (fixed 100 kW physics scale, as trained) + site context
    df = _build_surge_solar_features(weather_df.copy(), latitude, longitude,
                                     100.0, altitude, surface_tilt, surface_azimuth)
    _add_site_context(df, latitude, longitude, altitude, surface_tilt, surface_azimuth)

    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols].fillna(0)

    # Point prediction
    ml_pred = np.clip(model.predict(X), 0, 100.0)
    ml_pred = _apply_solar_physics(ml_pred, df, 100.0)
    ml_pred = np.clip(ml_pred * (capacity_kw / 100.0), 0, capacity_kw)

    # Quantile predictions (SURGE quantile forecaster)
    q_data = _load_solar_quantile()
    if q_data is not None:
        try:
            q_models = q_data["models"]
            q_features = q_data["feature_columns"]
            q_X = df[[c for c in q_features if c in df.columns]].fillna(0)

            p10 = np.clip(q_models["p10"].predict(q_X), 0, 100.0)
            p50 = np.clip(q_models["p50"].predict(q_X), 0, 100.0)
            p90 = np.clip(q_models["p90"].predict(q_X), 0, 100.0)

            # Apply physics constraints
            p10 = _apply_solar_physics(p10, df, 100.0)
            p50 = _apply_solar_physics(p50, df, 100.0)
            p90 = _apply_solar_physics(p90, df, 100.0)

            # Enforce monotonicity
            p10, p50, p90 = _enforce_monotonicity(p10, p50, p90)

            # Band calibration: deviation scaling around p50 + conformal CQR margin
            p10, p50, p90 = _apply_calibrated_bands(
                p10, p50, p90, _load_solar_calibration())
            # Scale to requested capacity (features stay at trained 100 kW scale)
            s = capacity_kw / 100.0
            p10 = np.clip(p10 * s, 0, capacity_kw)
            p50 = np.clip(p50 * s, 0, capacity_kw)
            p90 = np.clip(p90 * s, 0, capacity_kw)
        except Exception:
            # Fallback: GHI-dependent heuristic bands
            ghi = df["shortwave_radiation"].values if "shortwave_radiation" in df.columns else np.zeros(len(df))
            ghi_factor = np.clip(ghi / 800, 0, 1)
            uncertainty = capacity_kw * 0.1 * (0.3 + 0.7 * ghi_factor)
            p10 = np.clip(ml_pred - uncertainty * 1.28, 0, capacity_kw)
            p50 = ml_pred.copy()
            p90 = np.clip(ml_pred + uncertainty * 1.28, 0, capacity_kw)
    else:
        ghi = df["shortwave_radiation"].values if "shortwave_radiation" in df.columns else np.zeros(len(df))
        ghi_factor = np.clip(ghi / 800, 0, 1)
        uncertainty = capacity_kw * 0.1 * (0.3 + 0.7 * ghi_factor)
        p10 = np.clip(ml_pred - uncertainty * 1.28, 0, capacity_kw)
        p50 = ml_pred.copy()
        p90 = np.clip(ml_pred + uncertainty * 1.28, 0, capacity_kw)

    # Final monotonicity pass
    p10, p50, p90 = _enforce_monotonicity(p10, p50, p90)

    timestamps = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist() if "timestamp" in df.columns else []

    return {
        "model_type": "surge_solar_xgboost",
        "timestamps": timestamps,
        "p10": p10.tolist(),
        "p50": p50.tolist(),
        "p90": p90.tolist(),
        "ml_prediction": ml_pred.tolist(),
        "feature_count": len(available_cols),
        "capacity_kw": capacity_kw,
    }


def predict_wind(weather_df: pd.DataFrame, hub_height: float = 80.0,
                 rated_capacity_kw: float = 100,
                 latitude: float = 26.9157, longitude: float = 70.9083,
                 altitude: float = 225.0) -> dict:
    """
    SURGE-inspired wind prediction with LightGBM + physics constraints.

    Capacity handling mirrors predict_solar: features (incl. power_curve_estimate)
    are built at the trained 100 kW scale; point + quantile outputs are scaled
    linearly by rated_capacity_kw/100 afterwards.
    """
    model, feature_cols = _load_wind_model()

    # Build SURGE features (fixed 100 kW physics scale, as trained) + site context
    df = _build_surge_wind_features(weather_df.copy(), 100.0)
    _add_site_context(df, latitude, longitude, altitude, 0.0, 0.0)

    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols].fillna(0)

    # Point prediction
    ml_pred = np.clip(model.predict(X), 0, 100.0)
    ml_pred = _apply_wind_physics(ml_pred, df, 100.0)
    ml_pred = np.clip(ml_pred * (rated_capacity_kw / 100.0), 0, rated_capacity_kw)

    # Quantile predictions
    q_data = _load_wind_quantile()
    if q_data is not None:
        try:
            q_models = q_data["models"]
            q_features = q_data["feature_columns"]
            q_X = df[[c for c in q_features if c in df.columns]].fillna(0)

            p10 = np.clip(q_models["p10"].predict(q_X), 0, 100.0)
            p50 = np.clip(q_models["p50"].predict(q_X), 0, 100.0)
            p90 = np.clip(q_models["p90"].predict(q_X), 0, 100.0)

            p10 = _apply_wind_physics(p10, df, 100.0)
            p50 = _apply_wind_physics(p50, df, 100.0)
            p90 = _apply_wind_physics(p90, df, 100.0)

            p10, p50, p90 = _enforce_monotonicity(p10, p50, p90)

            # Band calibration: deviation scaling around p50 + conformal CQR margin
            p10, p50, p90 = _apply_calibrated_bands(
                p10, p50, p90, _load_wind_calibration())
            # Scale to requested capacity (features stay at trained 100 kW scale)
            s = rated_capacity_kw / 100.0
            p10 = np.clip(p10 * s, 0, rated_capacity_kw)
            p50 = np.clip(p50 * s, 0, rated_capacity_kw)
            p90 = np.clip(p90 * s, 0, rated_capacity_kw)
        except Exception:
            wind = df["wind_speed_10m"].values if "wind_speed_10m" in df.columns else np.zeros(len(df))
            uncertainty = rated_capacity_kw * 0.12 * (0.3 + 0.7 * np.clip(wind / 15, 0, 1))
            p10 = np.clip(ml_pred - uncertainty, 0, rated_capacity_kw)
            p50 = ml_pred.copy()
            p90 = np.clip(ml_pred + uncertainty, 0, rated_capacity_kw)
    else:
        wind = df["wind_speed_10m"].values if "wind_speed_10m" in df.columns else np.zeros(len(df))
        uncertainty = rated_capacity_kw * 0.12 * (0.3 + 0.7 * np.clip(wind / 15, 0, 1))
        p10 = np.clip(ml_pred - uncertainty, 0, rated_capacity_kw)
        p50 = ml_pred.copy()
        p90 = np.clip(ml_pred + uncertainty, 0, rated_capacity_kw)

    p10, p50, p90 = _enforce_monotonicity(p10, p50, p90)

    timestamps = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist() if "timestamp" in df.columns else []

    return {
        "model_type": "surge_wind_xgboost",
        "timestamps": timestamps,
        "p10": p10.tolist(),
        "p50": p50.tolist(),
        "p90": p90.tolist(),
        "prediction": p50.tolist(),
        "feature_count": len(available_cols),
        "rated_capacity_kw": rated_capacity_kw,
    }


def predict_hybrid(df: pd.DataFrame, latitude: float, longitude: float,
                   capacity_kw: float = 100, solar_share: float = 0.6) -> dict:
    """Hybrid site = solar + wind."""
    solar_kw = capacity_kw * solar_share
    wind_kw = capacity_kw * (1 - solar_share)

    solar = predict_solar(df, latitude, longitude, solar_kw)
    wind = predict_wind(df.copy(), hub_height=80, rated_capacity_kw=wind_kw,
                        latitude=latitude, longitude=longitude)

    p50 = np.array(solar["p50"]) + np.array(wind["p50"])
    p10 = np.array(solar["p10"]) + np.array(wind["p10"])
    p90 = np.array(solar["p90"]) + np.array(wind["p90"])

    p10, p50, p90 = _enforce_monotonicity(p10, p50, p90)

    return {
        "model_type": "surge_hybrid",
        "timestamps": solar["timestamps"],
        "p10": np.clip(p10, 0, capacity_kw).tolist(),
        "p50": np.clip(p50, 0, capacity_kw).tolist(),
        "p90": np.clip(p90, 0, capacity_kw).tolist(),
        "feature_count": solar["feature_count"] + wind["feature_count"],
        "capacity_kw": capacity_kw,
        "solar_share": solar_share,
        "solar": solar["p50"],
        "wind": wind["p50"],
    }


def predict_from_weather_records(records: list, site_type: str,
                                 latitude: float, longitude: float,
                                 capacity_kw: float) -> dict:
    """Take raw WeatherData dicts from DB, build features, and predict."""
    if not records:
        return None

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    col_map = {"temperature": "temp_air", "wind_speed": "wind_speed"}
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    if site_type == "wind":
        return predict_wind(df, hub_height=80, rated_capacity_kw=capacity_kw,
                            latitude=latitude, longitude=longitude)
    elif site_type == "hybrid":
        return predict_hybrid(df, latitude, longitude, capacity_kw)
    else:
        return predict_solar(df, latitude, longitude, capacity_kw)


def reload_models():
    """Force reload all models (after retraining)."""
    global _solar_model, _solar_features, _solar_quantile, _solar_calibration
    global _wind_model, _wind_features, _wind_quantile, _wind_calibration

    _solar_model = None
    _solar_features = None
    _solar_quantile = None
    _solar_calibration = None
    _wind_model = None
    _wind_features = None
    _wind_quantile = None
    _wind_calibration = None

    try:
        _load_solar_model()
        _load_solar_quantile()
    except FileNotFoundError:
        pass
    try:
        _load_wind_model()
        _load_wind_quantile()
    except FileNotFoundError:
        pass

    print("SURGE models reloaded")
