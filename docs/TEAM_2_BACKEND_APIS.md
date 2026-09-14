# Team 2 — Backend, Database & External APIs

## Owner
Person 2

## Mission
Own the stable application backbone.

## Responsibilities
- FastAPI application
- SQLite/PostgreSQL schema
- repository/data-access layer
- weather adapters
- incident/assets APIs
- prediction/risk API integration
- scenario API
- error handling
- caching
- API documentation

## Inputs
Read:
- `TRD.md`
- `CONTEXT.md`
- `INTEGRATION.md`
- `src/contracts/`

## Outputs
Deliver:
- `src/backend/`
- database migrations/schema
- API routes
- OpenAPI docs
- weather client
- synthetic data loaders

## External APIs
Open-Meteo primary.
NASA POWER secondary/historical.
Optional OSM/Overpass.

## Critical rule
Frontend and other teammates consume JSON APIs; they should not access the database directly.

## Must not touch
- ML internals
- React styling
- presentation assets

## Done when
A fresh clone can start the API and answer health/assets/telemetry/weather/prediction/risk endpoints with documented schemas.
