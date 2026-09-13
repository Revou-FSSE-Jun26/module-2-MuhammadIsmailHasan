#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0

echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
until nc -z "${DB_HOST}" "${DB_PORT}"; do
  RETRY_COUNT=$((RETRY_COUNT + 1))

  if [ "${RETRY_COUNT}" -ge "${MAX_RETRIES}" ]; then
    echo "ERROR: Database not available after ${MAX_RETRIES} attempts." >&2
    exit 1
  fi

  echo "Database not ready. Retry ${RETRY_COUNT}/${MAX_RETRIES}..."
  sleep "${RETRY_INTERVAL}"
done
echo "Database is up."

if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "Running database migrations..."
  flask db upgrade
else
  echo "Skipping database migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS})."
fi

echo "Starting application: $*"
exec "$@"
