#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-kafka}"
PORT="${2:-9092}"
MAX_RETRIES="${3:-30}"
RETRY_INTERVAL="${4:-5}"

echo "Waiting for Kafka at ${HOST}:${PORT}..."

for i in $(seq 1 "$MAX_RETRIES"); do
    if bash -c "echo > /dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
        echo "Kafka is ready at ${HOST}:${PORT} (attempt ${i}/${MAX_RETRIES})"
        exit 0
    fi
    echo "  Attempt ${i}/${MAX_RETRIES} - Kafka not ready, retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

echo "ERROR: Kafka did not become ready after ${MAX_RETRIES} attempts"
exit 1
