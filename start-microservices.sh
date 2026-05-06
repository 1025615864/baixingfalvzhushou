#!/bin/bash
# 微服务启动脚本

set -e

echo "=========================================="
echo "百姓法律助手 - 微服务启动脚本"
echo "=========================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 启动基础设施服务
echo "[1/5] 启动数据库和Redis..."
docker compose up -d db redis

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 启动Kafka
echo "[2/5] 启动Kafka..."
docker compose -f docker-compose.microservices.yml up -d zookeeper kafka kafka-ui

# 等待Kafka就绪
echo "等待Kafka就绪..."
sleep 10

# 启动用户服务
echo "[3/5] 启动用户服务..."
docker compose -f docker-compose.microservices.yml up -d user-service

# 启动AI服务
echo "[4/5] 启动AI服务..."
docker compose -f docker-compose.microservices.yml up -d ai-service

# 启动后端(单体)
echo "[5/5] 启动后端(单体)..."
docker compose up -d backend

echo ""
echo "=========================================="
echo "服务启动完成!"
echo "=========================================="
echo ""
echo "服务地址:"
echo "  - 前端:      http://localhost:3000"
echo "  - Backend:   http://localhost:8000"
echo "  - 用户服务:  http://localhost:8001"
echo "  - AI服务:    http://localhost:8005"
echo "  - Kafka UI:  http://localhost:8090"
echo "  - 数据库:    localhost:5433"
echo "  - Redis:     localhost:16379"
echo ""
echo "查看日志: docker compose logs -f [service-name]"
echo "停止服务: docker compose down"
echo ""
