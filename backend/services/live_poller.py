"""
Live Data Polling Service - Scheduled Open-Meteo sync
"""
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import async_session
from backend.models_db import Site, WeatherData
from backend.weather.provider import fetch_historical_weather, fetch_forecast_weather
from backend.forecasting.anomaly import AnomalyDetector

logger = logging.getLogger(__name__)

class LiveDataPoller:
    def __init__(self):
        self.running = False
        self.poll_interval_minutes = 15
        self.anomaly_detector = AnomalyDetector()

    async def start(self):
        self.running = True
        logger.info("LiveDataPoller started")
        while self.running:
            try:
                await self._poll_all_sites()
            except Exception as e:
                logger.error(f"Polling error: {e}")
            await asyncio.sleep(self.poll_interval_minutes * 60)

    async def stop(self):
        self.running = False
        logger.info("LiveDataPoller stopped")

    async def _poll_all_sites(self):
        async with async_session() as db:
            result = await db.execute(
                select(Site).where(Site.is_active == True)
            )
            sites = result.scalars().all()

            for site in sites:
                try:
                    await self._poll_site(site, db)
                except Exception as e:
                    logger.error(f"Error polling site {site.id}: {e}")

    async def _poll_site(self, site: Site, db: AsyncSession):
        logger.info(f"Polling site: {site.name} ({site.latitude}, {site.longitude})")

        try:
            forecast_df = await fetch_forecast_weather(
                latitude=site.latitude,
                longitude=site.longitude,
                days=3,
            )

            existing = await db.execute(
                select(WeatherData.timestamp).where(WeatherData.site_id == site.id)
            )
            existing_ts = set(existing.scalars().all())

            added = 0
            for _, row in forecast_df.iterrows():
                ts = pd.Timestamp(row["timestamp"]).tz_localize(None).to_pydatetime()
                if ts in existing_ts:
                    continue
                weather = WeatherData(
                    site_id=site.id,
                    timestamp=ts,
                    ghi=row.get("ghi"),
                    dni=row.get("dni"),
                    dhi=row.get("dhi"),
                    temperature=row.get("temp_air"),
                    wind_speed=row.get("wind_speed"),
                    wind_direction=row.get("wind_direction"),
                    humidity=row.get("humidity"),
                    cloud_cover=row.get("cloud_cover"),
                    pressure=row.get("pressure"),
                    source="open-meteo-forecast",
                )
                db.add(weather)
                existing_ts.add(ts)
                added += 1

            await db.commit()
            logger.info(f"Saved {added} new weather records for {site.name}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to fetch weather for {site.name}: {e}")

    async def poll_single_site(self, site_id: str):
        async with async_session() as db:
            result = await db.execute(select(Site).where(Site.id == site_id))
            site = result.scalar_one_or_none()
            if site:
                await self._poll_site(site, db)

poller = LiveDataPoller()
