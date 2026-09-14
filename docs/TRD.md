# Bottleneck AI — Technical Requirements Document

## Architecture
Use a modular monolith for the hackathon.

Frontend
→ FastAPI
→ services
→ database/model inference
→ external APIs.

## Stack
### Frontend
- React
- TypeScript
- Tailwind CSS
- Recharts
- Leaflet

### Backend
- Python
- FastAPI
- Pydantic
- Uvicorn

### ML
- pandas
- NumPy
- scikit-learn
- XGBoost
- optional SHAP

### Storage
- SQLite for MVP
- PostgreSQL-compatible repository design

### AI
- IBM watsonx.ai/Granite if provisioned and practical
- grounded fallback if AI service is unavailable

## External data
### Open-Meteo
Forecast/historical weather.

### NASA POWER
Historical meteorological/solar context for training/analysis.

### OpenStreetMap/Overpass
Optional geographic context. Cache results.

## Backend contracts
GET /api/assets
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/telemetry
GET /api/assets/{asset_id}/weather
GET /api/assets/{asset_id}/prediction
GET /api/risk-ranking
GET /api/risk/{asset_id}
GET /api/maintenance/plan
GET /api/crews
GET /api/crew/plan
POST /api/copilot/query
POST /api/scenarios/run
GET /api/health

## Canonical telemetry payload
{
  "asset_id": "TR-104",
  "timestamp": "ISO-8601",
  "temperature": 84.2,
  "vibration": 5.8,
  "partial_discharge": 21.4,
  "oil_quality": 71,
  "load_percent": 91,
  "current": 420.1,
  "voltage": 11000
}

## Canonical prediction payload
{
  "asset_id": "TR-104",
  "timestamp": "ISO-8601",
  "horizon_hours": 24,
  "failure_probability": 0.92,
  "confidence": 0.84,
  "risk_level": "CRITICAL",
  "model_version": "bottleneck-failure-v1"
}

## Integration rules
Every team module communicates through typed JSON contracts.
No teammate should import another teammate's internal implementation.
Shared models/schema/interfaces live under `src/contracts/`.
Mock adapters must implement the same interfaces as real adapters.

## External API resilience
All external API clients require:
- timeout
- error handling
- validation
- caching where appropriate
- fallback to cached/historical data

## Security
- Never commit `.env`.
- Never commit API keys, tokens, passwords, IBM credentials, or cloud credentials.
- Maintain `.env.example`.
- Do not expose raw secrets in logs or AI prompts.

## Testing
Unit:
- feature engineering
- risk score
- recommendation rules
- API schemas
- crew assignment

Integration:
- weather adapter
- telemetry pipeline
- ML inference
- risk ranking
- copilot grounding

End-to-end:
- scenario → prediction → dashboard → recommendation.

## Performance
No training during a normal dashboard request.
Predictions should use pre-trained/versioned models.
Cache repeated weather requests.
