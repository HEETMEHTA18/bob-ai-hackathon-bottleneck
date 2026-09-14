from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np
from backend.database import get_db
from backend.models_db import User, Site, WeatherData
from backend.dependencies import get_current_user
from backend.schemas import ScenarioRequest

router = APIRouter(prefix="/api", tags=["Forecast & Decision"])


async def get_user_site(site_id: str, user: User, db: AsyncSession):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


async def get_weather_for_site(site_id: str, hours: int, db: AsyncSession):
    """Get weather records for forecasting — deduplicates timestamps, prioritizes daytime."""
    from datetime import datetime
    from sqlalchemy import func

    now = datetime.utcnow()

    # Get future records with deduplication (take latest record per timestamp)
    subq = (
        select(
            WeatherData.timestamp,
            func.max(WeatherData.id).label("latest_id"),
        )
        .where(WeatherData.site_id == site_id, WeatherData.timestamp >= now)
        .group_by(WeatherData.timestamp)
        .order_by(WeatherData.timestamp.asc())
        .limit(72)
    )
    result = await db.execute(subq)
    latest_ids = [row.latest_id for row in result.all()]

    if latest_ids:
        result = await db.execute(
            select(WeatherData).where(WeatherData.id.in_(latest_ids)).order_by(WeatherData.timestamp.asc())
        )
        all_future = result.scalars().all()

        if len(all_future) >= 6:
            daytime_records = [r for r in all_future if (r.ghi or 0) > 10]
            if daytime_records:
                start_idx = max(0, all_future.index(daytime_records[0]) - 2)
                selected = all_future[start_idx:start_idx + hours]
            else:
                selected = all_future[:hours]

            return [
                {
                    "timestamp": r.timestamp,
                    "ghi": r.ghi or 0,
                    "dni": r.dni or 0,
                    "dhi": r.dhi or 0,
                    "temperature": r.temperature or 25,
                    "wind_speed": r.wind_speed or 5,
                    "wind_direction": 180,
                    "humidity": r.humidity or 50,
                    "cloud_cover": r.cloud_cover or 0,
                    "pressure": r.pressure or 1013,
                }
                for r in selected
            ]

    # Fallback: use recent historical data with deduplication
    subq_hist = (
        select(
            WeatherData.timestamp,
            func.max(WeatherData.id).label("latest_id"),
        )
        .where(WeatherData.site_id == site_id)
        .group_by(WeatherData.timestamp)
        .order_by(WeatherData.timestamp.desc())
        .limit(72)
    )
    result = await db.execute(subq_hist)
    hist_ids = [row.latest_id for row in result.all()]
    result = await db.execute(
        select(WeatherData).where(WeatherData.id.in_(hist_ids)).order_by(WeatherData.timestamp.asc())
    )
    records = list(result.scalars().all())

    if records and len(records) >= 6:
        daytime_records = [r for r in records if (r.ghi or 0) > 10]
        if daytime_records:
            start_idx = max(0, records.index(daytime_records[0]) - 2)
            selected = records[start_idx:start_idx + hours]
        else:
            selected = records[:hours]

        return [
            {
                "timestamp": r.timestamp,
                "ghi": r.ghi or 0,
                "dni": r.dni or 0,
                "dhi": r.dhi or 0,
                "temperature": r.temperature or 25,
                "wind_speed": r.wind_speed or 5,
                "wind_direction": 180,
                "humidity": r.humidity or 50,
                "cloud_cover": r.cloud_cover or 0,
                "pressure": r.pressure or 1013,
            }
            for r in selected
        ]
    return None


