from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import get_db
from backend.models_db import User, Site, WeatherData, Forecast
from backend.dependencies import get_current_user
import io, pandas as pd

MAX_IMPORT_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMPORT_ROWS = 1_000_000

router = APIRouter(prefix="/api/data", tags=["Data Operations"])


@router.get("/status/{site_id}")
async def get_data_status(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    weather_count = (await db.execute(
        select(func.count(WeatherData.id)).where(WeatherData.site_id == site_id)
    )).scalar()

    latest = (await db.execute(
        select(WeatherData)
        .where(WeatherData.site_id == site_id)
        .order_by(WeatherData.timestamp.desc())
        .limit(1)
    )).scalar_one_or_none()

    oldest = (await db.execute(
        select(WeatherData)
        .where(WeatherData.site_id == site_id)
        .order_by(WeatherData.timestamp.asc())
        .limit(1)
    )).scalar_one_or_none()

    return {
        "site_id": site_id,
        "weather_records": weather_count,
        "latest_timestamp": str(latest.timestamp) if latest else None,
        "oldest_timestamp": str(oldest.timestamp) if oldest else None,
        "sources": {"live": "Open-Meteo API (auto-polling)", "historical": "CSV import / Open-Meteo archive"},
    }


@router.post("/sync/{site_id}")
async def sync_weather_data(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    from backend.weather.provider import fetch_forecast_weather, fetch_historical_weather
    from datetime import datetime, timedelta
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    count = 0
    errors = []

    try:
        forecast_df = await fetch_forecast_weather(
            latitude=site.latitude, longitude=site.longitude, days=7,
        )
        for _, row in forecast_df.iterrows():
            ts = row["timestamp"]
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            stmt = sqlite_insert(WeatherData).values(
                site_id=site_id, timestamp=ts,
                ghi=float(row.get("ghi", 0) or 0),
                dni=float(row.get("dni", 0) or 0),
                dhi=float(row.get("dhi", 0) or 0),
                temperature=float(row.get("temp_air", 0) or 0),
                wind_speed=float(row.get("wind_speed", 0) or 0),
                wind_direction=float(row.get("wind_direction", 0) or 0),
                humidity=float(row.get("humidity", 0) or 0),
                cloud_cover=float(row.get("cloud_cover", 0) or 0),
                pressure=float(row.get("pressure", 0) or 0),
                source="open-meteo-forecast",
            ).on_conflict_do_update(
                index_elements=["site_id", "timestamp"],
                set_={
                    "ghi": float(row.get("ghi", 0) or 0),
                    "dni": float(row.get("dni", 0) or 0),
                    "dhi": float(row.get("dhi", 0) or 0),
                    "temperature": float(row.get("temp_air", 0) or 0),
                    "wind_speed": float(row.get("wind_speed", 0) or 0),
                    "wind_direction": float(row.get("wind_direction", 0) or 0),
                    "humidity": float(row.get("humidity", 0) or 0),
                    "cloud_cover": float(row.get("cloud_cover", 0) or 0),
                    "pressure": float(row.get("pressure", 0) or 0),
                    "source": "open-meteo-forecast",
                },
            )
            await db.execute(stmt)
            count += 1
    except Exception as e:
        errors.append(f"Forecast: {str(e)}")

    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        historical_df = await fetch_historical_weather(
            latitude=site.latitude, longitude=site.longitude,
            start_date=start_date, end_date=end_date,
        )
        for _, row in historical_df.iterrows():
            ts = row["timestamp"]
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            stmt = sqlite_insert(WeatherData).values(
                site_id=site_id, timestamp=ts,
                ghi=float(row.get("ghi", 0) or 0),
                dni=float(row.get("dni", 0) or 0),
                dhi=float(row.get("dhi", 0) or 0),
                temperature=float(row.get("temp_air", 0) or 0),
                wind_speed=float(row.get("wind_speed", 0) or 0),
                wind_direction=float(row.get("wind_direction", 0) or 0),
                humidity=float(row.get("humidity", 0) or 0),
                cloud_cover=float(row.get("cloud_cover", 0) or 0),
                pressure=float(row.get("pressure", 0) or 0),
                source="open-meteo-archive",
            ).on_conflict_do_update(
                index_elements=["site_id", "timestamp"],
                set_={
                    "ghi": float(row.get("ghi", 0) or 0),
                    "dni": float(row.get("dni", 0) or 0),
                    "dhi": float(row.get("dhi", 0) or 0),
                    "temperature": float(row.get("temp_air", 0) or 0),
                    "wind_speed": float(row.get("wind_speed", 0) or 0),
                    "wind_direction": float(row.get("wind_direction", 0) or 0),
                    "humidity": float(row.get("humidity", 0) or 0),
                    "cloud_cover": float(row.get("cloud_cover", 0) or 0),
                    "pressure": float(row.get("pressure", 0) or 0),
                    "source": "open-meteo-archive",
                },
            )
            await db.execute(stmt)
            count += 1
    except Exception as e:
        errors.append(f"Historical: {str(e)}")

    await db.commit()

    return {
        "site_id": site_id,
        "records_synced": count,
        "errors": errors,
        "status": "success" if not errors else "partial",
    }


@router.post("/import/{site_id}")
async def import_csv(
    site_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    content = await file.read()
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    df = pd.read_csv(io.BytesIO(content))
    if len(df) == 0:
        raise HTTPException(status_code=400, detail="CSV contains no data rows")
    if len(df) > MAX_IMPORT_ROWS:
        raise HTTPException(status_code=413, detail=f"Too many rows (max {MAX_IMPORT_ROWS})")

    col_map = {
        "date": "timestamp", "datetime": "timestamp", "time": "timestamp",
        "temp_air": "temperature", "temperature_2m": "temperature",
        "wind_speed_10m": "wind_speed", "relative_humidity_2m": "humidity",
        "pressure_msl": "pressure",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    if "timestamp" not in df.columns:
        raise HTTPException(status_code=400, detail="CSV must have a 'timestamp' column")

    count = 0
    for _, row in df.iterrows():
        ts = pd.to_datetime(row["timestamp"])
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        w = WeatherData(
            site_id=site_id, timestamp=ts,
            ghi=float(row.get("ghi", 0) or 0),
            dni=float(row.get("dni", 0) or 0),
            dhi=float(row.get("dhi", 0) or 0),
            temperature=float(row.get("temperature", 0) or 0),
            wind_speed=float(row.get("wind_speed", 0) or 0),
            wind_direction=float(row.get("wind_direction", 0) or 0),
            humidity=float(row.get("humidity", 0) or 0),
            cloud_cover=float(row.get("cloud_cover", 0) or 0),
            pressure=float(row.get("pressure", 0) or 0),
            source="csv-import",
        )
        db.add(w)
        count += 1

    await db.commit()
    return {"site_id": site_id, "rows_imported": count, "columns": list(df.columns)}
