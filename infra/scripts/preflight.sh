#!/usr/bin/env bash
set -euo pipefail

REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-${REGION}}"
PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || true)}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3-pro}"
MONGODB_URI_SECRET="${MONGODB_URI_SECRET:-MONGODB_URI}"
MDB_MCP_CONNECTION_STRING_SECRET="${MDB_MCP_CONNECTION_STRING_SECRET:-MDB_MCP_CONNECTION_STRING}"
REQUIRED_SERVICES=(
  aiplatform.googleapis.com
  artifactregistry.googleapis.com
  cloudbuild.googleapis.com
  run.googleapis.com
  secretmanager.googleapis.com
)

failures=0

ok() {
  printf 'ok: %s\n' "$1"
}

warn() {
  printf 'missing: %s\n' "$1"
  failures=$((failures + 1))
}

if command -v gcloud >/dev/null 2>&1; then
  ok "gcloud installed ($(gcloud --version | head -n 1))"
else
  warn "gcloud command is not installed"
  exit 1
fi

ACTIVE_ACCOUNT="$(gcloud auth list --filter='status:ACTIVE' --format='value(account)' 2>/dev/null || true)"
if [[ -n "${ACTIVE_ACCOUNT}" ]]; then
  ok "active gcloud account ${ACTIVE_ACCOUNT}"
else
  warn "no active gcloud account; run gcloud auth login"
fi

if [[ -n "${PROJECT}" && "${PROJECT}" != "(unset)" ]]; then
  ok "Google Cloud project ${PROJECT}"
  ok "Vertex AI location ${LOCATION}"
  ok "Gemini model ${GEMINI_MODEL}"
  PROJECT_NUMBER="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)' 2>/dev/null || true)"
  if [[ -n "${PROJECT_NUMBER}" ]]; then
    ok "Cloud Run API service account ${CLOUD_RUN_SERVICE_ACCOUNT:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"
  fi
else
  warn "no Google Cloud project; set GOOGLE_CLOUD_PROJECT or gcloud config set project"
fi

if [[ -n "${PROJECT}" && "${PROJECT}" != "(unset)" ]]; then
  for service in "${REQUIRED_SERVICES[@]}"; do
    if gcloud services list --enabled --project "${PROJECT}" --filter="config.name=${service}" --format='value(config.name)' 2>/dev/null | grep -qx "${service}"; then
      ok "service enabled ${service}"
    else
      warn "service not enabled or inaccessible ${service}"
    fi
  done

  for secret in "${MONGODB_URI_SECRET}" "${MDB_MCP_CONNECTION_STRING_SECRET}"; do
    if gcloud secrets describe "${secret}" --project "${PROJECT}" >/dev/null 2>&1; then
      ok "secret exists ${secret}"
    else
      warn "secret missing or inaccessible ${secret}"
    fi
  done

  if gcloud artifacts repositories describe venueops --location "${REGION}" --project "${PROJECT}" >/dev/null 2>&1; then
    ok "Artifact Registry repo venueops in ${REGION}"
  else
    printf 'info: Artifact Registry repo venueops in %s will be created by deploy.sh if permissions allow\n' "${REGION}"
  fi
else
  printf 'info: skipped service and secret checks until a project is configured\n'
fi

if [[ "${failures}" -gt 0 ]]; then
  printf 'preflight failed with %s missing prerequisite(s)\n' "${failures}"
  exit 1
fi

printf 'preflight passed; run infra/scripts/deploy.sh\n'
