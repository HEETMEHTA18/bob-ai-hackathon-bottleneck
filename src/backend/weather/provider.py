import ssl
import certifi
import aiohttp
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

HOURLY_PARAMS = "temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m,cloud_cover,pressure_msl,shortwave_radiation,direct_normal_irradiance,global_tilted_irradiance"


def _get_ssl_context():
    return ssl.create_default_context(cafile=certifi.where())


def _parse_hourly(data: dict) -> pd.DataFrame:
    hourly = data.get("hourly", {})
    if "time" not in hourly:
        raise ValueError(f"Open-Meteo error: {data.get('reason', 'unknown')}")

    n = len(hourly["time"])
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "ghi": hourly.get("shortwave_radiation", [0]*n),  # GHI = shortwave_radiation
        "dni": hourly.get("direct_normal_irradiance", [0]*n),
        "dhi": hourly.get("global_tilted_irradiance", [0]*n),
        "temp_air": hourly.get("temperature_2m", [0]*n),
        "wind_speed": hourly.get("wind_speed_10m", [0]*n),
        "wind_direction": hourly.get("wind_direction_10m", [0]*n),
        "humidity": hourly.get("relative_humidity_2m", [0]*n),
        "cloud_cover": hourly.get("cloud_cover", [0]*n),
        "pressure": hourly.get("pressure_msl", [0]*n),
    })

    # Replace None with 0
    df = df.fillna(0)

    return df


async def fetch_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": HOURLY_PARAMS,
        "timezone": "Asia/Kolkata",
    }
    ssl_ctx = _get_ssl_context()
    async with aiohttp.ClientSession() as session:
        async with session.get(OPEN_METEO_ARCHIVE, params=params, ssl=ssl_ctx) as resp:
            data = await resp.json()

    df = _parse_hourly(data)
    df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
    return df


async def fetch_forecast_weather(
    latitude: float,
    longitude: float,
    days: int = 3,
) -> pd.DataFrame:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": days,
        "hourly": HOURLY_PARAMS,
        "timezone": "Asia/Kolkata",
    }
    ssl_ctx = _get_ssl_context()
    async with aiohttp.ClientSession() as session:
        async with session.get(OPEN_METEO_FORECAST, params=params, ssl=ssl_ctx) as resp:
            data = await resp.json()

    df = _parse_hourly(data)
    df["timestamp"] = df["timestamp"].dt.tz_localize("Asia/Kolkata")
    return df
