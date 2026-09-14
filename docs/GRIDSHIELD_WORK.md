# GridShield — IBM Bob Master Work Specification

## Project
- Project name: GridShield
- Starting codebase: Gridkavach
- Hackathon track: IBM Bob AI Hackathon 2026 — U1
- U1: Power Outage Prediction & Grid Equipment Failure Advisor

## Mission

Transform the existing Gridkavach renewable-energy forecasting application into a complete, runnable GridShield application while preserving useful engineering infrastructure.

Target workflow:

Asset Telemetry + Weather + Incident History
→ Failure Prediction
→ Explain
→ Impact-Aware Risk Ranking
→ Maintenance Plan
→ Crew Pre-Positioning

The real ML pipeline is being developed separately by another teammate.

**NON-NEGOTIABLE: use a deterministic mock ML pipeline for this work. Do not implement or replace the teammate's real ML model. Build a clean adapter/interface so the real model can later replace the mock without rewriting the backend or frontend.**

---

# 1. Rules

1. Do not start from a blank project.
2. Audit Gridkavach before making destructive changes.
3. Reuse useful FastAPI, React/TypeScript, weather, charts, maps, validation, testing, Docker and model-infrastructure patterns.
4. Do not blindly rename strings; transform the domain.
5. Frontend must use APIs, not direct DB/ML access.
6. Keep the application runnable throughout the migration.
7. No secrets/API keys in source control.
8. The MVP must work without an external LLM API key.
9. Renewable metrics must not be presented as outage metrics.
10. Run tests/build/lint after relevant changes.

---

# 2. Phase 1 — Repository Audit

Before major edits:

- inspect the full repository tree
- read README and package manifests
- inspect backend entry points and routes
- inspect frontend routes/pages/components
- inspect DB/configuration
- inspect forecasting/model/optimization code
- inspect tests
- inspect Docker/config files
- inspect model/metric files

Create a migration map with four categories:

### KEEP
Reusable infrastructure.

### MODIFY
Infrastructure that can be adapted.

### REMOVE/DEPRECATE
Renewable-only functionality that should no longer be part of the primary GridShield UX.

### CREATE
New GridShield functionality.

Do not delete code until dependencies are understood.

---

# 3. Domain Transformation

Replace:

Site → Weather → Renewable Forecast → Renewable Risk → Battery Optimization → Energy Dashboard

with:

Grid Asset → Asset Telemetry → Weather Exposure → Incident History → Failure Prediction → Grid Impact → Risk Score → Maintenance Prioritization → Crew Pre-Positioning → Grid Operations Command Center

GridShield is not a renewable-energy forecasting product.

---

# 4. Core Data Entities

Create/adapt contracts for:

- Asset
- Telemetry
- WeatherExposure
- Incident
- MaintenanceRecord
- FailurePrediction
- GridImpact
- RiskAssessment
- MaintenanceRecommendation
- Crew
- CrewAssignment
- ScenarioResult

Example Asset:

```json
{
  "id": "TR-1042",
  "name": "North Feeder Transformer 1042",
  "asset_type": "transformer",
  "substation_id": "SUB-NORTH-01",
  "location": {"lat": 23.0225, "lon": 72.5714},
  "criticality": 0.92,
  "capacity_mva": 25,
  "age_years": 17,
  "redundancy_level": 0.30,
  "status": "degraded"
}
```

Supported asset types should include at least:
- transformer
- feeder
- breaker
- recloser
- switch
- capacitor_bank

---

# 5. Mock Telemetry/Data

Create deterministic synthetic data for a convincing demo.

Minimum:
- 20–50 assets
- multiple asset types
- telemetry history
- incident history
- maintenance history
- weather
- grid impact metadata
- crews

Telemetry should include appropriate fields such as:
- oil temperature
- load percentage
- vibration
- current unbalance
- voltage deviation
- partial discharge/anomaly indicators

Include different risk profiles:
1. Critical
2. High risk
3. Medium risk
4. Healthy
5. Weather-sensitive
6. Degrading
7. High-impact but moderate-failure-probability

