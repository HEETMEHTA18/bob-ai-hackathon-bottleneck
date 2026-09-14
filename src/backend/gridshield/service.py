"""
GridShield — Orchestrator service.

Single entry point for computing all GridShield outputs for one or all assets.
Keeps route handlers thin.
"""
from __future__ import annotations
from typing import List, Optional, Dict

from backend.gridshield.contracts import (
    Asset, RiskAssessment, GridImpact, WeatherExposure, FailurePrediction,
    MaintenanceRecommendation, Crew, CrewAssignment, RiskRankingEntry,
    DashboardKPIs, Alert, ScenarioResult,
)
from backend.gridshield.mock_data import (
    ASSETS, ASSET_MAP, CREWS, get_latest_telemetry, get_incidents,
)
from backend.gridshield.ml_adapter import get_predictor
from backend.gridshield.grid_impact import compute_grid_impact
from backend.gridshield.weather_adapter import get_weather_exposure
from backend.gridshield.risk_engine import (
    compute_risk, build_maintenance_recommendation, assign_crew,
)
from datetime import datetime


def _compute_for_asset(
    asset: Asset,
    scenario: Optional[str] = None,
    crews_pool: Optional[List[Crew]] = None,
    priority_override: Optional[int] = None,
) -> tuple[FailurePrediction, GridImpact, WeatherExposure, RiskAssessment, MaintenanceRecommendation]:
    telemetry = get_latest_telemetry(asset.id)
    incidents = get_incidents(asset.id)
    weather   = get_weather_exposure(asset, scenario=scenario)
    predictor = get_predictor(scenario=scenario)
    prediction = predictor.predict(
        asset_id=asset.id,
        latest_telemetry=telemetry,
        incidents=incidents,
        weather=weather,
        asset_age_years=asset.age_years,
        asset_criticality=asset.criticality,
    )
    grid_impact = compute_grid_impact(asset)
    risk        = compute_risk(asset, prediction, grid_impact, weather)
    maint       = build_maintenance_recommendation(asset, risk, priority_override or 0)

    # Log prediction for monitoring (only non-scenario predictions; scenarios are ephemeral)
    if scenario is None:
        try:
            import os
            if os.environ.get("GRIDSHIELD_USE_REAL_ML", "0") == "1":
                from backend.gridshield.ml.monitoring.monitor import log_prediction, PredictionLogEntry
                from datetime import datetime as _dt
                log_prediction(PredictionLogEntry(
                    asset_id                = prediction.asset_id,
                    timestamp               = _dt.utcnow(),
                    failure_probability_24h = prediction.failure_probability_24h,
                    failure_probability_72h = prediction.failure_probability_72h,
                    anomaly_score           = prediction.anomaly_score,
                    health_score            = prediction.health_score,
                    confidence              = prediction.confidence,
                    model_version           = prediction.model_version,
                    is_fallback             = "+heuristic" in prediction.model_version,
                ))
        except Exception:
            pass  # Monitoring must never break prediction

    return prediction, grid_impact, weather, risk, maint


import threading

_ranking_cache = {}
_ranking_lock = threading.Lock()

def get_full_ranking(scenario: Optional[str] = None) -> List[RiskRankingEntry]:
    """Compute ranked risk assessment for all assets."""
    global _ranking_cache
    cache_key = scenario or "default"
    
    with _ranking_lock:
        now = datetime.now()
        if cache_key in _ranking_cache:
            cache_time, cached_ranking = _ranking_cache[cache_key]
            if (now - cache_time).total_seconds() < 15:
                return cached_ranking

        entries = []
        available_crews = list(CREWS)
    
        # Phase 1: compute all risks
        intermediate = []
    for asset in ASSETS:
        pred, impact, wx, risk, _ = _compute_for_asset(asset, scenario=scenario)
        intermediate.append((asset, pred, impact, wx, risk))

    # Sort by risk score descending
    intermediate.sort(key=lambda x: x[4].risk_score, reverse=True)

    # Phase 2: build ranked entries with correct priority and crew assignments
    assigned_crews: set[str] = set()
    for rank, (asset, pred, impact, wx, risk) in enumerate(intermediate, start=1):
        maint = build_maintenance_recommendation(asset, risk, rank)
        # Find crew not yet assigned
        pool = [c for c in available_crews if c.crew_id not in assigned_crews]
        crew_assign = assign_crew(asset, maint, pool)
        if crew_assign:
            assigned_crews.add(crew_assign.crew_id)
            maint.assigned_crew_id = crew_assign.crew_id

        entries.append(RiskRankingEntry(
            rank=rank,
            asset=asset,
            risk=risk,
            prediction=pred,
            grid_impact=impact,
            weather=wx,
            maintenance=maint,
        ))

    with _ranking_lock:
        _ranking_cache[cache_key] = (datetime.now(), entries)

    return entries


