#!/usr/bin/env python3
"""
GridMind AI — Data Pipeline Setup
Connects live data, downloads datasets, trains models, and verifies everything.

Usage:
    python3 setup_data.py                    # Full setup
    python3 setup_data.py --live-only        # Only fetch live weather data
    python3 setup_data.py --train-only       # Only train models
    python3 setup_data.py --import-csv FILE  # Import a CSV file for a site
"""
import asyncio
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import async_session, init_db
from backend.models_db import Site, WeatherData, User, Forecast
from sqlalchemy import select, func

# ─── Step 1: Pull Live Weather Data from Open-Meteo ───────────
async def fetch_live_weather(site):
    """Fetch current weather from Open-Meteo for a specific site."""
    from backend.weather.provider import fetch_forecast_weather, fetch_historical_weather
    
    print(f"\n📡 Fetching weather data for: {site.name}")
    print(f"   Location: {site.latitude}°N, {site.longitude}°E")
    
    # Fetch 7-day forecast
    forecast_df = await fetch_forecast_weather(
        latitude=site.latitude,
        longitude=site.longitude,
        days=7,
    )
    print(f"   ✅ Forecast: {len(forecast_df)} hourly records (7 days)")
    
    # Fetch last 30 days of historical data
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    try:
        historical_df = await fetch_historical_weather(
            latitude=site.latitude,
            longitude=site.longitude,
            start_date=start_date,
            end_date=end_date,
        )
        print(f"   ✅ Historical: {len(historical_df)} hourly records (30 days)")
    except Exception as e:
        print(f"   ⚠️  Historical fetch failed: {e}")
        historical_df = None
    
    return forecast_df, historical_df


async def save_weather_to_db(site_id, forecast_df, historical_df):
    """Save weather data to the database."""
    async with async_session() as db:
        count = 0
        for df in [forecast_df, historical_df]:
            if df is None:
                continue
            for _, row in df.iterrows():
                ts = row["timestamp"]
                if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                    ts = ts.tz_localize(None)
                weather = WeatherData(
                    site_id=site_id,
                    timestamp=ts,
                    ghi=float(row.get("ghi", 0) or 0),
                    dni=float(row.get("dni", 0) or 0),
                    dhi=float(row.get("dhi", 0) or 0),
                    temperature=float(row.get("temp_air", 0) or 0),
                    wind_speed=float(row.get("wind_speed", 0) or 0),
                    wind_direction=float(row.get("wind_direction", 0) or 0),
                    humidity=float(row.get("humidity", 0) or 0),
                    cloud_cover=float(row.get("cloud_cover", 0) or 0),
                    pressure=float(row.get("pressure", 0) or 0),
                    source="open-meteo",
                )
                db.add(weather)
                count += 1
        
        await db.commit()
        print(f"   💾 Saved {count} weather records to database")
        return count


