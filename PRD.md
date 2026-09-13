# Product Requirements Document (PRD)
## GridMind AI — Renewable Generation Forecasting & Decision Platform

**Hackathon:** HackOut'26
**Theme:** Renewable Energy Intelligence
**Problem Statement:** AI-Powered Renewable Generation Forecasting Platform

---

## 1. Problem Statement (from HackOut'26)

Solar and wind power output fluctuates constantly with weather, time of day, and season, making it difficult for grid operators and utilities to plan capacity, schedule backup power, or avoid curtailment. GridMind AI ingests weather data, historical generation records, and site-level parameters to forecast solar/wind output over the next 24–72 hours, flags periods of expected over/under-generation, and recommends grid actions (curtailment, storage dispatch, backup activation).

**Target users:** Grid operators, utility companies, renewable plant owners, energy traders — with a specific focus on **smaller renewable operators who lack expensive SCADA/forecasting infrastructure**.

---

## 2. Product Vision

> "Existing forecasting platforms (Solcast, Meteomatics) tell renewable operators what the weather may produce. GridMind AI tells smaller renewable operators what they should do about it."

GridMind AI is **not** a weather-forecasting competitor. It is an **explainable decision layer** that sits on top of a forecast — converting generation predictions into concrete, justified operating actions (charge battery, curtail, activate backup) along with their financial and CO₂ impact.

---

## 3. Goals & Non-Goals

### Goals
- Forecast solar and wind generation 24–72 hours ahead for a given site.
- Quantify forecast uncertainty (not just a point estimate).
- Flag over-generation (curtailment risk) and under-generation (backup risk) periods.
- Recommend concrete actions: battery charge/discharge, curtailment, backup activation.
- Explain *why* each recommendation was made, in plain language.
- Estimate the financial (₹) and CO₂ impact of following the recommendation.
- Support easy onboarding for small plants via CSV upload (no SCADA required).

### Non-Goals (explicitly out of scope for the hackathon build)
- Beating commercial forecast accuracy (Solcast/Meteomatics-grade infrastructure is out of reach in 48h).
- Real grid control / actual dispatch execution — this is a **decision-support** tool, not an EMS.
- Real-time SCADA integration — historical CSV + public weather API only.
- Training large foundation models from scratch (WindFM, if used, is inference-only).
- Multi-tenant production auth/billing systems.

---

## 4. User Stories

| # | As a... | I want to... | So that... |
|---|---------|---------------|------------|
| 1 | Plant owner | Upload my historical generation CSV and enter site parameters | I can get a forecast without expensive infrastructure |
| 2 | Grid operator | See a 24–72h solar/wind forecast with confidence bands | I can plan backup/capacity in advance |
| 3 | Plant operator | Get a clear recommendation (charge/curtail/backup) instead of a raw number | I can act quickly without interpreting charts myself |
| 4 | Operator | Understand *why* a recommendation was made | I can trust and justify the decision |
| 5 | Trader/operator | See the estimated ₹ and CO₂ impact of a decision | I can prioritize actions by value |
| 6 | Operator | Simulate "what if the forecast is wrong" | I can assess risk before committing to a plan |

---

## 5. Core Features

### 5.1 Forecast Engine
- Input: historical generation (CSV), site location/capacity, weather forecast (Open-Meteo).
- Output: 24h / 48h / 72h generation forecast with P10/P50/P90 uncertainty bands, for solar and/or wind.

### 5.2 Decision Engine
- Compares forecast against export limit, load/demand, and battery state of charge (SOC).
- Classifies each forecast window: **surplus / deficit / balanced**.
- Recommends: battery charge, battery discharge, curtailment, or backup activation.
- Produces a curtailment-risk rating: LOW / MEDIUM / HIGH.

### 5.3 Explainability Panel
- Every recommendation ships with a short, plain-language justification (e.g., "Solar generation expected +38%, battery at 42%, export limit reached at 15:00 → charge now, preserve 30% SOC for evening discharge").

### 5.4 Impact Estimation
- Estimated ₹ savings/avoided cost and CO₂ avoided/impact per recommendation, clearly labeled as **scenario estimates** for the hackathon build.

### 5.5 Scenario Simulator (differentiator)
- Let the user perturb inputs (e.g., "cloud cover +30%", "wind speed −20%", "battery already at 90%") and see the forecast, risk level, and recommendation update live.

### 5.6 Small-Plant Onboarding
- Simple form: plant capacity, location, battery size, export limit + CSV upload of historical generation. No SCADA/API integration required to get a first forecast.

---

## 6. Success Metrics (for the Demo)

| Metric | Target |
|--------|--------|
| Forecast accuracy vs. persistence baseline | Clearly beats naive persistence model on MAE/RMSE |
| 24h forecast error (nMAE) | Reported and compared across models (not just claimed) |
| End-to-end demo flow | Site upload → forecast → recommendation → scenario simulation, all working live |
| Explainability | Every recommendation has a human-readable justification |
| Judge Q&A readiness | Can defend accuracy numbers, methodology, and scope honestly |

---

## 7. Positioning & Judging Narrative

Do **not** pitch: *"We built a model that predicts solar/wind output."* — this is table stakes and already done well commercially.

Do pitch: *"We built the missing forecast-to-action layer, made it explainable, and made it accessible to renewable operators who don't have Solcast-grade infrastructure."*

Judging criteria alignment:
- **Innovation/technical feasibility** → hybrid physics + ML model, uncertainty-aware decisions.
- **Impact** → reduces wastage, improves grid stability, aids financial planning (directly from the PS's stated impact goals).
- **Explainability** → dedicated panel, not a black box.
- **Feasibility in 48h** → deliberately scoped against a gap analysis (see §8), not an attempt to out-build commercial platforms.

---

## 8. Risks & Open Questions (be ready for judge questions)

- **"98% accuracy" type claims are a trap.** Always report accuracy against a stated baseline (persistence) and specify the forecast horizon (24h/48h/72h) — a judge can and should probe this.
- **Data availability**: confirm the chosen Kaggle/public dataset has enough history and the right granularity before committing to it (do this in Hour 0–2, not later).
- **Attribution**: if any UI template (e.g., the "Solartec" template in the reference repo) is reused, its CC-BY-4.0 attribution requirement must be honored, or the UI should be rebuilt independently.
- **Scope creep**: uncertainty modeling, scenario simulation, and hybrid solar+wind are all "should-have," not "must-have" — see workflow.md §4 for the cut order if time runs short.
