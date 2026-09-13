# GridMind AI — Renewable Energy Forecasting & Decision Platform

> **HackOut'26** · Theme: Renewable Energy Intelligence · Built in 48 hours

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)](https://xgboost.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

GridMind AI is an explainable decision layer for renewable energy operators. It forecasts solar and wind generation 24–72 hours ahead with calibrated uncertainty bands, flags over/under-generation risks, and recommends grid actions (battery dispatch, curtailment, backup activation) — all with financial (₹) and environmental (CO₂) impact estimates.

**Target users:** Smaller renewable operators who lack expensive SCADA/forecasting infrastructure.

---

## Key Features

- **Physics-Informed ML Models** — pvlib solar physics + XGBoost residual correction; LightGBM for wind with IEC power curve gating
- **SURGE Architecture** — 21 solar features, 16 wind features, site-agnostic and capacity-agnostic
- **Uncertainty Quantification** — P10/P50/P90 quantile regression with band calibration
- **Lambda Architecture** — Batch (historical) + Speed (real-time) + Serving (merged) layers
- **AI Copilot** — Gemini-powered chat interface with structured markdown responses
- **Risk Analysis** — Hourly over/under-generation risk with financial impact
- **Battery Optimization** — Charge/discharge scheduling with savings estimates
- **Real-Time Weather** — Open-Meteo API (GHI, DNI, DHI, wind, temperature) — no API key required

---

## Model Performance

### Solar (XGBoost + pvlib physics, 100 kW Bhadla)

| Metric | Value |
|--------|-------|
| MAE | 0.63 kW |
| R² | **0.9986** |
| nMAE | 0.63% |
| Walk-Forward R² | **0.9991** |
| 80% Coverage | 82% |

### Wind (LightGBM + IEC physics, 100 kW Jaisalmer)

| Metric | Value |
|--------|-------|
| MAE | 0.92 kW |
| R² | **0.9988** |
| nMAE | 0.92% |

### Baseline Comparison (Solar)

| Model | MAE | R² | vs Deployed |
|-------|-----|-----|-------------|
| **Deployed (XGBoost + physics)** | **1.11** | **0.9898** | — |
| Persistence (24h) | 2.17 | 0.954 | −49% worse |
| Climatology | 5.21 | 0.922 | −79% worse |
| Physics-only (pvlib) | 5.27 | 0.935 | −79% worse |
| Naive mean | 29.51 | −0.978 | −96% worse |

### Generalization

| Experiment | Solar R² | Wind R² |
|------------|----------|---------|
| Cross-year (2023, same sites) | 0.994 | 0.987 |
| Cross-site (Chennai/Kanyakumari) | 0.960 | 0.977 |

---

## Architecture

```
Weather API (Open-Meteo)  ──┐
                             ├──▶ Feature Engineering ──▶ Forecast Engine ──▶ Decision Engine ──▶ Dashboard
Historical Generation CSV ──┘
```

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Auth     │  │ Forecast │  │ Chat     │  │ Data     │   │
│  │ (JWT)    │  │ (SURGE)  │  │ (Gemini) │  │ (Sync)   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Risk     │  │ Optimize │  │ Insights │                  │
│  │ Analysis │  │ Battery  │  │ Weather  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              React + TypeScript Frontend (SPA)              │
│  Dashboard · Forecast · Risk · Optimize · AI Chat · Data   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| ML Models | XGBoost, LightGBM, pvlib, scikit-learn |
| Uncertainty | Quantile regression (P10/P50/P90) |
| Weather | Open-Meteo API (free, no key) |
| AI Copilot | Google Gemini 2.5 Flash |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Charts | Recharts |
| Auth | JWT (bcrypt + python-jose) |
| Deployment | Docker, Uvicorn |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/HEETMEHTA18/Gridkavach.git
cd Gridkavach

# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings (defaults work for local dev)
```

### 3. Run

```bash
# Backend (port 8000)
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Frontend (dev, port 5173)
cd frontend && npm run dev
```

### 4. Login

- **Email:** `demo@gridmind.com`
- **Password:** `demo1234`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Get JWT token |
| GET | `/sites/` | List sites |
| POST | `/sites/` | Create site |
| POST | `/api/forecast/{site_id}` | Generate forecast |
| POST | `/api/risk/{site_id}` | Analyze risk |
| POST | `/api/optimize/{site_id}` | Battery optimization |
| GET | `/api/data/status/{site_id}` | Data status |
| POST | `/api/data/sync/{site_id}` | Sync weather data |
| POST | `/api/chat/sessions` | Create chat session |
| POST | `/api/chat/sessions/{id}/chat` | Send message |

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product Requirements Document — problem statement, user stories, features |
| [TRD.md](TRD.md) | Technical Requirements Document — architecture, tech stack, API design |
| [model.md](model.md) | Model Development Specification — architecture, hyperparameters, training protocol |
| [output.md](output.md) | Publication-stage metrics, maths & baseline comparison (SURGE Forecaster) |
| [workflow.md](workflow.md) | End-to-end system workflow and data pipeline |
| [work1.md](work1.md) | Module 1: Backend, ML Models & Data Pipeline (48h breakdown) |
| [work2.md](work2.md) | Module 2: Frontend Dashboard & UI (48h breakdown) |
| [SECURITY_REVIEW.md](SECURITY_REVIEW.md) | Security audit — CORS, XSS, SQL injection, secrets |
| [VERTEX_AI_GUIDE.md](VERTEX_AI_GUIDE.md) | Vertex AI free tier integration guide |
| [benchmarks/HONEST_BENCHMARK_REPORT.md](benchmarks/HONEST_BENCHMARK_REPORT.md) | Honest model benchmark with Diebold-Mariano tests |
| [.env.example](.env.example) | Environment configuration template |

---

## Project Structure

```
Gridkavach/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Environment config
│   ├── database.py          # SQLAlchemy async engine
│   ├── models_db.py         # DB models (User, Site, WeatherData, etc.)
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT + bcrypt auth
│   ├── gemini_copilot.py    # Gemini AI integration
│   ├── forecasting/
│   │   ├── inference.py     # SURGE inference (XGBoost + quantile)
│   │   ├── features.py      # Feature engineering
│   │   ├── solar.py         # pvlib physics model
│   │   └── wind.py          # IEC power curve
│   ├── weather/
│   │   └── provider.py      # Open-Meteo API client
│   ├── optimization/
│   │   └── dispatch.py      # Battery dispatch engine
│   └── routes/
│       ├── auth.py          # Auth endpoints
│       ├── forecast.py      # Forecast endpoints
│       ├── risk.py          # Risk analysis
│       ├── chat.py          # AI copilot chat
│       └── data.py          # Data sync & status
├── frontend/
│   └── src/
│       ├── App.tsx          # Main app (9 pages)
│       ├── api/client.ts    # API client
│       └── components/      # UI components
├── models/
│   ├── solar/               # XGBoost + quantile models
│   └── wind/                # LightGBM + quantile models
├── data/raw/                # Training datasets
├── benchmarks/              # Evaluation reports
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Deployment

### Docker

```bash
docker-compose up --build
```

### Manual

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Frontend (production build)
cd frontend && npm run build
# Serve from FastAPI (built-in)
```

---

## License

MIT

---

Built for **HackOut'26** by Team GridKavach
