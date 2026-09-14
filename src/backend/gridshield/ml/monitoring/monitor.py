"""
GridShield ML — Prediction Monitoring & Drift Detection
=========================================================
Tracks live prediction statistics and detects distribution drift.

Monitoring strategy
--------------------
  - PredictionLog: ring-buffer of the last N predictions per asset.
  - DriftDetector: compares rolling mean probability to a baseline (training mean).
    If the rolling mean shifts by > DRIFT_THRESHOLD, a drift alert is raised.
  - ModelHealthReport: aggregates recent predictions into a health summary
    (mean probability, anomaly rate, confidence) returned by the /api/gs/model/status endpoint.

Design decisions
----------------
  - In-memory only (no extra DB table) — fits the hackathon SQLite-first rule.
  - Thread-safe via a single RLock.
  - Clear/reset on model reload.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional


# ─── Configuration ────────────────────────────────────────────────────────────

MAX_LOG_PER_ASSET  = 200          # last N predictions per asset
DRIFT_THRESHOLD    = 0.15         # absolute shift from baseline to trigger alert
DRIFT_WINDOW       = 50           # rolling window size (predictions)
ANOMALY_RATE_ALERT = 0.30         # fraction of anomalous predictions before alert


# ─── Prediction log entry ─────────────────────────────────────────────────────

@dataclass
class PredictionLogEntry:
    asset_id                : str
    timestamp               : datetime
    failure_probability_24h : float
    failure_probability_72h : float
    anomaly_score           : float
    health_score            : float
    confidence              : float
    model_version           : str
    is_fallback             : bool


# ─── In-memory store ─────────────────────────────────────────────────────────

_lock  = threading.RLock()
_logs  : Dict[str, Deque[PredictionLogEntry]] = {}
_baseline_p24: Optional[float] = None   # set after first training run


def log_prediction(entry: PredictionLogEntry) -> None:
    with _lock:
        if entry.asset_id not in _logs:
            _logs[entry.asset_id] = deque(maxlen=MAX_LOG_PER_ASSET)
        _logs[entry.asset_id].append(entry)


def set_baseline(mean_p24: float) -> None:
    """Call after training with the training-set mean failure_within_24h probability."""
    global _baseline_p24
    with _lock:
        _baseline_p24 = mean_p24


def clear_logs() -> None:
    with _lock:
        _logs.clear()


# ─── Drift detection ──────────────────────────────────────────────────────────

@dataclass
class DriftAlert:
    asset_id        : str
    drift_detected  : bool
    baseline_mean   : float
    recent_mean     : float
    delta           : float
    window          : int
    message         : str


def check_drift(asset_id: str) -> Optional[DriftAlert]:
    """
    Returns a DriftAlert if the rolling mean p24 for this asset has shifted
    more than DRIFT_THRESHOLD from the global baseline.
    Returns None if not enough data or no baseline set.
    """
    with _lock:
        if _baseline_p24 is None:
            return None
        entries = list(_logs.get(asset_id, []))
        if len(entries) < DRIFT_WINDOW:
            return None
        recent = entries[-DRIFT_WINDOW:]
        recent_mean = sum(e.failure_probability_24h for e in recent) / len(recent)
        delta = abs(recent_mean - _baseline_p24)
        detected = delta > DRIFT_THRESHOLD

    return DriftAlert(
        asset_id       = asset_id,
        drift_detected = detected,
        baseline_mean  = round(_baseline_p24, 4),
        recent_mean    = round(recent_mean, 4),
        delta          = round(delta, 4),
        window         = DRIFT_WINDOW,
        message        = (
            f"Prediction drift detected on {asset_id}: "
            f"recent mean p24={recent_mean:.3f} vs baseline={_baseline_p24:.3f} (Δ={delta:.3f})"
            if detected else "No drift detected"
        ),
    )


def check_all_drift() -> List[DriftAlert]:
    """Check drift for all assets that have sufficient prediction logs."""
    with _lock:
        asset_ids = list(_logs.keys())
    return [a for aid in asset_ids if (a := check_drift(aid)) is not None and a.drift_detected]


# ─── Model health report ──────────────────────────────────────────────────────

@dataclass
class ModelHealthReport:
    generated_at         : str
    total_predictions    : int
    unique_assets        : int
    mean_p24             : float
    mean_anomaly_score   : float
    mean_confidence      : float
    fallback_rate        : float       # fraction of heuristic predictions
    drift_alerts         : List[dict]
    anomaly_rate_alert   : bool        # True if anomaly_rate > threshold
    model_version        : str
    baseline_p24         : Optional[float]
    status               : str         # "healthy" | "degraded" | "no_data"


def get_health_report() -> ModelHealthReport:
    with _lock:
        all_entries: List[PredictionLogEntry] = [
            e for dq in _logs.values() for e in dq
        ]

    if not all_entries:
        return ModelHealthReport(
            generated_at       = datetime.utcnow().isoformat(),
            total_predictions  = 0,
            unique_assets      = 0,
            mean_p24           = 0.0,
            mean_anomaly_score = 0.0,
            mean_confidence    = 0.0,
            fallback_rate      = 0.0,
            drift_alerts       = [],
            anomaly_rate_alert = False,
            model_version      = "unknown",
            baseline_p24       = _baseline_p24,
            status             = "no_data",
        )

    n = len(all_entries)
    mean_p24    = sum(e.failure_probability_24h for e in all_entries) / n
    mean_anom   = sum(e.anomaly_score           for e in all_entries) / n
    mean_conf   = sum(e.confidence              for e in all_entries) / n
    fallback_n  = sum(1 for e in all_entries if e.is_fallback)
    anom_rate   = sum(1 for e in all_entries if e.anomaly_score > 0.50) / n
    mv          = all_entries[-1].model_version

    drift_alerts = [
        {
            "asset_id"     : a.asset_id,
            "drift_detected": a.drift_detected,
            "delta"        : a.delta,
            "message"      : a.message,
        }
        for a in check_all_drift()
    ]

    anom_alert  = anom_rate > ANOMALY_RATE_ALERT
    fallback_r  = fallback_n / n

    status = "healthy"
    if fallback_r > 0.50:
        status = "degraded"   # more than half of predictions are heuristic
    if len(drift_alerts) > 2:
        status = "degraded"

    return ModelHealthReport(
        generated_at       = datetime.utcnow().isoformat(),
        total_predictions  = n,
        unique_assets      = len(_logs),
        mean_p24           = round(mean_p24, 4),
        mean_anomaly_score = round(mean_anom, 4),
        mean_confidence    = round(mean_conf, 4),
        fallback_rate      = round(fallback_r, 4),
        drift_alerts       = drift_alerts,
        anomaly_rate_alert = anom_alert,
        model_version      = mv,
        baseline_p24       = _baseline_p24,
        status             = status,
    )
