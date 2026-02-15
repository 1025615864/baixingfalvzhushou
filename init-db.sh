#!/bin/bash
# ============================================
# 数据库初始化脚本
# ============================================

set -e

echo "=========================================="
echo "   百姓法律助手 - 数据库初始化"
echo "=========================================="

# 使用 docker compose 或 docker-compose
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

echo ""
echo "1. 运行数据库迁移..."
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic upgrade head

echo ""
echo "2. 检查迁移状态..."
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic current

echo ""
echo "=========================================="
echo "✅ 数据库初始化完成！"
echo "=========================================="
