import numpy as np
import pandas as pd
import pvlib


def add_cyclical_time_features(df: pd.DataFrame, col: str, period: int, prefix: str) -> pd.DataFrame:
    df = df.copy()
    df[f"{prefix}_sin"] = np.sin(2 * np.pi * df[col] / period)
    df[f"{prefix}_cos"] = np.cos(2 * np.pi * df[col] / period)
    return df


def add_solar_position(df: pd.DataFrame, latitude: float, longitude: float) -> pd.DataFrame:
    df = df.copy()
    solpos = pvlib.solarposition.get_solarposition(df.index, latitude, longitude)
    df["solar_elevation"] = solpos["apparent_elevation"].values
    df["solar_azimuth"] = solpos["azimuth"].values
    return df


def add_lag_and_rolling(df: pd.DataFrame, target_col: str,
                        lags=(1, 24), windows=(24,)) -> pd.DataFrame:
    df = df.copy()
    for lag in lags:
        df[f"lag_{lag}h_generation"] = df[target_col].shift(lag)
    for w in windows:
        df[f"rolling_mean_{w}h"] = df[target_col].shift(1).rolling(w).mean()
        df[f"rolling_std_{w}h"] = df[target_col].shift(1).rolling(w).std()
    return df


def air_density(pressure_hpa: pd.Series, temp_c: pd.Series) -> pd.Series:
    R_specific = 287.05
    return (pressure_hpa * 100) / (R_specific * (temp_c + 273.15))


def power_curve_estimate(v: float, v_cutin: float = 3.0, v_rated: float = 12.0,
                         v_cutout: float = 25.0, p_rated_kw: float = 100.0) -> float:
    if v < v_cutin or v > v_cutout:
        return 0.0
    if v >= v_rated:
        return p_rated_kw
    return p_rated_kw * ((v - v_cutin) / (v_rated - v_cutin)) ** 3


def prepare_solar_features(df: pd.DataFrame, latitude: float, longitude: float) -> pd.DataFrame:
    df = df.copy()
    if "timestamp" in df.columns and "hour" not in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    elif df.index.name == "timestamp":
        df = df.reset_index()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    if "hour" not in df.columns:
        df["hour"] = df["timestamp"].dt.hour
    if "day_of_year" not in df.columns:
        df["day_of_year"] = df["timestamp"].dt.dayofyear
    if "month" not in df.columns:
        df["month"] = df["timestamp"].dt.month

    df = add_cyclical_time_features(df, "hour", 24, "hour")
    df = add_cyclical_time_features(df, "day_of_year", 365, "doy")
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("Asia/Kolkata")
        df = df.set_index(ts)
    df = add_solar_position(df, latitude, longitude)
    df = df.reset_index(drop=True)
    if "timestamp" in df.columns:
        pd.to_datetime(df["timestamp"], errors="coerce")
        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("Asia/Kolkata")
        df["timestamp"] = ts
    df = add_lag_and_rolling(df, "generation_kw")

    if "clearsky_index" not in df.columns and "ghi" in df.columns:
        df["clearsky_index"] = df["ghi"] / df["ghi"].rolling(24, min_periods=1).max().clip(lower=1)

    if "cloud_cover" in df.columns:
        df["cloud_cover_pct"] = df["cloud_cover"]
    else:
        df["cloud_cover_pct"] = 0.0

    return df


def prepare_wind_features(df: pd.DataFrame, hub_height: float = 80.0,
                          rated_capacity_kw: float = 100.0) -> pd.DataFrame:
    df = df.copy()
    if "hour" not in df.columns:
        df["hour"] = df["timestamp"].dt.hour
    if "month" not in df.columns:
        df["month"] = df["timestamp"].dt.month

    df = add_cyclical_time_features(df, "hour", 24, "hour")
    df = add_cyclical_time_features(df, "month", 12, "month")

    alpha = 0.14
    df["wind_speed_hub"] = df["wind_speed"] * (hub_height / 10) ** alpha

    if "wind_direction" in df.columns:
        df["wind_dir_sin"] = np.sin(np.radians(df["wind_direction"]))
        df["wind_dir_cos"] = np.cos(np.radians(df["wind_direction"]))
    else:
        df["wind_dir_sin"] = 0.0
        df["wind_dir_cos"] = 0.0

    if "pressure" in df.columns and "temp_air" in df.columns:
        df["air_density"] = air_density(df["pressure"], df["temp_air"])
    else:
        df["air_density"] = 1.225

    if "wind_speed" in df.columns:
        df["power_curve_estimate"] = df["wind_speed_hub"].apply(
            lambda v: power_curve_estimate(v, p_rated_kw=rated_capacity_kw)
        )
        df["wind_speed_std_3h"] = df["wind_speed"].rolling(3, min_periods=1).std()
    else:
        df["power_curve_estimate"] = 0.0
        df["wind_speed_std_3h"] = 0.0

    df["turbine_rated_capacity_kw"] = rated_capacity_kw

    df = add_lag_and_rolling(df, "generation_kw", lags=(1, 24), windows=(6,))

    return df


SOLAR_FEATURE_COLS = [
    "ghi", "dni", "dhi", "temp_air", "wind_speed", "humidity", "cloud_cover_pct",
    "hour_sin", "hour_cos", "doy_sin", "doy_cos",
    "solar_elevation", "solar_azimuth", "clearsky_index",
    "lag_1h_generation", "lag_24h_generation",
    "rolling_mean_24h", "rolling_std_24h", "physics_estimate_kw",
]

WIND_FEATURE_COLS = [
    "wind_speed_10m", "wind_speed_hub", "wind_direction_deg",
    "wind_dir_sin", "wind_dir_cos",
    "air_temp", "pressure", "air_density",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "lag_1h_generation", "lag_24h_generation",
    "rolling_mean_6h", "turbine_rated_capacity_kw",
    "power_curve_estimate", "wind_speed_std_3h",
]
