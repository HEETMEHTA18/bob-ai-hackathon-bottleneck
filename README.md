# Bottleneck AI — IBM Bob Hackathon 2026

## Power Outage Prediction & Grid Equipment Failure Advisor

Bottleneck AI is an enterprise grid reliability platform that combines asset telemetry, weather forecasts, and incident history to predict equipment failures, rank assets by operational risk, generate impact-aware maintenance plans, and pre-position field crews before power outages occur.

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

No external API keys are required. The application works fully in demo mode using deterministic/real ML models and synthetic asset telemetry.

**Optional:** Set `GEMINI_API_KEY` in `.env` to enable the Gemini-powered AI copilot.

---

## Key Features & Operations Views

| Feature View | Description |
|--------------|-------------|
| 🛡️ **Command Center** | Live operational dashboard with fleet KPIs, risk-ranked asset ranking, and real-time failure alerts |
| 🔍 **Asset Intelligence** | Diagnostic detail view per asset — hourly telemetry (48h), 24h/72h failure probabilities, health score, grid impact, and incidents |
| 🚀 **Maintenance Planner** | Impact-aware maintenance prioritisation ranked by operational consequence, downtime, safety risks, and crew assignments |
| 🧭 **Crew Planner** | Intelligent field crew pre-positioning and dispatch plan by region and specialty |
| 🔀 **Scenario Simulator** | What-if simulation for grid stress scenarios: Severe Storm, Heatwave, Load Surge, Equipment Degradation |
| 🤖 **AI Operations Advisor** | Grounded Bottleneck AI Copilot — provides explainable, data-backed operational recommendations |
| 📊 **ML Model Management** | Real-time health metrics, drift detection, anomaly monitoring, and background model retraining pipeline |

---

## API Endpoints

All Bottleneck endpoints live under `/api/bottleneck/` (with backwards-compatible `/api/gs/` aliases):

```
GET  /api/bottleneck/assets                        # List grid assets (with filtering)
GET  /api/bottleneck/assets/{id}                   # Asset details
GET  /api/bottleneck/assets/{id}/telemetry         # Hourly telemetry records
GET  /api/bottleneck/assets/{id}/incidents         # Asset incident history
GET  /api/bottleneck/assets/{id}/maintenance       # Maintenance records
GET  /api/bottleneck/assets/{id}/intelligence      # Full asset intelligence page data
GET  /api/bottleneck/weather                       # Weather exposure metrics
GET  /api/bottleneck/predictions                   # Failure risk predictions
GET  /api/bottleneck/risk/ranking                  # Risk-ranked asset list
GET  /api/bottleneck/dashboard/kpis                # Fleet KPI metrics
GET  /api/bottleneck/dashboard/alerts              # Active grid alerts
GET  /api/bottleneck/maintenance/priorities        # Consequence-ranked maintenance actions
GET  /api/bottleneck/crew                          # Field crew status
GET  /api/bottleneck/crew/plan                     # Pre-positioning & dispatch plan
POST /api/bottleneck/scenarios/simulate            # Run what-if scenario simulation
POST /api/bottleneck/chat                          # Bottleneck AI Copilot query
GET  /api/bottleneck/model/status                  # ML model health & drift monitoring
GET  /api/bottleneck/model/metrics                 # Evaluation metrics
POST /api/bottleneck/model/retrain                 # Trigger background model retraining
GET  /health                                       # Service health check
```

---

## Architecture Overview

```
Asset Telemetry (30-asset synthetic fleet)
      +
Incident History & Asset Metadata
      +
Weather Exposure (Open-Meteo & extreme weather metrics)
      ↓
ML Engine / ML Adapter (XGBoost 24h/72h Failure Predictor + Anomaly Model)
      ↓
FailurePrediction Contract
      ↓
Grid Impact Engine (Customers at risk, critical facilities, downstream capacity)
      ↓
Composite Risk Engine (Risk Score 0-100 & Priority Levels)
      ↓
      ┌──────────────────┬────────────────────┐
      ↓                  ↓
Maintenance            Crew
Prioritization         Pre-positioning
      └──────────────────┴────────────────────┘
                          ↓
             Bottleneck AI Platform (React 18 / TypeScript)
```

---

## Environment Variables

See `.env.example`. No secrets required for basic operation.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Enables AI copilot LLM responses |
| `BOTTLENECK_USE_REAL_ML` | Optional | Set to `1` to enable real XGBoost ML models |
| `DATABASE_URL` | Optional | PostgreSQL URL (SQLite used by default) |
