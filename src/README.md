# GridShield AI — Source Code

## IBM Bob Hackathon 2026 — Track U1

This directory contains the full source code for GridShield AI.

## Structure

```
src/
├── backend/          FastAPI backend
│   ├── gridshield/   All GridShield modules (contracts, ML, risk engine, APIs)
│   ├── weather/      Open-Meteo weather provider
│   ├── routes/       Legacy Gridkavach routes
│   └── main.py       Application entry point
├── frontend/         React 18 + TypeScript frontend
│   ├── src/
│   │   ├── components/gridshield/   6 GridShield pages
│   │   ├── api/gridshield.ts        TypeScript API client
│   │   └── App.tsx                  App shell with sidebar navigation
│   └── package.json
├── tests/            Pytest test suite (44 tests)
├── requirements.txt  Python dependencies
└── .env.example      Environment variable template
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
