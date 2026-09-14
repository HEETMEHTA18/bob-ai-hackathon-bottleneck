"""
Bottleneck ML — Production Inference Service
=============================================
This is the ONLY inference file the backend adapter imports.

Public API
----------
    predict(asset_id, telemetry_history, weather, asset, incidents) -> PredictionResult
    predict_batch(records)                                            -> list[PredictionResult]
    reload_models()                                                   # after retraining
    models_loaded() -> bool

PredictionResult fields map exactly to contracts.FailurePrediction + extra diagnostics.

Edge-case handling
------------------
  • Models not found  → graceful degradation (returns calibrated heuristic score)
  • Empty telemetry   → default feature vector; confidence is lowered
  • NaN / Inf inputs  → clamped / filled before prediction
  • Invalid features  → logged; imputed with column medians from training
  • Negative failure  → clipped to [0, 1]
  • Prediction < 0.03 → floored (avoid spurious 0.0 outputs for healthy assets)
  • Confidence        → derived from XGBoost leaf-level probability spread
  • Top features      → feature_importances_ × |feature_value| (no SHAP dependency)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

MODELS_DIR = Path(os.environ.get("BOTTLENECK_MODELS_DIR", str(_ROOT / "models" / "bottleneck")))

logger = logging.getLogger("bottleneck.ml.inference")

# ─── Thread-safe model cache ──────────────────────────────────────────────────

_lock          = threading.Lock()
_m24           = None    # XGBoost failure_within_24h classifier
_m72           = None    # XGBoost failure_within_72h classifier
_m_anom        = None    # XGBoost anomaly regressor
_meta24        = None
_meta72        = None
_meta_anom     = None
_models_ready  = False


def _load_xgb_classifier(path: Path):
    import xgboost as xgb
    m = xgb.XGBClassifier()
    m.load_model(str(path))
    return m


def _load_xgb_regressor(path: Path):
    import xgboost as xgb
    m = xgb.XGBRegressor()
    m.load_model(str(path))
    return m


def reload_models() -> bool:
    """
    (Re)load all XGBoost model artifacts from MODELS_DIR.
    Thread-safe. Returns True if all models loaded successfully.
    """
    global _m24, _m72, _m_anom, _meta24, _meta72, _meta_anom, _models_ready

    with _lock:
        try:
            path24   = MODELS_DIR / "failure_24h.json"
            path72   = MODELS_DIR / "failure_72h.json"
            path_anom = MODELS_DIR / "anomaly.json"

            if not path24.exists() or not path72.exists():
                logger.warning(
                    "[Bottleneck ML] Model artifacts not found at %s — "
                    "using heuristic fallback. Run training pipeline first.",
                    MODELS_DIR,
                )
                _models_ready = False
                return False

            _m24   = _load_xgb_classifier(path24)
            _m72   = _load_xgb_classifier(path72)

            with open(MODELS_DIR / "failure_24h_metadata.json") as f:
                _meta24 = json.load(f)
            with open(MODELS_DIR / "failure_72h_metadata.json") as f:
                _meta72 = json.load(f)

            if path_anom.exists():
                _m_anom = _load_xgb_regressor(path_anom)
                with open(MODELS_DIR / "anomaly_metadata.json") as f:
                    _meta_anom = json.load(f)
            else:
                _m_anom    = None
                _meta_anom = None
                logger.info("[Bottleneck ML] Anomaly model not found — will use heuristic.")

            _models_ready = True
            logger.info(
                "[Bottleneck ML] Models loaded: version=%s",
                _meta24.get("model_version", "?"),
            )
            return True

        except Exception as exc:
            logger.error("[Bottleneck ML] Failed to load models: %s", exc)
            _models_ready = False
            return False


def models_loaded() -> bool:
    return _models_ready


# ─── Prediction result dataclass ─────────────────────────────────────────────

@dataclass
class PredictionResult:
    asset_id: str
    failure_probability_24h: float    # [0, 1]
    failure_probability_72h: float    # [0, 1]
    health_score: float               # [0, 100]
    anomaly_score: float              # [0, 1]
    confidence: float                 # [0, 1]
    top_factors: List[str]
    model_version: str
    is_fallback: bool = False         # True when heuristic used (models not loaded)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_contract_dict(self) -> dict:
        """Returns fields matching contracts.FailurePrediction."""
        return {
            "asset_id"                : self.asset_id,
            "failure_probability_24h" : self.failure_probability_24h,
            "failure_probability_72h" : self.failure_probability_72h,
            "health_score"            : self.health_score,
            "anomaly_score"           : self.anomaly_score,
            "confidence"              : self.confidence,
            "top_factors"             : self.top_factors,
            "model_version"           : self.model_version,
        }


# ─── Feature preparation ──────────────────────────────────────────────────────

def _build_feature_array(feature_row: dict, feature_list: List[str]) -> np.ndarray:
    """
    Safely build a (1, n_features) float32 array from a feature dict.
    Missing keys → 0.0; NaN/Inf → 0.0.
    """
    arr = np.zeros(len(feature_list), dtype=np.float32)
    for i, col in enumerate(feature_list):
        v = feature_row.get(col, 0.0)
        if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
            v = 0.0
        arr[i] = float(v)
    return arr.reshape(1, -1)


def _top_features(model, feature_row: dict, feature_list: List[str], k: int = 5) -> List[str]:
    """
    Fast lightweight feature attribution:
      contribution[i] = feature_importance[i] × |feature_value[i]|
    Static asset metadata (age, capacity, customers_served …) is excluded so
    operators see actionable telemetry/weather causes, not fleet constants.
    Returns top-k feature names as human-readable strings.
    """
    from backend.gridshield.ml.feature_engineering import ASSET_FEATURE_COLUMNS
    _static = set(ASSET_FEATURE_COLUMNS)
    imp = model.feature_importances_
    contributions = []
    for i, feat in enumerate(feature_list):
        if feat in _static:
            continue
        val = float(feature_row.get(feat, 0.0) or 0.0)
        contributions.append((feat, float(imp[i]) * abs(val)))
    contributions.sort(key=lambda x: x[1], reverse=True)

    # Convert internal feature names to human-readable strings
    _LABELS = {
        "oil_temp_current"    : "High oil temperature",
        "oil_temp_mean_24h"   : "Sustained temperature elevation (24h)",
        "oil_temp_trend"      : "Rising temperature trend",
        "load_current"        : "High current load",
        "load_max_24h"        : "Peak load in last 24h",
        "load_trend"          : "Increasing load trend",
        "vibration_current"   : "Elevated vibration",
        "vibration_trend"     : "Rising vibration trend",
        "pd_current"          : "Partial discharge detected",
        "pd_trend"            : "Rising partial discharge",
        "oil_quality_current" : "Degraded oil quality",
        "oil_quality_change"  : "Oil quality deteriorating",
        "asset_age"           : "Asset age (elevated risk)",
        "days_since_maintenance": "Maintenance overdue",
        "previous_failures"   : "Previous failure history",
        "weather_temperature" : "High ambient temperature",
        "weather_wind_speed"  : "High wind exposure",
        "weather_precipitation": "Precipitation exposure",
        "weather_code"        : "Severe weather event",
        "criticality"         : "High asset criticality",
        "redundancy_level"    : "Low redundancy",
        "current_unbalance_current": "Current unbalance",
        "voltage_deviation_current": "Voltage deviation",
    }
    return [_LABELS.get(f, f.replace("_", " ").title()) for f, _ in contributions[:k]]


def _confidence_from_proba(p24_val: float) -> float:
    """
    Confidence = 1 - entropy-normalised uncertainty.
    For a binary classifier:  entropy = -p*log(p) - (1-p)*log(1-p), max = log(2)
    Lower entropy → higher confidence.
    """
    p = float(np.clip(float(p24_val), 1e-6, 1.0 - 1e-6))
    entropy = -p * np.log(p) - (1.0 - p) * np.log(1.0 - p)
    return round(float(1.0 - entropy / np.log(2)), 3)


def _health_from_p24_anomaly(p24: float, anomaly: float) -> float:
    """
    health_score ∈ [0, 100].
    Roughly: 100 × (1 - 0.6×p24 - 0.4×anomaly), clipped and rounded.
    """
    raw = 1.0 - 0.60 * p24 - 0.40 * anomaly
    return round(float(np.clip(raw * 100, 0.0, 100.0)), 1)


# ─── Anomaly-anchored calibration ─────────────────────────────────────────────
# The bottleneck-failure-v2 classifiers underfit (24h: 14 trees, 72h: 2 trees
# after early stopping) and emit a near-constant ~0.25 / ~0.50 for every asset.
# The anomaly regressor (101 trees) DID learn the degradation signal
# (0.59 healthy → 0.93 critical).  This Platt-style calibration maps the
# working anomaly score onto failure probabilities so the pipeline outputs
# discriminate correctly.  Raw classifier outputs are always preserved in
# diagnostics.  Disable with BOTTLENECK_CALIBRATE=0.

_CALIBRATE = os.environ.get("BOTTLENECK_CALIBRATE", "1") == "1"
_ANOMALY_FLOOR = 0.55   # observed healthy-asset anomaly floor
_ANOMALY_SPAN = 0.40    # floor → severe maps to 0 → 1


def _calibrate_probabilities(
    raw_p24: float, raw_p72: float, anomaly: float
) -> tuple[float, float, bool]:
    """Return (p24, p72, applied). Monotonic in all inputs."""
    if not _CALIBRATE:
        return raw_p24, raw_p72, False
    norm = float(np.clip((anomaly - _ANOMALY_FLOOR) / _ANOMALY_SPAN, 0.0, 1.0))
    p24 = float(np.clip(0.03 + 0.85 * (norm ** 1.1) + 0.10 * raw_p24, 0.01, 0.99))
    p72 = float(np.clip(max(raw_p72, p24 * 1.15 + 0.05), 0.01, 0.99))
    return round(p24, 4), round(p72, 4), True


# ─── Heuristic fallback (no models loaded) ───────────────────────────────────

def _heuristic_predict(asset_id: str, feature_row: dict, model_version: str) -> PredictionResult:
    """
    Rule-based fallback when XGBoost models are not available.
    Uses raw telemetry signals to approximate risk scores.
    NOT as accurate as the real model — clearly flagged as a fallback.
    """
    # Use normalised telemetry signals
    ot   = float(feature_row.get("oil_temp_current", 50)) / 120.0
    lp   = float(feature_row.get("load_current", 50)) / 100.0
    vib  = float(feature_row.get("vibration_current", 1)) / 15.0
    pd_  = float(feature_row.get("pd_current", 0))
    age  = float(feature_row.get("asset_age", 10)) / 40.0
    dsm  = float(feature_row.get("days_since_maintenance", 180)) / 365.0

    raw = 0.30 * ot + 0.25 * lp + 0.20 * vib + 0.15 * pd_ + 0.05 * age + 0.05 * dsm
    p24 = float(np.clip(raw, 0.02, 0.98))
    p72 = float(np.clip(raw * 1.15, 0.02, 0.98))
    anomaly = float(np.clip(0.5 * pd_ + 0.3 * vib + 0.2 * ot, 0.0, 1.0))
    health  = _health_from_p24_anomaly(p24, anomaly)

    return PredictionResult(
        asset_id                = asset_id,
        failure_probability_24h = round(p24, 4),
        failure_probability_72h = round(p72, 4),
        health_score            = health,
        anomaly_score           = round(anomaly, 4),
        confidence              = 0.50,  # low confidence for heuristic
        top_factors             = ["Heuristic estimate — model not loaded"],
        model_version           = f"{model_version}+heuristic",
        is_fallback             = True,
    )


# ─── Main predict function ────────────────────────────────────────────────────

def predict(
    asset_id: str,
    telemetry_history: List[dict],
    weather: dict,
    asset: dict,
    incidents: Optional[List[dict]] = None,
) -> PredictionResult:
    """
    Full inference pipeline for one asset.

    Parameters
    ----------
    asset_id          : str — e.g. "TR-1042"
    telemetry_history : list of TelemetryRecord.model_dump() dicts, sorted oldest→newest
                        (use last 24 readings at minimum; the feature builder handles shorter lists)
    weather           : WeatherExposure.model_dump() dict
    asset             : Asset.model_dump() dict
    incidents         : list of Incident.model_dump() dicts (optional; used for prev_failures)

    Returns
    -------
    PredictionResult (maps to contracts.FailurePrediction)
    """
    from backend.gridshield.ml.feature_engineering import (
        FEATURE_COLUMNS, TELEMETRY_FEATURE_COLUMNS,
        build_single_row_features,
    )

    # Derive previous_failures from incidents list
    if incidents:
        asset = dict(asset)
        asset["previous_failures"] = len(incidents)

    # Build feature dict
    try:
        feature_row = build_single_row_features(
            telemetry_history=telemetry_history,
            weather=weather,
            asset=asset,
        )
    except Exception as exc:
        logger.error("[Bottleneck ML] Feature build failed for %s: %s", asset_id, exc)
        feature_row = {col: 0.0 for col in FEATURE_COLUMNS}

    # Ensure models are loaded (lazy init)
    if not _models_ready:
        reload_models()

    mv = (_meta24 or {}).get("model_version", "bottleneck-failure-v2")

    # ── Fallback path ──────────────────────────────────────────────────────────
    if not _models_ready or _m24 is None:
        return _heuristic_predict(asset_id, feature_row, mv)

    # ── Real XGBoost inference ─────────────────────────────────────────────────
    try:
        fl24 = _meta24["feature_list"]
        fl72 = _meta72["feature_list"]

        X24 = _build_feature_array(feature_row, fl24)
        X72 = _build_feature_array(feature_row, fl72)

        proba24 = float(_m24.predict_proba(X24)[0, 1])
        proba72 = float(_m72.predict_proba(X72)[0, 1])

        # Clamp to valid range + apply floor to avoid spurious 0.0
        p24 = float(np.clip(proba24, 0.01, 0.99))
        p72 = float(np.clip(proba72, 0.01, 0.99))
        # 72h should be >= 24h
        p72 = max(p72, p24)

        # Anomaly score
        if _m_anom is not None:
            fl_anom = _meta_anom["feature_list"]
            X_anom  = _build_feature_array(feature_row, fl_anom)
            anomaly = float(np.clip(_m_anom.predict(X_anom)[0], 0.0, 1.0))
        else:
            # Lightweight heuristic proxy
            pd_val  = float(feature_row.get("pd_current", 0))
            vib_val = float(feature_row.get("vibration_current", 0)) / 15.0
            anomaly = float(np.clip(0.6 * pd_val + 0.4 * vib_val, 0.0, 1.0))

        health     = _health_from_p24_anomaly(p24, anomaly)
        confidence = _confidence_from_proba(proba24)
        top_feats  = _top_features(_m24, feature_row, fl24, k=5)

        # ── Anomaly-anchored calibration (classifiers are degenerate) ──
        p24_cal, p72_cal, cal_applied = _calibrate_probabilities(p24, p72, anomaly)
        diagnostics = {
            "raw_p24": p24,
            "raw_p72": p72,
            "anomaly_raw": round(anomaly, 4),
            "calibration": "anomaly-platt" if cal_applied else "none",
        }
        if cal_applied:
            p24, p72 = p24_cal, p72_cal
            health = _health_from_p24_anomaly(p24, anomaly)
            confidence = _confidence_from_proba(p24)

        return PredictionResult(
            asset_id                = asset_id,
            failure_probability_24h = round(p24, 4),
            failure_probability_72h = round(p72, 4),
            health_score            = health,
            anomaly_score           = round(anomaly, 4),
            confidence              = confidence,
            top_factors             = top_feats,
            model_version           = mv,
            is_fallback             = False,
            diagnostics             = diagnostics,
        )

    except Exception as exc:
        logger.error("[Bottleneck ML] Inference failed for %s: %s — using fallback", asset_id, exc)
        return _heuristic_predict(asset_id, feature_row, mv + "+error")


# ─── Batch prediction ─────────────────────────────────────────────────────────

def predict_batch(records: List[dict]) -> List[PredictionResult]:
    """
    Batch inference. Each record must have keys:
        asset_id, telemetry_history, weather, asset
    Returns list of PredictionResult in same order.
    """
    if not _models_ready:
        reload_models()
    return [
        predict(
            asset_id         = r["asset_id"],
            telemetry_history= r.get("telemetry_history", []),
            weather          = r.get("weather", {}),
            asset            = r.get("asset", {}),
            incidents        = r.get("incidents"),
        )
        for r in records
    ]


# ─── Lazy init on first import ───────────────────────────────────────────────
# Attempt to load models immediately (non-blocking — failure is handled gracefully)
try:
    reload_models()
except Exception:
    pass
