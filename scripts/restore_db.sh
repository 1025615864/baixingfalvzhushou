#!/bin/bash
set -euo pipefail

BACKUP_FILE="${1:?用法: restore_db.sh <backup_file.sql.gz> [database_name]}"
DB_NAME="${2:-}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"

if [ -z "${DB_NAME}" ]; then
    DB_NAME=$(basename "${BACKUP_FILE}" | sed 's/_[0-9]\{8\}_[0-9]\{6\}\.sql\.gz$//')
fi

echo "[$(date)] === 数据库恢复 ==="
echo "[$(date)] 文件: ${BACKUP_FILE}"
echo "[$(date)] 目标: ${DB_NAME}@${DB_HOST}:${DB_PORT}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[$(date)] ✗ 备份文件不存在: ${BACKUP_FILE}" >&2
    exit 1
fi

echo "[$(date)] 检查数据库是否存在..."
if ! psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "${DB_NAME}"; then
    echo "[$(date)] 创建数据库: ${DB_NAME}"
    createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" 2>/dev/null || true
fi

echo "[$(date)] 终止活跃连接..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

echo "[$(date)] 恢复中..."
gunzip -c "${BACKUP_FILE}" | pg_restore \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    2>/dev/null || true

echo "[$(date)] ✓ 恢复完成: ${DB_NAME}"
