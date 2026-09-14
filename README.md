# GridShield AI — IBM Bob Hackathon 2026

## Power Outage Prediction & Grid Equipment Failure Advisor

GridShield is an AI-powered grid reliability platform that predicts equipment failures,
ranks assets by operational risk, generates maintenance plans, and pre-positions field crews
before outages occur.

**Core product story:** PREDICT → EXPLAIN → PRIORITIZE → POSITION

---

## Quick Start

```bash
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Start the backend (port 8000)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 3. Build and serve the frontend
cd frontend && npm install && npm run build
# Then open http://localhost:8000 in your browser

# OR for frontend dev server:
cd frontend && npm run dev   # http://localhost:5173
```

No external API keys are required. The application works fully in demo mode
using the deterministic mock ML pipeline and synthetic asset data.

**Optional:** Set `GEMINI_API_KEY` in `.env` to enable the Gemini-powered AI copilot.

---

## Application Pages

| Page | Description |
|------|-------------|
| **Command Center** | Dashboard with KPIs, risk ranking table, and live alerts |
| **Asset Intelligence** | Full detail view for any asset — telemetry, risk, incidents, grid impact |
| **Maintenance Planner** | Impact-aware maintenance priorities with filtering |
| **Crew Planner** | Field crew pre-positioning and dispatch assignments |
| **Scenario Simulator** | What-if analysis: Severe Storm, Heatwave, Asset Degradation |
| **AI Copilot** | Grounded Grid Operations Advisor — answers from backend data only |

---

## API Endpoints

All GridShield endpoints are under `/api/gs/`:

```
GET  /api/gs/assets                        # List all 30 grid assets
GET  /api/gs/assets/{id}                   # Asset detail
GET  /api/gs/assets/{id}/telemetry         # 48h hourly telemetry
GET  /api/gs/assets/{id}/incidents         # Incident history
GET  /api/gs/assets/{id}/maintenance       # Maintenance history
GET  /api/gs/assets/{id}/intelligence      # Full intelligence page data
GET  /api/gs/weather                       # Weather exposure for all/one asset
GET  /api/gs/predictions                   # ML failure predictions
GET  /api/gs/risk/ranking                  # Risk-ranked asset list
GET  /api/gs/dashboard/kpis                # Dashboard KPI counts
GET  /api/gs/dashboard/alerts              # Active alerts
GET  /api/gs/maintenance/priorities        # Maintenance priorities (filterable)
GET  /api/gs/crew                          # All crews
GET  /api/gs/crew/plan                     # Crew pre-positioning plan
POST /api/gs/scenarios/simulate            # Run a scenario
POST /api/gs/chat                          # AI copilot query
GET  /health                               # Health check
```

---

## Architecture

```
Asset Telemetry (deterministic synthetic)
      +
Incident History
      +
Weather Exposure (Open-Meteo live or deterministic mock fallback)
      ↓
MockFailurePredictor  ←── INTEGRATION SEAM (replace with RealFailurePredictor)
      ↓
FailurePrediction contract (stable)
      ↓
Grid Impact Engine  +  Risk Engine (composite score 0-100)
      ↓
Risk Ranking
      ↓
      ┌──────────────────┬────────────────────┐
      ↓                  ↓
Maintenance            Crew
Prioritization         Pre-positioning
      └──────────────────┴────────────────────┘
                          ↓
              GridShield Command Center (React/TypeScript)
```

### ML Integration Seam

To replace the mock predictor with the real ML pipeline:

```python
# backend/gridshield/ml_adapter.py
# Change get_predictor() to return RealFailurePredictor()
# Set env: GRIDSHIELD_USE_REAL_ML=1

class RealFailurePredictor(FailurePredictor):
    def predict(self, asset_id, latest_telemetry, incidents, weather,
                asset_age_years, asset_criticality) -> FailurePrediction:
        # Call teammate's model
        ...
```

The `FailurePrediction` contract is stable. No frontend, risk engine, maintenance
planner, or crew planner changes are needed.

---

## Gridkavach Foundation Reused

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI setup | ✅ KEPT | app structure, middleware, CORS, lifespan |
| Weather provider (Open-Meteo) | ✅ ADAPTED | transformed to asset exposure scores |
| Gemini copilot infrastructure | ✅ ADAPTED | transformed to Grid Operations Advisor |
| React/TypeScript frontend | ✅ ADAPTED | GridShield pages added, old pages preserved |
| Docker/deployment config | ✅ KEPT | unchanged |
| Auth system | ✅ KEPT | legacy Gridkavach auth preserved |
| Solar/wind forecasting | ⚠️ PRESERVED | not the primary UX; accessible via old routes |

---

## Tests

```bash
# Run GridShield test suite
python3 -m pytest tests/test_gridshield.py -v

# 44 tests: risk engine, mock ML, maintenance, crew, all API endpoints
```

---

## Environment Variables

See `.env.example`. No secrets required for demo mode.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Enables AI copilot LLM responses |
| `GRIDSHIELD_USE_REAL_ML` | Optional | Set to `1` to enable real ML adapter |
| `DATABASE_URL` | Optional | PostgreSQL URL (SQLite used by default) |

---

## IBM Bob Engineering

IBM Bob (IBM Codex AI) was used as the primary AI coding and development agent
for the GridShield migration. Sessions are recorded in `docs/BOB_ENGINEERING_LOG.md`.
