# Technical Requirements Document (TRD)
## GridMind AI — Renewable Generation Forecasting & Decision Platform

---

## 1. Architecture Overview

```
Weather API (Open-Meteo)  ──┐
                             ├──▶ Feature Engineering ──▶ Forecast Engine ──▶ Decision Engine ──▶ Explainability ──▶ API ──▶ Dashboard
Historical Generation CSV ──┘
```

**Design principle:** physics-informed baseline + ML residual correction, not a black-box model. This is more defensible and typically more accurate than a raw ML model trained directly on weather → power.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language (backend/ML) | Python |
| API framework | FastAPI |
| Solar physics model | pvlib-python |
| ML models | XGBoost, LightGBM |
| Optional advanced wind model | WindFM (pretrained, zero-shot; inference only, not trained from scratch) |
| Data handling | Pandas, NumPy |
| Weather data | Open-Meteo API (historical + forecast, no key required) |
| Database | SQLite (hackathon) → PostgreSQL (if time allows) |
| Frontend | React + Tailwind |
| Charts | Recharts or ECharts |
| Containerization | Docker / docker-compose (optional, if time allows) |

**Explicitly avoid (per feasibility analysis):** training large transformers/foundation models from scratch, Kubernetes, microservices, blockchain, complex mobile apps, reinforcement-learning grid control.

---

## 3. Repository Structure

```
gridmind-ai/
│
├── frontend/
│   ├── dashboard/
│   ├── forecast/
│   ├── scenario/
│   └── assets/
│
├── backend/
│   ├── api/                    # FastAPI routes
│   ├── forecasting/
│   │   ├── solar.py            # pvlib physics + XGBoost residual
│   │   ├── wind.py             # LightGBM/XGBoost (+ optional WindFM)
│   │   ├── features.py         # feature engineering (shared)
│   │   └── uncertainty.py      # P10/P50/P90 bands
│   ├── weather/
│   │   └── provider.py         # Open-Meteo client
│   ├── optimization/
│   │   └── dispatch.py         # decision engine (battery/curtailment/backup)
│   └── services/
│
├── models/
│   ├── solar/
│   └── wind/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
│
├── notebooks/
│   ├── solar_training.ipynb
│   └── wind_training.ipynb
│
├── docker-compose.yml
└── README.md
```

---

## 4. Data Sources

| Source | Purpose |
|--------|---------|
| Kaggle solar power generation dataset | Historical solar generation + capacity |
| Kaggle wind turbine SCADA dataset | Historical wind generation |
| Open-Meteo (historical + forecast API) | GHI/DNI/DHI, temperature, wind speed/direction, humidity |
| User-uploaded CSV (small-plant onboarding) | Site-specific historical generation for custom sites |

**Feature set (solar):** GHI, DNI, DHI, ambient temperature, humidity, wind speed, hour of day, day of year, month, solar elevation angle, lagged generation, rolling-average generation.

**Feature set (wind):** wind speed/direction forecast, temperature, pressure, hour/day/month, lagged generation, rolling-average generation, turbine/site parameters (rated capacity, hub height if available).

---

## 5. Forecasting Models

### 5.1 Solar — Hybrid Physics + ML (recommended primary model)
```
Weather forecast (GHI/DNI/DHI)
        ↓
   pvlib physics model  ──▶  baseline PV estimate
        ↓
Historical generation + weather + time features
        ↓
   XGBoost residual model  ──▶  learns site-specific error
        ↓
   Final forecast = physics baseline + ML correction
```

### 5.2 Wind — ML-first (no direct physics equivalent to pvlib)
```
NWP weather + historical generation
        ↓
   Feature engineering
        ↓
   LightGBM / XGBoost  ──▶  primary forecast
        ↓
   (optional) WindFM comparison ──▶  advanced/zero-shot benchmark
```

