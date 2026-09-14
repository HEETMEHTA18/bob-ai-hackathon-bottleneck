# GridShield AI — Power Outage Prediction & Grid Equipment Failure Advisor

> IBM Bob Hackathon 2026 · Track U1

GridShield is an AI-powered grid reliability platform that combines asset telemetry, weather forecasts, and incident history to predict equipment failures, rank assets by operational risk, generate maintenance plans, and pre-position field crews before outages occur.

**Core story:** PREDICT → EXPLAIN → PRIORITIZE → POSITION

---

## Team

| Field | Value |
|-------|-------|
| Team Name | bottleneck |
| Track | U1 — Power Outage Prediction & Grid Equipment Failure Advisor |
| Team Lead | Heet Mehta — heetmehta18125@gmail.com |

---

## Problem Statement

Power utilities lose billions annually to preventable equipment failures. Reactive maintenance wastes resources on low-risk assets while critical ones degrade undetected. Existing tools focus on failure probability alone, ignoring the downstream grid impact — how many customers lose power, which critical facilities go dark, and what the cascading effects are. Without impact-aware prioritization, crews are dispatched reactively rather than pre-positioned proactively.

---

## Solution

GridShield combines asset telemetry, weather exposure, and incident history into a composite risk score that factors in failure probability, grid impact, weather severity, asset criticality, and redundancy. The platform then translates this risk into actionable outputs: prioritized maintenance plans, crew pre-positioning by specialty and region, and a grounded AI advisor that explains every recommendation with real data.

---

## Key Features

- **Impact-aware risk scoring** — Failure probability × grid impact × weather × criticality × redundancy (0–100 scale)
- **30-asset synthetic fleet** — Realistic degradation profiles with telemetry, incidents, and maintenance history
- **Deterministic mock ML** — Clean swap seam: `MockFailurePredictor` → `RealFailurePredictor`
- **Scenario simulator** — Severe Storm, Heatwave, Asset Degradation what-if analysis
- **Crew pre-positioning** — Dispatch by specialty and region based on risk rankings
- **Grounded AI copilot** — All answers backed by backend data; never invents sensor values or statistics
- **16 REST API endpoints** — Full CRUD under `/api/gs/`

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Languages | Python 3.11, TypeScript |
| Frameworks | FastAPI, React 18, Vite |
| IBM Technologies | IBM Bob (primary AI coding agent) |
| AI/ML | Google Gemini 1.5 Flash (optional copilot), Deterministic Mock ML (demo mode) |
| Databases | SQLite (dev) / PostgreSQL (prod) |
| Infrastructure | Docker, GitHub Actions CI |
| Weather | Open-Meteo API |

---

## Repository Structure

```
├── backend/                 # FastAPI backend
│   ├── gridshield/          # GridShield modules (contracts, risk, ML, copilot)
│   ├── routes/              # API route handlers
│   └── main.py              # App entry point
├── frontend/                # React/TypeScript frontend
│   └── src/
│       └── components/
│           └── gridshield/  # GridShield UI components
├── src/                     # Alternate source layout
├── docs/                    # Documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                    # Demo artifacts
│   ├── screenshots/         # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/            # Slide deck
├── models/                  # Trained ML models
├── scripts/                 # Utility scripts
├── submission.yaml          # Structured submission metadata
├── Dockerfile               # Container build
├── docker-compose.yml       # Local dev orchestration
└── requirements.txt         # Python dependencies
```

---

## How to Run

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |
| Git | any |

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/HEETMEHTA18/Gridkavach.git
cd Gridkavach

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Start the backend (port 8000)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 4. Install frontend dependencies and start dev server
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

No external API keys required. The app works fully in demo mode.

### Docker

```bash
docker-compose up --build
# Backend: http://localhost:8000
```

---

## Application Pages

| Page | Description |
|------|-------------|
| **Command Center** | Dashboard with KPIs, risk ranking table, and live alerts |
| **Asset Intelligence** | Full detail view — telemetry, risk breakdown, incidents, grid impact |
| **Maintenance Planner** | Impact-aware maintenance priorities with filtering |
| **Crew Planner** | Field crew pre-positioning and dispatch assignments |
| **Scenario Simulator** | What-if analysis: Severe Storm, Heatwave, Asset Degradation |
| **AI Advisor** | Grounded Grid Operations Intelligence — answers from backend data only |

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
```

The `FailurePrediction` contract is stable. No frontend, risk engine, maintenance planner, or crew planner changes are needed.

---

## Demo

| Artifact | Link |
|----------|------|
| Demo Video | See demo/demo-video-link.txt |
| Live Demo | Local — see setup guide above |
| Screenshots | See demo/screenshots/ |
| Presentation | See presentation/ |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Enables AI copilot LLM responses |
| `GRIDSHIELD_USE_REAL_ML` | Optional | Set to `1` to enable real ML adapter |
| `DATABASE_URL` | Optional | PostgreSQL URL (SQLite used by default) |

---

## Known Limitations

- Authentication is functional but basic — production-ready auth would use OAuth2/OIDC
- The ML predictor is a deterministic mock — real models require training data and GPU
- Crew locations are synthetic — real deployment would integrate with GIS/asset management systems
- The 30-asset fleet is synthetic — real telemetry would come from SCADA/IoT

---

## What We're Most Proud Of

The **ML Integration Seam** — the `FailurePrediction` contract allows swapping `MockFailurePredictor` for a real ML model without changing any other component (frontend, risk engine, maintenance planner, or crew planner). This clean separation means the entire platform is production-ready the moment a real model is plugged in.

---

## IBM Bob Usage

IBM Bob (IBM Codex AI) was used as the primary AI coding and development agent throughout the entire GridShield development. Sessions are documented in `docs/BOB_ENGINEERING_LOG.md`.

---

## License

Internal — IBM Bob Hackathon 2026
