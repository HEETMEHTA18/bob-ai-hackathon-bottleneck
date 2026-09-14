# GridShield AI — Data Strategy

## Sources
### Public/live
- Open-Meteo forecast/historical weather
- NASA POWER historical weather/solar variables
- Optional OpenStreetMap/Overpass geographic context

### Controlled/synthetic
- Asset inventory
- Telemetry
- Incidents
- Maintenance history
- Crew locations
- Customer/grid impact metadata

## Synthetic telemetry design
Synthetic data must model plausible relationships.

### Thermal degradation
Temperature and load rise before failure.

### Mechanical degradation
Vibration trend rises before failure.

### Insulation degradation
Partial discharge increases and oil-quality indicators worsen.

### Weather stress
Wind, precipitation, temperature extremes, or severe-weather flags increase environmental risk.

### Combined scenario
Equipment degradation + high load + severe weather creates the strongest failure signal.

## Required datasets
- `assets.csv`
- `telemetry.csv`
- `incidents.csv`
- `maintenance.csv`
- `crews.csv`
- `weather_cache.csv`

## Data quality
Validate:
- timestamps
- ranges
- missing values
- duplicates
- impossible sensor values
- foreign-key consistency

## Licensing
Every external source used in the project must be recorded with source URL and applicable terms.

## Privacy
Do not use client data, personal information, confidential utility data, or social-media data.

## Reproducibility
Synthetic generator must use configurable seeds and store generation parameters.
