# Setup Guide — GridShield AI

## IBM Bob Hackathon 2026 — Track U1

This guide walks through running GridShield locally from a fresh clone.
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
pip install -r requirements.txt
```

---

## 3. Configure Environment

```bash
# Copy the example file
cp .env.example .env
```

The default `.env.example` values work for demo mode — no changes needed.

Optional settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (empty) | Enables Gemini-powered AI Copilot responses |
| `GRIDSHIELD_USE_REAL_ML` | `0` | Set to `1` to activate real ML adapter |
| `DATABASE_URL` | SQLite | PostgreSQL URL for production database |
| `SECRET_KEY` | (auto-generated) | JWT secret for auth |

**The application is fully functional without setting any of these.**

---

## 4. Start the Backend

```bash
# From the repository root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     GridShield AI — Grid Equipment Failure Advisor
INFO:     GridShield router mounted at /api/gs/
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify the API is running:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"GridShield AI"}
```

---

## 5. Set Up the Frontend

**Option A: Development server** (recommended for active development)

```bash
cd frontend
npm install
npm run dev
# Frontend available at: http://localhost:5173
```

**Option B: Production build** (served by the backend)

```bash
cd frontend
npm install
npm run build
# Built files appear in frontend/dist/
# Backend serves them at http://localhost:8000
```

---

## 6. Open GridShield

Navigate to **http://localhost:5173** (dev) or **http://localhost:8000** (production build).

The app opens directly to the **Command Center** — no login required for GridShield pages.

---

## 7. Verify the Demo Scenario

Run through the complete demo flow to verify everything is working:

### Step 1 — Command Center
- Open the app → Command Center loads
- Verify KPI bar: Critical Assets, High Risk, Customers at Risk
- Verify TR-1042 appears in the risk ranking table (rank #1 or #2)
- Verify alerts bar shows critical transformer warning

### Step 2 — Asset Intelligence
- Click on asset **TR-1042** from the risk ranking
- Verify: Risk Score ≥ 90, Health ≤ 40, Failure Probability (24h) ≥ 85%
- Verify: 8,420 customers at risk, 7 critical facilities
- Verify: Top factors list (temperature, vibration, overheating incident, weather)
- Verify: Maintenance recommendation and assigned crew shown

### Step 3 — Maintenance Planner
- Navigate to Maintenance Planner
- Verify TR-1042 is Priority #1 with "Immediate" action level

### Step 4 — Crew Planner
- Navigate to Crew Planner
- Verify CREW-07 is assigned to TR-1042

### Step 5 — Scenario Simulator
- Navigate to Scenario Simulator
- Run the **Severe Storm** scenario
- Verify: risk scores change, TR-1042 remains critical, maintenance plan updates

### Step 6 — AI Copilot (optional)
- Navigate to AI Copilot
- Ask: "Why is TR-1042 critical?"
- Verify: Response includes actual asset values (not invented statistics)

---

## 8. Frontend Type Check + Build

```bash
cd frontend
npm run build
```

Expected: 0 TypeScript errors, build completes successfully.

---

## Troubleshooting

### Backend fails to import `google.generativeai`

This is expected if the package is not installed. The application gracefully falls back
to the deterministic copilot. Install the package to enable Gemini responses:
```bash
pip install google-generativeai
```

### Frontend dev server shows CORS errors

The Vite dev server proxies API requests to `http://localhost:8000`. Ensure the backend is running on port 8000.
Check `frontend/vite.config.ts` for the proxy configuration.

### Port 8000 already in use

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
# Then update the frontend proxy in vite.config.ts to port 8001
```

### SQLite database locked

Delete `gridmind.db` from the repository root and restart the backend. The DB is recreated automatically.

---

## Docker (Optional)

```bash
docker-compose up --build
```

This starts the backend on port 8000 and serves the pre-built frontend. See `docker-compose.yml` for details.
