# GridShield AI — Model Specification

## Objective
Predict the probability that a monitored asset experiences a failure within a defined future horizon.

Primary target:
`failure_within_24h`

Optional target:
`failure_within_72h`

## Architecture
### Model 1 — Failure prediction
Primary: XGBoost classifier.
Baseline: Logistic Regression.
Optional comparison: Random Forest.

### Model 2 — Anomaly detection
Isolation Forest or robust rolling-statistical anomaly detection.

### Model 3 — Risk prioritisation
Deterministic scoring, not an opaque ML model.

## Inputs
### Telemetry
- temperature_current
- temperature_mean_1h
- temperature_mean_6h
- temperature_mean_24h
- temperature_trend
- vibration_current
- vibration_mean_6h
- vibration_trend
- partial_discharge_current
- partial_discharge_trend
- oil_quality_current
- oil_quality_change
- load_current
- load_max_24h
- load_mean_24h

### Weather
- temperature
- humidity
- precipitation
- wind_speed
- wind_gust
- pressure
- cloud_cover
- weather_code

### Asset
- asset_age
- capacity_mw
- customers_served
- criticality
- redundancy
- previous_failures
- days_since_maintenance

## Leakage prevention
Use only information available at prediction time.
Use chronological train/validation/test splits.
Never shuffle time series for final evaluation.

## Metrics
Primary:
- PR-AUC
- Recall
- Precision
- F1

Secondary:
- ROC-AUC
- Brier score
- Calibration
- confusion matrix

## Risk score
Overall score should combine:
- failure probability
- weather risk
- customer impact
- capacity impact
- criticality
- redundancy

Normalize to 0–100.

Initial application bands:
0–39 LOW
40–69 MEDIUM
70–84 HIGH
85–100 CRITICAL

These are product thresholds, not universal engineering safety limits.

## Explainability
Every high/critical prediction must expose:
- probability
- confidence
- top contributing factors
- recent trends
- weather contribution
- impact factors.

## Model governance
Version all model artifacts.
Store:
- model version
- dataset version
- feature list
- evaluation metrics
- training date
- hyperparameters

## Limitations
This is a proof-of-concept using public and synthetic/controlled data. Performance must not be presented as a guarantee for a real utility. Human engineering review remains necessary.
