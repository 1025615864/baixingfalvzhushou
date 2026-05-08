#!/bin/bash
# ==========================================
# 生产环境数据库自动备份脚本
# 使用方式：添加到 crontab，每天 2:00 执行
# 0 2 * * * /opt/baixing-assistant/scripts/backup_db_prod.sh
# ==========================================

set -euo pipefail

# 配置
BACKUP_DIR="/opt/baixing-backups/db"
DB_NAME="${POSTGRES_DB:-baixing_law}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] 开始数据库备份: ${DB_NAME}"

# 执行备份
pg_dump -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --verbose \
        --no-owner \
        --no-privileges \
        | gzip > "${BACKUP_FILE}"

# 检查备份是否成功
if [ -f "${BACKUP_FILE}" ]; then
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] 备份完成: ${BACKUP_FILE} (${FILE_SIZE})"
else
    echo "[$(date)] ❌ 备份失败！" >&2
    exit 1
fi

# 清理过期备份
echo "[$(date)] 清理 ${RETENTION_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] 数据库备份完成"
