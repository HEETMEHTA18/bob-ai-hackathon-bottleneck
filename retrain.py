#!/usr/bin/env python3
"""Retrain models using weather data from the database."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime

from backend.database import async_session, init_db
from backend.models_db import Site, WeatherData, ModelVersion
from sqlalchemy import select
from backend.forecasting.features import prepare_solar_features, prepare_wind_features
from backend.forecasting.solar import get_solar_feature_cols
from backend.forecasting.wind import get_wind_feature_cols
from backend.forecasting.evaluate import evaluate

MODELS_DIR = Path(__file__).parent / "models"


async def retrain():
    await init_db()
    
    async with async_session() as db:
        result = await db.execute(select(Site).where(Site.is_active == True))
        sites = result.scalars().all()
    
    if not sites:
        print("No sites found")
        return
    
    for site in sites:
        print(f"\n{'='*50}")
        print(f"Retraining for: {site.name} ({site.site_type})")
        print(f"{'='*50}")
        
        async with async_session() as db:
            result = await db.execute(
                select(WeatherData)
                .where(WeatherData.site_id == site.id)
                .order_by(WeatherData.timestamp.asc())
            )
            records = result.scalars().all()
        
        if len(records) < 50:
            print(f"Only {len(records)} records — need at least 50. Skipping.")
            continue
        
        df = pd.DataFrame([{
            "timestamp": r.timestamp,
            "ghi": r.ghi or 0,
            "dni": r.dni or 0,
            "dhi": r.dhi or 0,
            "temperature_2m": r.temperature or 25,
            "wind_speed_10m": r.wind_speed or 5,
            "relative_humidity_2m": r.humidity or 50,
            "cloud_cover": r.cloud_cover or 0,
            "pressure_msl": r.pressure or 1013,
            "generation_kw": (r.ghi or 0) * site.capacity_kw / 1000,
        } for r in records])
        
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if df["timestamp"].dt.tz is not None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        print(f"Data: {len(df)} rows, {df['timestamp'].min()} → {df['timestamp'].max()}")
        
        if site.site_type in ("solar", "hybrid"):
            print("\nTraining Solar Hybrid Model (XGBoost)...")
            
            solar_df = prepare_solar_features(df, site.latitude, site.longitude)
            solar_df["capacity_kw"] = site.capacity_kw
            solar_df["physics_estimate_kw"] = np.clip(
                site.capacity_kw * np.maximum(0, np.sin(np.pi * (solar_df["timestamp"].dt.hour - 6) / 12)),
                0, site.capacity_kw
            )
            
            solar_df["residual"] = solar_df["generation_kw"] - solar_df["physics_estimate_kw"]
            
            feature_cols = get_solar_feature_cols()
            available = [c for c in feature_cols if c in solar_df.columns]
            print(f"Features: {len(available)} — {available}")
            
            X = solar_df[available].fillna(0)
            y = solar_df["residual"]
            
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
            
            import xgboost as xgb
            model = xgb.XGBRegressor(
                objective="reg:squarederror",
                n_estimators=400,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=5,
                reg_alpha=0.1,
                reg_lambda=1.0,
                tree_method="hist",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            
            val_physics = solar_df["physics_estimate_kw"].iloc[split_idx:]
            val_pred = np.clip(val_physics + model.predict(X_val), 0, site.capacity_kw)
            y_true = solar_df["generation_kw"].iloc[split_idx:]
            
            metrics = evaluate(y_true.values, val_pred, site.capacity_kw)
            print(f"Solar Metrics: nMAE={metrics['nMAE_%']:.1f}%, R²={metrics['R2']:.3f}")
            
            solar_dir = MODELS_DIR / "solar"
            solar_dir.mkdir(parents=True, exist_ok=True)
            model.save_model(str(solar_dir / "solar_hybrid.json"))
            with open(solar_dir / "feature_cols.json", "w") as f:
                json.dump(available, f)
            
            # Quantile models
            print("Training Quantile Models (P10/P50/P90)...")
            import lightgbm as lgb
            q_dir = solar_dir / "quantile"
            q_dir.mkdir(parents=True, exist_ok=True)
            for name, alpha in [("p10", 0.1), ("p50", 0.5), ("p90", 0.9)]:
                q_model = lgb.LGBMRegressor(
                    objective="quantile", alpha=alpha,
                    num_leaves=31, learning_rate=0.05, n_estimators=300,
                    random_state=42, n_jobs=-1, verbosity=-1,
                )
                q_model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
                q_model.booster_.save_model(str(q_dir / f"{name}.txt"))
                q_pred = q_model.predict(X_val)
                print(f"  {name}: mean={np.mean(q_pred):.2f}")
            
            print(f"✅ Solar model saved: {solar_dir / 'solar_hybrid.json'}")
        
        if site.site_type in ("wind", "hybrid"):
            print("\nTraining Wind Model (LightGBM)...")
            
            wind_df = prepare_wind_features(df)
            feature_cols = get_wind_feature_cols()
            available = [c for c in feature_cols if c in wind_df.columns]
            print(f"Features: {len(available)} — {available}")
            
            X = wind_df[available].fillna(0)
            y = wind_df["generation_kw"]
            
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
            
            import lightgbm as lgb
            model = lgb.LGBMRegressor(
                objective="regression", metric="mae",
                boosting_type="gbdt", num_leaves=31,
                learning_rate=0.05, n_estimators=500,
                subsample=0.8, colsample_bytree=0.8,
                min_child_samples=20, reg_alpha=0.1, reg_lambda=1.0,
                random_state=42, n_jobs=-1, verbosity=-1,
            )
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
            
            val_pred = np.clip(model.predict(X_val), 0, site.capacity_kw)
            y_true = y.iloc[split_idx:]
            metrics = evaluate(y_true.values, val_pred, site.capacity_kw)
            print(f"Wind Metrics: nMAE={metrics['nMAE_%']:.1f}%, R²={metrics['R2']:.3f}")
            
            wind_dir = MODELS_DIR / "wind"
            wind_dir.mkdir(parents=True, exist_ok=True)
            model.booster_.save_model(str(wind_dir / "wind_lgbm.txt"))
            with open(wind_dir / "feature_cols.json", "w") as f:
                json.dump(available, f)
            print(f"✅ Wind model saved: {wind_dir / 'wind_lgbm.txt'}")
    
    # Save model version
    async with async_session() as db:
        for site in sites:
            mv = ModelVersion(
                model_name=f"{site.site_type}_hybrid",
                version=f"retrained_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                metrics_json=json.dumps({"status": "retrained", "records": len(records)}),
                is_active=True,
            )
            db.add(mv)
        await db.commit()
    
    print(f"\n{'='*50}")
    print("✅ All models retrained!")
    print("Restart the backend to load new models.")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(retrain())