### 5.3 Baseline Models (required for honest evaluation)
- **Model A — Persistence:** tomorrow's generation ≈ today's generation. Mandatory baseline; all other models must be evaluated against it.
- **Model B — pvlib physics only** (solar).
- **Model C — XGBoost/LightGBM only** (no physics baseline).
- **Model D — Hybrid** (physics + ML residual) — the model actually shipped.

### 5.4 Uncertainty Quantification
- Quantile regression (LightGBM/XGBoost quantile objective) or historical residual-distribution sampling to produce P10/P50/P90 forecast bands.
- Used downstream by the decision engine to size battery reserve and set curtailment-risk level.

### 5.5 Evaluation Metrics
Report **per forecast horizon (24h / 48h / 72h)**, not as a single blended number:
- MAE, RMSE, nMAE, MAPE (where meaningful), R²
- Always alongside the persistence baseline for context

---

## 6. Decision Engine Logic

```python
# Simplified decision logic (starting point)
if generation_forecast > export_limit:
    if battery_soc < battery_capacity:
        action = "charge_battery"
    else:
        action = "curtail"
        risk = "HIGH" if surplus > threshold_high else "MEDIUM"

elif generation_forecast < demand_forecast:
    if battery_soc > min_soc:
        action = "discharge_battery"
    else:
        action = "activate_backup"
        risk = "HIGH"

else:
    action = "hold"
    risk = "LOW"
```

Inputs required: generation forecast (P50, plus P10/P90 for reserve sizing), demand/load forecast (can be a simple historical-average proxy for the hackathon), export limit, battery SOC and capacity, backup availability flag.

Outputs: recommended action, curtailment-risk rating (LOW/MEDIUM/HIGH), estimated financial (₹) and CO₂ impact (using a simple tariff/emissions-factor multiplier).

---

## 7. API Design (FastAPI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sites` | POST | Register a new site (capacity, location, battery, export limit) |
| `/sites/{id}/upload` | POST | Upload historical generation CSV |
| `/forecast/{site_id}` | GET | Return 24/48/72h forecast with P10/P50/P90 bands |
| `/risk/{site_id}` | GET | Return curtailment/deficit risk rating for the forecast window |
| `/optimize/{site_id}` | GET | Return recommended action schedule + ₹/CO₂ impact |
| `/explain/{site_id}` | GET | Return plain-language justification for current recommendation |
| `/scenario/{site_id}` | POST | Accept a perturbation (e.g., cloud_cover_delta, wind_speed_delta, battery_soc_override) and return updated forecast/risk/recommendation |

---

## 8. Explainability Implementation

Rule-based (not LLM-dependent, to keep it fast and deterministic for the demo):
- Template-driven natural-language generation from the same variables the decision engine used (forecast delta, battery SOC, export limit proximity, time-of-day price period if modeled).
- Example: `"Solar generation expected {delta}%, battery at {soc}%, export limit reached at {time} → {action}."`

---

## 9. Non-Functional Requirements

- **Response time:** forecast + decision endpoints should return in well under 2 seconds for the demo (models are lightweight; avoid heavy real-time retraining on request).
- **Reproducibility:** model training scripts in `notebooks/` should be re-runnable end-to-end on the sample dataset in `data/sample/`.
- **Explainability over black-box performance:** if a marginal accuracy gain requires sacrificing interpretability (e.g., swapping to a large opaque deep model) under time pressure, prefer the interpretable hybrid model.
- **Licensing:** if reusing UI components from the reference GitHub repo's bundled template, preserve required CC-BY-4.0 attribution, or rebuild the affected components independently.

---

## 10. Explicit Scope Boundaries (Out of Scope for 48h Build)

- Real SCADA/live telemetry integration
- Actual grid dispatch execution (this is decision-support only)
- Training WindFM or any foundation model from scratch
- Multi-tenant auth, billing, production deployment infrastructure
- Reinforcement-learning-based control policies
- Claims of beating commercial forecasting accuracy (Solcast/Meteomatics-class systems)
