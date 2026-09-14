"""
Bottleneck ML — Feature Engineering
======================================
Transforms raw telemetry + weather + asset metadata into the model feature matrix.

Column name mapping
-------------------
Backend TelemetryRecord (contracts.py) → Training CSV → Feature matrix
  oil_temperature       → oil_temperature       (pass-through, rename below for compactness)
  load_percentage       → load_percentage
  vibration             → vibration
  current_unbalance     → current_unbalance
  voltage_deviation     → voltage_deviation
  partial_discharge     → partial_discharge
  ambient_temperature   → ambient_temperature
  oil_quality           → oil_quality           (derived in generator; default 90 if absent)

Leakage prevention (MODEL.md)
------------------------------
  - All rolling/lag features use only backward-looking windows (min_periods=1 to
    avoid NaN explosions, filled with the first available value).
  - Chronological split is enforced in training, NOT shuffled.
  - Asset-level features (age, cap, criticality …) do NOT depend on the future.

Feature groups
--------------
  Telemetry (rolling stats + trends)  : 20 features
  Weather                             :  8 features
  Asset metadata                      :  7 features
  ─────────────────────────────────────────────────
  Total FEATURE_COLUMNS               : 35 features
"""

from __future__ import annotations
from typing import List

import numpy as np
import pandas as pd

# ─── Canonical feature list (matches XGBoost training) ───────────────────────

TELEMETRY_FEATURE_COLUMNS: List[str] = [
    # oil temperature
    "oil_temp_current",
    "oil_temp_mean_1h",
    "oil_temp_mean_6h",
    "oil_temp_mean_24h",
    "oil_temp_trend",
    # load
    "load_current",
    "load_mean_6h",
    "load_mean_24h",
    "load_max_24h",
    "load_trend",
    # vibration
    "vibration_current",
    "vibration_mean_6h",
    "vibration_trend",
    # partial discharge
    "pd_current",
    "pd_trend",
    # oil quality
    "oil_quality_current",
    "oil_quality_change",
    # current/voltage
    "current_unbalance_current",
    "voltage_deviation_current",
    # ambient temperature
    "ambient_temp_current",
]

WEATHER_FEATURE_COLUMNS: List[str] = [
    "weather_temperature",
    "weather_humidity",
    "weather_precipitation",
    "weather_wind_speed",
    "weather_wind_gust",
    "weather_pressure",
    "weather_cloud_cover",
    "weather_code",          # 1 = severe, 0 = normal
]

ASSET_FEATURE_COLUMNS: List[str] = [
    "asset_age",
    "capacity_mva",
    "customers_served",
    "criticality",
    "redundancy_level",
    "previous_failures",
    "days_since_maintenance",
]

FEATURE_COLUMNS: List[str] = (
    TELEMETRY_FEATURE_COLUMNS +
    WEATHER_FEATURE_COLUMNS +
    ASSET_FEATURE_COLUMNS
)

# ─── Validation constants ─────────────────────────────────────────────────────

TELEMETRY_BOUNDS: dict = {
    "oil_temperature"     : (  0,  200),
    "load_percentage"     : (  0,  110),
    "vibration"           : (  0,   50),
    "current_unbalance"   : (  0,   25),
    "voltage_deviation"   : (  0,   30),
    "partial_discharge"   : (  0,    1),
    "ambient_temperature" : (-10,   60),
    "oil_quality"         : (  0,  100),
}


# ─── Data validation ──────────────────────────────────────────────────────────