Create a fixed demo asset such as TR-1042 that becomes #1 critical.

---

# 6. Mock ML Adapter

Create a dedicated ML abstraction following existing repository conventions.

Conceptually:

```python
class FailurePredictor:
    def predict(self, asset_context) -> FailurePrediction:
        ...
```

Implement:

```text
MockFailurePredictor
```

It should return structured data like:

```json
{
  "asset_id": "TR-1042",
  "failure_probability_24h": 0.87,
  "failure_probability_72h": 0.93,
  "health_score": 38,
  "anomaly_score": 0.82,
  "confidence": 0.89,
  "top_factors": [
    "High transformer temperature",
    "Increasing vibration",
    "High recent load",
    "Recent overheating incident"
  ]
}
```

The mock predictor MUST be deterministic. Do not generate different predictions on every request.

The future integration must be:

CURRENT:
Backend → MockFailurePredictor → Risk Engine → Frontend

FUTURE:
Backend → RealFailurePredictor → Risk Engine → Frontend

Do not couple frontend code to XGBoost/model files.

---

# 7. Risk Engine

Create a separate deterministic, explainable risk service.

Risk must not equal failure probability.

Conceptual formulation:

Risk =
Failure Probability
× Grid Impact
× Weather Exposure
× Asset Criticality
× Lack of Redundancy

Normalize to 0–100.

Example:

```json
{
  "asset_id": "TR-1042",
  "risk_score": 94,
  "risk_level": "critical",
  "failure_probability_24h": 0.87,
  "grid_impact_score": 0.95,
  "weather_exposure_score": 0.90,
  "criticality_score": 0.92,
  "redundancy_score": 0.70
}
```

The UI must explain the score.

---

# 8. Grid Impact Engine

Estimate operational impact using:
- customers affected
- critical facilities served
- feeder/substation importance
- asset capacity
- redundancy
- downstream assets
- geographic importance

Example:

```json
{
  "asset_id": "TR-1042",
  "customers_at_risk": 8420,
  "critical_facilities_at_risk": 7,
  "capacity_mva": 25,
  "grid_impact_score": 0.95
}
```

This is a core differentiator.

---

# 9. Weather Adapter

Reuse Gridkavach's weather adapter pattern where useful.

Transform weather usage into asset exposure.

Use:
- temperature
- precipitation
- wind speed
- storm severity
- humidity
- heatwave indicator
- severe-weather indicator

Weather must influence risk.

If an external weather API is unavailable, use deterministic/mock fallback data.

---

# 10. Asset Health Profile

Asset detail pages must show:

- Asset ID/type/location
- Health score
- 24h and 72h failure probability
- Risk score/level
- Anomaly score
- Telemetry trends
- Weather exposure
- Recent incidents
- Last maintenance
- Customers at risk
- Critical facilities at risk
- Top risk factors
- Recommended action

Example narrative:

TR-1042
Health 38/100
Risk 94/100 — CRITICAL
24h failure probability 87%
72h failure probability 93%
Customers at risk 8,420
Critical facilities 7

Why risky:
- high temperature
- increasing vibration
- high loading
- recent overheating
- severe weather exposure

---

# 11. Maintenance Prioritization

Create a maintenance recommendation service.

Example:

```json
{
  "asset_id": "TR-1042",
  "priority": 1,
  "priority_level": "critical",
  "recommended_action": "Immediate thermal and vibration inspection",
  "recommended_window": "Within 6 hours",
  "reason": "High failure probability combined with high grid impact and severe weather exposure"
}
```

Support:
- Immediate
- High
- Medium
- Monitor

Rank assets operationally, not merely by failure probability.

---

# 12. Crew Pre-Positioning

Create deterministic mock crew data and assignment logic.

Example crew:

```json
{
  "crew_id": "CREW-07",
  "specialty": "transformer",
  "location": "North Division",
  "availability": "available",
  "capacity": 2
}
```

Example assignment:

