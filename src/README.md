# GridShield AI — Source Code

## IBM Bob Hackathon 2026 — Track U1

This directory contains the full source code for GridShield AI.

## Structure

```
src/
├── backend/                      FastAPI backend
│   ├── gridshield/               GridShield core modules
│   │   ├── contracts.py          Pydantic request/response schemas
│   │   ├── ml_adapter.py         ML integration seam (swap here to use real models)
│   │   ├── risk_engine.py        Risk scoring & alert logic
│   │   ├── grid_impact.py        Grid impact calculations
│   │   ├── service.py            Business logic layer
│   │   ├── routes.py             /api/gs/* route handlers
│   │   ├── copilot.py            AI copilot integration
│   │   ├── weather_adapter.py    Weather data adapter
│   │   └── mock_data.py          Deterministic mock responses
│   ├── forecasting/              ML forecasting pipeline
│   │   ├── solar.py              Solar generation forecasting
│   │   ├── wind.py               Wind generation forecasting
│   │   ├── inference.py          Model inference helpers
│   │   ├── features.py           Feature engineering
│   │   ├── anomaly.py            Anomaly detection
│   │   ├── uncertainty.py        Uncertainty quantification
│   │   └── evaluate.py           Model evaluation utilities
│   ├── training/                 Model training scripts
│   │   ├── pipeline.py           End-to-end training pipeline
│   │   ├── train_solar.py        Solar model training
│   │   ├── train_wind.py         Wind model training
│   │   ├── train_generic.py      Generic model trainer
│   │   ├── build_dataset.py      Dataset construction
│   │   ├── build_wind_dataset.py Wind-specific dataset builder
│   │   ├── download_datasets.py  Dataset download helpers
│   │   ├── retrain.py            Retraining entrypoint
│   │   ├── tune_utils.py         Hyperparameter tuning utilities
│   │   └── unsloth_analysis.py   Unsloth fine-tune analysis
│   ├── optimization/             Dispatch & scheduling
│   │   └── dispatch.py           Economic dispatch optimizer
│   ├── services/                 Background & async services
│   │   ├── batch_processor.py    Batch inference service
│   │   ├── live_poller.py        Live data polling service
│   │   └── explain.py            Explainability service
│   ├── routes/                   Legacy Gridkavach routes
│   │   ├── auth.py               Authentication routes
│   │   ├── chat.py               Chat / AI assistant routes
│   │   ├── data.py               Data ingestion routes
│   │   ├── forecast.py           Forecast routes
│   │   ├── insights.py           Insights routes
│   │   └── sites.py              Site management routes
│   ├── weather/
│   │   └── provider.py           Open-Meteo weather provider
│   ├── api/
│   │   └── database.py           Database API helpers
│   ├── data/
│   │   ├── raw/                  Raw training data (CSV)
│   │   └── sample/               Sample datasets
│   ├── models/
│   │   └── metrics/              Saved model metrics (JSON)
│   ├── main.py                   Application entry point
│   ├── auth.py                   Auth utilities
│   ├── config.py                 App configuration
│   ├── database.py               SQLAlchemy DB setup
│   ├── dependencies.py           FastAPI dependency injection
│   ├── gemini_copilot.py         Gemini AI integration
│   ├── lambda_architecture.py    Lambda architecture helpers
│   ├── models_db.py              SQLAlchemy ORM models
│   ├── schemas.py                Shared Pydantic schemas
│   └── websocket.py              WebSocket handler
├── frontend/                     React 18 + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── gridshield/       6 GridShield feature pages
│   │   │   │   ├── GridShieldApp.tsx      Main app shell
│   │   │   │   ├── CommandCenter.tsx      Operations dashboard
│   │   │   │   ├── AssetIntelligence.tsx  Asset monitoring
│   │   │   │   ├── MaintenancePlanner.tsx Maintenance scheduling
│   │   │   │   ├── CrewPlanner.tsx        Crew dispatch planner
│   │   │   │   ├── ScenarioSimulator.tsx  What-if simulator
│   │   │   │   ├── Copilot.tsx            AI copilot chat
│   │   │   │   └── index.ts               Barrel export
│   │   │   ├── layout/           App layout & navigation
│   │   │   ├── landing/          Landing page
│   │   │   ├── forecast/         Forecast chart components
│   │   │   ├── anomaly/          Anomaly detection UI
│   │   │   ├── risk/             Risk timeline components
│   │   │   ├── scenario/         Scenario control components
│   │   │   ├── site/             Site form & list components
│   │   │   ├── recommendation/   Recommendation card
│   │   │   ├── datasources/      Data source manager
│   │   │   ├── common/           Shared UI primitives
│   │   │   └── ui/               Radix-based UI components
│   │   ├── api/
│   │   │   ├── gridshield.ts     TypeScript GridShield API client
│   │   │   └── client.ts         Axios base client
│   │   ├── context/
│   │   │   └── SiteContext.tsx   Global site state
│   │   ├── hooks/                Custom React hooks
│   │   │   ├── useForecast.ts
│   │   │   ├── useRisk.ts
│   │   │   ├── useScenario.ts
│   │   │   ├── useOptimize.ts
│   │   │   └── useExplain.ts
│   │   ├── lib/
│   │   │   └── utils.ts          Shared utilities
│   │   ├── App.tsx               App shell with sidebar navigation
│   │   └── main.tsx              React entry point
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── tests/                        Pytest test suite (44 tests)
│   ├── test_gridshield.py        GridShield unit tests
│   ├── test_integration.py       Integration tests
│   └── test_models.py            Model tests
├── requirements.txt              Python dependencies
└── .env.example                  Environment variable template
```

## Quick Start

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev
# Open http://localhost:5173
```

No API keys required. See [../docs/setup-guide.md](../docs/setup-guide.md) for full instructions.

## API Endpoints

All GridShield endpoints: `/api/gs/*`

See [../README.md](../README.md) for the full endpoint list.

## ML Integration Seam

To integrate the real ML pipeline, only `backend/gridshield/ml_adapter.py` needs to change.
See [../docs/architecture.md](../docs/architecture.md) for details.