def validate_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Flag out-of-range values (clip to physical bounds; log count).
    - Forward-fill ≤5 consecutive NaNs per column per asset; remaining → median.
    - Drop rows where the timestamp is NaT or duplicated within the same asset.
    """
    df = df.copy()

    # Deduplicate
    df = df.drop_duplicates(subset=["asset_id", "timestamp"])

    # Parse timestamps; drop invalid
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    invalid_ts = df["timestamp"].isna().sum()
    if invalid_ts:
        print(f"[FeatureEng] Dropped {invalid_ts} rows with invalid timestamps")
    df = df.dropna(subset=["timestamp"])

    # Sort
    df = df.sort_values(["asset_id", "timestamp"]).reset_index(drop=True)

    # Per-column range enforcement
    clipped_total = 0
    for col, (lo, hi) in TELEMETRY_BOUNDS.items():
        if col in df.columns:
            out_mask = (df[col] < lo) | (df[col] > hi)
            clipped_total += int(out_mask.sum())
            df[col] = df[col].clip(lo, hi)
    if clipped_total:
        print(f"[FeatureEng] Clipped {clipped_total} out-of-range values to physical bounds")

    # Missing value fill (per asset group)
    telem_cols = list(TELEMETRY_BOUNDS.keys())
    for col in telem_cols:
        if col not in df.columns:
            continue
        df[col] = (
            df.groupby("asset_id")[col]
            .transform(lambda s: s.ffill(limit=5).bfill(limit=5))
        )
    # Any remaining NaN → column median (global fallback)
    for col in telem_cols:
        if col in df.columns and df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    return df


def validate_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing weather values with sensible neutral defaults.
    weather_code is encoded to 0/1 if it arrives as a string.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # Normalise string weather_code
    if "weather_code" in df.columns and df["weather_code"].dtype == object:
        df["weather_code"] = df["weather_code"].apply(
            lambda v: 1 if str(v).lower() in ("severe", "storm", "1", "true") else 0
        )

    defaults = dict(temperature=30, humidity=60, precipitation=0,
                    wind_speed=5, wind_gust=7, pressure=1013,
                    cloud_cover=30, weather_code=0)
    for col, val in defaults.items():
        if col in df.columns:
            df[col] = df[col].fillna(val)
        else:
            df[col] = val

    return df


# ─── Telemetry feature engineering ───────────────────────────────────────────

def build_telemetry_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input  : validated telemetry DataFrame with standard backend column names.
    Output : DataFrame with TELEMETRY_FEATURE_COLUMNS added.

    All windows are backward-looking (no data leakage).
    min_periods=1 so early rows in a sequence still get a value (rolling mean
    of 1 observation rather than NaN).
    """
    df = df.copy()
    df = df.sort_values(["asset_id", "timestamp"])

    def _roll(series: pd.Series, w: int) -> pd.Series:
        return series.rolling(w, min_periods=1)

    def _trend(series: pd.Series) -> pd.Series:
        """Simple backward delta: value[t] - value[t-1]. NaN for first row → 0."""
        return series.diff().fillna(0.0)

    g = df.groupby("asset_id", group_keys=False)

    # ── oil temperature ──────────────────────────────────────────────────────
    df["oil_temp_current"]  = df["oil_temperature"]
    df["oil_temp_mean_1h"]  = g["oil_temperature"].transform(lambda s: _roll(s, 1).mean())
    df["oil_temp_mean_6h"]  = g["oil_temperature"].transform(lambda s: _roll(s, 6).mean())
    df["oil_temp_mean_24h"] = g["oil_temperature"].transform(lambda s: _roll(s, 24).mean())
    df["oil_temp_trend"]    = g["oil_temperature"].transform(_trend)

    # ── load ─────────────────────────────────────────────────────────────────
    df["load_current"]  = df["load_percentage"]
    df["load_mean_6h"]  = g["load_percentage"].transform(lambda s: _roll(s, 6).mean())
    df["load_mean_24h"] = g["load_percentage"].transform(lambda s: _roll(s, 24).mean())
    df["load_max_24h"]  = g["load_percentage"].transform(lambda s: _roll(s, 24).max())
    df["load_trend"]    = g["load_percentage"].transform(_trend)

    # ── vibration ────────────────────────────────────────────────────────────
    df["vibration_current"] = df["vibration"]
    df["vibration_mean_6h"] = g["vibration"].transform(lambda s: _roll(s, 6).mean())
    df["vibration_trend"]   = g["vibration"].transform(_trend)

    # ── partial discharge ─────────────────────────────────────────────────────
    df["pd_current"] = df["partial_discharge"]
    df["pd_trend"]   = g["partial_discharge"].transform(_trend)

    # ── oil quality ───────────────────────────────────────────────────────────
    if "oil_quality" not in df.columns:
        df["oil_quality"] = 90.0   # neutral default
    df["oil_quality_current"] = df["oil_quality"]
    df["oil_quality_change"]  = g["oil_quality"].transform(_trend)

    # ── current unbalance & voltage deviation ─────────────────────────────────
    df["current_unbalance_current"] = df["current_unbalance"]
    df["voltage_deviation_current"] = df["voltage_deviation"]

    # ── ambient temperature ───────────────────────────────────────────────────
    df["ambient_temp_current"] = df["ambient_temperature"]

    return df


