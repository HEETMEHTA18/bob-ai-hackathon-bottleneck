"""
Model Training Pipeline for Bottleneck AI
Supports: Solar Hybrid (pvlib + XGBoost), Wind LightGBM, Quantile models
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.forecasting.features import (
    prepare_solar_features, prepare_wind_features,
    SOLAR_FEATURE_COLS, WIND_FEATURE_COLS,
)
from backend.forecasting.solar import run_physics_model, get_solar_feature_cols
from backend.forecasting.wind import get_wind_feature_cols
from backend.forecasting.evaluate import evaluate, walk_forward_split
from backend.forecasting.uncertainty import compute_quantile_bands, validate_coverage

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class SolarTrainer:
    def __init__(self, site_params: dict):
        self.site_params = site_params
        self.feature_cols = get_solar_feature_cols()

    def train(self, df: pd.DataFrame) -> dict:
        print("[Solar] Running physics model...")
        try:
            df["physics_estimate_kw"] = run_physics_model(df, self.site_params)
        except Exception as e:
            print(f"[Solar] Physics model failed: {e}, using GHI-based estimate")
            df["physics_estimate_kw"] = df["ghi"] * self.site_params["capacity_kw"] / 1000

        df["residual"] = df["generation_kw"] - df["physics_estimate_kw"]

        available_features = [c for c in self.feature_cols if c in df.columns]
        print(f"[Solar] Using {len(available_features)} features")

        import xgboost as xgb

        X = df[available_features].fillna(0)
        y = df["residual"]

        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        print("[Solar] Training XGBoost residual model...")
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
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        val_physics = df["physics_estimate_kw"].iloc[split_idx:]
        val_pred = val_physics + model.predict(X_val)
        val_pred = np.clip(val_pred, 0, self.site_params["capacity_kw"])
        y_true = df["generation_kw"].iloc[split_idx:]

        metrics = evaluate(y_true.values, val_pred, self.site_params["capacity_kw"])
        print(f"[Solar] Metrics: nMAE={metrics['nMAE_%']:.1f}%, R²={metrics['R2']:.3f}")

        model_dir = MODELS_DIR / "solar"
        model_dir.mkdir(exist_ok=True)
        model.save_model(str(model_dir / "solar_hybrid.json"))

        with open(model_dir / "feature_cols.json", "w") as f:
            json.dump(available_features, f)

        return {"model": model, "metrics": metrics, "features": available_features}


class WindTrainer:
    def __init__(self, site_params: dict):
        self.site_params = site_params
        self.feature_cols = get_wind_feature_cols()

    def train(self, df: pd.DataFrame) -> dict:
        available_features = [c for c in self.feature_cols if c in df.columns]
        print(f"[Wind] Using {len(available_features)} features")

        import lightgbm as lgb

        X = df[available_features].fillna(0)
        y = df["generation_kw"]

        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        print("[Wind] Training LightGBM model...")
        model = lgb.LGBMRegressor(
            objective="regression",
            metric="mae",
            boosting_type="gbdt",
            num_leaves=31,
            learning_rate=0.05,
            n_estimators=500,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=-1,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)],
        )

        val_pred = model.predict(X_val)
        val_pred = np.clip(val_pred, 0, self.site_params.get("capacity_kw", 100))
        y_true = y.iloc[split_idx:]

        metrics = evaluate(y_true.values, val_pred, self.site_params.get("capacity_kw", 100))
        print(f"[Wind] Metrics: nMAE={metrics['nMAE_%']:.1f}%, R²={metrics['R2']:.3f}")

        model_dir = MODELS_DIR / "wind"
        model_dir.mkdir(exist_ok=True)
        model.booster_.save_model(str(model_dir / "wind_lgbm.txt"))

        with open(model_dir / "feature_cols.json", "w") as f:
            json.dump(available_features, f)

        return {"model": model, "metrics": metrics, "features": available_features}


class QuantileTrainer:
    def __init__(self):
        self.quantiles = {"p10": 0.1, "p50": 0.5, "p90": 0.9}

    def train(self, df: pd.DataFrame, feature_cols: list, target: str) -> dict:
        import lightgbm as lgb

        available = [c for c in feature_cols if c in df.columns]
        X = df[available].fillna(0)
        y = df[target]

        split_idx = int(len(df) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        models = {}
        for name, alpha in self.quantiles.items():
            print(f"[Quantile] Training {name} (α={alpha})...")
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=alpha,
                num_leaves=31,
                learning_rate=0.05,
                n_estimators=300,
                random_state=42,
                n_jobs=-1,
                verbosity=-1,
            )
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
            models[name] = model

        p10_pred = models["p10"].predict(X_val)
        p50_pred = models["p50"].predict(X_val)
        p90_pred = models["p90"].predict(X_val)

        stacked = np.stack([p10_pred, p50_pred, p90_pred], axis=1)
        stacked = np.sort(stacked, axis=1)

        coverage = validate_coverage(y_val.values, stacked[:, 0], stacked[:, 2])
        print(f"[Quantile] 80% coverage: {coverage:.1%}")

        q_dir = MODELS_DIR / "solar" / "quantile"
        q_dir.mkdir(parents=True, exist_ok=True)
        for name, model in models.items():
            model.booster_.save_model(str(q_dir / f"{name}.txt"))

        return {"models": models, "coverage": coverage}


def run_full_pipeline(site_params: dict, solar_csv: str = None, wind_csv: str = None) -> dict:
    results = {}

    if solar_csv and os.path.exists(solar_csv):
        print("\n" + "=" * 60)
        print("SOLAR MODEL TRAINING")
        print("=" * 60)
        df = pd.read_csv(solar_csv)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        solar_df = prepare_solar_features(df, site_params["latitude"], site_params["longitude"])
        trainer = SolarTrainer(site_params)
        results["solar"] = trainer.train(solar_df)

        q_trainer = QuantileTrainer()
        results["solar_quantile"] = q_trainer.train(
            solar_df, get_solar_feature_cols(), "generation_kw"
        )

    if wind_csv and os.path.exists(wind_csv):
        print("\n" + "=" * 60)
        print("WIND MODEL TRAINING")
        print("=" * 60)
        df = pd.read_csv(wind_csv)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        wind_df = prepare_wind_features(df)
        trainer = WindTrainer(site_params)
        results["wind"] = trainer.train(wind_df)

    report = {
        "timestamp": datetime.now().isoformat(),
        "site_params": site_params,
        "results": {},
    }
    for key, val in results.items():
        if "metrics" in val:
            report["results"][key] = val["metrics"]
        elif "coverage" in val:
            report["results"][key] = {"coverage": val["coverage"]}

    metrics_dir = MODELS_DIR / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    with open(metrics_dir / "evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Report saved to: {metrics_dir / 'evaluation_report.json'}")

    return report


if __name__ == "__main__":
    site_params = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "altitude": 216,
        "capacity_kw": 100,
        "surface_tilt": 28,
        "surface_azimuth": 180,
    }

    solar_csv = str(DATA_DIR / "raw" / "solar_generation.csv")
    wind_csv = str(DATA_DIR / "raw" / "wind_generation.csv")

    if not os.path.exists(solar_csv):
        print("Generating sample solar data...")
        from notebooks.generate_sample_data import *
        solar_csv = str(DATA_DIR / "sample" / "solar_generation.csv")

    run_full_pipeline(site_params, solar_csv=solar_csv)