@router.get("/forecast/{site_id}")
async def get_forecast(
    site_id: str,
    horizon: int = 24,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await get_user_site(site_id, user, db)

    # Try to get real weather data from DB
    weather_records = await get_weather_for_site(site_id, horizon, db)

    if weather_records:
        # Use trained ML model with real data
        try:
            from backend.forecasting.inference import predict_from_weather_records
            prediction = predict_from_weather_records(
                records=weather_records,
                site_type=site.site_type,
                latitude=site.latitude,
                longitude=site.longitude,
                capacity_kw=site.capacity_kw,
            )
            return {
                "site_id": str(site_id),
                "horizon_hours": horizon,
                "timestamps": prediction["timestamps"],
                "forecast": {
                    "p10": prediction["p10"],
                    "p50": prediction["p50"],
                    "p90": prediction["p90"],
                },
                "model_type": prediction["model_type"],
                "feature_count": prediction["feature_count"],
                "weather": {
                    "ghi": [r["ghi"] for r in weather_records[:horizon]],
                    "wind_speed": [r["wind_speed"] for r in weather_records[:horizon]],
                    "temperature": [r["temperature"] for r in weather_records[:horizon]],
                },
            }
        except Exception as e:
            # Fall through to physics fallback
            pass

    # Fallback: physics-based estimate when no weather data available
    try:
        from backend.forecasting.inference import _load_solar_calibration
        physics_bias = _load_solar_calibration().get("physics_bias_scale", 1.0)
    except Exception:
        physics_bias = 1.0
    hours = horizon
    physics = np.array([
        site.capacity_kw * physics_bias * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
        for i in range(hours)
    ])
    point_forecast = np.clip(physics, 0, site.capacity_kw)
    noise = np.random.normal(0, site.capacity_kw * 0.05, len(point_forecast))
    p10 = np.maximum(point_forecast + np.percentile(noise, 10), 0)
    p50 = point_forecast
    p90 = np.maximum(point_forecast + np.percentile(noise, 90), 0)
    p90 = np.minimum(p90, site.capacity_kw)
    stacked = np.sort(np.stack([p10, p50, p90], axis=1), axis=1)

    return {
        "site_id": str(site_id),
        "horizon_hours": horizon,
        "timestamps": [f"2024-01-01T{i:02d}:00:00" for i in range(horizon)],
        "forecast": {
            "p10": stacked[:, 0].tolist(),
            "p50": stacked[:, 1].tolist(),
            "p90": stacked[:, 2].tolist(),
        },
        "model_type": "physics_fallback",
        "feature_count": 0,
        "weather": {
            "ghi": (physics * 8).tolist(),
            "wind_speed": np.random.uniform(3, 12, horizon).tolist(),
            "temperature": (25 + 5 * np.sin(np.pi * np.arange(horizon) / 12)).tolist(),
        },
    }


@router.get("/risk/{site_id}")
async def get_risk(
    site_id: str,
    horizon: int = 24,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await get_user_site(site_id, user, db)
    from backend.optimization.dispatch import decide_action

    # Get forecast data
    weather_records = await get_weather_for_site(site_id, horizon, db)

    if weather_records:
        try:
            from backend.forecasting.inference import predict_from_weather_records
            prediction = predict_from_weather_records(
                records=weather_records,
                site_type=site.site_type,
                latitude=site.latitude,
                longitude=site.longitude,
                capacity_kw=site.capacity_kw,
            )
            hourly_gen = prediction["p50"]
        except Exception:
            hourly_gen = [
                site.capacity_kw * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
                for i in range(horizon)
            ]
    else:
        hourly_gen = [
            site.capacity_kw * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
            for i in range(horizon)
        ]

    hourly_risks = []
    battery_soc = site.battery_capacity_kwh * 0.5
    demand = site.capacity_kw * 0.7

    for i in range(horizon):
        gen = hourly_gen[i] if i < len(hourly_gen) else 0
        decision = decide_action(gen, site.export_limit_kw, battery_soc, site.battery_capacity_kwh, demand)
        hourly_risks.append({
            "hour": i,
            "generation_kw": float(gen),
            "risk": decision["risk"],
            "action": decision["action"],
        })

    return {"site_id": str(site_id), "horizon_hours": horizon, "risks": hourly_risks}


@router.get("/optimize/{site_id}")
async def get_optimization(
    site_id: str,
    horizon: int = 24,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await get_user_site(site_id, user, db)
    from backend.optimization.dispatch import generate_optimization_schedule

    weather_records = await get_weather_for_site(site_id, horizon, db)

    if weather_records:
        try:
            from backend.forecasting.inference import predict_from_weather_records
            prediction = predict_from_weather_records(
                records=weather_records,
                site_type=site.site_type,
                latitude=site.latitude,
                longitude=site.longitude,
                capacity_kw=site.capacity_kw,
            )
            hourly_gen = np.array(prediction["p50"])
            p10 = np.array(prediction["p10"])
            p90 = np.array(prediction["p90"])
        except Exception:
            hourly_gen = np.array([
                site.capacity_kw * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
                for i in range(horizon)
            ])
            p10 = hourly_gen * 0.8
            p90 = hourly_gen * 1.2
    else:
        hourly_gen = np.array([
            site.capacity_kw * max(0, np.sin(np.pi * (i - 6) / 12)) if 6 <= i <= 18 else 0
            for i in range(horizon)
        ])
        p10 = hourly_gen * 0.8
        p90 = hourly_gen * 1.2

    schedule = generate_optimization_schedule(
        forecast_p50=hourly_gen,
        forecast_p10=p10,
        forecast_p90=p90,
        export_limit=site.export_limit_kw,
        battery_soc=site.battery_capacity_kwh * 0.5,
        battery_capacity=site.battery_capacity_kwh,
        demand_forecast=site.capacity_kw * 0.7,
    )

    return {
        "site_id": str(site_id),
        "horizon_hours": horizon,
        "schedule": schedule,
        "total_financial_impact_inr": sum(s["financial_impact_inr"] for s in schedule),
        "total_co2_impact_tonnes": sum(s["co2_impact_tonnes"] for s in schedule),
    }


@router.get("/explain/{site_id}")
async def get_explanation(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await get_user_site(site_id, user, db)
    from backend.optimization.dispatch import decide_action, estimate_financial_impact, estimate_co2_impact
    from backend.services.explain import generate_explanation

    weather_records = await get_weather_for_site(site_id, 1, db)

    if weather_records:
        try:
            from backend.forecasting.inference import predict_from_weather_records
            prediction = predict_from_weather_records(
                records=weather_records,
                site_type=site.site_type,
                latitude=site.latitude,
                longitude=site.longitude,
                capacity_kw=site.capacity_kw,
            )
            gen_kw = prediction["p50"][0] if prediction["p50"] else site.capacity_kw * 0.5
        except Exception:
            gen_kw = site.capacity_kw * 0.8
    else:
        gen_kw = site.capacity_kw * 0.8

    battery_soc = site.battery_capacity_kwh * 0.5
    demand = site.capacity_kw * 0.7

    decision = decide_action(gen_kw, site.export_limit_kw, battery_soc, site.battery_capacity_kwh, demand)
    explanation = generate_explanation(
        action=decision["action"],
        gen_kw=gen_kw,
        export_limit=site.export_limit_kw,
        battery_soc=battery_soc,
        battery_capacity=site.battery_capacity_kwh,
        demand_kw=demand,
        surplus=decision["surplus_kwh"],
        deficit=decision["deficit_kwh"],
    )

    return {
        "site_id": str(site_id),
        "action": decision["action"],
        "risk": decision["risk"],
        "explanation": explanation,
        "financial_impact_inr": estimate_financial_impact(decision["action"], abs(decision["surplus_kwh"] - decision["deficit_kwh"])),
        "co2_impact_tonnes": estimate_co2_impact(decision["action"], abs(decision["surplus_kwh"] - decision["deficit_kwh"])),
    }


@router.post("/scenario/{site_id}")
async def run_scenario(
    site_id: str,
    request: ScenarioRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await get_user_site(site_id, user, db)
    from backend.optimization.dispatch import decide_action, estimate_financial_impact, estimate_co2_impact
    from backend.services.explain import generate_explanation

    weather_records = await get_weather_for_site(site_id, 1, db)

    if weather_records:
        try:
            from backend.forecasting.inference import predict_from_weather_records
            prediction = predict_from_weather_records(
                records=weather_records,
                site_type=site.site_type,
                latitude=site.latitude,
                longitude=site.longitude,
                capacity_kw=site.capacity_kw,
            )
            gen_kw = prediction["p50"][0] if prediction["p50"] else site.capacity_kw * 0.5
        except Exception:
            gen_kw = site.capacity_kw * 0.8
    else:
        gen_kw = site.capacity_kw * 0.8

    # Apply scenario adjustments
    if request.cloud_cover_delta != 0:
        gen_kw *= (1 - request.cloud_cover_delta / 100)
    if request.wind_speed_delta != 0:
        gen_kw *= (1 + request.wind_speed_delta / 100 * 0.3)
    gen_kw = max(0, gen_kw)

    battery_soc = request.battery_soc_override if request.battery_soc_override is not None else site.battery_capacity_kwh * 0.5
    demand = site.capacity_kw * 0.7

    decision = decide_action(gen_kw, site.export_limit_kw, battery_soc, site.battery_capacity_kwh, demand)
    explanation = generate_explanation(
        action=decision["action"],
        gen_kw=gen_kw,
        export_limit=site.export_limit_kw,
        battery_soc=battery_soc,
        battery_capacity=site.battery_capacity_kwh,
        demand_kw=demand,
        surplus=decision["surplus_kwh"],
        deficit=decision["deficit_kwh"],
    )

    return {
        "site_id": str(site_id),
        "adjusted_generation_kw": gen_kw,
        "action": decision["action"],
        "risk": decision["risk"],
        "explanation": explanation,
        "financial_impact_inr": estimate_financial_impact(decision["action"], abs(decision["surplus_kwh"] - decision["deficit_kwh"])),
        "co2_impact_tonnes": estimate_co2_impact(decision["action"], abs(decision["surplus_kwh"] - decision["deficit_kwh"])),
    }
