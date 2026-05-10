#!/bin/bash
# ==========================================
# 百姓法律助手 - 一键启动脚本
# 使用方式：bash scripts/quick-start.sh
# ==========================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_DIR}"

echo "=========================================="
echo "  百姓法律助手 - 一键启动"
echo "=========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请安装 Docker Compose v2"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件并配置正确的密钥："
    echo "   vim .env"
    echo ""
    echo "或者运行密钥生成脚本："
    echo "   bash scripts/generate_secrets.sh"
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查必要环境变量
source .env
if [ -z "${POSTGRES_PASSWORD:-}" ] || [[ "${POSTGRES_PASSWORD}" == *"dev_password"* ]]; then
    echo "⚠️  POSTGRES_PASSWORD 未配置，将使用默认开发密码"
fi

# 停止已存在的容器
echo "🛑 停止已存在的容器..."
docker compose down 2>/dev/null || true

# 启动服务
echo "🚀 启动所有服务..."
docker compose up -d --build

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 30

# 健康检查
echo "🔍 检查服务状态..."
docker compose ps

echo ""
echo "=========================================="
echo "  ✅ 启动完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端：http://localhost:3000"
echo "  后端 API：http://localhost:8000"
echo "  API 文档：http://localhost:8000/docs"
echo "  Prometheus：http://localhost:9090"
echo "  Grafana：http://localhost:3001 (admin/admin)"
echo ""
echo "查看日志：docker compose logs -f"
echo "停止服务：docker compose down"
echo "重启服务：docker compose restart"
echo ""