```json
{
  "crew_id": "CREW-07",
  "asset_id": "TR-1042",
  "assignment": "Pre-position",
  "priority": 1,
  "reason": "Critical transformer risk with high customer impact"
}
```

Do not build a complex routing optimizer for MVP.

---

# 13. Required APIs

Adapt the existing FastAPI architecture.

Create/adapt APIs equivalent to:

GET /api/assets
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/telemetry
GET /api/assets/{asset_id}/incidents
GET /api/assets/{asset_id}/maintenance

GET /api/weather
GET /api/predictions
GET /api/risk
GET /api/risk/ranking

GET /api/maintenance/priorities
GET /api/crew
GET /api/crew/plan

POST /api/scenarios/simulate

Use existing project conventions where possible. Do not create duplicate API frameworks.

---

# 14. Frontend — GridShield Command Center

Transform the renewable dashboard.

Main dashboard:

### KPIs
- Critical Assets
- High-Risk Assets
- Customers at Risk
- Critical Facilities at Risk
- Crews Pre-Positioned

### Risk Ranking

Columns:
Rank | Asset | Type | Risk | Failure Probability | Impact | Action

### Risk Map
Show grid assets geographically with risk state.

### Weather
Show current conditions, forecast/exposure and severe-weather indicators.

### Alerts
Examples:
- Critical transformer failure risk
- Severe storm exposure
- Rising thermal anomaly
- Maintenance overdue

---

# 15. Asset Intelligence Page

Build a detailed asset page with:
- health score
- risk score
- failure probability
- telemetry trends
- weather exposure
- incidents
- maintenance
- grid impact
- explanation
- recommendation
- assigned crew

---

# 16. Maintenance Planner

Show:
- ranked assets
- recommended action
- time window
- reason
- assigned crew
- estimated operational impact

Filtering:
- risk
- asset type
- region
- action
- time window

---

# 17. Crew Planner

Show:
- crew
- specialty
- region
- availability
- assigned asset
- assignment reason
- priority
- status

---

# 18. Scenario Simulator

Implement at least:

### Severe Storm
Increase weather exposure and failure risk.

### Heatwave
Increase temperature/load/thermal stress.

### Asset Degradation
Increase vibration/anomaly/failure probability.

Show before/after changes.

Example:

BEFORE:
TR-1042 Risk 61

AFTER STORM:
TR-1042 Risk 94
Priority #1
Crew CREW-07

The scenario must update risk/ranking/maintenance/crew outputs coherently.

---

# 19. Copilot

If the existing Gridkavach Gemini/copilot infrastructure is reusable, transform it into a Grid Operations Advisor.

It must be grounded in backend structured data.

Example:

User: Why is TR-1042 critical?

Expected answer should use actual backend values and explain:
- failure probability
- health
- customers/critical facilities
- telemetry factors
- weather
- recommended action

The copilot must never invent statistics.

If no LLM API key exists, the application must still work with a deterministic fallback advisor.

---

# 20. Renewable Features to Remove from Primary UX

Do not leave these as central GridShield features:
- solar generation forecasting
- wind generation forecasting
- PV forecasting
- pvlib solar prediction
- IEC wind curve presentation
- battery dispatch
- renewable curtailment
- renewable financial optimization
- renewable-site terminology

Reusable implementation may remain temporarily if required during migration, but it must not define the final product.

---

# 21. Testing

Create/update tests for:

### Risk
- high probability + high impact → high risk
- low probability + low impact → low risk
- impact changes ranking
- weather changes risk

### Mock ML
- deterministic
- probability range valid
- health range valid
- factors returned

### Maintenance
- critical assets get urgent priority
- recommendations include reasons

### Crew
- suitable available crews assigned
- unavailable crews not assigned

### API
- assets
- telemetry
- predictions
- risk/ranking
- maintenance
- crew
- scenarios

### Frontend
- dashboard loads
- asset page loads
- ranking renders
- scenario works
- error/loading/empty states work

---

# 22. Error Handling

