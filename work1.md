# Module 1: Backend, ML Models & Data Pipeline

**Owner:** Agent 1  
**Duration:** 48 hours (HackOut'26)

---

## Scope

All server-side logic, machine learning models, data processing, API endpoints, and database operations.

---

## Tasks Breakdown

### Phase 0 — Setup (Hours 0–2)

| # | Task | Details | Output |
|---|------|---------|--------|
| 1 | Initialize backend project | Create `backend/` directory structure as per TRD §3 | Folder skeleton |
| 2 | Set up Python environment | Create `requirements.txt` with: fastapi, uvicorn, pandas, numpy, xgboost, lightgbm, pvlib, scikit-learn, sqlite3 | Working venv |
| 3 | Create FastAPI skeleton | `backend/main.py` with CORS middleware, basic health endpoint `/health` | Running server |
| 4 | Verify data sources | Confirm Open-Meteo API works (no key needed), download sample Kaggle solar/wind datasets | `data/raw/` populated |

---

### Phase 1 — Data Pipeline & Feature Engineering (Hours 2–8)

| # | Task | Details | Output |
|---|------|---------|--------|
| 5 | Build Open-Meteo client | `backend/weather/provider.py` — fetch historical + forecast data (GHI, DNI, DHI, temp, wind speed, humidity, pressure) for given lat/lon/date range | Reusable API client |
| 6 | Build CSV loader | `backend/data/loader.py` — load user-uploaded or sample CSV, validate columns, parse timestamps | Normalized DataFrame |
| 7 | Feature engineering module | `backend/forecasting/features.py` — compute: hour, day_of_year, month, solar_elevation, lagged_generation (1h, 24h), rolling_avg (24h, 72h), GHI/DNI/DHI ratios | Feature matrix |
| 8 | Data cleaning pipeline | Handle missing values, resample to hourly, align weather + generation timestamps | Clean dataset |

---

### Phase 2 — Solar Forecasting Models (Hours 6–14)

| # | Task | Details | Output |
|---|------|---------|--------|
| 9 | Persistence baseline | `backend/forecasting/solar.py` — Model A: tomorrow = today (naive). Required as accuracy floor. | Baseline MAE/RMSE |
| 10 | pvlib physics baseline | Model B: use pvlib to estimate clear-sky + actual irradiance PV output. Input: GHI/DNI/DHI + site params (tilt, azimuth, capacity). | Physics estimate |
| 11 | XGBoost residual model | Model D (hybrid): train XGBoost on residuals (actual - physics). Features: time, weather, lagged residuals. | Trained model |
| 12 | Hybrid forecast pipeline | Final = pvlib output + XGBoost correction. Save model artifacts to `models/solar/`. | Inference pipeline |
| 13 | Evaluation harness | `backend/forecasting/evaluate.py` — compute MAE, RMSE, nMAE, MAPE, R² for 24h/48h/72h horizons. Compare all models. | Metrics report |

---

### Phase 3 — Wind Forecasting Models (Hours 8–14)

| # | Task | Details | Output |
|---|------|---------|--------|
| 14 | Wind feature engineering | Extend `features.py` for wind: wind speed/direction, pressure, hub height adjustment, turbine power curve params | Wind features |
| 15 | LightGBM/XGBoost wind model | `backend/forecasting/wind.py` — train directly on weather → generation (no physics baseline for wind). | Trained model |
| 16 | (Optional) WindFM inference | If time permits, run WindFM zero-shot as comparison benchmark | Benchmark metrics |

---

### Phase 4 — Uncertainty Quantification (Hours 12–18)

| # | Task | Details | Output |
|---|------|---------|--------|
| 17 | Quantile regression models | `backend/forecasting/uncertainty.py` — train LightGBM with quantile objective (α=0.1, 0.5, 0.9) for P10/P50/P90 | Quantile models |
| 18 | Residual distribution fallback | If quantile models underfit, use historical residual distribution to compute P10/P90 bands | Uncertainty bands |
| 19 | Band calibration | Validate P10/P90 coverage (should contain ~80% of actuals) | Calibrated bands |

---

### Phase 5 — Decision Engine (Hours 14–24)

| # | Task | Details | Output |
|---|------|---------|--------|
| 20 | Core decision logic | `backend/optimization/dispatch.py` — implement TRD §6 logic: surplus/deficit classification, battery charge/discharge, curtailment, backup | Decision engine |
| 21 | Curtailment risk classifier | Classify each hour: LOW / MEDIUM / HIGH based on surplus magnitude + export limit + battery SOC | Risk ratings |
| 22 | Financial impact estimator | ₹ savings per recommendation: (energy_mismatch_kWh × tariff_rate). Use configurable tariff (default ₹5/kWh). | ₹ estimates |
| 23 | CO₂ impact estimator | CO₂ avoided/saved: (energy_kWh × grid_emission_factor). Use configurable factor (default 0.82 tCO₂/MWh for India). | CO₂ estimates |
| 24 | Optimization schedule | "Optimize Next 24 Hours" — full hourly schedule of recommended actions with cumulative ₹ and CO₂ impact | Schedule output |

---

### Phase 6 — Explainability Layer (Hours 20–26)

| # | Task | Details | Output |
|---|------|---------|--------|
| 25 | Template-based NLG | `backend/services/explain.py` — rule-based natural language generation from decision variables | Why statements |
| 26 | Explanation templates | Cover all scenarios: surplus→charge, surplus→curtail, deficit→discharge, deficit→backup, balanced→hold | Template library |
| 27 | Hook into decision engine | Every recommendation output includes a `why` field with plain-language justification | Integrated explanations |

---

### Phase 7 — API Endpoints (Hours 22–30)

| # | Task | Details | Output |
|---|------|---------|--------|
| 28 | `POST /sites` | Register site: capacity, location, battery_size, export_limit. Store in SQLite. | Site creation |
| 29 | `POST /sites/{id}/upload` | Upload CSV, trigger data cleaning + feature engineering, store processed data. | CSV ingestion |
| 30 | `GET /forecast/{site_id}` | Return 24/48/72h forecast with P10/P50/P90 bands for solar and wind. | Forecast endpoint |
| 31 | `GET /risk/{site_id}` | Return hourly curtailment/deficit risk ratings. | Risk endpoint |
| 32 | `GET /optimize/{site_id}` | Return recommended action schedule + ₹/CO₂ impact. | Optimize endpoint |
| 33 | `GET /explain/{site_id}` | Return plain-language justification for current recommendation. | Explain endpoint |
| 34 | `POST /scenario/{site_id}` | Accept perturbations (cloud_cover_delta, wind_speed_delta, battery_soc_override), re-run forecast + decision, return updated results. | Scenario endpoint |

---

### Phase 8 — Database & Services (Hours 24–30)

| # | Task | Details | Output |
|---|------|---------|--------|
| 35 | SQLite schema | `backend/models/` — tables: sites, forecasts, decisions, explanations | DB schema |
| 36 | Data access layer | CRUD operations for sites, forecasts, decisions | Service layer |
| 37 | Caching | Cache Open-Meteo responses (same location+date = same data) to avoid re-fetching | In-memory or SQLite cache |

---

### Phase 9 — Integration & Testing (Hours 30–42)

| # | Task | Details | Output |
|---|------|---------|--------|
| 38 | End-to-end pipeline test | Upload CSV → generate forecast → get decision → get explanation → simulate scenario | Full flow works |
| 39 | Edge case handling | Zero-generation periods, battery-full, battery-empty, missing weather data, single-day history | Robust error handling |
| 40 | Performance check | Forecast + decision endpoints return in < 2 seconds | Meets latency target |
| 41 | Model reproducibility | Training notebooks runnable end-to-end on sample data in `data/sample/` | Reproducible pipeline |

---

## Key Deliverables

1. **Working FastAPI server** with all 7 endpoints
2. **Solar forecasting pipeline** (hybrid pvlib + XGBoost)
3. **Wind forecasting pipeline** (LightGBM/XGBoost)
4. **Uncertainty bands** (P10/P50/P90)
5. **Decision engine** with risk classification
6. **Explainability layer** with plain-language outputs
7. **SQLite database** for site storage
8. **Evaluation metrics** comparing against persistence baseline
9. **Scenario simulator** endpoint

---

## Phase 11 — ML Model Retraining & Hugging Face Release ✅

Completed: Open-Meteo/IMDA data-source survey → `build_dataset.py` (Bhadla, Rajasthan; 17,544 hourly rows 2023–24; pvlib-modelled pv system ground truth) → `retrain.py` (XGBoost residual + LightGBM quantile p10/p50/p90; holdout nMAE 0.25%, R² 0.9996, MAPE 1.23%, 80% coverage 87.0%; walk-forward avg nMAE 0.23%) → fixed `features.py` tz-aware DatetimeIndex → wired `predict_solar` to real pvlib physics + trained quantile bands → live `/api/forecast` returns `solar_hybrid` (19 features) with weather-seeded DB → `hf_release/` pip package `gridmind-solar-forecast` (SolarForecaster, bundled models, quickstart, publish.py) + Gradio Space (`hf_release/space/`, live Open-Meteo + pvlib+XGB+LGBM, P10/P50/P90 band chart) → both package and Space verified locally. HF push pending user token: `HF_TOKEN=hf_... python3 publish.py`.

---

## Dependencies for Module 2

- API contract (endpoint URLs, request/response schemas)
- Sample API responses for frontend development
- CORS configured on backend

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Open-Meteo API rate limits | Cache aggressively, use sample data for demo |
| pvlib complexity | Fallback to simpler clear-sky model if pvlib setup takes too long |
| Model accuracy below baseline | Ensure persistence baseline is always available as fallback |
| Time overrun | Decision engine is highest priority after basic forecast works |
