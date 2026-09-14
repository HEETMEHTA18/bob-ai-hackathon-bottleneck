# Demo — GridShield AI

## IBM Bob Hackathon 2026 — Track U1

---

## Demo Flow

The demo is designed around a single grid operations story:

> **A critical transformer (TR-1042) is showing signs of imminent failure.
> GridShield detects it, explains why, ranks it #1, plans maintenance,
> and pre-positions a crew — before any outage occurs.**

### Walkthrough Steps

1. **Command Center** — Open the app. See TR-1042 ranked #1 critical with risk score 94/100.
2. **Asset Intelligence** — Click TR-1042. See: Health 38/100, 24h failure prob 87%, 8,420 customers at risk, 7 critical facilities. Read the explanation.
3. **Maintenance Planner** — TR-1042 is Priority #1. Action: "Immediate thermal and vibration inspection within 6 hours."
4. **Crew Planner** — CREW-07 (transformer specialist, North Division) is pre-positioned.
5. **Scenario Simulator** — Run Severe Storm. Watch risk scores increase, ranking update, crew plan change.
6. **AI Copilot** — Ask "Why is TR-1042 critical?" — receive a grounded explanation using actual backend data.

---

## Screenshots

Screenshots are in the `screenshots/` directory.

| File | Shows |
|------|-------|
| `01_command_center.png` | Command Center with KPIs and risk ranking |
| `02_asset_intelligence.png` | TR-1042 full detail view |
| `03_maintenance_planner.png` | Maintenance priority list |
| `04_crew_planner.png` | Crew pre-positioning assignments |
| `05_scenario_simulator.png` | Before/after storm scenario |

---

## Running Locally

See [../docs/setup-guide.md](../docs/setup-guide.md) for full instructions.

**Quick start:**
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

No API keys required. Full demo runs offline.

---

## Video

See `demo-video-link.txt` for the demo video URL.
