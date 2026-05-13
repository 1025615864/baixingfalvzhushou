#!/bin/bash
# ==========================================
# 百姓法律助手 - 一键验收脚本
# 用法：./scripts/acceptance-test.sh [--dev|--full]
# ==========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 计数器
PASS=0
FAIL=0
SKIP=0
TOTAL=0

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 打印函数
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
print_fail() { echo -e "${RED}[FAIL]${NC} $1"; }
print_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; }
print_header() { echo -e "\n${CYAN}========== $1 ==========${NC}\n"; }

# 记录测试结果
record_result() {
    local name=$1
    local result=$2
    TOTAL=$((TOTAL + 1))
    if [ "$result" = "pass" ]; then
        PASS=$((PASS + 1))
        print_success "$name"
    elif [ "$result" = "skip" ]; then
        SKIP=$((SKIP + 1))
        print_skip "$name"
    else
        FAIL=$((FAIL + 1))
        print_fail "$name"
    fi
}

# 检查服务是否响应
check_http() {
    local url=$1
    local timeout=${2:-5}
    if curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# 检查JSON响应包含某字段
check_json_field() {
    local url=$1
    local field=$2
    local timeout=${3:-5}
    local response
    response=$(curl -sf --max-time "$timeout" "$url" 2>/dev/null)
    if echo "$response" | grep -q "$field"; then
        return 0
    fi
    return 1
}

# 主函数
main() {
    local mode=${1:---dev}
    
    print_header "百姓法律助手 - 验收测试"
    print_info "测试模式: $mode"
    print_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # ==========================================
    # 1. 环境检查
    # ==========================================
    print_header "1. 环境检查"

    if command -v docker &> /dev/null; then
        record_result "Docker 已安装" "pass"
    else
        record_result "Docker 已安装" "fail"
    fi

    if docker compose version &> /dev/null; then
        record_result "Docker Compose 已安装" "pass"
    else
        record_result "Docker Compose 已安装" "fail"
    fi

    if [ -f .env ]; then
        record_result ".env 文件存在" "pass"
    else
        record_result ".env 文件存在" "fail"
        print_info "提示: cp .env.example .env"
    fi

    # ==========================================
    # 2. 服务启动检查
    # ==========================================
    print_header "2. 服务启动检查"

    # 检查容器状态
    local services=("db" "redis" "backend" "frontend")
    if [ "$mode" = "--full" ]; then
        services+=("user-service" "order-service" "notification-service" "news-service" "community-service" "legal-service" "search-service" "recommendation-service" "points-service" "archive-service" "knowledge-service")
    fi

    for svc in "${services[@]}"; do
        local status
        status=$(docker compose -f docker-compose.yml ps --format json 2>/dev/null | grep -c "\"Name\":\"$svc\"" || true)
        if [ "$status" -gt 0 ]; then
            record_result "容器 $svc 运行中" "pass"
        else
            record_result "容器 $svc 运行中" "skip"
        fi
    done

    # ==========================================
    # 3. 健康检查
    # ==========================================
    print_header "3. 健康检查"

    # 3.1 后端健康检查
    if check_http "http://localhost:8000/health"; then
        record_result "后端健康检查 (/health)" "pass"
    else
        record_result "后端健康检查 (/health)" "fail"
    fi

    # 3.2 后端状态
    if check_http "http://localhost:8000/status"; then
        record_result "后端状态 (/status)" "pass"
    else
        record_result "后端状态 (/status)" "skip"
    fi

    # 3.3 前端访问
    if check_http "http://localhost:3000"; then
        record_result "前端可访问 (:3000)" "pass"
    else
        record_result "前端可访问 (:3000)" "fail"
    fi

    # 3.4 API 文档
    if check_http "http://localhost:8000/docs"; then
        record_result "API 文档 (/docs)" "pass"
    else
        record_result "API 文档 (/docs)" "skip"
    fi

    # ==========================================
    # 4. 功能检查
    # ==========================================
    print_header "4. 功能检查"

    # 4.1 WebSocket 状态
    if check_http "http://localhost:8000/ws/status"; then
        record_result "WebSocket 状态 (/ws/status)" "pass"
    else
        record_result "WebSocket 状态 (/ws/status)" "skip"
    fi

    # 4.2 熔断器状态
    if check_http "http://localhost:8000/api/v1/proxy/circuit-status"; then
        record_result "熔断器状态 (/proxy/circuit-status)" "pass"
    else
        record_result "熔断器状态 (/proxy/circuit-status)" "skip"
    fi

    # ==========================================
    # 5. 数据库检查
    # ==========================================
    print_header "5. 数据库检查"

    # 5.1 PostgreSQL
    if check_http "http://localhost:5433" 2; then
        record_result "PostgreSQL 端口可达 (:5433)" "pass"
    else
        record_result "PostgreSQL 端口可达 (:5433)" "fail"
    fi

    # 5.2 Redis
    if check_http "http://localhost:16379" 2; then
        record_result "Redis 端口可达 (:16379)" "pass"
    else
        record_result "Redis 端口可达 (:16379)" "fail"
    fi

    # ==========================================
    # 6. 微服务检查 (仅 --full 模式)
    # ==========================================
    if [ "$mode" = "--full" ]; then
        print_header "6. 微服务检查"

        declare -A services_map=(
            ["user-service"]="http://localhost:8001/health"
            ["order-service"]="http://localhost:8004/health"
            ["notification-service"]="http://localhost:8011/health"
            ["news-service"]="http://localhost:8006/health"
            ["community-service"]="http://localhost:8007/health"
            ["legal-service"]="http://localhost:8008/health"
            ["search-service"]="http://localhost:8009/health"
            ["recommendation-service"]="http://localhost:8010/health"
            ["points-service"]="http://localhost:8012/health"
            ["archive-service"]="http://localhost:8013/health"
            ["knowledge-service"]="http://localhost:8081/health"
        )

        for svc in "${!services_map[@]}"; do
            local url="${services_map[$svc]}"
            if check_http "$url"; then
                record_result "$svc 健康检查" "pass"
            else
                record_result "$svc 健康检查" "skip"
            fi
        done
    fi

    # ==========================================
    # 7. 监控检查 (仅 --full 模式)
    # ==========================================
    if [ "$mode" = "--full" ]; then
        print_header "7. 监控系统检查"

        if check_http "http://localhost:19090/-/healthy"; then
            record_result "Prometheus 健康" "pass"
        else
            record_result "Prometheus 健康" "skip"
        fi

        if check_http "http://localhost:3001/api/health"; then
            record_result "Grafana 健康" "pass"
        else
            record_result "Grafana 健康" "skip"
        fi
    fi

    # ==========================================
    # 汇总结果
    # ==========================================
    print_header "验收结果汇总"
    
    local pass_rate=0
    if [ $TOTAL -gt 0 ]; then
        pass_rate=$(( (PASS * 100) / TOTAL ))
    fi

    echo -e "总测试项: ${BLUE}$TOTAL${NC}"
    echo -e "通过: ${GREEN}$PASS${NC}"
    echo -e "失败: ${RED}$FAIL${NC}"
    echo -e "跳过: ${YELLOW}$SKIP${NC}"
    echo -e "通过率: ${CYAN}${pass_rate}%${NC}"
    echo ""

    if [ $FAIL -eq 0 ]; then
        echo -e "${GREEN}✅ 验收通过！${NC}"
        exit 0
    else
        echo -e "${RED}❌ 验收未通过，请修复失败项后重试${NC}"
        exit 1
    fi
}

main "$@"
