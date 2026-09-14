# Team 1 — ML & Data Intelligence

## Owner
Person 1

## Mission
Own the complete data → feature → prediction pipeline.

## Responsibilities
- Asset/telemetry/incident data schemas
- Synthetic data generator
- Data validation
- Feature engineering
- Failure prediction model
- Anomaly detection
- Evaluation
- Model artifact/versioning
- Inference interface

## Inputs
Read:
- `CONTEXT.md`
- `DATA.md`
- `MODEL.md`
- `src/contracts/`

## Outputs
Deliver:
- `src/ml/data/`
- `src/ml/features/`
- `src/ml/training/`
- `src/ml/inference/`
- `src/ml/evaluation/`
- versioned model artifact
- model metrics JSON
- documented inference API

## Contract
The model service MUST expose:

`predict(asset_id, timestamp_or_features)`

and return:
- failure_probability
- confidence
- risk_level candidate
- model_version
- top_features

## Must not touch
- React pages
- crew logic
- maintenance UI
- copilot UI

## Integration test
Given known telemetry for TR-104, the service returns a deterministic schema and valid probability [0,1].

## Done when
Another teammate can call the model through the agreed interface without importing internal ML code.
