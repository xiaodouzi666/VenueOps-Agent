#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT first}"
: "${MONGODB_URI:?Set MONGODB_URI to the MongoDB Atlas connection string}"
: "${MDB_MCP_CONNECTION_STRING:?Set MDB_MCP_CONNECTION_STRING to the MongoDB MCP connection string}"
: "${MONGODB_URI_SECRET:=MONGODB_URI}"
: "${MDB_MCP_CONNECTION_STRING_SECRET:=MDB_MCP_CONNECTION_STRING}"

write_secret() {
  local name="$1"
  local value="$2"

  if gcloud secrets describe "${name}" --project "${GOOGLE_CLOUD_PROJECT}" >/dev/null 2>&1; then
    printf '%s' "${value}" | gcloud secrets versions add "${name}" \
      --data-file=- \
      --project "${GOOGLE_CLOUD_PROJECT}" >/dev/null
    printf 'updated secret version: %s\n' "${name}"
  else
    printf '%s' "${value}" | gcloud secrets create "${name}" \
      --data-file=- \
      --replication-policy=automatic \
      --project "${GOOGLE_CLOUD_PROJECT}" >/dev/null
    printf 'created secret: %s\n' "${name}"
  fi
}

write_secret "${MONGODB_URI_SECRET}" "${MONGODB_URI}"
write_secret "${MDB_MCP_CONNECTION_STRING_SECRET}" "${MDB_MCP_CONNECTION_STRING}"

printf 'secret setup complete for project %s\n' "${GOOGLE_CLOUD_PROJECT}"