def get_dashboard_kpis(ranking: List[RiskRankingEntry]) -> DashboardKPIs:
    critical = sum(1 for e in ranking if e.risk.risk_level == "critical")
    high     = sum(1 for e in ranking if e.risk.risk_level == "high")
    customers = sum(e.risk.customers_at_risk for e in ranking
                    if e.risk.risk_level in ("critical", "high"))
    facilities = sum(e.risk.critical_facilities_at_risk for e in ranking
                     if e.risk.risk_level in ("critical", "high"))
    crews_positioned = sum(1 for e in ranking
                           if e.maintenance.assigned_crew_id is not None
                           and e.maintenance.priority_level in ("immediate", "high"))
    return DashboardKPIs(
        critical_assets=critical,
        high_risk_assets=high,
        customers_at_risk=customers,
        critical_facilities_at_risk=facilities,
        crews_pre_positioned=crews_positioned,
        total_assets=len(ranking),
        timestamp=datetime.now(),
    )


def get_alerts(ranking: List[RiskRankingEntry]) -> List[Alert]:
    alerts = []
    now = datetime.now()
    alert_id = 1
    for entry in ranking:
        r = entry.risk
        a = entry.asset
        if r.risk_level in ("critical", "high"):
            msg = _build_alert_message(a, r, entry.maintenance)
            alerts.append(Alert(
                alert_id=f"ALT-{alert_id:04d}",
                asset_id=a.id,
                asset_name=a.name,
                severity=r.risk_level,
                message=msg,
                timestamp=now,
            ))
            alert_id += 1
    return alerts[:20]  # cap at 20


def _build_alert_message(asset: Asset, risk: RiskAssessment, maint: MaintenanceRecommendation) -> str:
    parts = []
    if risk.failure_probability_24h >= 0.75:
        parts.append(f"CRITICAL: {asset.name} — {risk.failure_probability_24h:.0%} 24h failure probability")
    elif risk.risk_level == "critical":
        parts.append(f"CRITICAL RISK: {asset.name} — Risk Score {risk.risk_score:.0f}/100")
    else:
        parts.append(f"HIGH RISK: {asset.name} — Risk Score {risk.risk_score:.0f}/100")
    if risk.critical_facilities_at_risk > 0:
        parts.append(f"{risk.critical_facilities_at_risk} critical facilities at risk")
    parts.append(maint.recommended_action[:60])
    return " | ".join(parts)


def run_scenario(scenario: str, asset_id: Optional[str] = None) -> List[ScenarioResult]:
    """
    Run a scenario simulation.  Returns before/after comparison for affected assets.
    """
    assets = [ASSET_MAP[asset_id]] if asset_id and asset_id in ASSET_MAP else ASSETS

    # Only simulate high-risk assets or the requested specific asset
    if not asset_id:
        assets = [a for a in assets if a.status in ("degraded", "critical")][:10]

    results = []
    for asset in assets:
        _, _, _, risk_before, maint_before = _compute_for_asset(asset)
        _, _, _, risk_after,  maint_after  = _compute_for_asset(asset, scenario=scenario)

        crew_assignments = assign_crew(asset, maint_after, list(CREWS))
        crew_str = crew_assignments.crew_id if crew_assignments else None

        results.append(ScenarioResult(
            scenario=scenario,
            asset_id=asset.id,
            risk_before=risk_before.risk_score,
            risk_after=risk_after.risk_score,
            risk_level_before=risk_before.risk_level,
            risk_level_after=risk_after.risk_level,
            maintenance_priority_before=maint_before.priority,
            maintenance_priority_after=maint_after.priority,
            crew_assigned=crew_str,
            description=_scenario_description(scenario, asset, risk_before, risk_after),
        ))

    results.sort(key=lambda r: r.risk_after - r.risk_before, reverse=True)
    return results


def _scenario_description(scenario: str, asset: Asset, before: RiskAssessment, after: RiskAssessment) -> str:
    delta = after.risk_score - before.risk_score
    if scenario == "severe_storm":
        return (f"{asset.name}: Severe storm increases risk by {delta:+.1f} points "
                f"({before.risk_score:.0f} → {after.risk_score:.0f}). "
                f"Weather exposure drives failure probability to {after.failure_probability_24h:.0%}.")
    if scenario == "heatwave":
        return (f"{asset.name}: Heatwave thermal stress raises risk by {delta:+.1f} points "
                f"({before.risk_score:.0f} → {after.risk_score:.0f}). "
                f"Oil temperature and load increase accelerate degradation.")
    if scenario == "asset_degradation":
        return (f"{asset.name}: Accelerated degradation raises risk by {delta:+.1f} points "
                f"({before.risk_score:.0f} → {after.risk_score:.0f}). "
                f"Anomaly score increases to {after.anomaly_score:.2f}.")
    return f"Risk changed by {delta:+.1f} points."
