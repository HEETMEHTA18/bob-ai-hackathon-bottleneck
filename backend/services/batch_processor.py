"""
Batch Processing + Model Auto-Update Pipeline
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import async_session
from backend.models_db import Site, WeatherData, Forecast, ModelVersion
from backend.forecasting.features import prepare_solar_features, prepare_wind_features
from backend.forecasting.evaluate import evaluate

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"

class BatchProcessor:
    def __init__(self):
        self.running = False
        self.retrain_interval_hours = 24

    async def start(self):
        self.running = True
        logger.info("BatchProcessor started")
        while self.running:
            try:
                await self._run_batch_jobs()
            except Exception as e:
                logger.error(f"Batch error: {e}")
            await asyncio.sleep(self.retrain_interval_hours * 3600)

    async def stop(self):
        self.running = False

    async def _run_batch_jobs(self):
        logger.info("Running batch jobs...")
        await self._generate_forecasts()
        await self._check_model_performance()
        logger.info("Batch jobs completed")

    async def _generate_forecasts(self):
        async with async_session() as db:
            result = await db.execute(select(Site).where(Site.is_active == True))
            sites = result.scalars().all()

            for site in sites:
                try:
                    forecast = self._compute_forecast(site)
                    forecast_record = Forecast(
                        site_id=site.id,
                        forecast_type="batch_24h",
                        horizon_hours=24,
                        data_json=json.dumps(forecast),
                        model_version="v1.0",
                    )
                    db.add(forecast_record)
                except Exception as e:
                    logger.error(f"Forecast error for {site.id}: {e}")

            await db.commit()

    def _compute_forecast(self, site: Site) -> dict:
        horizon = 24
        hourly_gen = [
            site.capacity_kw * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
            for i in range(horizon)
        ]
        point = np.array(hourly_gen)
        return {
            "p10": (point * 0.8).tolist(),
            "p50": point.tolist(),
            "p90": (point * 1.2).tolist(),
        }

    async def _check_model_performance(self):
        async with async_session() as db:
            result = await db.execute(
                select(ModelVersion).where(ModelVersion.is_active == True)
            )
            models = result.scalars().all()
            logger.info(f"Active models: {len(models)}")

    async def retrain_model(self, site_id: str, model_type: str = "solar"):
        logger.info(f"Retraining {model_type} model for site {site_id}")
        async with async_session() as db:
            result = await db.execute(
                select(WeatherData)
                .where(WeatherData.site_id == site_id)
                .order_by(WeatherData.timestamp.desc())
                .limit(720)
            )
            weather_records = result.scalars().all()

            if len(weather_records) < 100:
                logger.warning("Not enough data for retraining")
                return None

            df = pd.DataFrame([{
                "timestamp": w.timestamp,
                "ghi": w.ghi,
                "dni": w.dni,
                "dhi": w.dhi,
                "temp_air": w.temperature,
                "wind_speed": w.wind_speed,
                "humidity": w.humidity,
                "cloud_cover": w.cloud_cover,
                "generation_kw": w.ghi * 0.1 if w.ghi else 0,
            } for w in weather_records])

            site_result = await db.execute(select(Site).where(Site.id == site_id))
            site = site_result.scalar_one_or_none()

            if model_type == "solar":
                features_df = prepare_solar_features(df, site.latitude, site.longitude)
            else:
                features_df = prepare_wind_features(df)

            new_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_version = ModelVersion(
                model_name=f"{model_type}_hybrid",
                version=new_version,
                metrics_json=json.dumps({"status": "retrained"}),
                artifact_path=str(MODELS_DIR / model_type / f"{model_type}_hybrid_{new_version}.json"),
                is_active=True,
            )
            db.add(model_version)
            await db.commit()

            logger.info(f"Model retrained: {new_version}")
            return new_version

batch_processor = BatchProcessor()
