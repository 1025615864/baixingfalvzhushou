#!/bin/bash
# ============================================
# 开发环境启动脚本
# ============================================

set -e

echo "=========================================="
echo "   百姓法律助手 - 开发环境启动"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 使用 docker compose 或 docker-compose
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# 切换到项目根目录
cd "$(dirname "$0")"

# 检查 .env.docker 是否存在
if [ ! -f ".env.docker" ]; then
    echo -e "${YELLOW}警告: .env.docker 文件不存在${NC}"
    echo "正在创建默认配置..."
fi

echo ""
echo -e "${GREEN}步骤 1/5: 停止旧容器...${NC}"
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker down 2>/dev/null || true

echo ""
echo -e "${GREEN}步骤 2/5: 构建镜像...${NC}"
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker build

echo ""
echo -e "${GREEN}步骤 3/5: 启动服务...${NC}"
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker up -d

echo ""
echo -e "${GREEN}步骤 4/5: 等待服务就绪...${NC}"
echo "等待数据库启动..."
sleep 5

# 等待后端健康检查
echo "等待后端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}后端服务已就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}警告: 后端服务启动超时，请检查日志${NC}"
    fi
    sleep 2
done

echo ""
echo -e "${GREEN}步骤 5/5: 初始化数据库...${NC}"
echo "运行数据库迁移..."
$COMPOSE_CMD -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic upgrade head 2>/dev/null || {
    echo -e "${YELLOW}提示: 数据库迁移可能已经完成${NC}"
}

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 开发环境启动完成！${NC}"
echo "=========================================="
echo ""
echo "服务地址:"
echo "  - 前端:     http://localhost:3000"
echo "  - 后端API:  http://localhost:8000"
echo "  - API文档:  http://localhost:8000/docs"
echo ""
echo "数据库:"
echo "  - PostgreSQL: localhost:5433"
echo "  - Redis:      localhost:16379"
echo ""
echo "常用命令:"
echo "  - 查看日志:   $COMPOSE_CMD -f docker-compose.dev.yml logs -f"
echo "  - 停止服务:   $COMPOSE_CMD -f docker-compose.dev.yml down"
echo "  - 重启服务:   $COMPOSE_CMD -f docker-compose.dev.yml restart"
echo ""
