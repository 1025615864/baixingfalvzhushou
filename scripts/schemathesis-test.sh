#!/bin/bash
# Schemathesis Quick Test Script
# 快速测试 API 的脚本 - 基于 OpenAPI Schema

set -euo pipefail

# 配置
SCHEMATHESIS_SOURCE="${SCHEMATHESIS_SOURCE:-http://localhost:8080/openapi.json}"
BASE_URL="${BASE_URL:-http://localhost:8080}"
OUTPUT_DIR="test-results"
CHECKS="${CHECKS:-all}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v schemathesis &> /dev/null; then
        log_error "schemathesis 未安装，请运行: pip install schemathesis"
        exit 1
    fi

    log_info "schemathesis 版本: $(schemathesis --version)"
}

# 检查服务器是否运行
check_server() {
    log_info "检查服务器可用性: $BASE_URL"

    if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" 2>/dev/null | grep -q "200"; then
        log_info "服务器运行正常"
        return 0
    else
        log_warn "服务器可能未运行或 /health 端点不可用，尝试直接测试..."
        return 0
    fi
}

# 运行完整测试
run_full_test() {
    log_info "运行完整 Schemathesis 测试..."
    log_info "Schema 来源: $SCHEMATHESIS_SOURCE"

    mkdir -p "$OUTPUT_DIR"

    schemathesis run "$SCHEMATHESIS_SOURCE" \
        --checks "$CHECKS" \
        --base-url "$BASE_URL" \
        --validate-schema \
        --verbosity verbose \
        --output-format cli \
        --junit-xml "$OUTPUT_DIR/schemathesis-junit.xml" \
        --json "$OUTPUT_DIR/schemathesis-report.json"
}

# 运行快速测试（仅基础检查）
run_quick_test() {
    log_info "运行快速 Schemathesis 测试..."

    mkdir -p "$OUTPUT_DIR"

    schemathesis run "$SCHEMATHESIS_SOURCE" \
        --checks response_schema,status_code \
        --base-url "$BASE_URL" \
        --validate-schema \
        --output-format cli \
        --junit-xml "$OUTPUT_DIR/schemathesis-quick-junit.xml" \
        --json "$OUTPUT_DIR/schemathesis-quick-report.json"
}

# 生成测试报告
generate_report() {
    log_info "生成测试报告..."

    if [ -f "$OUTPUT_DIR/schemathesis-report.json" ]; then
        python3 << 'EOF'
import json
import sys

try:
    with open('test-results/schemathesis-report.json', 'r') as f:
        data = json.load(f)

    print("\n" + "="*60)
    print("Schemathesis API 测试报告")
    print("="*60)

    if 'summary' in data:
        summary = data['summary']
        print(f"总测试数: {summary.get('total', 'N/A')}")
        print(f"通过: {summary.get('passed', 'N/A')}")
        print(f"失败: {summary.get('failed', 'N/A')}")
        print(f"跳过: {summary.get('skipped', 'N/A')}")

    print("="*60)
except Exception as e:
    print(f"无法生成报告: {e}")
    sys.exit(1)
EOF
    else
        log_warn "未找到测试报告文件"
    fi
}

# 显示帮助信息
show_help() {
    echo "Schemathesis Quick Test Script"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  full      运行完整测试 (默认)"
    echo "  quick     运行快速测试"
    echo "  report    生成测试报告"
    echo "  help      显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  SCHEMATHESIS_SOURCE  OpenAPI schema 来源 (默认: http://localhost:8080/openapi.json)"
    echo "  BASE_URL             API 基础 URL (默认: http://localhost:8080)"
    echo "  CHECKS               检查类型 (默认: all)"
    echo ""
    echo "示例:"
    echo "  $0 full                    # 运行完整测试"
    echo "  SCHEMATHESIS_SOURCE=http://example.com/openapi.json $0 quick  # 快速测试"
}

# 主函数
main() {
    case "${1:-full}" in
        full)
            check_dependencies
            check_server
            run_full_test
            ;;
        quick)
            check_dependencies
            check_server
            run_quick_test
            ;;
        report)
            generate_report
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
