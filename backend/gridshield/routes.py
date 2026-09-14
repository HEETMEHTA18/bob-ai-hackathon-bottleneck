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
import re
import time as _time
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime

from backend.gridshield.mock_data import ASSETS, ASSET_MAP, CREWS, CREW_MAP, get_telemetry, get_incidents, get_maintenance_records, get_hardware_config, get_all_hardware_configs
from backend.gridshield.weather_adapter import get_weather_exposure
from backend.gridshield.contracts import ScenarioType
from backend.gridshield import service
from backend.gridshield.copilot import gridshield_advisor
from backend.dependencies import get_current_user
from backend.models_db import User

router = APIRouter(prefix="/api/gs", tags=["GridShield"])

# Bounded in-memory chat session store with TTL
_chat_sessions: dict[str, dict] = {}
_CHAT_SESSION_MAX = 200
_CHAT_SESSION_TTL = 3600  # 1 hour


def _cleanup_chat_sessions():
    """Evict oldest sessions when exceeding max, and expired sessions."""
    now = _time.time()
    expired = [sid for sid, s in _chat_sessions.items() if now - s.get("created_at", 0) > _CHAT_SESSION_TTL]
    for sid in expired:
        del _chat_sessions[sid]
    # If still over limit, evict oldest
    if len(_chat_sessions) > _CHAT_SESSION_MAX:
        sorted_sessions = sorted(_chat_sessions.items(), key=lambda x: x[1].get("created_at", 0))
        for sid, _ in sorted_sessions[:len(_chat_sessions) - _CHAT_SESSION_MAX]:
            del _chat_sessions[sid]


def _sanitize_input(text: str, max_len: int = 2000) -> str:
    """Strip control characters and enforce length limit."""
    text = text.strip()[:max_len]
    # Remove null bytes and control chars except newline/tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text


# ─── Assets ──────────────────────────────────────────────────────────────────

