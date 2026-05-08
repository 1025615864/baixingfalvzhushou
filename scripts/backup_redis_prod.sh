#!/bin/bash
# ==========================================
# 生产环境 Redis 自动备份脚本
# 使用方式：添加到 crontab，每小时执行
# 0 * * * * /opt/baixing-assistant/scripts/backup_redis_prod.sh
# ==========================================

set -euo pipefail

BACKUP_DIR="/opt/baixing-backups/redis"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD}"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] 开始 Redis 备份..."

# 触发 BGSAVE
if [ -n "${REDIS_PASSWORD}" ]; then
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" BGSAVE 2>/dev/null || true
else
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" BGSAVE 2>/dev/null || true
fi

# 等待 BGSAVE 完成
sleep 5

# 获取 RDB 文件路径
RDB_DIR=$(if [ -n "${REDIS_PASSWORD}" ]; then
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" CONFIG GET dir 2>/dev/null | tail -1
else
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" CONFIG GET dir 2>/dev/null | tail -1
fi)

RDB_FILE="${RDB_DIR}/dump.rdb"

# 复制 RDB 文件
if [ -f "${RDB_FILE}" ]; then
    cp "${RDB_FILE}" "${BACKUP_FILE}"
    echo "[$(date)] 备份完成: ${BACKUP_FILE}"
else
    # 尝试通过 DEBUG SAVE 备份
    if [ -n "${REDIS_PASSWORD}" ]; then
        redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" DEBUG SAVE 2>/dev/null || true
    else
        redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" DEBUG SAVE 2>/dev/null || true
    fi
    echo "[$(date)] 使用 DEBUG SAVE 备份"
fi

# 清理过期备份
echo "[$(date)] 清理 ${RETENTION_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "redis_*.rdb" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Redis 备份完成"
