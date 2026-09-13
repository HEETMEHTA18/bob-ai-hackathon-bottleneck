# GridMind AI — Workflow

**HackOut'26 | Theme: Renewable Energy Intelligence**
**Problem Statement:** AI-Powered Renewable Generation Forecasting Platform
**Duration:** 48 hours

---

## 1. System Workflow (End-to-End Pipeline)

```
                         ┌──────────────────────┐
                         │   Weather Forecast    │
                         │   (Open-Meteo API)    │
                         └──────────┬────────────┘
                                    │
                                    ▼
┌─────────────────────┐    ┌───────────────────┐
│ Historical Generation│───▶│ Feature Engineering│
│ (CSV / dataset)      │    │                    │
└─────────────────────┘    └─────────┬──────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │     FORECAST ENGINE     │
                          │                         │
                          │ Solar: pvlib (physics)  │
                          │        + XGBoost         │
                          │        (residual)         │
                          │                         │
                          │ Wind: LightGBM/XGBoost   │
                          │       (+ optional WindFM)│
                          └───────────┬─────────────┘
                                      │
                                      ▼
                         24h / 48h / 72h Forecast
                         (P10 / P50 / P90 bands)
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   DECISION ENGINE      │
                          │                         │
                          │ Surplus / deficit calc  │
                          │ Battery SOC logic       │
                          │ Curtailment risk         │
                          │ Backup activation        │
                          └───────────┬─────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │  EXPLAINABILITY LAYER  │
                          │ Why this recommendation │
                          │ ₹ / CO₂ impact estimate │
                          └───────────┬─────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   REACT DASHBOARD      │
                          │ Forecast chart          │
                          │ Risk banner              │
                          │ Recommended action       │
                          │ Scenario simulator        │
                          └───────────────────────┘
```

---

## 2. Team Workflow (48-Hour Execution Plan)

### Phase 0 — Setup (Hours 0–2)
- Fork/clone reference repo (`mehakagg1313/SOLAR-AND-WIND-ENERGY-PREDICTION`) for UI scaffolding ideas only.
- Set up repo structure (see TRD for folder layout), FastAPI skeleton, React skeleton.
- Confirm data sources: Kaggle solar/wind generation dataset + Open-Meteo historical/forecast API.
- Assign tracks: (A) Data + Solar model, (B) Wind model, (C) Decision engine + backend API, (D) Frontend dashboard.

### Phase 1 — Data & Baseline Models (Hours 2–14)
- Clean and align historical generation data with weather features (GHI, DNI, DHI, temperature, wind speed, humidity, hour/day/month, solar elevation).
- Build **persistence baseline** (Model A) for both solar and wind — this is the accuracy floor everything else must beat.
- Build **pvlib physics baseline** for solar (Model B).
- Train **XGBoost/LightGBM residual correction** on top of the physics baseline (Model D — hybrid).
- Train **LightGBM/XGBoost** for wind directly (no physics equivalent to pvlib for wind).
- Evaluate all models: MAE, RMSE, nMAE, MAPE, R² — for 24h, 48h, and 72h horizons separately.

### Phase 2 — Uncertainty & Decision Layer (Hours 14–26)
- Add quantile regression or residual-distribution based P10/P50/P90 bands to the forecast.
- Build the rule-based decision engine:
  - `generation > export_limit` → curtailment risk / charge battery
  - `generation < demand` → discharge battery / flag backup need
  - battery SOC constraints feed back into the decision
- Add curtailment-risk classifier (LOW/MEDIUM/HIGH) based on forecast vs. export limit vs. battery state.
- Add financial (₹) and CO₂ impact estimate calculations.

### Phase 3 — API & Explainability (Hours 20–30, overlaps Phase 2)
- Build FastAPI endpoints: `/forecast`, `/risk`, `/optimize`, `/explain`.
- Build the explainability layer: convert model/decision outputs into a short natural-language "why" statement (rule-based, not necessarily LLM-generated, to keep it deterministic and fast).

### Phase 4 — Frontend Dashboard (Hours 20–36, parallel track)
- Site/plant selector + CSV upload for "bring your own data" small-plant onboarding.
- Forecast chart (predicted vs. actual, with uncertainty band).
- Risk banner (curtailment / deficit / backup flags).
- Recommendation panel (battery action, curtailment estimate, backup need, ₹/CO₂ impact).
- Scenario simulator button ("what if cloud cover +30%", "what if wind speed -20%", "what if battery is 90% full").

### Phase 5 — Integration & Testing (Hours 36–42)
- Connect frontend to live backend endpoints.
- Run through full demo flow end-to-end multiple times.
- Fix edge cases (missing data, battery-full state, zero-generation periods).

### Phase 6 — Pitch Prep (Hours 42–48)
- Prepare architecture diagram slide (this workflow, simplified).
- Prepare impact slide (₹/CO₂ savings framing, not just accuracy numbers).
- Rehearse the "what should I do?" and "what if forecast is wrong?" live demo moments — these are the differentiators vs. a plain forecasting dashboard.
- Prepare answers for likely judge questions (see PRD §8 — Risks & Open Questions).

---

## 3. Demo Flow (What Judges See)

1. Select or upload a plant (site config + historical CSV).
2. System auto-generates a 24–72h solar/wind forecast with confidence bands.
3. Dashboard shows surplus/deficit and a clear recommended action (charge/discharge/curtail/backup) with a plain-language "why."
4. Click **"Optimize Next 24 Hours"** → full schedule of recommended actions across the horizon, with estimated ₹ and CO₂ impact.
5. Click **"Simulate forecast error"** (e.g., cloud cover +30%, wind -20%) → recommendation and risk level update live.
6. Close on the positioning line: *"We don't compete with industrial forecasting platforms on raw weather-model accuracy — we make forecasts operationally useful by turning them into explainable battery, curtailment, and backup decisions."*

---

## 4. Build Priorities (If Time Runs Short)

**Must-have (core PS requirement):**
- Solar + wind forecast for 24–72h
- Surplus/deficit flagging
- Basic recommendation (curtailment / storage / backup)

**Should-have (differentiator, do next):**
- Uncertainty bands (P10/P50/P90)
- Explainability panel
- ₹/CO₂ impact estimate

**Nice-to-have (cut first if behind schedule):**
- Scenario simulator
- Hybrid solar+wind combined optimization
- WindFM comparison model
- CSV-based small-plant onboarding flow