@router.get("/assets")
def list_assets(
    asset_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    _user: User = Depends(get_current_user),
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
def get_asset(asset_id: str, _user: User = Depends(get_current_user)):
    asset = ASSET_MAP.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset.model_dump()


@router.get("/assets/{asset_id}/telemetry")
def asset_telemetry(asset_id: str, hours: int = Query(48, ge=1, le=168), _user: User = Depends(get_current_user)):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    records = get_telemetry(asset_id, hours=hours)
    return {"asset_id": asset_id, "records": [r.model_dump() for r in records], "count": len(records)}


@router.get("/assets/{asset_id}/incidents")
def asset_incidents(asset_id: str, _user: User = Depends(get_current_user)):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    incidents = get_incidents(asset_id)
    return {"asset_id": asset_id, "incidents": [i.model_dump() for i in incidents]}


@router.get("/assets/{asset_id}/maintenance")
def asset_maintenance(asset_id: str, _user: User = Depends(get_current_user)):
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    records = get_maintenance_records(asset_id)
    return {"asset_id": asset_id, "records": [r.model_dump() for r in records]}


# ─── Weather ─────────────────────────────────────────────────────────────────

@router.get("/weather")
def get_weather(asset_id: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
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
def get_predictions(asset_id: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
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
def get_risk(asset_id: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
    ranking = service.get_full_ranking()
    if asset_id:
        entry = next((e for e in ranking if e.asset.id == asset_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return entry.risk.model_dump()
    return {"risks": [e.risk.model_dump() for e in ranking]}


@router.get("/risk/ranking")
def get_risk_ranking(scenario: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
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
                "asset_lat": e.asset.location.lat,
                "asset_lon": e.asset.location.lon,
            }
            for e in ranking
        ],
        "total": len(ranking),
        "scenario": scenario,
    }


# ─── Asset detail (full intelligence) ────────────────────────────────────────

@router.get("/assets/{asset_id}/intelligence")
def asset_intelligence(asset_id: str, _user: User = Depends(get_current_user)):
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
    _user: User = Depends(get_current_user),
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
def list_crews(availability: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
    crews = CREWS
    if availability:
        crews = [c for c in crews if c.availability == availability]
    return {"crews": [c.model_dump() for c in crews], "count": len(crews)}


@router.get("/crew/plan")
def get_crew_plan(_user: User = Depends(get_current_user)):
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


@router.get("/assets/{asset_id}/crew/nearby")
def nearest_crew_for_asset(asset_id: str, limit: int = Query(4, ge=1, le=10), _user: User = Depends(get_current_user)):
    """Rank available crews by distance to the asset (nearest first)."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    from backend.gridshield.risk_engine import nearest_crews
    asset = ASSET_MAP[asset_id]
    nearby = nearest_crews(asset, CREWS, limit=limit)
    return {
        "asset_id": asset_id,
        "asset_lat": asset.location.lat,
        "asset_lon": asset.location.lon,
        "nearby": [n.model_dump() for n in nearby],
    }


@router.post("/assets/{asset_id}/crew/assign")
def assign_crew_to_asset(asset_id: str, data: dict, _user: User = Depends(get_current_user)):
    """Assign the asset to the nearest matching crew. Stateless simulation."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    from backend.gridshield.risk_engine import nearest_crews, haversine_km, eta_hours_for_distance, _crew_assignment_type
    created_crew_id = (data or {}).get("crew_id")
    if created_crew_id and created_crew_id not in CREW_MAP:
        raise HTTPException(status_code=404, detail=f"Crew {created_crew_id} not found")
    if created_crew_id:
        crew = CREW_MAP[created_crew_id]
        if crew.availability != "available":
            raise HTTPException(status_code=409, detail=f"{crew.name} is not available")
        asset = ASSET_MAP[asset_id]
        distance_km = haversine_km(asset.location.lat, asset.location.lon, crew.lat or asset.location.lat, crew.lon or asset.location.lon)
        eta_hours = eta_hours_for_distance(distance_km)
    else:
        asset = ASSET_MAP[asset_id]
        nearest = nearest_crews(asset, CREWS, limit=1)
        if not nearest:
            raise HTTPException(status_code=409, detail="No available crew within reach")
        crew = nearest[0].crew
        distance_km = nearest[0].distance_km
        eta_hours = nearest[0].eta_hours

    entry = next((e for e in service.get_full_ranking() if e.asset.id == asset_id), None)
    maint = entry.maintenance if entry else None
    assignment_type = _crew_assignment_type(maint.priority_level) if maint else "Pre-position"
    reason = f"{maint.priority_level.capitalize()} priority — {maint.reason[:80]}" if maint else "Nearest available crew assigned"
    return {
        "crew": crew.model_dump(),
        "asset_id": asset_id,
        "asset_name": asset.name,
        "distance_km": distance_km,
        "eta_hours": eta_hours,
        "assignment": assignment_type,
        "reason": reason,
    }


# ─── Scenarios ────────────────────────────────────────────────────────────────

@router.post("/scenarios/simulate")
def simulate_scenario(data: ScenarioType, _user: User = Depends(get_current_user)):
    results = service.run_scenario(data.scenario, asset_id=data.asset_id)
    return {
        "scenario": data.scenario,
        "asset_id": data.asset_id,
        "results": [r.model_dump() for r in results],
        "count": len(results),
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard/kpis")
def dashboard_kpis(scenario: Optional[str] = Query(None), _user: User = Depends(get_current_user)):
    ranking = service.get_full_ranking(scenario=scenario)
    kpis = service.get_dashboard_kpis(ranking)
    return kpis.model_dump()


@router.get("/dashboard/alerts")
def dashboard_alerts(_user: User = Depends(get_current_user)):
    ranking = service.get_full_ranking()
    alerts = service.get_alerts(ranking)
    return {"alerts": [a.model_dump() for a in alerts], "count": len(alerts)}


# ─── Copilot ─────────────────────────────────────────────────────────────────

class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, max_length=64)


class CopilotResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str


@router.post("/chat", response_model=CopilotResponse)
def gridshield_chat(data: CopilotRequest, _user: User = Depends(get_current_user)):
    _cleanup_chat_sessions()

    message = _sanitize_input(data.message)
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = data.session_id or str(uuid.uuid4())[:12]
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = {"messages": [], "created_at": _time.time(), "user_id": _user.id}
    session = _chat_sessions[session_id]

    # Ensure session belongs to this user
    if session.get("user_id") != _user.id:
        raise HTTPException(status_code=403, detail="Session access denied")

    session["messages"].append({"role": "user", "content": message})

    # Get full ranking for grounded responses
    ranking = service.get_full_ranking()
    try:
        response_text = gridshield_advisor(message, ranking, history=session["messages"])
    except Exception:
        response_text = "I encountered an error processing your request. Please try rephrasing."

    session["messages"].append({"role": "assistant", "content": response_text})
    now = datetime.now().isoformat()
    return CopilotResponse(session_id=session_id, response=response_text, timestamp=now)


@router.get("/chat/sessions/{session_id}")
def get_chat_session(session_id: str, _user: User = Depends(get_current_user)):
    if session_id not in _chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _chat_sessions[session_id]
    if session.get("user_id") != _user.id:
        raise HTTPException(status_code=403, detail="Session access denied")
    return session


# ─── ML Pipeline Status ─────────────────────────────────────────────────────

@router.get("/ml/status")
def ml_pipeline_status(_user: User = Depends(get_current_user)):
    """Return ML pipeline configuration and model status."""
    import os
    from pathlib import Path

    use_real_ml = os.environ.get("GRIDSHIELD_USE_REAL_ML", "0") == "1"
    models_dir = Path(__file__).resolve().parents[2] / "models" / "bottleneck"

    status = {
        "mode": "real_ml" if use_real_ml else "mock",
        "use_real_ml": use_real_ml,
        "models_available": models_dir.exists() and any(models_dir.glob("*.json")),
        "models_directory": str(models_dir),
        "model_files": {},
    }

    if models_dir.exists():
        for f in models_dir.glob("*.json"):
            if "_metadata" not in f.name:
                status["model_files"][f.name] = {
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }

    # Load metadata if available
    meta_path = models_dir / "failure_24h_metadata.json"
    if meta_path.exists():
        import json
        with open(meta_path) as f:
            meta = json.load(f)
        status["model_version"] = meta.get("model_version")
        status["trained_at"] = meta.get("trained_at")
        status["metrics"] = meta.get("metrics", {})

    return status


# ─── Hardware Integration ──────────────────────────────────────────────────────

@router.get("/hardware/configs")
def all_hardware_configs(_user: User = Depends(get_current_user)):
    """Return hardware integration configs for all configured assets."""
    return {"configs": get_all_hardware_configs()}


@router.get("/assets/{asset_id}/hardware")
def asset_hardware_config(asset_id: str, _user: User = Depends(get_current_user)):
    """Return hardware integration config for a single asset."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    config = get_hardware_config(asset_id)
    if not config:
        config = {
            "asset_id": asset_id,
            "device_type": "custom",
            "protocol": "http",
            "connection": {},
            "registers": [],
            "poll_interval_seconds": 60,
            "enabled": False,
            "status": "configuring",
        }
    return config


@router.put("/assets/{asset_id}/hardware")
def update_asset_hardware_config(asset_id: str, config: dict, _user: User = Depends(get_current_user)):
    """Update hardware integration config for an asset."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    current = get_hardware_config(asset_id) or {}
    merged = {**current, **config, "asset_id": asset_id}
    return merged


@router.post("/assets/{asset_id}/hardware/test")
def test_asset_hardware(asset_id: str, _user: User = Depends(get_current_user)):
    """Simulate a hardware connection test for an asset."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    config = get_hardware_config(asset_id)
    if not config or not config.get("enabled"):
        return {"success": False, "message": "No hardware device configured for this asset"}
    success = config.get("status") == "connected"
    return {
        "success": success,
        "message": "Device reachable" if success else "Device unreachable — check IP/port and unit ID",
    }


@router.get("/assets/{asset_id}/hardware/readings")
def asset_hardware_readings(asset_id: str, hours: int = Query(24, ge=1, le=168), _user: User = Depends(get_current_user)):
    """Simulate live hardware readings mapped to telemetry fields."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    records = get_telemetry(asset_id, hours=hours)
    cfg = get_hardware_config(asset_id)
    readings = [
        {
            "asset_id": asset_id,
            "timestamp": r.timestamp.isoformat(),
            "readings": {
                "oil_temperature": r.oil_temperature,
                "load_percentage": r.load_percentage,
                "vibration": r.vibration,
                "current_unbalance": r.current_unbalance,
                "voltage_deviation": r.voltage_deviation,
                "partial_discharge": r.partial_discharge,
                "ambient_temperature": r.ambient_temperature,
            },
            "quality": "good" if cfg and cfg.get("enabled") else "uncertain",
        }
        for r in records
    ]
    return {"asset_id": asset_id, "readings": readings}


@router.post("/assets/{asset_id}/hardware/sync")
def sync_asset_hardware(asset_id: str, _user: User = Depends(get_current_user)):
    """Simulate pulling fresh data from a connected hardware device."""
    if asset_id not in ASSET_MAP:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    config = get_hardware_config(asset_id)
    if not config or not config.get("enabled"):
        raise HTTPException(status_code=400, detail="Asset has no enabled hardware device")
    return {"synced": 1, "errors": []}
