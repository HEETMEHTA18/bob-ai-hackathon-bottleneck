"""
GridShield — Mock ML Adapter.

INTEGRATION SEAM: to replace with the real model, swap MockFailurePredictor
for RealFailurePredictor. The contract (FailurePrediction) does not change.
The risk engine, maintenance planner, crew planner, and frontend are
completely decoupled from this implementation.

Usage:
    from backend.gridshield.ml_adapter import get_predictor
    predictor = get_predictor()
    prediction = predictor.predict(asset_id, telemetry, incidents, weather_exposure)
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import Optional

from backend.gridshield.contracts import (
    FailurePrediction, TelemetryRecord, WeatherExposure, Incident,
)


# ─── Abstract interface (the stable seam) ────────────────────────────────────

class FailurePredictor(ABC):
    """Stable ML boundary.  Replace only this implementation."""

    @abstractmethod
    def predict(
        self,
        asset_id: str,
        latest_telemetry: TelemetryRecord,
        incidents: list[Incident],
        weather: WeatherExposure,
        asset_age_years: float,
        asset_criticality: float,
    ) -> FailurePrediction:
        ...


# ─── Deterministic mock predictor ────────────────────────────────────────────

# Pre-computed deterministic outputs so every call is identical.
# Designed to demonstrate rich variety of risk profiles.
_MOCK_PREDICTIONS: dict[str, dict] = {
    "TR-1042": dict(p24=0.87, p72=0.93, health=38, anomaly=0.82, conf=0.89,
                    factors=["High transformer oil temperature (92°C)",
                              "Elevated vibration (4.8 mm/s, +60% above threshold)",
                              "Load at 88% rated capacity — sustained overloading",
                              "Recent critical overheating incident (12 days ago)",
                              "Partial discharge index elevated (0.82)"]),
    "TR-1019": dict(p24=0.61, p72=0.74, health=52, anomaly=0.58, conf=0.82,
                    factors=["Load exceeded capacity recently",
                              "Oil dissolved-gas anomaly trend",
                              "Age 14 years — approaching inspection threshold",
                              "Moderate vibration increase trend"]),
    "BR-2201": dict(p24=0.79, p72=0.88, health=41, anomaly=0.76, conf=0.86,
                    factors=["Trip operation failure (8 days ago)",
                              "Contact resistance out of specification",
                              "20-year-old asset — critical replacement zone",
                              "Load at 91% rated capacity"]),
    "FD-3310": dict(p24=0.52, p72=0.63, health=60, anomaly=0.48, conf=0.78,
                    factors=["Cable insulation degradation detected",
                              "Phase imbalance events in past month",
                              "Current unbalance 4.2%"]),
    "TR-2055": dict(p24=0.55, p72=0.67, health=57, anomaly=0.50, conf=0.80,
                    factors=["Cooling fan failure event (25 days ago)",
                              "Winding resistance out of tolerance",
                              "Moderate temperature elevation trend"]),
    "RC-4401": dict(p24=0.18, p72=0.25, health=82, anomaly=0.15, conf=0.91,
                    factors=["All parameters within normal range",
                              "Recent recloser operations within specification"]),
    "BR-1175": dict(p24=0.64, p72=0.75, health=49, anomaly=0.61, conf=0.83,
                    factors=["Spurious tripping event (18 days ago)",
                              "16-year asset — maintenance interval due",
                              "Elevated vibration and current unbalance"]),
    "SW-5520": dict(p24=0.12, p72=0.18, health=88, anomaly=0.10, conf=0.93,
                    factors=["All telemetry nominal",
                              "Recent operational test passed"]),
    "TR-3088": dict(p24=0.28, p72=0.38, health=74, anomaly=0.25, conf=0.88,
                    factors=["Parameters within range",
                              "Minor temperature elevation noted"]),
    "CB-6601": dict(p24=0.08, p72=0.12, health=94, anomaly=0.06, conf=0.95,
                    factors=["All parameters excellent", "Low utilisation"]),
    "FD-2280": dict(p24=0.22, p72=0.31, health=79, anomaly=0.19, conf=0.89,
                    factors=["Normal load and temperature",
                              "Minor current unbalance trend"]),
    "RC-3320": dict(p24=0.10, p72=0.15, health=91, anomaly=0.08, conf=0.94,
                    factors=["All parameters excellent", "Low age and usage"]),
    "TR-5099": dict(p24=0.41, p72=0.55, health=65, anomaly=0.38, conf=0.82,
                    factors=["Elevated exposure to storm weather",
                              "Moderate temperature and vibration trends",
                              "Weather-sensitive location"]),
    "FD-1140": dict(p24=0.34, p72=0.46, health=69, anomaly=0.30, conf=0.83,
                    factors=["Coastal weather exposure",
                              "Moderate load and humidity stress"]),
    "TR-7001": dict(p24=0.06, p72=0.09, health=96, anomaly=0.04, conf=0.97,
                    factors=["New asset (2 years)", "All parameters excellent"]),
    "BR-7110": dict(p24=0.05, p72=0.08, health=97, anomaly=0.03, conf=0.97,
                    factors=["New asset", "All parameters nominal"]),
    "SW-7220": dict(p24=0.04, p72=0.07, health=98, anomaly=0.03, conf=0.98,
                    factors=["New asset", "All parameters nominal"]),
    "CB-7330": dict(p24=0.03, p72=0.05, health=99, anomaly=0.02, conf=0.98,
                    factors=["New asset", "Excellent condition"]),
    "TR-4060": dict(p24=0.48, p72=0.60, health=61, anomaly=0.44, conf=0.80,
                    factors=["Oil leak at gasket — slow but worsening",
                              "13-year asset trending toward failure band",
                              "Moderate vibration increase"]),
    "FD-4480": dict(p24=0.20, p72=0.28, health=81, anomaly=0.17, conf=0.88,
                    factors=["Normal parameters", "Minor load variation"]),
    "TR-9001": dict(p24=0.30, p72=0.42, health=72, anomaly=0.26, conf=0.86,
                    factors=["Annual inspection overdue",
                              "Moderate load on high-criticality asset",
                              "Serves hospital district — elevated consequence"]),
    "BR-9010": dict(p24=0.22, p72=0.32, health=78, anomaly=0.19, conf=0.88,
                    factors=["Normal parameters",
                              "High criticality — data centre supply",
                              "Inspection recommended"]),
    "RC-2210": dict(p24=0.15, p72=0.22, health=85, anomaly=0.12, conf=0.91,
                    factors=["Parameters normal", "Minor operation count increase"]),
    "SW-3301": dict(p24=0.08, p72=0.12, health=93, anomaly=0.06, conf=0.95,
                    factors=["Parameters excellent", "Low utilisation"]),
    "CB-2240": dict(p24=0.07, p72=0.10, health=94, anomaly=0.05, conf=0.96,
                    factors=["Parameters excellent"]),
    "TR-6050": dict(p24=0.36, p72=0.48, health=67, anomaly=0.32, conf=0.82,
                    factors=["Airport zone — high traffic vibration exposure",
                              "Moderate load and temperature trends",
                              "High criticality asset"]),
    "FD-6060": dict(p24=0.33, p72=0.45, health=68, anomaly=0.29, conf=0.82,
                    factors=["Airport zone feeder", "Moderate stress indicators"]),
    "BR-5511": dict(p24=0.58, p72=0.70, health=53, anomaly=0.55, conf=0.81,
                    factors=["Contact wear exceeds threshold",
                              "Elevated vibration and current unbalance",
                              "11-year asset — service due"]),
    "RC-6600": dict(p24=0.14, p72=0.20, health=86, anomaly=0.11, conf=0.91,
                    factors=["Parameters normal", "Minor age-related wear"]),
    "TR-8080": dict(p24=0.46, p72=0.58, health=62, anomaly=0.42, conf=0.80,
                    factors=["OLTC noise indicating mechanism wear",
                              "12-year asset with moderate degradation",
                              "Moderate temperature and vibration"]),
}

# Default for unknown assets
_DEFAULT_PREDICTION = dict(p24=0.15, p72=0.22, health=80, anomaly=0.12, conf=0.85,
                           factors=["Insufficient telemetry history",
                                    "Default risk estimate applied"])


class MockFailurePredictor(FailurePredictor):
    """
    Deterministic mock predictor.

    Returns pre-computed values — identical on every call, fully explainable.
    Replace this class with RealFailurePredictor when the teammate ML pipeline
    is ready.  The FailurePrediction contract does not change.
    """
    MODEL_VERSION = "mock-v1"

    def predict(
        self,
        asset_id: str,
        latest_telemetry: TelemetryRecord,
        incidents: list[Incident],
        weather: WeatherExposure,
        asset_age_years: float,
        asset_criticality: float,
    ) -> FailurePrediction:
        d = _MOCK_PREDICTIONS.get(asset_id, _DEFAULT_PREDICTION)
        return FailurePrediction(
            asset_id=asset_id,
            failure_probability_24h=d["p24"],
            failure_probability_72h=d["p72"],
            health_score=d["health"],
            anomaly_score=d["anomaly"],
            confidence=d["conf"],
            top_factors=list(d["factors"]),
            model_version=self.MODEL_VERSION,
        )


# ─── Scenario-aware predictor wrapper ────────────────────────────────────────

_SCENARIO_MODIFIERS = {
    "severe_storm": dict(p24=+0.20, p72=+0.15, health=-15, anomaly=+0.18),
    "heatwave":     dict(p24=+0.15, p72=+0.12, health=-10, anomaly=+0.12),
    "asset_degradation": dict(p24=+0.25, p72=+0.20, health=-20, anomaly=+0.22),
}


class ScenarioFailurePredictor(FailurePredictor):
    """Wraps MockFailurePredictor and applies scenario deltas deterministically."""

    def __init__(self, scenario: str, base: Optional[FailurePredictor] = None):
        self.scenario = scenario
        self.base = base or MockFailurePredictor()

    def predict(
        self,
        asset_id: str,
        latest_telemetry: TelemetryRecord,
        incidents: list[Incident],
        weather: WeatherExposure,
        asset_age_years: float,
        asset_criticality: float,
    ) -> FailurePrediction:
        base_pred = self.base.predict(
            asset_id, latest_telemetry, incidents, weather, asset_age_years, asset_criticality
        )
        mod = _SCENARIO_MODIFIERS.get(self.scenario, {})
        return FailurePrediction(
            asset_id=asset_id,
            failure_probability_24h=min(1.0, max(0.0, base_pred.failure_probability_24h + mod.get("p24", 0))),
            failure_probability_72h=min(1.0, max(0.0, base_pred.failure_probability_72h + mod.get("p72", 0))),
            health_score=min(100.0, max(0.0, base_pred.health_score + mod.get("health", 0))),
            anomaly_score=min(1.0, max(0.0, base_pred.anomaly_score + mod.get("anomaly", 0))),
            confidence=base_pred.confidence,
            top_factors=[f"[{self.scenario.upper()}] {f}" for f in base_pred.top_factors],
            model_version=f"mock-v1+{self.scenario}",
        )


# ─── Factory ─────────────────────────────────────────────────────────────────

def get_predictor(scenario: Optional[str] = None) -> FailurePredictor:
    """
    Factory.  Returns the active predictor.

    Future: check env/config, return RealFailurePredictor when available.
    """
    use_real = os.environ.get("GRIDSHIELD_USE_REAL_ML", "0") == "1"
    if use_real:
        # Future integration point
        # from backend.gridshield.real_ml_adapter import RealFailurePredictor
        # return RealFailurePredictor()
        pass

    if scenario:
        return ScenarioFailurePredictor(scenario)
    return MockFailurePredictor()
