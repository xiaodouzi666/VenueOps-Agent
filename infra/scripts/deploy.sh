#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT first}"
: "${GOOGLE_CLOUD_REGION:=us-central1}"
: "${MONGODB_URI_SECRET:=MONGODB_URI}"
: "${MDB_MCP_CONNECTION_STRING_SECRET:=MDB_MCP_CONNECTION_STRING}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AR_REPO="venueops"
API_IMAGE="${GOOGLE_CLOUD_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${AR_REPO}/venueops-api:latest"
WEB_IMAGE="${GOOGLE_CLOUD_REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/${AR_REPO}/venueops-web:latest"

gcloud artifacts repositories describe "${AR_REPO}" \
  --location "${GOOGLE_CLOUD_REGION}" \
  --project "${GOOGLE_CLOUD_PROJECT}" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format docker \
    --location "${GOOGLE_CLOUD_REGION}" \
    --project "${GOOGLE_CLOUD_PROJECT}"

gcloud builds submit "${ROOT_DIR}" \
  --config "${ROOT_DIR}/infra/cloudbuild-api.yaml" \
  --substitutions "_IMAGE=${API_IMAGE}" \
  --project "${GOOGLE_CLOUD_PROJECT}"
gcloud run deploy venueops-api \
  --image "${API_IMAGE}" \
  --region "${GOOGLE_CLOUD_REGION}" \
  --allow-unauthenticated \
  --set-env-vars "MONGODB_DB=venueops_demo,VENUEOPS_ALLOWED_DB=venueops_demo,VENUEOPS_DEMO_MODE=false,VENUEOPS_USE_REAL_MCP=true,GOOGLE_GENAI_USE_VERTEXAI=true" \
  --set-secrets "MONGODB_URI=${MONGODB_URI_SECRET}:latest,MDB_MCP_CONNECTION_STRING=${MDB_MCP_CONNECTION_STRING_SECRET}:latest" \
  --project "${GOOGLE_CLOUD_PROJECT}"

API_URL="$(gcloud run services describe venueops-api --region "${GOOGLE_CLOUD_REGION}" --format 'value(status.url)' --project "${GOOGLE_CLOUD_PROJECT}")"

gcloud builds submit "${ROOT_DIR}/apps/web" --tag "${WEB_IMAGE}" --project "${GOOGLE_CLOUD_PROJECT}"
gcloud run deploy venueops-web \
  --image "${WEB_IMAGE}" \
  --region "${GOOGLE_CLOUD_REGION}" \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_BASE_URL=${API_URL}" \
  --project "${GOOGLE_CLOUD_PROJECT}"

gcloud run services describe venueops-web --region "${GOOGLE_CLOUD_REGION}" --format 'value(status.url)' --project "${GOOGLE_CLOUD_PROJECT}"
