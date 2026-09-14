# GridShield AI — Integration Contract

## Principle
Each of the four workstreams must be independently runnable and integrated only through stable contracts.

## Repository layout

```text
src/
  contracts/
  backend/
  ml/
  frontend/
  ai/
  risk/
  optimization/
  data/
tests/
docs/
bob_sessions/
```

## Shared contracts

The only cross-module imports allowed are:
- shared schemas/types
- public service interfaces
- API clients

Do not import private implementation files across workstreams.

## Canonical service boundaries

### Telemetry
`TelemetryProvider`
→ returns `TelemetryRecord[]`

### Weather
`WeatherProvider`
→ returns `WeatherRecord[]`

### Model
`PredictionService`
→ returns `PredictionResult`

### Risk
`RiskService`
→ returns `RiskResult`

### Maintenance
`MaintenancePlanner`
→ returns `MaintenanceRecommendation[]`

### Crew
`CrewPlanner`
→ returns `CrewAssignment[]`

### Copilot
`CopilotService`
→ accepts `CopilotRequest`
→ returns `CopilotResponse`

## Integration sequence

1. Team 1 publishes schemas + model adapter.
2. Team 2 publishes API endpoints using those schemas.
3. Team 3 consumes APIs using generated/handwritten typed clients.
4. Team 4 integrates copilot and end-to-end orchestration.
5. Final merge owner runs full regression tests.

## Branching

Each teammate works on:

- `feature/ml-data`
- `feature/backend-api`
- `feature/frontend`
- `feature/ai-integration`

Merge to main only after:
- tests pass
- contract check passes
- no secrets
- no unrelated changes

## Merge order

1. Contracts
2. Data/backend foundation
3. ML adapter
4. Frontend
5. AI integration
6. Scenario/demo
7. Documentation/submission artifacts

## Mocking strategy

Every service should have:
- real implementation
- local mock/fallback implementation

This allows work to continue even when one component is unfinished.

## Integration test
A single scenario should traverse:

synthetic telemetry
→ model
→ risk
→ maintenance
→ crew
→ API
→ frontend
→ copilot.

## Rule
No "works on my machine" integration. Every component must have setup instructions and a health check.
