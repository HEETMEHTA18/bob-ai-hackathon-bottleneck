"""
Bottleneck — Shared Pydantic contracts.

These are the stable data contracts for the entire Bottleneck system.
The ML boundary is: FailurePrediction — replace MockFailurePredictor with
RealFailurePredictor without changing anything downstream.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ── Asset ───────────────────────────────────────────────────────────────────

AssetType = Literal["transformer", "feeder", "breaker", "recloser", "switch", "capacitor_bank"]
AssetStatus = Literal["healthy", "degraded", "critical", "offline", "maintenance"]
RiskLevel = Literal["critical", "high", "medium", "low"]
ActionPriority = Literal["immediate", "high", "medium", "monitor"]


class Location(BaseModel):
    lat: float
    lon: float


class Asset(BaseModel):
    id: str
    name: str
    asset_type: AssetType
    substation_id: str
    location: Location
    criticality: float = Field(..., ge=0.0, le=1.0)
    capacity_mva: float
    age_years: float
    redundancy_level: float = Field(..., ge=0.0, le=1.0)
    status: AssetStatus
    region: str


# ── Telemetry ────────────────────────────────────────────────────────────────

class TelemetryRecord(BaseModel):
    asset_id: str
    timestamp: datetime
    oil_temperature: float          # °C
    load_percentage: float          # 0–100
    vibration: float                # mm/s
    current_unbalance: float        # %
    voltage_deviation: float        # %
    partial_discharge: float        # pC (picocoulombs, normalised 0-1)
    ambient_temperature: float      # °C


# ── Incident ─────────────────────────────────────────────────────────────────

class Incident(BaseModel):
    incident_id: str
    asset_id: str
    timestamp: datetime
    description: str
    severity: Literal["minor", "moderate", "major", "critical"]


# ── Maintenance ───────────────────────────────────────────────────────────────

class MaintenanceRecord(BaseModel):
    record_id: str
    asset_id: str
    date: datetime
    work_done: str
    technician: str


# ── Failure Prediction (ML boundary) ─────────────────────────────────────────

class FailurePrediction(BaseModel):
    """
    Stable ML contract.
    Replace MockFailurePredictor → RealFailurePredictor here only.
    Downstream (risk engine, APIs, frontend) must not change.
    """
    asset_id: str
    failure_probability_24h: float = Field(..., ge=0.0, le=1.0)
    failure_probability_72h: float = Field(..., ge=0.0, le=1.0)
    health_score: float = Field(..., ge=0.0, le=100.0)
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_factors: List[str]
    model_version: str = "mock-v1"


# ── Weather Exposure ──────────────────────────────────────────────────────────

class WeatherExposure(BaseModel):
    asset_id: str
    temperature: float          # °C
    wind_speed: float           # m/s
    precipitation: float        # mm/h
    humidity: float             # %
    storm_severity: float       # 0–1
    heatwave_indicator: bool
    severe_weather_indicator: bool
    weather_exposure_score: float = Field(..., ge=0.0, le=1.0)


# ── Grid Impact ───────────────────────────────────────────────────────────────

class GridImpact(BaseModel):
    asset_id: str
    customers_at_risk: int
    critical_facilities_at_risk: int
    capacity_mva: float
    grid_impact_score: float = Field(..., ge=0.0, le=1.0)
    downstream_assets: int


# ── Risk Assessment ───────────────────────────────────────────────────────────

class RiskAssessment(BaseModel):
    asset_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    failure_probability_24h: float
    failure_probability_72h: float
    health_score: float
    anomaly_score: float
    grid_impact_score: float
    weather_exposure_score: float
    criticality_score: float
    redundancy_score: float
    customers_at_risk: int
    critical_facilities_at_risk: int
    top_factors: List[str]


# ── Maintenance Recommendation ────────────────────────────────────────────────

class MaintenanceRecommendation(BaseModel):
    asset_id: str
    priority: int                           # rank 1 = most urgent
    priority_level: ActionPriority
    recommended_action: str
    recommended_window: str
    reason: str
    estimated_duration_hours: float
    assigned_crew_id: Optional[str] = None


# ── Crew ──────────────────────────────────────────────────────────────────────

class Crew(BaseModel):
    crew_id: str
    name: str
    specialty: AssetType
    region: str
    availability: Literal["available", "busy", "offline"]
    capacity: int                           # number of jobs concurrently


class CrewAssignment(BaseModel):
    crew_id: str
    asset_id: str
    assignment: Literal["Pre-position", "Dispatch", "Standby"]
    priority: int
    reason: str
    eta_hours: float


# ── Scenario ──────────────────────────────────────────────────────────────────

class ScenarioType(BaseModel):
    scenario: Literal["severe_storm", "heatwave", "asset_degradation"]
    asset_id: Optional[str] = None          # None = apply to all assets

class ScenarioResult(BaseModel):
    scenario: str
    asset_id: str
    risk_before: float
    risk_after: float
    risk_level_before: RiskLevel
    risk_level_after: RiskLevel
    maintenance_priority_before: int
    maintenance_priority_after: int
    crew_assigned: Optional[str]
    description: str


# ── API response envelopes ────────────────────────────────────────────────────

class RiskRankingEntry(BaseModel):
    rank: int
    asset: Asset
    risk: RiskAssessment
    prediction: FailurePrediction
    grid_impact: GridImpact
    weather: WeatherExposure
    maintenance: MaintenanceRecommendation


class DashboardKPIs(BaseModel):
    critical_assets: int
    high_risk_assets: int
    customers_at_risk: int
    critical_facilities_at_risk: int
    crews_pre_positioned: int
    total_assets: int
    timestamp: datetime


class Alert(BaseModel):
    alert_id: str
    asset_id: str
    asset_name: str
    severity: RiskLevel
    message: str
    timestamp: datetime
