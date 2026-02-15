#!/bin/bash
# 自动化备份脚本
# 定期备份数据库、Redis和静态资源

set -e

# 配置
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR/db"
mkdir -p "$BACKUP_DIR/redis"
mkdir -p "$BACKUP_DIR/static"

# 数据库备份
echo "[$(date)] Starting database backup..."
if [ "$DATABASE_URL" == *"postgresql"* ]; then
    # PostgreSQL备份
    pg_dump "$DATABASE_URL" -f "$BACKUP_DIR/db/postgres_${TIMESTAMP}.sql"
    echo "[$(date)] PostgreSQL backup completed: postgres_${TIMESTAMP}.sql"
elif [ "$DATABASE_URL" == *"sqlite"* ]; then
    # SQLite备份
    DB_PATH=$(echo "$DATABASE_URL" | sed 's/.*:\/\/\///')
    cp "$DB_PATH" "$BACKUP_DIR/db/sqlite_${TIMESTAMP}.db"
    echo "[$(date)] SQLite backup completed: sqlite_${TIMESTAMP}.db"
fi

# Redis备份
echo "[$(date)] Starting Redis backup..."
if [ -n "$REDIS_URL" ]; then
    redis-cli -u "$REDIS_URL" BGSAVE
    redis-cli -u "$REDIS_URL" LASTSAVE
    echo "[$(date)] Redis backup completed"
fi

# 清理过期备份
echo "[$(date)] Cleaning old backups..."
find "$BACKUP_DIR" -name "*.sql" -o -name "*.db" -o -name "*.dump" | while read -r file; do
    if [ $(($(date +%s) - $(stat -c %Y "$file"))) -gt $((RETENTION_DAYS * 86400)) ]; then
        rm "$file"
        echo "[$(date)] Removed old backup: $file"
    fi
done

echo "[$(date)] Backup completed successfully"
