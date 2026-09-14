# Setup Guide — Bottleneck AI

## IBM Bob Hackathon 2026 — Track U1

This guide walks through running Bottleneck AI locally from a fresh clone.
No external API keys or cloud services are required for the demo.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | https://python.org |
| pip | latest | bundled with Python |
| Node.js | 18+ | https://nodejs.org |
| npm | 9+ | bundled with Node |
| Git | any | https://git-scm.com |

---

## 1. Clone the Repository

```bash
git clone https://github.com/HEETMEHTA18/bob-ai-hackathon-bottleneck.git
cd bob-ai-hackathon-bottleneck
```

---

## 2. Set Up the Python Environment

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate       # Linux / macOS
# or: venv\Scripts\activate    # Windows

# Install all dependencies
pip install -r src/requirements.txt
```

---

## 3. Configure Environment

```bash
# Copy the example file
cp src/.env.example .env
```

The default `.env.example` values work for demo mode — no changes needed.

Optional settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (empty) | Enables Gemini-powered AI Copilot responses |
| `BOTTLENECK_USE_REAL_ML` | `0` | Set to `1` to activate real XGBoost ML models |
| `DATABASE_URL` | SQLite | PostgreSQL URL for production database |

**The application is fully functional without setting any of these.**

---

## 4. Start the Backend

```bash
# Start backend from src directory
cd src
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
[Bottleneck] Gemini API key loaded — AI copilot enabled (or fallback)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify the API is running:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"Bottleneck AI","version":"3.0.0"}
```

---

## 5. Set Up the Frontend

**Option A: Development server** (recommended for active development)

```bash
cd src/frontend
npm install
npm run dev
# Frontend available at: http://localhost:5173
```

**Option B: Production build** (served by the backend)

```bash
cd src/frontend
npm install
npm run build
# Built files appear in src/frontend/dist/
# Backend serves them at http://localhost:8000
```

---

## 6. Open Bottleneck AI

Navigate to **http://localhost:5173** (dev) or **http://localhost:8000** (production build).

The app opens directly to the **Command Center** dashboard.

---

## 7. Run Tests

```bash
# From the repository root
python -m pytest src/tests/test_bottleneck.py -v
```

Expected output:
```
44 passed in X.XXs
```

---

## 8. Frontend Type Check & Build

```bash
cd src/frontend
npm run build
```

Expected: 0 TypeScript errors, build completes successfully.