# ─── Weather feature attachment ───────────────────────────────────────────────

def attach_weather_features(features_df: pd.DataFrame,
                             weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Nearest-timestamp backward merge of weather onto telemetry features.
    If no weather row is available for an asset, fills with neutral defaults.
    """
    w = weather_df.copy()
    w["timestamp"] = pd.to_datetime(w["timestamp"])

    merged_parts = []
    for asset_id, f_grp in features_df.groupby("asset_id"):
        w_grp = w[w["asset_id"] == asset_id].sort_values("timestamp")
        if w_grp.empty:
            merged = f_grp.copy()
            for col in WEATHER_FEATURE_COLUMNS:
                merged[col] = 0.0
        else:
            merged = pd.merge_asof(
                f_grp.sort_values("timestamp"),
                w_grp[["timestamp", "temperature", "humidity", "precipitation",
                        "wind_speed", "wind_gust", "pressure", "cloud_cover",
                        "weather_code"]],
                on="timestamp", direction="backward",
            )
            merged = merged.rename(columns={
                "temperature"  : "weather_temperature",
                "humidity"     : "weather_humidity",
                "precipitation": "weather_precipitation",
                "wind_speed"   : "weather_wind_speed",
                "wind_gust"    : "weather_wind_gust",
                "pressure"     : "weather_pressure",
                "cloud_cover"  : "weather_cloud_cover",
                "weather_code" : "weather_code",
            })
        merged_parts.append(merged)

    result = pd.concat(merged_parts, ignore_index=True)

    # Fill any NaN weather columns
    weather_defaults = dict(
        weather_temperature=30.0, weather_humidity=60.0,
        weather_precipitation=0.0, weather_wind_speed=5.0,
        weather_wind_gust=7.0, weather_pressure=1013.0,
        weather_cloud_cover=30.0, weather_code=0.0,
    )
    for col, val in weather_defaults.items():
        if col in result.columns:
            result[col] = result[col].fillna(val)
        else:
            result[col] = val

    return result


# ─── Asset feature attachment ─────────────────────────────────────────────────

def attach_asset_features(features_df: pd.DataFrame,
                           assets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join asset static features onto the feature matrix.
    Handles both float criticality (contracts.py) and string (gridshield-ml legacy).
    """
    keep = ["asset_id", "asset_age", "capacity_mva", "customers_served",
            "criticality", "redundancy_level", "previous_failures",
            "days_since_maintenance"]
    available = [c for c in keep if c in assets_df.columns]
    merged = features_df.merge(assets_df[available], on="asset_id", how="left")

    # Encode criticality if it arrived as a string (legacy)
    if "criticality" in merged.columns and merged["criticality"].dtype == object:
        crit_map = {"LOW": 0.33, "MEDIUM": 0.66, "HIGH": 1.0}
        merged["criticality"] = merged["criticality"].map(crit_map).fillna(0.5)

    # Fill missing asset features with neutral defaults
    defaults = dict(asset_age=10, capacity_mva=15, customers_served=2000,
                    criticality=0.6, redundancy_level=0.5,
                    previous_failures=1, days_since_maintenance=180)
    for col, val in defaults.items():
        if col in merged.columns:
            merged[col] = merged[col].fillna(val)
        else:
            merged[col] = val

    return merged


# ─── End-to-end pipeline ──────────────────────────────────────────────────────

def build_full_feature_set(telemetry_df: pd.DataFrame,
                            weather_df: pd.DataFrame,
                            assets_df: pd.DataFrame) -> pd.DataFrame:
    """
    Full MODEL.md feature pipeline:
      raw telemetry → validate → rolling features
      → attach weather → attach asset metadata → fill NA → return

    Returns a DataFrame with FEATURE_COLUMNS (35 features) plus asset_id,
    timestamp, and any label columns that were present in the input.
    """
    t = validate_telemetry(telemetry_df)
    w = validate_weather(weather_df)

    features = build_telemetry_features(t)
    features = attach_weather_features(features, w)
    features = attach_asset_features(features, assets_df)

    # Final global NaN fill → should be zero residual after validate + attach
    features[FEATURE_COLUMNS] = features[FEATURE_COLUMNS].fillna(0.0)

    return features


# ─── Single-row feature builder (for live inference) ──────────────────────────

def build_single_row_features(
    *,
    telemetry_history: list[dict],    # list of TelemetryRecord.model_dump() dicts, sorted oldest→newest
    weather: dict,                     # WeatherExposure.model_dump()
    asset: dict,                       # Asset.model_dump()
) -> dict:
    """
    Build the feature vector for a single asset at the current moment.

    This mirrors build_full_feature_set but operates on a short telemetry
    history list (typically the last 24 readings from mock_data.get_telemetry()).

    Returns a flat dict with all FEATURE_COLUMNS keys — ready for XGBoost.
    """
    if not telemetry_history:
        # No telemetry at all — return all-zero features with neutral defaults
        row = {col: 0.0 for col in FEATURE_COLUMNS}
        row["asset_age"] = float(asset.get("age_years", 10))
        row["capacity_mva"] = float(asset.get("capacity_mva", 15))
        row["customers_served"] = float(asset.get("capacity_mva", 2000))
        row["criticality"] = float(asset.get("criticality", 0.5))
        row["redundancy_level"] = float(asset.get("redundancy_level", 0.5))
        row["previous_failures"] = 0.0
        row["days_since_maintenance"] = 365.0
        return row

    # Build a small DataFrame from the history list
    telem_cols = ["asset_id", "timestamp", "oil_temperature", "load_percentage",
                  "vibration", "current_unbalance", "voltage_deviation",
                  "partial_discharge", "ambient_temperature"]
    rows_with_valid_cols = []
    for r in telemetry_history:
        rows_with_valid_cols.append({c: r.get(c, 0.0) for c in telem_cols})

    df = pd.DataFrame(rows_with_valid_cols)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # oil_quality default if not present
    if "oil_quality" not in df.columns:
        df["oil_quality"] = 90.0

    # Validate + compute rolling features
    df = validate_telemetry(df)
    df = build_telemetry_features(df)

    # Take the last (most recent) row
    last = df.iloc[-1]

    feature_row: dict = {}

    # Telemetry features
    for col in TELEMETRY_FEATURE_COLUMNS:
        feature_row[col] = float(last.get(col, 0.0))

    # Weather features
    weather_map = {
        "weather_temperature"  : weather.get("temperature",   30.0),
        "weather_humidity"     : weather.get("humidity",       60.0),
        "weather_precipitation": weather.get("precipitation",   0.0),
        "weather_wind_speed"   : weather.get("wind_speed",      5.0),
        "weather_wind_gust"    : weather.get("wind_speed",      7.0),  # no gust in WeatherExposure
        "weather_pressure"     : 1013.0,
        "weather_cloud_cover"  : 30.0,
        "weather_code"         : float(weather.get("severe_weather_indicator", False)),
    }
    feature_row.update(weather_map)

    # Asset features
    feature_row["asset_age"]              = float(asset.get("age_years", 10))
    feature_row["capacity_mva"]           = float(asset.get("capacity_mva", 15))
    feature_row["customers_served"]       = float(
        asset.get("customers_served", asset.get("capacity_mva", 2000))
    )
    feature_row["criticality"]            = float(asset.get("criticality", 0.5))
    feature_row["redundancy_level"]       = float(asset.get("redundancy_level", 0.5))
    feature_row["previous_failures"]      = float(asset.get("previous_failures", 0))
    feature_row["days_since_maintenance"] = float(asset.get("days_since_maintenance", 365))

    return feature_row
