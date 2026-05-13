#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/baixing-backups/db}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
UPLOAD_S3="${UPLOAD_S3:-false}"
S3_BUCKET="${S3_BUCKET:-baixing-backups}"

DATABASES=(
    "baixing_law"
    "user_service"
    "payment_channel"
    "embedding_service"
    "order_service"
    "ai_service"
    "news_service"
    "community_service"
    "legal_service"
    "search_service"
    "recommendation_service"
    "notification_service"
    "points_service"
    "archive_service"
    "knowledge_service"
)

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] === 开始全量数据库备份 ==="
echo "[$(date)] 目标: ${#DATABASES[@]} 个数据库"

SUCCESS_COUNT=0
FAIL_COUNT=0

for DB_NAME in "${DATABASES[@]}"; do
    BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

    echo "[$(date)] 备份: ${DB_NAME}..."

    if pg_dump -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --no-owner \
        --no-privileges \
        2>/dev/null | gzip > "${BACKUP_FILE}"; then

        FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        echo "[$(date)] ✓ ${DB_NAME}: ${FILE_SIZE}"

        if [ "${UPLOAD_S3}" = "true" ]; then
            aws s3 cp "${BACKUP_FILE}" \
                "s3://${S3_BUCKET}/db/${DB_NAME}/${TIMESTAMP}.sql.gz" \
                --endpoint-url "${S3_ENDPOINT_URL:-}" 2>/dev/null && \
                echo "[$(date)]   ↑ S3 上传成功" || \
                echo "[$(date)]   ✗ S3 上传失败"
        fi

        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "[$(date)] ✗ ${DB_NAME}: 备份失败"
        rm -f "${BACKUP_FILE}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo "[$(date)] 清理 ${RETENTION_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "*_${TIMESTAMP_PATTERN:-[0-9]*}.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

echo "[$(date)] === 备份完成: ${SUCCESS_COUNT} 成功, ${FAIL_COUNT} 失败 ==="

if [ "${FAIL_COUNT}" -gt 0 ]; then
    exit 1
fi
