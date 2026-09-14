# Solution Overview — Bottleneck AI

## IBM Bob Hackathon 2026 — Track U1

---

## What Bottleneck Does

Bottleneck is a software-first AI-powered grid reliability platform.

It takes **three inputs**:
- Asset telemetry (transformer temperature, vibration, load, voltage, partial discharge)
- Weather exposure (temperature, wind, precipitation, storm severity, heatwave index)
- Incident and maintenance history

And produces **four actionable outputs**:
1. **Failure Predictions** — which asset, 24h and 72h probabilities, health score
2. **Risk Rankings** — ordered by composite risk (probability × impact × weather × criticality × redundancy)
3. **Maintenance Plans** — prioritised actions with time windows and reasons
4. **Crew Pre-Positioning** — field crew assignments matched by specialty and region

Core product story: **PREDICT → EXPLAIN → PRIORITIZE → POSITION**

---

## Key Differentiators

### 1. Impact-Aware Risk, Not Just Failure Probability

Most failure prediction systems rank by probability alone.

Bottleneck computes a **composite risk score**:

```
Risk = f(failure_probability × grid_impact × weather_exposure × criticality × (1 − redundancy))
Normalized 0–100
```

A medium-probability failure on a transformer serving 8,000 customers outranks
a high-probability failure on a redundant, low-impact switch.

### 2. Explainability at Every Layer

The UI does not just show a number. For every high-risk asset, it shows:
- Which telemetry readings are anomalous
- What the weather contribution is
- How many customers and critical facilities are at risk
- What maintenance action is recommended and why
- Which crew is assigned and what their specialty is

### 3. Clean ML Integration Seam

The ML layer is isolated behind the `FailurePredictor` interface:

```python
class FailurePredictor:
    def predict(self, asset_id, telemetry, incidents, weather,
                age_years, criticality) -> FailurePrediction:
        ...
```

The running application uses `MockFailurePredictor` (deterministic, no model files needed).
When the real ML pipeline is ready, `RealFailurePredictor` replaces it in one file,
with zero changes to the risk engine, maintenance planner, crew planner, or frontend.

### 4. Scenario Simulation

Operators can run "what-if" scenarios:
- **Severe Storm** — weather exposure increases across affected assets
- **Heatwave** — thermal and load stress increases
- **Asset Degradation** — accelerated aging applied to a specific asset

The entire pipeline (predictions → risk → maintenance → crew) re-runs coherently with the scenario modifiers applied.

---

## System Architecture (Summary)

```
Asset Telemetry (synthetic / future IoT)
      +  Incident History
      +  Weather Exposure (Open-Meteo live or mock fallback)
            ↓
    MockFailurePredictor  ←── ML seam (swap → RealFailurePredictor)
            ↓
     FailurePrediction (stable Pydantic contract)
            ↓
  Grid Impact Engine  +  Risk Engine
            ↓
      Risk Ranking (composite score 0–100)
            ↓
   Maintenance Prioritization   +   Crew Pre-Positioning
            ↓
  Bottleneck Command Center (React / TypeScript frontend)
```

---

## Application Pages

| Page | What It Shows |
|------|--------------|
| **Command Center** | KPI bar (critical assets, customers at risk), risk ranking table, live alerts |
| **Asset Intelligence** | Full detail — telemetry charts, risk breakdown, incidents, grid impact, recommendation |
| **Maintenance Planner** | Priority-ordered maintenance actions with time windows and reasons |
| **Crew Planner** | Field crew pre-positioning assignments with specialty and region matching |
| **Scenario Simulator** | Before/after risk comparison under Severe Storm / Heatwave / Asset Degradation |
| **AI Copilot** | Grounded Grid Operations Advisor — explains risk using actual backend data |

---

## Technical Foundation

Built on **Bottleneck** (Bottleneck renewable-energy forecasting platform):

| Component | Reuse Status |
|-----------|-------------|
| FastAPI app structure, middleware, CORS | ✅ Kept |
| Open-Meteo weather provider | ✅ Adapted → asset exposure scores |
| Gemini copilot infrastructure | ✅ Adapted → Grid Operations Advisor |
| React 18 + TypeScript + Vite frontend | ✅ Adapted — Bottleneck pages added |
| Auth system, Docker, deployment configs | ✅ Kept |
| Solar/wind forecasting | ⚠️ Preserved, not primary UX |

All new Bottleneck functionality lives under `backend/bottleneck/` and `frontend/src/components/bottleneck/`.

---

## Demo Scenario

The demo is built around a single story:

1. Open Command Center → see TR-1042 ranked #1 critical
2. Open Asset Intelligence → see Risk 94/100, Health 38/100, 8,420 customers at risk
3. Read the explanation: high temperature + vibration + recent overheating incident + severe weather exposure
4. See Maintenance Planner → TR-1042 is Priority #1, action within 6 hours
5. See Crew Planner → CREW-07 (transformer specialist) pre-positioned
6. Run Severe Storm scenario → risk changes, ranking updates, crew plan updates

No external credentials required. The full demo runs offline.
