#!/bin/bash
set -e

PROJECT_ID="project-55baabff-7a22-41ac-91e"
REGION="us-central1"
SERVICE_NAME="data-rescue-agent"

echo "=== Setting environment variables ==="
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us"
echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "Location: $GOOGLE_CLOUD_LOCATION"

echo ""
echo "=== Deploying to Cloud Run ==="
adk deploy cloud_run \
  --project="$GOOGLE_CLOUD_PROJECT" \
  --region="$REGION" \
  --service_name="$SERVICE_NAME" \
  --with_ui \
  ./rescue_agent

echo ""
echo "=== Re-applying location override (safety net) ==="
gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --update-env-vars=GOOGLE_CLOUD_LOCATION=us

echo ""
echo "=== Done! ==="
echo "Service URL: https://data-rescue-agent-249981837129.us-central1.run.app"
echo "Dev UI: https://data-rescue-agent-249981837129.us-central1.run.app/dev-ui/?app=rescue_agent"