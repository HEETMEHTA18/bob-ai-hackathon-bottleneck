"""
GridShield — Risk Engine.

Computes composite, explainable risk scores.

Risk ≠ Failure Probability.

Risk formula:
    risk_raw = failure_probability_24h
             × grid_impact_score
             × weather_exposure_score
             × criticality
             × (1 - redundancy)          ← lack-of-redundancy factor

Normalised to 0–100.

This engine is deterministic and has no external dependencies.
"""
from __future__ import annotations
import math
from typing import List, Optional

from backend.gridshield.contracts import (
    Asset, FailurePrediction, GridImpact, WeatherExposure, RiskAssessment,
    RiskLevel, RiskRankingEntry, MaintenanceRecommendation, Crew,
    CrewAssignment, NearbyCrew,
)


def _normalise(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp and normalise to [0, 1]."""
    return min(1.0, max(0.0, (value - min_val) / (max_val - min_val)))


def _risk_level(score: float) -> RiskLevel:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def compute_risk(
    asset: Asset,
    prediction: FailurePrediction,
    grid_impact: GridImpact,
    weather: WeatherExposure,
) -> RiskAssessment:
    """
    Core risk computation.  All inputs are structured contracts — no raw ML
    model internals leak through.
    """
    p24    = prediction.failure_probability_24h
    impact = grid_impact.grid_impact_score
    wx     = weather.weather_exposure_score
    crit   = asset.criticality
    redund = asset.redundancy_level

    # Composite raw risk (product of independent risk dimensions)
    lack_of_redundancy = 1.0 - redund

    # Geometric mean-style product keeps all factors influential
    raw = (
        p24 ** 0.35
        * impact ** 0.25
        * wx ** 0.15
        * crit ** 0.15
        * lack_of_redundancy ** 0.10
    )

    # Scale to 0-100 and apply a slight boost for extreme cases
    score = raw * 100.0 * 1.35
    # Apply age factor (assets > 15 years get a small bump)
    if asset.age_years > 15:
        age_boost = min(5.0, (asset.age_years - 15) * 0.5)
        score += age_boost

    score = round(min(100.0, max(0.0, score)), 1)
    level = _risk_level(score)

    return RiskAssessment(
        asset_id=asset.id,
        risk_score=score,
        risk_level=level,
        failure_probability_24h=p24,
        failure_probability_72h=prediction.failure_probability_72h,
        health_score=prediction.health_score,
        anomaly_score=prediction.anomaly_score,
        grid_impact_score=impact,
        weather_exposure_score=wx,
        criticality_score=crit,
        redundancy_score=redund,
        customers_at_risk=grid_impact.customers_at_risk,
        critical_facilities_at_risk=grid_impact.critical_facilities_at_risk,
        top_factors=prediction.top_factors,
    )


# ─── Maintenance Prioritization ──────────────────────────────────────────────

def _maintenance_action_and_window(risk: RiskAssessment) -> tuple[str, str, str, float]:
    """Returns (priority_level, action, window, estimated_hours)."""
    score = risk.risk_score
    p24   = risk.failure_probability_24h

    if score >= 80 or p24 >= 0.75:
        return (
            "immediate",
            "Immediate thermal and vibration inspection + emergency crew dispatch",
            "Within 6 hours",
            4.0,
        )
    if score >= 60 or p24 >= 0.55:
        return (
            "high",
            "Urgent inspection — oil sample, thermal imaging, contact check",
            "Within 24 hours",
            6.0,
        )
    if score >= 35 or p24 >= 0.30:
        return (
            "medium",
            "Scheduled inspection and diagnostic testing",
            "Within 72 hours",
            3.0,
        )
    return (
        "monitor",
        "Continue telemetry monitoring — schedule next routine inspection",
        "Next maintenance cycle",
        1.0,
    )


def build_maintenance_recommendation(
    asset: Asset,
    risk: RiskAssessment,
    priority_rank: int,
) -> MaintenanceRecommendation:
    level, action, window, hours = _maintenance_action_and_window(risk)

    reasons = []
    if risk.failure_probability_24h >= 0.75:
        reasons.append(f"24h failure probability {risk.failure_probability_24h:.0%}")
    if risk.grid_impact_score >= 0.70:
        reasons.append(f"grid impact affects {risk.customers_at_risk:,} customers")
    if risk.weather_exposure_score >= 0.55:
        reasons.append("severe weather exposure")
    if risk.health_score <= 50:
        reasons.append(f"asset health score {risk.health_score:.0f}/100")
    if asset.age_years > 15:
        reasons.append(f"asset age {asset.age_years:.0f} years")
    if not reasons:
        reasons.append(f"composite risk score {risk.risk_score:.0f}/100")

    reason = " — ".join(reasons).capitalize()

    return MaintenanceRecommendation(
        asset_id=asset.id,
        priority=priority_rank,
        priority_level=level,
        recommended_action=action,
        recommended_window=window,
        reason=reason,
        estimated_duration_hours=hours,
    )


# ─── Crew Pre-Positioning ─────────────────────────────────────────────────────


def _crew_assignment_type(priority_level: str) -> str:
    if priority_level == "immediate":
        return "Dispatch"
    if priority_level == "high":
        return "Pre-position"
    return "Standby"


def assign_crew(
    asset: Asset,
    maint: MaintenanceRecommendation,
    available_crews: List[Crew],
) -> Optional[CrewAssignment]:
    """
    Assign the best available crew to an asset.

    Preference order:
    1. Same region + matching specialty + available
    2. Any region + matching specialty + available
    3. Same region + available
    """
    if maint.priority_level == "monitor":
        return None

    # Score each crew
    def score(c: Crew) -> int:
        if c.availability != "available":
            return -1
        s = 0
        if c.specialty == asset.asset_type:
            s += 10
        if c.region == asset.region:
            s += 5
        return s

    ranked = sorted(available_crews, key=score, reverse=True)
    best = next((c for c in ranked if score(c) >= 0), None)
    if best is None:
        return None

    assignment_type = _crew_assignment_type(maint.priority_level)
    eta = 1.0 if assignment_type == "Dispatch" else 2.0

    return CrewAssignment(
        crew_id=best.crew_id,
        asset_id=asset.id,
        assignment=assignment_type,
        priority=maint.priority,
        reason=f"{maint.priority_level.capitalize()} priority — {maint.reason[:80]}",
        eta_hours=eta,
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def eta_hours_for_distance(distance_km: float) -> float:
    """Assume avg convoy speed of ~35 km/h inside the city network,
    with a floor for mobilization + safety time."""
    return round(max(distance_km / 35.0, 0.35), 1)


def nearest_crews(
    asset: Asset,
    crews: List[Crew],
    limit: int = 4,
    only_available: bool = True,
) -> List[NearbyCrew]:
    """
    Rank crews by distance to the asset, favouring the right specialty.
    Uses the crew depot base location (crew.lat/lon).
    """
    matching = []
    for c in crews:
        if only_available and c.availability != "available":
            continue
        if c.lat is None or c.lon is None:
            continue
        d = haversine_km(asset.location.lat, asset.location.lon, c.lat, c.lon)
        matching.append((c, d, c.specialty == asset.asset_type))

    # Specialty match first, then by distance.
    matching.sort(key=lambda t: (not t[2], t[1]))
    return [
        NearbyCrew(
            crew=c,
            distance_km=d,
            eta_hours=eta_hours_for_distance(d),
            specialty_match=match,
        )
        for c, d, match in matching[:limit]
    ]
