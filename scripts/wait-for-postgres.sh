#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-5432}"
USER="${3:-postgres}"
MAX_RETRIES="${4:-30}"
RETRY_INTERVAL="${5:-2}"

echo "Waiting for PostgreSQL at ${HOST}:${PORT}..."

for i in $(seq 1 "$MAX_RETRIES"); do
    if pg_isready -h "$HOST" -p "$PORT" -U "$USER" -q 2>/dev/null; then
        echo "PostgreSQL is ready at ${HOST}:${PORT} (attempt ${i}/${MAX_RETRIES})"
        exit 0
    fi
    echo "  Attempt ${i}/${MAX_RETRIES} - PostgreSQL not ready, retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

echo "ERROR: PostgreSQL did not become ready after ${MAX_RETRIES} attempts"
exit 1
