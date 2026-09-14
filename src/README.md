# Bottleneck AI — Source Code Structure

This directory contains the full source code for **Bottleneck AI**.

## Directory Layout

```
src/
├── backend/                      FastAPI backend
│   ├── bottleneck/               Bottleneck core modules
│   │   ├── contracts.py          Pydantic request/response schemas
│   │   ├── ml_adapter.py         ML integration seam & model loader
│   │   ├── risk_engine.py        Composite risk scoring & crew assignment
│   │   ├── grid_impact.py        Grid impact calculations
│   │   ├── service.py            Business logic orchestrator
│   │   ├── routes.py             /api/bottleneck/* API route handlers
│   │   ├── copilot.py            Grounded Bottleneck AI Copilot
│   │   ├── weather_adapter.py    Weather exposure calculations
│   │   ├── mock_data.py          Deterministic synthetic fleet data
│   │   └── ml/                   XGBoost Machine Learning pipeline
│   │       ├── data/             Training dataset generator
│   │       ├── features/         Feature matrix engineering
│   │       ├── training/         XGBoost training pipeline
│   │       ├── evaluation/       Model evaluation & metrics exporter
│   │       ├── inference/        Inference service & model reloader
│   │       └── monitoring/       Model health & drift monitoring
│   ├── main.py                   FastAPI application entry point
│   ├── database.py               Database connection setup
│   ├── models_db.py              SQLAlchemy models
│   └── gemini_copilot.py         Gemini LLM integration
├── frontend/                     React 18 + TypeScript SPA
│   ├── src/
│   │   ├── components/
│   │   │   └── bottleneck/       Bottleneck UI feature views
│   │   │       ├── CommandCenter.tsx      Fleet operations dashboard
│   │   │       ├── AssetIntelligence.tsx  Detailed asset diagnostics
│   │   │       ├── MaintenancePlanner.tsx Consequence-ranked priorities
│   │   │       ├── CrewPlanner.tsx        Crew pre-positioning planner
│   │   │       ├── ScenarioSimulator.tsx  What-if scenario simulator
│   │   │       ├── Copilot.tsx            AI Advisor interface
│   │   │       └── BottleneckApp.tsx      Standalone app shell
│   │   ├── api/
│   │   │   ├── bottleneck.ts     Bottleneck API client
│   │   │   └── client.ts         Axios base client configuration
│   │   ├── App.tsx               Main application shell
│   │   └── main.tsx              React entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── requirements.txt              Python backend dependencies
└── .env.example                  Environment variables template
```

## Running the Code

```bash
# 1. Start backend (FastAPI)
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# 2. Start frontend (Vite Dev Server)
cd frontend
npm install
npm run dev
```
