"""
GridShield — API Routes.

All GridShield endpoints live under /api/gs/ to coexist with existing Gridkavach
routes during the transition period.

Required endpoints:
  GET  /api/gs/assets
  GET  /api/gs/assets/{asset_id}
  GET  /api/gs/assets/{asset_id}/telemetry
  GET  /api/gs/assets/{asset_id}/incidents
  GET  /api/gs/assets/{asset_id}/maintenance
  GET  /api/gs/weather
  GET  /api/gs/predictions
  GET  /api/gs/risk
  GET  /api/gs/risk/ranking
  GET  /api/gs/maintenance/priorities
  GET  /api/gs/crew
  GET  /api/gs/crew/plan
  POST /api/gs/scenarios/simulate
  GET  /api/gs/dashboard/kpis
  GET  /api/gs/dashboard/alerts
  POST /api/gs/chat
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime

from backend.gridshield.mock_data import ASSETS, ASSET_MAP, CREWS, get_telemetry, get_incidents, get_maintenance_records
from backend.gridshield.weather_adapter import get_weather_exposure
from backend.gridshield.contracts import ScenarioType
from backend.gridshield import service
from backend.gridshield.copilot import gridshield_advisor

router = APIRouter(prefix="/api/gs", tags=["GridShield"])

# In-memory chat session store (same pattern as Gridkavach chat.py)
_chat_sessions: dict[str, dict] = {}


# ─── Assets ──────────────────────────────────────────────────────────────────

@router.get("/assets")
def list_assets(
    asset_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    assets = ASSETS
    if asset_type:
        assets = [a for a in assets if a.asset_type == asset_type]
    if region:
        assets = [a for a in assets if a.region.lower() == region.lower()]
    if status:
        assets = [a for a in assets if a.status == status]
    return {"assets": [a.model_dump() for a in assets], "count": len(assets)}


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    asset = ASSET_MAP.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset.model_dump()


@router.get("/assets/{asset_id}/telemetry")
def asset_telemetry(asset_id: str, hours: int = Query(48, ge=1, le=168)):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    records = get_telemetry(asset_id, hours=hours)
    return {"asset_id": asset_id, "records": [r.model_dump() for r in records], "count": len(records)}


@router.get("/assets/{asset_id}/incidents")
def asset_incidents(asset_id: str):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    incidents = get_incidents(asset_id)
    return {"asset_id": asset_id, "incidents": [i.model_dump() for i in incidents]}


@router.get("/assets/{asset_id}/maintenance")
def asset_maintenance(asset_id: str):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    records = get_maintenance_records(asset_id)
    return {"asset_id": asset_id, "records": [r.model_dump() for r in records]}


# ─── Weather ─────────────────────────────────────────────────────────────────

@router.get("/weather")
def get_weather(asset_id: Optional[str] = Query(None)):
    if asset_id:
        asset = ASSET_MAP.get(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return get_weather_exposure(asset).model_dump()
    # Return all assets' weather exposure
    return {
        "exposures": [get_weather_exposure(a).model_dump() for a in ASSETS]
    }


# ─── Predictions ─────────────────────────────────────────────────────────────

@router.get("/predictions")
def get_predictions(asset_id: Optional[str] = Query(None)):
    from backend.gridshield.ml_adapter import get_predictor
    from backend.gridshield.mock_data import get_latest_telemetry, get_incidents
    predictor = get_predictor()

    if asset_id:
        asset = ASSET_MAP.get(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        telemetry = get_latest_telemetry(asset_id)
        incidents = get_incidents(asset_id)
        weather   = get_weather_exposure(asset)
        pred = predictor.predict(asset_id, telemetry, incidents, weather, asset.age_years, asset.criticality)
        return pred.model_dump()

    preds = []
    for asset in ASSETS:
        telemetry = get_latest_telemetry(asset.id)
        incidents = get_incidents(asset.id)
        weather   = get_weather_exposure(asset)
        pred = predictor.predict(asset.id, telemetry, incidents, weather, asset.age_years, asset.criticality)
        preds.append(pred.model_dump())
    return {"predictions": preds}


# ─── Risk ─────────────────────────────────────────────────────────────────────

@router.get("/risk")
def get_risk(asset_id: Optional[str] = Query(None)):
    ranking = service.get_full_ranking()
    if asset_id:
        entry = next((e for e in ranking if e.asset.id == asset_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return entry.risk.model_dump()
    return {"risks": [e.risk.model_dump() for e in ranking]}


@router.get("/risk/ranking")
def get_risk_ranking(scenario: Optional[str] = Query(None)):
    ranking = service.get_full_ranking(scenario=scenario)
    return {
        "ranking": [
            {
                "rank": e.rank,
                "asset_id": e.asset.id,
                "asset_name": e.asset.name,
                "asset_type": e.asset.asset_type,
                "region": e.asset.region,
                "status": e.asset.status,
                "risk_score": e.risk.risk_score,
                "risk_level": e.risk.risk_level,
                "failure_probability_24h": e.risk.failure_probability_24h,
                "failure_probability_72h": e.risk.failure_probability_72h,
                "health_score": e.risk.health_score,
                "customers_at_risk": e.risk.customers_at_risk,
                "critical_facilities_at_risk": e.risk.critical_facilities_at_risk,
                "grid_impact_score": e.risk.grid_impact_score,
                "recommended_action": e.maintenance.recommended_action,
                "priority_level": e.maintenance.priority_level,
                "assigned_crew": e.maintenance.assigned_crew_id,
                "top_factors": e.risk.top_factors,
            }
            for e in ranking
        ],
        "total": len(ranking),
        "scenario": scenario,
    }


# ─── Asset detail (full intelligence) ────────────────────────────────────────

@router.get("/assets/{asset_id}/intelligence")
def asset_intelligence(asset_id: str):
    """Full asset intelligence page data."""
    asset = ASSET_MAP.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    ranking = service.get_full_ranking()
    entry = next((e for e in ranking if e.asset.id == asset_id), None)
    if not entry:
        raise HTTPException(status_code=500, detail="Risk computation failed")
    telemetry = get_telemetry(asset_id, hours=24)
    incidents = get_incidents(asset_id)
    maintenance = get_maintenance_records(asset_id)
    return {
        "asset": asset.model_dump(),
        "risk": entry.risk.model_dump(),
        "prediction": entry.prediction.model_dump(),
        "grid_impact": entry.grid_impact.model_dump(),
        "weather": entry.weather.model_dump(),
        "maintenance_recommendation": entry.maintenance.model_dump(),
        "telemetry_24h": [t.model_dump() for t in telemetry],
        "incidents": [i.model_dump() for i in incidents],
        "maintenance_history": [m.model_dump() for m in maintenance],
    }


# ─── Maintenance ─────────────────────────────────────────────────────────────

@router.get("/maintenance/priorities")
def get_maintenance_priorities(
    priority_level: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
):
    ranking = service.get_full_ranking()
    results = []
    for entry in ranking:
        m = entry.maintenance
        a = entry.asset
        r = entry.risk
        if priority_level and m.priority_level != priority_level:
            continue
        if asset_type and a.asset_type != asset_type:
            continue
        if region and a.region.lower() != region.lower():
            continue
        results.append({
            "priority": m.priority,
            "priority_level": m.priority_level,
            "asset_id": a.id,
            "asset_name": a.name,
            "asset_type": a.asset_type,
            "region": a.region,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "failure_probability_24h": r.failure_probability_24h,
            "recommended_action": m.recommended_action,
            "recommended_window": m.recommended_window,
            "reason": m.reason,
            "estimated_duration_hours": m.estimated_duration_hours,
            "assigned_crew_id": m.assigned_crew_id,
            "customers_at_risk": r.customers_at_risk,
            "critical_facilities_at_risk": r.critical_facilities_at_risk,
        })
    return {"priorities": results, "count": len(results)}


# ─── Crew ─────────────────────────────────────────────────────────────────────

@router.get("/crew")
def list_crews(availability: Optional[str] = Query(None)):
    crews = CREWS
    if availability:
        crews = [c for c in crews if c.availability == availability]
    return {"crews": [c.model_dump() for c in crews], "count": len(crews)}


@router.get("/crew/plan")
def get_crew_plan():
    """Full crew pre-positioning plan."""
    from backend.gridshield.risk_engine import assign_crew
    ranking = service.get_full_ranking()
    assignments = []
    assigned_crews: set[str] = set()
    for entry in ranking:
        if entry.maintenance.priority_level == "monitor":
            continue
        available = [c for c in CREWS if c.crew_id not in assigned_crews and c.availability == "available"]
        assignment = assign_crew(entry.asset, entry.maintenance, available)
        if assignment:
            assigned_crews.add(assignment.crew_id)
            crew_detail = next((c for c in CREWS if c.crew_id == assignment.crew_id), None)
            assignments.append({
                **assignment.model_dump(),
                "asset_name": entry.asset.name,
                "asset_type": entry.asset.asset_type,
                "region": entry.asset.region,
                "risk_score": entry.risk.risk_score,
                "risk_level": entry.risk.risk_level,
                "crew_name": crew_detail.name if crew_detail else assignment.crew_id,
                "crew_specialty": crew_detail.specialty if crew_detail else None,
            })
    # Crews not assigned → standby
    standby = [
        {
            "crew_id": c.crew_id,
            "crew_name": c.name,
            "specialty": c.specialty,
            "region": c.region,
            "availability": c.availability,
            "status": "standby" if c.availability == "available" else c.availability,
        }
        for c in CREWS if c.crew_id not in assigned_crews
    ]
    return {
        "assignments": assignments,
        "standby": standby,
        "total_assigned": len(assignments),
        "total_standby": len(standby),
    }


# ─── Scenarios ────────────────────────────────────────────────────────────────

@router.post("/scenarios/simulate")
def simulate_scenario(data: ScenarioType):
    results = service.run_scenario(data.scenario, asset_id=data.asset_id)
    return {
        "scenario": data.scenario,
        "asset_id": data.asset_id,
        "results": [r.model_dump() for r in results],
        "count": len(results),
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard/kpis")
def dashboard_kpis(scenario: Optional[str] = Query(None)):
    ranking = service.get_full_ranking(scenario=scenario)
    kpis = service.get_dashboard_kpis(ranking)
    return kpis.model_dump()


@router.get("/dashboard/alerts")
def dashboard_alerts():
    ranking = service.get_full_ranking()
    alerts = service.get_alerts(ranking)
    return {"alerts": [a.model_dump() for a in alerts], "count": len(alerts)}


# ─── Copilot ─────────────────────────────────────────────────────────────────

class CopilotRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class CopilotResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str


@router.post("/chat", response_model=CopilotResponse)
def gridshield_chat(data: CopilotRequest):
    session_id = data.session_id or str(uuid.uuid4())[:8]
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = {"messages": []}
    session = _chat_sessions[session_id]

    session["messages"].append({"role": "user", "content": data.message})

    # Get full ranking for grounded responses
    ranking = service.get_full_ranking()
    response_text = gridshield_advisor(data.message, ranking, history=session["messages"])

    session["messages"].append({"role": "assistant", "content": response_text})
    now = datetime.now().isoformat()
    return CopilotResponse(session_id=session_id, response=response_text, timestamp=now)


@router.get("/chat/sessions/{session_id}")
def get_chat_session(session_id: str):
    if session_id not in _chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _chat_sessions[session_id]
