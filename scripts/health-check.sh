#!/bin/bash
# ==========================================
# 服务健康检查脚本
# 用法：
#   ./scripts/health-check.sh         # 检查完整微服务集群
#   ./scripts/health-check.sh --dev   # 仅检查开发环境核心服务
# ==========================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 开发模式标志
DEV_MODE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        *)
            echo "用法：$0 [--dev]"
            echo "  --dev  仅检查开发环境核心服务"
            exit 1
            ;;
    esac
done

check_http_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    if curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name: $url"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name: $url (不可达)"
        return 1
    fi
}

check_tcp_service() {
    local name=$1
    local host=$2
    local port=$3
    local timeout=${4:-3}
    
    if timeout $timeout bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name: $host:$port"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name: $host:$port (不可达)"
        return 1
    fi
}

echo "========================================"
echo "  百姓法律助手 - 服务健康检查"
if [ "$DEV_MODE" = true ]; then
    echo "  (开发环境模式)"
fi
echo "========================================"
echo ""

echo -e "${BLUE}核心服务：${NC}"
check_tcp_service "PostgreSQL" "localhost" "5433" || true
check_tcp_service "Redis" "localhost" "16379" || true
check_http_service "Backend API" "http://localhost:8000/health"
check_http_service "Frontend" "http://localhost:3000"
echo ""

if [ "$DEV_MODE" = false ]; then
    echo -e "${BLUE}微服务集群：${NC}"
    check_http_service "法律服务 (8008)" "http://localhost:8008/health"
    check_http_service "社区服务 (8007)" "http://localhost:8007/health"
    check_http_service "新闻服务 (8006)" "http://localhost:8006/health"
    check_http_service "搜索服务 (8009)" "http://localhost:8009/health"
    check_http_service "推荐服务 (8010)" "http://localhost:8010/health"
    check_http_service "通知服务 (8005)" "http://localhost:8005/health"
    check_http_service "用户服务 (8001)" "http://localhost:8001/health"
    check_http_service "订单服务 (8004)" "http://localhost:8004/health"
    check_http_service "积分服务 (8012)" "http://localhost:8012/health"
    check_http_service "知识库服务 (8081)" "http://localhost:8081/health"
    check_http_service "归档服务 (8013)" "http://localhost:8013/health"
    echo ""
    
    echo -e "${BLUE}监控系统：${NC}"
    check_http_service "Prometheus" "http://localhost:19090/-/healthy"
    check_http_service "Grafana" "http://localhost:3001/api/health"
    check_http_service "Alertmanager" "http://localhost:9200/-/healthy"
    echo ""
fi

echo "========================================"
echo "检查完成"
echo "========================================"
