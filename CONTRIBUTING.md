# Contributing to GridShield AI

## IBM Bob Hackathon 2026 — U1: Power Outage Prediction & Grid Equipment Failure Advisor

---

## Repository Layout

```
backend/          FastAPI backend (GridShield modules + legacy Gridkavach)
  gridshield/     All new GridShield modules
    contracts.py      Pydantic data contracts (stable integration seam)
    mock_data.py      30-asset deterministic synthetic fleet
    ml_adapter.py     MockFailurePredictor + FailurePredictor ABC
    risk_engine.py    Composite risk scoring engine
    grid_impact.py    Grid impact (customers, critical facilities)
    weather_adapter.py  Weather exposure adapter
    service.py        Orchestrator service
    copilot.py        Grid Operations AI Advisor
    routes.py         All 16 /api/gs/* endpoints
frontend/         React 18 + TypeScript frontend
  src/
    api/gridshield.ts           TypeScript API client
    components/gridshield/      6 GridShield pages
docs/             Architecture, PRD, TRD, MODEL, DATA, setup guide
```

---

## Development Setup

See [docs/setup-guide.md](docs/setup-guide.md) for full instructions.

**Quick start:**
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev
```

---

## ML Integration Seam

The key design decision is the `MockFailurePredictor → RealFailurePredictor` swap.

When the real ML pipeline is ready:

1. Open `backend/gridshield/ml_adapter.py`
2. Implement `RealFailurePredictor(FailurePredictor)` — same `predict()` signature
3. Set `GRIDSHIELD_USE_REAL_ML=1` in `.env`
4. No other changes needed — the risk engine, frontend, and tests remain intact

The `FailurePrediction` contract in `backend/gridshield/contracts.py` is stable.

---

## Frontend Build

```bash
cd frontend && npm run build
# Must complete with 0 TypeScript errors
```

---

## Code Style

- **Python:** follow existing file conventions; no unused imports; type hints on function signatures
- **TypeScript:** no `any` without comment; no unused state variables
- **Commits:** `[scope] short description` — e.g. `[backend] add RealFailurePredictor stub`

---

## IBM Bob

IBM Bob (IBM Codex AI) is the primary AI coding agent for this project.
Record meaningful Bob sessions in `docs/BOB_ENGINEERING_LOG.md`.

---

## Environment

Copy `.env.example` to `.env`. Never commit `.env` or any API key.
The application works fully in demo mode without any external credentials.
