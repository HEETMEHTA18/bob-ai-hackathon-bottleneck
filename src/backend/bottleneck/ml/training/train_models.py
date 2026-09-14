"""
Bottleneck ML — XGBoost Failure Prediction Training
====================================================
Trains two binary XGBoost classifiers:
  1. failure_within_24h   (primary target, MODEL.md)
  2. failure_within_72h   (secondary target, MODEL.md)

Design rules (MODEL.md / AGENTS.md)
-------------------------------------
  - Chronological train/val/test split (70/15/15) — NO random shuffle of time.
  - class_weight / scale_pos_weight to handle class imbalance.
  - eval_metric = "aucpr" (PR-AUC) — the primary MODEL.md metric.
  - Early stopping on validation set.
  - Artifacts written to  models/  directory at project root.
  - Model version + feature list + metrics stored in JSON metadata sidecar.
  - No data leakage: features built from backward-looking windows only.

Anomaly XGBoost scorer (Model 2)
---------------------------------
  An XGBoost regressor trained to predict a continuous anomaly score [0,1]
  using only telemetry features (no weather, no asset metadata).
  Labels: use the 72h failure flag as weak supervision (assets that fail within
  72 h are anomalous; assets that never fail get score≈0).
  This produces a differentiable, orderable anomaly signal that is more
  useful for ranking than IsolationForest's binary -1/+1 output.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Allow running as __main__ from any cwd
_ROOT = Path(__file__).resolve().parents[4]   # bob-ai-hackathon-bottleneck/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.bottleneck.ml.features.feature_engineering import (
    FEATURE_COLUMNS, TELEMETRY_FEATURE_COLUMNS,
    build_full_feature_set, validate_telemetry, validate_weather,
    build_telemetry_features,
)

DATA_DIR   = _ROOT / "data"
MODELS_DIR = _ROOT / "models" / "bottleneck"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_VERSION_FAILURE = "bottleneck-failure-v2"
MODEL_VERSION_ANOMALY = "bottleneck-anomaly-v2"


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_training_data() -> pd.DataFrame:
    """Load the generated CSV from DATA_DIR and return a merged DataFrame."""
    telem_path   = DATA_DIR / "telemetry.csv"
    weather_path = DATA_DIR / "weather_cache.csv"

    if not telem_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {telem_path}. "
            "Run: python -m backend.bottleneck.ml.data.generate_training_data"
        )

    telemetry_df = pd.read_csv(telem_path)
    weather_df   = pd.read_csv(weather_path)

    # Build asset metadata from the telemetry file (columns were embedded at generation)
    asset_cols = ["asset_id", "asset_age", "capacity_mva", "customers_served",
                  "criticality", "redundancy_level", "previous_failures",
                  "days_since_maintenance"]
    available_asset_cols = [c for c in asset_cols if c in telemetry_df.columns]
    assets_df = telemetry_df[available_asset_cols].drop_duplicates("asset_id")

    full = build_full_feature_set(telemetry_df, weather_df, assets_df)
    return full


# ─── Chronological split ──────────────────────────────────────────────────────

def chronological_split(
    df: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float   = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Per-asset chronological split.
    For each asset, the FIRST 70% of its rows go to train, next 15% to val,
    last 15% to test. This guarantees that every asset with positive labels
    has those labels represented in the val/test splits (because failure rows
    appear near the END of each asset's time-series).
    No data leakage: within each asset, rows are processed in temporal order.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["asset_id", "timestamp"]).reset_index(drop=True)

    train_parts, val_parts, test_parts = [], [], []
    for _, grp in df.groupby("asset_id", sort=False):
        n = len(grp)
        t_end = int(n * train_frac)
        v_end = int(n * (train_frac + val_frac))
        train_parts.append(grp.iloc[:t_end])
        val_parts.append(grp.iloc[t_end:v_end])
        test_parts.append(grp.iloc[v_end:])

    train_df = pd.concat(train_parts, ignore_index=True)
    val_df   = pd.concat(val_parts,   ignore_index=True)
    test_df  = pd.concat(test_parts,  ignore_index=True)

    return train_df, val_df, test_df


# ─── XGBoost failure classifier ───────────────────────────────────────────────

def train_failure_model(
    df: pd.DataFrame,
    target: str = "failure_within_24h",
    max_estimators: int = 600,
) -> Tuple[object, dict]:
    """
    Train one XGBoost binary classifier for the given target column.
    Returns (trained_model, metrics_dict).
    """
    import xgboost as xgb
    from sklearn.metrics import (
        average_precision_score, recall_score, precision_score,
        f1_score, roc_auc_score, brier_score_loss, confusion_matrix,
    )

    train_df, val_df, test_df = chronological_split(df)

    X_train = train_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_train = train_df[target].values.astype(int)
    X_val   = val_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_val   = val_df[target].values.astype(int)
    X_test  = test_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_test  = test_df[target].values.astype(int)

    # Class imbalance
    pos = y_train.sum()
    neg = len(y_train) - pos
    spw = float(neg / max(pos, 1))

    # Check if val set has both classes (needed for aucpr early stopping)
    val_has_both_classes = (y_val.sum() > 0) and (y_val.sum() < len(y_val))

    if val_has_both_classes:
        model = xgb.XGBClassifier(
            n_estimators          = max_estimators,
            max_depth             = 5,
            learning_rate         = 0.04,
            subsample             = 0.80,
            colsample_bytree      = 0.75,
            min_child_weight      = 3,
            gamma                 = 0.1,
            reg_alpha             = 0.1,
            reg_lambda            = 1.5,
            scale_pos_weight      = spw,
            eval_metric           = "aucpr",
            early_stopping_rounds = 40,
            random_state          = 42,
            n_jobs                = -1,
            tree_method           = "hist",
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    else:
        # Val set is all-negative or all-positive — skip early stopping
        print(f"  [Note] Val set missing a class (y_val pos={y_val.sum()}) "
              f"— using fixed n_estimators={max_estimators // 2}")
        model = xgb.XGBClassifier(
            n_estimators     = max_estimators // 2,
            max_depth        = 5,
            learning_rate    = 0.04,
            subsample        = 0.80,
            colsample_bytree = 0.75,
            min_child_weight = 3,
            gamma            = 0.1,
            reg_alpha        = 0.1,
            reg_lambda       = 1.5,
            scale_pos_weight = spw,
            random_state     = 42,
            n_jobs           = -1,
            tree_method      = "hist",
        )
        model.fit(X_train, y_train, verbose=False)

    # Evaluate on test set
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.50).astype(int)

    metrics: dict = {}
    if y_test.sum() > 0 and y_test.sum() < len(y_test):
        metrics = {
            "pr_auc"    : round(float(average_precision_score(y_test, y_prob)), 4),
            "roc_auc"   : round(float(roc_auc_score(y_test, y_prob)), 4),
            "recall"    : round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "precision" : round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1"        : round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "brier"     : round(float(brier_score_loss(y_test, y_prob)), 4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
    else:
        metrics = {"warning": "Test set has too few positive/negative samples for full metrics"}

    best_iter = getattr(model, "best_iteration", None)
    n_ests = int(best_iter + 1) if best_iter is not None else int(model.n_estimators)

    metrics.update({
        "threshold"          : 0.50,
        "train_rows"         : int(len(y_train)),
        "val_rows"           : int(len(y_val)),
        "test_rows"          : int(len(y_test)),
        "positive_rate_train": round(float(y_train.mean()), 4),
        "positive_rate_test" : round(float(y_test.mean()), 4),
        "scale_pos_weight"   : round(spw, 3),
        "best_n_estimators"  : n_ests,
    })

    print(f"[Train:{target}] n_estimators={n_ests}  "
          f"PR-AUC={metrics.get('pr_auc','?')}  "
          f"F1={metrics.get('f1','?')}  "
          f"recall={metrics.get('recall','?')}")

    return model, metrics


# ─── XGBoost anomaly scorer ───────────────────────────────────────────────────

def train_anomaly_model(df: pd.DataFrame) -> Tuple[object, dict]:
    """
    Train a XGBoost regressor as a continuous anomaly scorer [0,1].

    Supervision: rows labelled failure_within_72h=1 → anomaly_score target ≈ 1.0
                 rows labelled failure_within_72h=0 → anomaly_score target ≈ 0.0
    We use a soft target to avoid overconfidence:
        target = 0.90 × failure_within_72h + 0.05  (so range is [0.05, 0.95])

    Only TELEMETRY features are used (no weather/asset) so the anomaly model
    detects unusual sensor patterns, not just high-risk asset profiles.
    """
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error

    # Build soft target
    df = df.copy()
    if "failure_within_72h" not in df.columns:
        raise ValueError("'failure_within_72h' column required to train anomaly model")
    df["anomaly_target"] = df["failure_within_72h"] * 0.90 + 0.05

    train_df, val_df, test_df = chronological_split(df)

    X_train = train_df[TELEMETRY_FEATURE_COLUMNS].values.astype(np.float32)
    y_train = train_df["anomaly_target"].values.astype(np.float32)
    X_val   = val_df[TELEMETRY_FEATURE_COLUMNS].values.astype(np.float32)
    y_val   = val_df["anomaly_target"].values.astype(np.float32)
    X_test  = test_df[TELEMETRY_FEATURE_COLUMNS].values.astype(np.float32)
    y_test  = test_df["anomaly_target"].values.astype(np.float32)

    model = xgb.XGBRegressor(
        n_estimators          = 400,
        max_depth             = 4,
        learning_rate         = 0.04,
        subsample             = 0.80,
        colsample_bytree      = 0.75,
        min_child_weight      = 5,
        reg_alpha             = 0.1,
        reg_lambda            = 1.5,
        objective             = "reg:squarederror",
        eval_metric           = "mae",
        early_stopping_rounds = 30,
        random_state          = 42,
        n_jobs                = -1,
        tree_method           = "hist",
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    y_pred = np.clip(model.predict(X_test), 0.0, 1.0)
    mae    = float(mean_absolute_error(y_test, y_pred))
    best_iter = getattr(model, "best_iteration", None)
    n_ests = int(best_iter + 1) if best_iter is not None else int(model.n_estimators)

    metrics = {
        "mae"             : round(mae, 4),
        "train_rows"      : int(len(y_train)),
        "test_rows"       : int(len(y_test)),
        "best_n_estimators": n_ests,
    }

    print(f"[Train:anomaly] n_estimators={n_ests}  MAE={mae:.4f}")
    return model, metrics


# ─── Feature importance ───────────────────────────────────────────────────────

def extract_feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    """Return top features sorted by gain importance."""
    imp = model.feature_importances_
    return {
        feature_names[i]: round(float(imp[i]), 6)
        for i in np.argsort(imp)[::-1]
    }


# ─── Save / load artifacts ────────────────────────────────────────────────────

def save_model(
    model,
    name: str,              # e.g. "failure_24h", "failure_72h", "anomaly"
    metrics: dict,
    feature_list: List[str],
    model_version: str,
    hyperparams: Optional[dict] = None,
) -> Path:
    """Save XGBoost model + metadata JSON sidecar to MODELS_DIR."""
    import xgboost as xgb

    model_path = MODELS_DIR / f"{name}.json"
    meta_path  = MODELS_DIR / f"{name}_metadata.json"

    if isinstance(model, xgb.XGBClassifier) or isinstance(model, xgb.XGBRegressor):
        model.save_model(str(model_path))
    else:
        import joblib
        model_path = MODELS_DIR / f"{name}.joblib"
        joblib.dump(model, model_path)

    metadata = {
        "model_version" : model_version,
        "model_name"    : name,
        "trained_at"    : datetime.utcnow().isoformat(),
        "feature_list"  : feature_list,
        "hyperparameters": hyperparams or {},
        "metrics"       : metrics,
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[Save] {model_path}")
    return model_path


# ─── Main training pipeline ───────────────────────────────────────────────────

def run_training_pipeline() -> None:
    print("=" * 60)
    print("Bottleneck — XGBoost Training Pipeline")
    print("=" * 60)

    # 1. Load data
    print("\n[1/4] Loading training data...")
    df = load_training_data()
    print(f"      {len(df)} rows, {df['asset_id'].nunique()} assets")
    print(f"      24h positive: {df['failure_within_24h'].mean():.1%}")
    print(f"      72h positive: {df['failure_within_72h'].mean():.1%}")

    # 2. Train failure models
    print("\n[2/4] Training failure_within_24h model...")
    m24, metrics24 = train_failure_model(df, target="failure_within_24h")

    print("\n[3/4] Training failure_within_72h model...")
    m72, metrics72 = train_failure_model(df, target="failure_within_72h")

    # 3. Train anomaly model
    print("\n[4/4] Training anomaly scorer...")
    m_anom, metrics_anom = train_anomaly_model(df)

    # 4. Extract feature importance
    fi24   = extract_feature_importance(m24, FEATURE_COLUMNS)
    fi72   = extract_feature_importance(m72, FEATURE_COLUMNS)
    fi_anom = extract_feature_importance(m_anom, TELEMETRY_FEATURE_COLUMNS)

    # 5. Save artifacts
    save_model(m24,    "failure_24h", metrics24, FEATURE_COLUMNS,
               MODEL_VERSION_FAILURE,
               hyperparams={**metrics24, "target": "failure_within_24h",
                            "feature_importance": fi24})
    save_model(m72,    "failure_72h", metrics72, FEATURE_COLUMNS,
               MODEL_VERSION_FAILURE,
               hyperparams={**metrics72, "target": "failure_within_72h",
                            "feature_importance": fi72})
    save_model(m_anom, "anomaly",     metrics_anom, TELEMETRY_FEATURE_COLUMNS,
               MODEL_VERSION_ANOMALY,
               hyperparams={**metrics_anom, "feature_importance": fi_anom})

    # 6. Combined summary
    summary = {
        "trained_at"     : datetime.utcnow().isoformat(),
        "model_version"  : MODEL_VERSION_FAILURE,
        "failure_24h"    : metrics24,
        "failure_72h"    : metrics72,
        "anomaly"        : metrics_anom,
        "top_features_24h": list(fi24.keys())[:10],
    }
    with open(MODELS_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"  Models saved to: {MODELS_DIR}")
    print(f"  24h PR-AUC:  {metrics24.get('pr_auc', 'n/a')}")
    print(f"  72h PR-AUC:  {metrics72.get('pr_auc', 'n/a')}")
    print(f"  Anomaly MAE: {metrics_anom.get('mae', 'n/a')}")
    print("=" * 60)


if __name__ == "__main__":
    run_training_pipeline()
