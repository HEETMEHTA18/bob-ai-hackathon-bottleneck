# Bottleneck AI — Product Requirements Document

## Product
Bottleneck AI is a decision-support platform for power-grid asset reliability.

## Users
- Grid operations managers
- Reliability engineers
- Maintenance planners
- Field service coordinators

## Primary goals
- Detect abnormal equipment behaviour.
- Predict near-term failure risk.
- Combine equipment risk with weather risk.
- Rank assets by grid impact.
- Recommend maintenance actions.
- Recommend crew pre-positioning.
- Explain recommendations through a grounded AI copilot.

## MVP features

### F1 — Asset Monitoring
Show asset metadata, telemetry trends, current state, and maintenance history.

### F2 — Weather Intelligence
Associate forecast/historical weather with each asset and expose severe-weather risk.

### F3 — Failure Prediction
Predict failure probability within 24h; 72h can be an extension.

### F4 — Anomaly Detection
Detect abnormal telemetry relative to asset baselines.

### F5 — Risk & Impact Ranking
Calculate a 0–100 priority score from failure risk, weather, customer impact, capacity, criticality, and redundancy.

### F6 — Maintenance Planner
Generate deterministic recommendations with urgency and reasoning.

### F7 — Crew Planner
Assign/pre-position available crews using priority + distance + availability.

### F8 — AI Copilot
Answer grounded operational questions from backend evidence.

### F9 — Scenario Simulator
Simulate severe weather, overload, sensor degradation, and asset outage scenarios.

## Required user journey
Dashboard → identify risk → open asset → inspect evidence → see risk prediction → view recommendation → view crew plan → ask copilot → simulate scenario.

## MVP non-goals
- Direct SCADA control
- Autonomous switching
- Real utility deployment
- Safety certification
- Hardware/IoT integration before software MVP works
- Complex microservices
- Deep-learning research project

## Product success
The application should demonstrate a complete loop:
Detection → Prediction → Prioritisation → Action recommendation → Explanation.

## Demo scenario
A weather event approaches while one transformer develops abnormal temperature, vibration, partial discharge, and load behaviour. The risk rises, the system ranks the asset as critical, creates an inspection recommendation, selects a nearby crew, and explains the decision.

## Design principle
Working end-to-end functionality is higher priority than feature count.