Gracefully handle:
- weather API failure
- ML failure
- malformed telemetry
- empty data
- copilot failure

Do not expose stack traces to users.

---

# 23. Documentation

Update existing documentation instead of creating duplicates.

Maintain:
- README
- CONTEXT.md
- PRD.md
- TRD.md
- MODEL.md
- DATA.md
- ARCHITECTURE.md
- INTEGRATION.md
- ROADMAP.md
- BOB_ENGINEERING_LOG.md

Document:
- Gridkavach components reused
- components transformed
- components deprecated
- new GridShield components
- mock ML boundary
- future real ML integration
- API contracts
- demo scenario

---

# 24. IBM Bob Engineering Log

IBM Bob is the AI coding/development agent for this project.

Maintain:

BOB_ENGINEERING_LOG.md

Record meaningful sessions:
- audit
- architecture migration
- contracts
- mock ML
- risk engine
- backend
- frontend
- maintenance
- crew
- scenarios
- testing
- documentation
- integration readiness

Do not claim every line was automatically generated.

Use accurate wording:
“IBM Bob was used as the primary/sole AI coding and development agent throughout the implementation.”

---

# 25. Environment

Update .env.example.

Never commit:
- API keys
- credentials
- tokens
- secrets

Demo mode should work without external credentials wherever practical.

---

# 26. Implementation Order

Follow this order exactly:

1. Repository audit
2. Migration map
3. Shared contracts
4. Mock synthetic data
5. Mock ML adapter
6. Grid impact engine
7. Risk engine
8. Backend APIs
9. GridShield Command Center
10. Asset Intelligence
11. Maintenance Planner
12. Crew Planner
13. Scenario Simulator
14. Copilot/fallback
15. Tests
16. Documentation
17. Final end-to-end validation

---

# 27. Final Demo Flow

The final application must support this story:

Open dashboard
→ see critical assets
→ open TR-1042
→ understand why it is risky
→ inspect telemetry/weather/grid impact
→ see recommended maintenance
→ see assigned crew
→ run Severe Storm scenario
→ risk changes
→ ranking changes
→ maintenance plan changes
→ crew plan changes

Central product story:

# PREDICT → EXPLAIN → PRIORITIZE → POSITION

Predict which asset may fail.
Explain why.
Prioritize based on probability AND grid impact.
Position crews before an outage.

---

# 28. Definition of Done

### Application
- GridShield branding
- Grid operations domain
- runnable locally
- command center
- asset detail
- risk ranking
- maintenance planner
- crew planner
- scenario simulator

### Backend
- asset API
- telemetry API
- weather API
- prediction API
- risk API
- maintenance API
- crew API
- scenario API

### ML boundary
- deterministic mock predictor
- stable contract
- documented replacement path
- no frontend dependency on model internals

### Product logic
- impact-aware risk
- ranked assets
- maintenance priorities
- crew pre-positioning
- weather influence
- scenario effects

### Quality
- tests pass
- frontend build passes
- backend starts
- no secrets
- no broken primary routes
- renewable forecasting is no longer the primary UX

---

# 29. Final Architecture

Conceptually:

Asset Telemetry
      +
Incident History
      +
Weather Exposure
      ↓
Feature Builder
      ↓
Mock ML Adapter
      ↓
Failure Prediction
      ↓
Grid Impact + Risk Engine
      ↓
Risk Ranking
      ↓
 ┌───────────────┬────────────────┐
 ↓               ↓
Maintenance      Crew
Prioritization   Pre-positioning
 └───────────────┴────────────────┘
                  ↓
          GridShield Command Center

The real teammate ML pipeline must later replace only the mock prediction implementation as far as practical.

---

# 30. Final Response Required From Bob

After completing the work, report:

1. Files changed
2. Files created
3. Files deprecated
4. APIs created/changed
5. Mock ML interface
6. Exact steps to replace mock ML with the real teammate pipeline
7. Tests/build/lint commands executed and results
8. How to run GridShield locally
9. Remaining integration work
10. Any known limitations

Leave the repository in a runnable state.
