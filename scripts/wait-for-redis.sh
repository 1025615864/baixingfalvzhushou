#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-redis}"
PORT="${2:-6379}"
MAX_RETRIES="${4:-30}"
RETRY_INTERVAL="${5:-2}"

echo "Waiting for Redis at ${HOST}:${PORT}..."

for i in $(seq 1 "$MAX_RETRIES"); do
    if redis-cli -h "$HOST" -p "$PORT" ping 2>/dev/null | grep -q PONG; then
        echo "Redis is ready at ${HOST}:${PORT} (attempt ${i}/${MAX_RETRIES})"
        exit 0
    fi
    echo "  Attempt ${i}/${MAX_RETRIES} - Redis not ready, retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

echo "ERROR: Redis did not become ready after ${MAX_RETRIES} attempts"
exit 1
