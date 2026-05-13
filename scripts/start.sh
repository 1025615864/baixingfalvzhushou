#!/bin/bash
# ==========================================
# 百姓法律助手 - 项目启动脚本
# 用法：
#   ./scripts/start.sh              # 启动完整微服务集群
#   ./scripts/start.sh --dev        # 启动开发环境（仅核心服务）
#   ./scripts/start.sh --stop       # 停止所有服务
#   ./scripts/start.sh --logs       # 查看日志
# ==========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请安装 Docker Compose v2"
        exit 1
    fi
    
    print_success "Docker $(docker --version) 已安装"
    print_success "Docker Compose $(docker compose version --short) 已安装"
}

# 检查 .env 文件
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，正在创建..."
        cp .env.example .env
        print_success ".env 文件已创建"
        echo ""
        print_warning "请编辑 .env 文件并配置正确的密钥："
        print_warning "   vim .env 或 notepad .env"
        echo ""
        print_info "或者运行以下命令生成随机密钥："
        print_info "   bash scripts/generate_secrets.sh"
        echo ""
        read -p "是否继续？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 停止所有服务
stop_services() {
    print_info "停止所有服务..."
    docker compose -f docker-compose.yml down
    print_success "所有服务已停止"
}

# 查看日志
view_logs() {
    print_info "查看服务日志..."
    docker compose -f docker-compose.yml logs -f
}

# 启动开发环境
start_dev() {
    print_info "启动开发环境（核心服务）..."
    print_info "包含：PostgreSQL, Redis, Backend, Frontend"
    echo ""
    
    docker compose -f docker-compose.dev.yml up -d --build
    
    print_success "开发环境已启动！"
    echo ""
    print_info "服务访问地址："
    print_info "  前端：http://localhost:3000"
    print_info "  后端 API：http://localhost:8000"
    print_info "  后端健康检查：http://localhost:8000/health"
    print_info "  PostgreSQL：localhost:5433"
    print_info "  Redis：localhost:16379"
    echo ""
    print_info "查看日志：docker compose -f docker-compose.dev.yml logs -f"
    print_info "停止服务：docker compose -f docker-compose.dev.yml down"
}

# 启动完整微服务集群
start_full() {
    print_info "启动完整微服务集群..."
    print_info "包含：PostgreSQL, Redis, Backend, Frontend, 11个微服务, 监控系统"
    echo ""
    
    docker compose -f docker-compose.yml up -d --build
    
    print_success "完整微服务集群已启动！"
    echo ""
    print_info "服务访问地址："
    print_info "  前端：http://localhost:3000"
    print_info "  后端 API：http://localhost:8000"
    print_info "  后端健康检查：http://localhost:8000/health"
    echo ""
    print_info "微服务端口："
    print_info "  法律服务 (legal-service)：http://localhost:8008"
    print_info "  社区服务 (community-service)：http://localhost:8007"
    print_info "  新闻服务 (news-service)：http://localhost:8006"
    print_info "  搜索服务 (search-service)：http://localhost:8009"
    print_info "  推荐服务 (recommendation-service)：http://localhost:8010"
    print_info "  通知服务 (notification-service)：http://localhost:8011"
    print_info "  用户服务 (user-service)：http://localhost:8001"
    print_info "  订单服务 (order-service)：http://localhost:8004"
    print_info "  积分服务 (points-service)：http://localhost:8012"
    print_info "  知识库服务 (knowledge-service)：http://localhost:8081"
    print_info "  归档服务 (archive-service)：http://localhost:8013"
    echo ""
    print_info "监控系统："
    print_info "  Prometheus：http://localhost:19090"
    print_info "  Grafana：http://localhost:3001 (admin/admin123)"
    print_info "  Alertmanager：http://localhost:9200"
    echo ""
    print_info "基础设施："
    print_info "  PostgreSQL：localhost:5433"
    print_info "  Redis：localhost:16379"
    echo ""
    print_info "查看日志：docker compose logs -f [service-name]"
    print_info "停止服务：docker compose down"
}

# 显示帮助
show_help() {
    echo "用法：$0 [选项]"
    echo ""
    echo "选项："
    echo "  --dev       启动开发环境（仅核心服务：PostgreSQL, Redis, Backend, Frontend）"
    echo "  --full      启动完整微服务集群（默认）"
    echo "  --stop      停止所有服务"
    echo "  --logs      查看所有服务日志"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例："
    echo "  $0              # 启动完整微服务集群"
    echo "  $0 --dev        # 启动开发环境"
    echo "  $0 --stop       # 停止所有服务"
    echo "  $0 --logs       # 查看日志"
}

# 主函数
main() {
    case "${1:-}" in
        --dev)
            check_dependencies
            check_env
            start_dev
            ;;
        --full)
            check_dependencies
            check_env
            start_full
            ;;
        --stop)
            check_dependencies
            stop_services
            ;;
        --logs)
            check_dependencies
            view_logs
            ;;
        --help|-h)
            show_help
            ;;
        "")
            check_dependencies
            check_env
            start_full
            ;;
        *)
            print_error "未知选项：$1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
