# Four-Person Work Split

| Person | Ownership | Main Deliverables | Integration Surface |
|---|---|---|---|
| 1 | ML & Data | datasets, feature engineering, XGBoost, anomaly detection, evaluation | `PredictionService` |
| 2 | Backend & APIs | DB, FastAPI, weather adapters, risk/asset APIs | REST API + contracts |
| 3 | Frontend & UX | dashboard, assets, map, maintenance, crew, scenario UI | typed API client |
| 4 | AI + Integration | copilot, grounded prompts, orchestration, merge/testing, demo | `CopilotService` + E2E |

## Independence rules
- Each owner has a clear directory boundary.
- No direct database access from frontend.
- No ML internals imported by backend; call a public model adapter.
- No LLM access to raw database tables.
- Shared schemas live in `src/contracts/`.
- Each workstream provides mock adapters so teammates can work independently.

## Final integrator
Person 4 coordinates final integration, but ownership remains with the original contributor for bug fixes in their module.

## Common definition of done
- module runs independently
- unit tests pass
- public interface documented
- no secrets
- no broken imports
- integration test passes
