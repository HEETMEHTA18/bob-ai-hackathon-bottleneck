"""
GridShield — Weather Adapter.

Reuses Open-Meteo infrastructure from Gridkavach but transforms weather
data into asset exposure scores for grid equipment risk assessment.

Falls back to deterministic mock data when the external API is unavailable,
ensuring the application works in demo mode without credentials.
"""
from __future__ import annotations
import asyncio
from typing import Optional
from datetime import datetime

from backend.gridshield.contracts import Asset, WeatherExposure

# ─── Mock weather base (per-region) ─────────────────────────────────────────
# Deterministic mock: each region has a fixed weather profile.
# Severe weather is simulated for North (storm exposure).

_REGION_WEATHER: dict[str, dict] = {
    "North":   dict(temp=38.5, wind=9.2,  precip=18.0, humid=72, storm=0.75, heatwave=True,  severe=True),
    "South":   dict(temp=34.0, wind=6.5,  precip=5.0,  humid=65, storm=0.30, heatwave=False, severe=False),
    "East":    dict(temp=35.5, wind=7.0,  precip=8.0,  humid=68, storm=0.45, heatwave=False, severe=False),
    "West":    dict(temp=36.0, wind=7.8,  precip=10.0, humid=70, storm=0.50, heatwave=True,  severe=False),
    "Central": dict(temp=37.0, wind=6.0,  precip=4.0,  humid=62, storm=0.20, heatwave=True,  severe=False),
}

_DEFAULT_WEATHER = dict(temp=35.0, wind=7.0, precip=8.0, humid=65, storm=0.35, heatwave=False, severe=False)


def _compute_exposure_score(temp: float, wind: float, precip: float,
                             storm: float, heatwave: bool, severe: bool) -> float:
    """
    Composite weather exposure score (0–1) for grid equipment.

    High temperature → thermal stress on transformers.
    High wind → mechanical stress on lines and equipment.
    Precipitation → insulation/flashover risk.
    Storm severity → direct exposure risk.
    """
    temp_score   = min(1.0, max(0.0, (temp  - 25.0) / 25.0))   # 25–50°C range
    wind_score   = min(1.0, max(0.0, (wind  -  3.0) / 17.0))   # 3–20 m/s range
    precip_score = min(1.0, max(0.0, precip          / 50.0))   # 0–50 mm/h range
    storm_score  = storm

    raw = (
        0.30 * temp_score
        + 0.20 * wind_score
        + 0.20 * precip_score
        + 0.30 * storm_score
    )
    bonus = 0.1 if heatwave else 0.0
    bonus += 0.15 if severe else 0.0
    return round(min(1.0, max(0.0, raw + bonus)), 4)


def get_weather_exposure(asset: Asset, scenario: Optional[str] = None) -> WeatherExposure:
    """
    Return deterministic weather exposure for an asset.

    The scenario parameter allows the Scenario Simulator to override weather.
    """
    w = dict(_REGION_WEATHER.get(asset.region, _DEFAULT_WEATHER))

    # Apply scenario modifiers
    if scenario == "severe_storm":
        w["storm"]  = min(1.0, w["storm"] + 0.40)
        w["wind"]   = min(25.0, w["wind"] + 8.0)
        w["precip"] = min(60.0, w["precip"] + 30.0)
        w["severe"] = True
    elif scenario == "heatwave":
        w["temp"]    = min(55.0, w["temp"] + 8.0)
        w["heatwave"] = True
        w["storm"]   = min(1.0, w["storm"] + 0.10)

    exposure_score = _compute_exposure_score(
        temp=w["temp"], wind=w["wind"], precip=w["precip"],
        storm=w["storm"], heatwave=w["heatwave"], severe=w["severe"],
    )

    return WeatherExposure(
        asset_id=asset.id,
        temperature=w["temp"],
        wind_speed=w["wind"],
        precipitation=w["precip"],
        humidity=w["humid"],
        storm_severity=w["storm"],
        heatwave_indicator=w["heatwave"],
        severe_weather_indicator=w["severe"],
        weather_exposure_score=exposure_score,
    )


async def fetch_live_weather_exposure(asset: Asset) -> WeatherExposure:
    """
    Attempt to fetch live weather from Open-Meteo and compute exposure.
    Falls back to mock data on any error.
    """
    try:
        import aiohttp, ssl, certifi
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        params = {
            "latitude": asset.location.lat,
            "longitude": asset.location.lon,
            "current": "temperature_2m,wind_speed_10m,precipitation,relative_humidity_2m",
            "timezone": "Asia/Kolkata",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                data = await resp.json()

        cur = data.get("current", {})
        temp  = float(cur.get("temperature_2m", 35.0))
        wind  = float(cur.get("wind_speed_10m", 7.0))
        precip = float(cur.get("precipitation", 0.0))
        humid = float(cur.get("relative_humidity_2m", 65.0))

        # Storm severity heuristic from wind + precip
        storm = min(1.0, (wind / 20.0) * 0.5 + (precip / 30.0) * 0.5)
        heatwave = temp >= 42.0
        severe = storm >= 0.6 or heatwave

        exposure_score = _compute_exposure_score(temp, wind, precip, storm, heatwave, severe)
        return WeatherExposure(
            asset_id=asset.id,
            temperature=round(temp, 1),
            wind_speed=round(wind, 1),
            precipitation=round(precip, 1),
            humidity=round(humid, 1),
            storm_severity=round(storm, 3),
            heatwave_indicator=heatwave,
            severe_weather_indicator=severe,
            weather_exposure_score=exposure_score,
        )
    except Exception:
        # Any failure → deterministic mock
        return get_weather_exposure(asset)
