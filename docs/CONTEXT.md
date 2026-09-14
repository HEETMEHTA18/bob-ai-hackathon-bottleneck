# GridShield AI — Project Context

## Mission
GridShield AI is a software-first AI-powered grid reliability platform for the IBM Bob Hackathon U1 problem:
**Power Outage Prediction & Grid Equipment Failure Advisor**.

The official challenge requires a solution that combines asset-health sensor data, weather forecasts, and historical incident records to:
1. Predict outage-prone areas and at-risk equipment.
2. Rank assets by grid-impact severity.
3. Generate prioritised maintenance plans.
4. Generate crew pre-positioning plans.

## Core product question
Do not stop at:
> "Which asset is likely to fail?"

Answer:
> "Which asset is likely to fail, how serious would the consequence be, why is it risky, and what should the operator do next?"

## System pipeline
Asset telemetry
→ weather
→ incident history
→ asset/grid metadata
→ data validation
→ feature engineering
→ anomaly detection
→ failure-risk prediction
→ weather risk
→ impact/risk scoring
→ maintenance prioritisation
→ crew pre-positioning
→ grounded AI explanation
→ operator dashboard.

## Software-first scope
Hardware is intentionally deferred. Telemetry must enter the platform through the same API schema that a future ESP32/IoT layer can use.

## Data strategy
Real/public:
- Weather forecasts/history
- Geographic context when needed

Synthetic/controlled:
- Transformer/substation telemetry
- Failure/incident history
- Maintenance history
- Crew locations
- Grid impact metadata

Synthetic data must model realistic degradation patterns; do not use pure random noise.

## Product modules
- Command Center
- Asset Intelligence
- Risk Map
- Predictive Analytics
- Maintenance Planner
- Crew Planner
- AI Copilot
- Scenario Simulator
- Data/Model monitoring

## AI rule
The copilot explains structured backend evidence. It must not invent sensor values, weather, predictions, incidents, or operational actions.

## Hackathon rule
IBM Bob IDE is a core engineering component. Keep Bob session exports in `bob_sessions/` and keep the official submission structure intact.

## Definition of done
A judge can:
1. Start the app from the setup guide.
2. See assets and telemetry.
3. see weather risk.
4. inspect a predicted high-risk asset.
5. understand why it is risky.
6. see an actionable maintenance plan.
7. see a crew pre-positioning plan.
8. run a scenario.
9. ask the AI copilot a grounded question.
10. reproduce the result.
