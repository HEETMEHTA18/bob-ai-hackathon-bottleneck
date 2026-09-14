# Bottleneck AI — Agent Instructions

## Mission
Build a working IBM Bob Hackathon proof of concept for U1 Power Outage Prediction & Grid Equipment Failure Advisor.

## Priorities
1. Working functionality
2. Correct interfaces
3. Explainability
4. Reliable integration
5. UI quality
6. Documentation

## Architecture discipline
- Keep modules independent.
- Communicate through typed contracts.
- Do not create hidden cross-module dependencies.
- Keep ML training separate from inference.
- Keep business logic out of React components.
- Keep external API adapters isolated.

## Bob workflow
PLAN → REVIEW → IMPLEMENT → TEST → REVIEW.

Before changing a major subsystem:
1. Inspect existing files.
2. State assumptions.
3. Propose the minimal change.
4. Implement.
5. Run tests.
6. Summarize changed files and remaining risks.

## Data/ML rules
- No data leakage.
- No fabricated evaluation metrics.
- No claims of 100% accuracy.
- Do not invent sensor values.
- Use reproducible seeds for synthetic data where useful.
- Keep model versions explicit.

## AI copilot rules
The copilot is a grounded explanation layer.
It must not invent:
- telemetry
- weather
- incident history
- prediction probabilities
- crew locations
- operational actions.

When information is missing, say so.

## Security
Never commit:
- `.env`
- API keys
- access tokens
- passwords
- IBM credentials
- cloud credentials.

## Scope control
Do not start hardware work until the software-only MVP passes end-to-end tests.

Do not add:
- Kubernetes
- unnecessary microservices
- autonomous grid control
- complex digital twins
unless the team explicitly promotes them into scope.

## Git rules
Use focused commits.
Do not rewrite another person's module unless the owning teammate agrees.
Keep contracts backward-compatible where practical.

## Documentation
Keep PRD.md, TRD.md, MODEL.md, CONTEXT.md, DATA.md and INTEGRATION.md synchronized with implementation.
