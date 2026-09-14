# Team 3 — Frontend, UX & Visualization

## Owner
Person 3

## Mission
Build the operational dashboard and visual story.

## Responsibilities
- App shell/navigation
- Command Center
- Asset Intelligence
- Risk Map
- Predictive Analytics
- Maintenance Planner UI
- Crew Planner UI
- Scenario Simulator UI
- charts and tables
- loading/error/empty states
- responsive behaviour

## Inputs
Read:
- `PRD.md`
- `TRD.md`
- `INTEGRATION.md`
- API contracts

## Required routes
- `/dashboard`
- `/assets`
- `/assets/:id`
- `/risk-map`
- `/maintenance`
- `/crews`
- `/scenarios`

## API discipline
Use typed API client functions.
Do not hardcode fake production values into UI.
Mock data may be used only behind a dev/mock adapter.

## Must not touch
- ML code
- database schema
- backend route implementation

## Done when
The frontend works entirely from API responses and presents the full user journey without requiring direct database access.
