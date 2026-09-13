"""
Lambda Architecture for GridMind AI
- Batch Layer: Historical data processing, model training
- Speed Layer: Real-time forecast updates
- Serving Layer: Merged view for API
"""
import os
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = DATA_DIR / "cache"

for d in [DATA_DIR / "raw", DATA_DIR / "processed", DATA_DIR / "sample", MODELS_DIR / "solar", MODELS_DIR / "wind", MODELS_DIR / "metrics", CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class BatchLayer:
    """Processes historical data and trains models offline."""

    def __init__(self):
        self.raw_dir = DATA_DIR / "raw"
        self.processed_dir = DATA_DIR / "processed"
        self.models_dir = MODELS_DIR

    def load_historical_data(self, source: str) -> pd.DataFrame:
        cache_file = self.processed_dir / f"{source}_processed.parquet"
        if cache_file.exists():
            return pd.read_parquet(cache_file)
        raw_file = self.raw_dir / f"{source}.csv"
        if raw_file.exists():
            df = pd.read_csv(raw_file)
            df = self._clean(df, source)
            df.to_parquet(cache_file)
            return df
        return pd.DataFrame()

    def _clean(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        if "timestamp" not in df.columns and "date" in df.columns:
            df.rename(columns={"date": "timestamp"}, inplace=True)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = df[col].fillna(df[col].median())
        return df

    def prepare_features(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        df = df.copy()
        if "timestamp" in df.columns:
            df["hour"] = df["timestamp"].dt.hour
            df["day_of_year"] = df["timestamp"].dt.dayofyear
            df["month"] = df["timestamp"].dt.month

        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        if source_type == "solar":
            df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
            df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)

        if "generation_kw" in df.columns:
            for lag in [1, 24]:
                df[f"lag_{lag}h"] = df["generation_kw"].shift(lag)
            df["rolling_mean_24h"] = df["generation_kw"].shift(1).rolling(24).mean()
            df["rolling_std_24h"] = df["generation_kw"].shift(1).rolling(24).std()

        df = df.dropna()
        return df

    def save_model(self, model, name: str, model_type: str):
        model_dir = self.models_dir / model_type
        model_dir.mkdir(exist_ok=True)
        if hasattr(model, "save_model"):
            model.save_model(str(model_dir / f"{name}.json"))
        elif hasattr(model, "booster_"):
            model.booster_.save_model(str(model_dir / f"{name}.txt"))

    def load_model(self, name: str, model_type: str):
        import xgboost as xgb
        import lightgbm as lgb
        model_path = self.models_dir / model_type / f"{name}"
        if (model_path).with_suffix(".json").exists():
            model = xgb.XGBRegressor()
            model.load_model(str(model_path.with_suffix(".json")))
            return model
        elif (model_path).with_suffix(".txt").exists():
            return lgb.Booster(model_file=str(model_path.with_suffix(".txt")))
        return None


class SpeedLayer:
    """Handles real-time forecast updates using cached models."""

    def __init__(self, batch_layer: BatchLayer):
        self.batch = batch_layer
        self._cache = {}

    async def get_realtime_forecast(self, site_id: int, weather_forecast: pd.DataFrame) -> dict:
        cache_key = f"forecast_{site_id}_{datetime.now().hour}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        solar_model = self.batch.load_model("solar_hybrid", "solar")
        wind_model = self.batch.load_model("wind_lgbm", "wind")

        result = {
            "timestamp": datetime.now().isoformat(),
            "site_id": site_id,
            "solar_forecast": None,
            "wind_forecast": None,
        }

        if solar_model is not None and "ghi" in weather_forecast.columns:
            features = self._prepare_solar_features(weather_forecast)
            solar_pred = solar_model.predict(features)
            result["solar_forecast"] = np.clip(solar_pred, 0, None).tolist()

        if wind_model is not None and "wind_speed" in weather_forecast.columns:
            features = self._prepare_wind_features(weather_forecast)
            wind_pred = wind_model.predict(features)
            result["wind_forecast"] = np.clip(wind_pred, 0, None).tolist()

        self._cache[cache_key] = result
        return result

    def _prepare_solar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_cols = ["ghi", "dni", "dhi", "temp_air", "wind_speed", "hour_sin", "hour_cos"]
        available = [c for c in feature_cols if c in df.columns]
        return df[available].fillna(0)

    def _prepare_wind_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_cols = ["wind_speed", "wind_direction", "temp_air", "pressure", "hour_sin", "hour_cos"]
        available = [c for c in feature_cols if c in df.columns]
        return df[available].fillna(0)


class ServingLayer:
    """Merges batch and speed layer outputs for API consumption."""

    def __init__(self):
        self.batch = BatchLayer()
        self.speed = SpeedLayer(self.batch)

    async def get_forecast(self, site_id: int, horizon: int = 24) -> dict:
        weather_forecast = await self._fetch_weather(site_id, horizon)
        realtime = await self.speed.get_realtime_forecast(site_id, weather_forecast)

        return {
            "site_id": site_id,
            "horizon_hours": horizon,
            "timestamp": datetime.now().isoformat(),
            "batch_forecast": realtime,
            "weather": weather_forecast.to_dict(orient="records") if not weather_forecast.empty else [],
        }

    async def _fetch_weather(self, site_id: int, horizon: int) -> pd.DataFrame:
        from backend.api.database import get_site
        site = get_site(site_id)
        if not site:
            return pd.DataFrame()
        try:
            from backend.weather.provider import fetch_forecast_weather
            return await fetch_forecast_weather(
                latitude=site["latitude"],
                longitude=site["longitude"],
                days=max(1, horizon // 24 + 1),
            )
        except Exception:
            return pd.DataFrame()


serving_layer = ServingLayer()
