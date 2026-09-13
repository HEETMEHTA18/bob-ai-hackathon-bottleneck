# Vertex AI Free Tier Integration Guide for GridMind AI

## Overview
Google Cloud Vertex AI offers a free tier that allows you to deploy and scale ML models without upfront costs.

## Free Tier Limits (as of 2024)
| Resource | Free Tier |
|----------|-----------|
| Online Prediction | 1,000 hours/month |
| Batch Prediction | 1,000 hours/month |
| Notebooks | 120 vCPU-hours/month |
| Storage | 5 GB |
| Training | $300 credit for new accounts |

## Step 1: Setup Google Cloud Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Create project
gcloud projects create gridmind-ai --name="GridMind AI"
gcloud config set project gridmind-ai

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

## Step 2: Export Models to GCS

```python
# export_to_vertex.py
from google.cloud import storage
import joblib
import json

def export_model_to_gcs(model_path, bucket_name, destination):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination)
    blob.upload_from_filename(model_path)
    print(f"Model uploaded to gs://{bucket_name}/{destination}")

# Export models
export_model_to_gcs("models/solar/solar_hybrid.json", "gridmind-models", "solar/v1/model.json")
export_model_to_gcs("models/wind/wind_lgbm.txt", "gridmind-models", "wind/v1/model.txt")
```

## Step 3: Deploy to Vertex AI Endpoint

```python
# deploy_to_vertex.py
from google.cloud import aiplatform

aiplatform.init(project="gridmind-ai", region="us-central1")

# Upload model
model = aiplatform.Model.upload(
    display_name="gridmind-solar-v1",
    serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
    serving_container_predict_route="/predict",
    serving_container_health_route="/health",
    artifact_uri="gs://gridmind-models/solar/v1/",
)

# Deploy endpoint
endpoint = model.deploy(
    deployed_model_display_name="gridmind-solar-endpoint",
    machine_type="n1-standard-2",
    min_replica_count=0,
    max_replica_count=3,
)
```

## Step 4: Free Deployment Alternative (Cloud Run)

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/gridmind-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/gridmind-api']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - gcloud
      - run
      - deploy
      - gridmind-api
      - --image
      - gcr.io/$PROJECT_ID/gridmind-api
      - --region
      - us-central1
      - --allow-unauthenticated
      - --memory
      - 512Mi
      - --cpu
      - 1
      - --min-instances
      - '0'
      - --max-instances
      - '5'
```

## Step 5: Cost Optimization

1. **Use Cloud Run** (free tier: 240,000 vCPU-seconds/month)
2. **Set min_instances=0** to scale to zero when not in use
3. **Use batch prediction** for training re-runs (cheaper than online)
4. **Store models in GCS** (5 GB free)

## Step 6: Monitoring

```python
# monitor.py
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/gridmind-ai"

# Query prediction latency
interval = monitoring_v3.TimeInterval()
results = client.list_time_series(
    request={
        "name": project_name,
        "filter": 'metric.type="aiplatform.googleapis.com/prediction/latencies"',
        "interval": interval,
    }
)
```

## Quick Start Commands

```bash
# 1. Create bucket
gsutil mb -l us-central1 gs://gridmind-models

# 2. Copy models
gsutil cp models/solar/* gs://gridmind-models/solar/v1/
gsutil cp models/wind/* gs://gridmind-models/wind/v1/

# 3. Deploy (simplified)
gcloud ai models upload \
  --region=us-central1 \
  --display-name=gridmind-solar \
  --artifact-uri=gs://gridmind-models/solar/v1/ \
  --serving-container-image-uri=us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest
```