# ─── Step 2: Import CSV Data ──────────────────────────────────
async def import_csv_to_site(site_id, csv_path):
    """Import a CSV file into weather data for a site."""
    import pandas as pd
    
    df = pd.read_csv(csv_path)
    print(f"\n📄 Importing CSV: {csv_path}")
    print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")
    
    # Normalize column names
    col_map = {
        "date": "timestamp", "datetime": "timestamp", "time": "timestamp",
        "temp_air": "temperature", "temperature_2m": "temperature",
        "wind_speed_10m": "wind_speed", "relative_humidity_2m": "humidity",
        "pressure_msl": "pressure",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    
    if "timestamp" not in df.columns:
        print("   ❌ No 'timestamp' column found!")
        return 0
    
    async with async_session() as db:
        count = 0
        for _, row in df.iterrows():
            ts = pd.to_datetime(row["timestamp"])
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            weather = WeatherData(
                site_id=site_id,
                timestamp=ts,
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
            db.add(weather)
            count += 1
        
        await db.commit()
        print(f"   ✅ Imported {count} records to database")
        return count


# ─── Step 3: Generate Synthetic Training Data ─────────────────
def generate_training_data():
    """Generate synthetic solar + wind training datasets."""
    from backend.training.download_datasets import generate_solar_dataset, generate_wind_dataset
    
    print("\n🔧 Generating training datasets...")
    solar_path = generate_solar_dataset(n_days=30)
    wind_path = generate_wind_dataset(n_days=30)
    return solar_path, wind_path


# ─── Step 4: Train Models ─────────────────────────────────────
async def train_models(site):
    """Train ML models using available data."""
    from backend.training.pipeline import run_full_pipeline
    
    print(f"\n🧠 Training models for: {site.name}")
    site_params = {
        "latitude": site.latitude,
        "longitude": site.longitude,
        "altitude": site.altitude or 0,
        "capacity_kw": site.capacity_kw,
        "surface_tilt": 28,
        "surface_azimuth": 180,
    }
    
    solar_csv = str(Path(__file__).parent / "data" / "raw" / "solar_generation.csv")
    wind_csv = str(Path(__file__).parent / "data" / "raw" / "wind_generation.csv")
    
    if not os.path.exists(solar_csv) or not os.path.exists(wind_csv):
        generate_training_data()
    
    report = run_full_pipeline(site_params, solar_csv=solar_csv, wind_csv=wind_csv)
    
    # Save model version to DB
    async with async_session() as db:
        from backend.models_db import ModelVersion
        mv = ModelVersion(
            model_name="solar_hybrid",
            version=f"v{datetime.now().strftime('%Y%m%d')}",
            metrics_json=json.dumps(report.get("results", {})),
            is_active=True,
        )
        db.add(mv)
        await db.commit()
        print("   ✅ Model version saved to database")
    
    return report


# ─── Step 5: Verify & Report ──────────────────────────────────
async def print_status():
    """Print full system status."""
    async with async_session() as db:
        users = (await db.execute(select(func.count(User.id)))).scalar()
        sites = (await db.execute(select(func.count(Site.id)))).scalar()
        weather = (await db.execute(select(func.count(WeatherData.id)))).scalar()
        forecasts = (await db.execute(select(func.count(Forecast.id)))).scalar()
    
    print("\n" + "=" * 50)
    print("  📊 GridMind AI — System Status")
    print("=" * 50)
    print(f"  Users:       {users}")
    print(f"  Sites:       {sites}")
    print(f"  Weather:     {weather} records")
    print(f"  Forecasts:   {forecasts}")
    print("=" * 50)


# ─── Main ─────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="GridMind AI Data Pipeline")
    parser.add_argument("--live-only", action="store_true", help="Only fetch live weather")
    parser.add_argument("--train-only", action="store_true", help="Only train models")
    parser.add_argument("--import-csv", type=str, help="Import a CSV file")
    parser.add_argument("--import-site", type=str, help="Site ID for CSV import")
    parser.add_argument("--generate-data", action="store_true", help="Only generate synthetic data")
    args = parser.parse_args()
    
    print("⚡ GridMind AI — Data Pipeline")
    print("=" * 50)
    
    await init_db()
    
    async with async_session() as db:
        result = await db.execute(select(Site).where(Site.is_active == True))
        sites = result.scalars().all()
    
    if not sites:
        print("\n⚠️  No sites found! Create a site first:")
        print("   1. Go to http://localhost:5173")
        print("   2. Sign up / login")
        print("   3. Go to Settings → + New Site")
        print("   4. Then run this script again")
        return
    
    if args.generate_data:
        generate_training_data()
        await print_status()
        return
    
    if args.train_only:
        for site in sites:
            await train_models(site)
        await print_status()
        return
    
    if args.import_csv and args.import_site:
        await import_csv_to_site(args.import_site, args.import_csv)
        await print_status()
        return
    
    # Full pipeline
    for site in sites:
        print(f"\n{'─' * 50}")
        print(f"  Site: {site.name} ({site.capacity_kw} kW {site.site_type})")
        print(f"{'─' * 50}")
        
        if not args.live_only:
            # Import existing CSV data
            solar_csv = Path(__file__).parent / "data" / "raw" / "solar_generation.csv"
            if solar_csv.exists():
                await import_csv_to_site(site.id, str(solar_csv))
        
        # Fetch live weather
        try:
            forecast_df, historical_df = await fetch_live_weather(site)
            await save_weather_to_db(site.id, forecast_df, historical_df)
        except Exception as e:
            print(f"   ⚠️  Live fetch failed: {e}")
            print("   ℹ️  The app will use physics-based estimates")
        
        if not args.live_only:
            # Train models
            await train_models(site)
    
    # Generate training data if not exists
    solar_csv = Path(__file__).parent / "data" / "raw" / "solar_generation.csv"
    if not solar_csv.exists():
        generate_training_data()
    
    await print_status()
    
    print("\n✅ Data pipeline complete!")
    print("   → Start the app: bash start.sh")
    print("   → Live data will auto-refresh every 15 minutes")


if __name__ == "__main__":
    asyncio.run(main())
