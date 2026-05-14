#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  百姓法律助手 - 全栈启动脚本"
echo "========================================="
echo ""

PROFILE="${1:-all}"

case "$PROFILE" in
    core)
        echo "Starting core services (db/redis/backend/frontend/minio)..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d
        ;;
    infra)
        echo "Starting core + infrastructure services..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" --profile infra up -d
        ;;
    micro)
        echo "Starting core + microservice cluster..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" --profile microservice up -d
        ;;
    all)
        echo "Starting ALL services..."
        docker compose -f "$PROJECT_DIR/docker-compose.yml" --profile infra --profile microservice up -d
        ;;
    *)
        echo "Usage: $0 {core|infra|micro|all}"
        echo ""
        echo "  core   - db, redis, backend, frontend, minio"
        echo "  infra  - core + kafka, monitoring"
        echo "  micro  - core + 15 microservices"
        echo "  all    - everything"
        exit 1
        ;;
esac

echo ""
echo "Waiting for services to be healthy..."

sleep 5

CORE_SERVICES=("db" "redis" "minio" "backend" "frontend")
ALL_OK=true

for svc in "${CORE_SERVICES[@]}"; do
    STATUS=$(docker compose -f "$PROJECT_DIR/docker-compose.yml" ps --format json "$svc" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    echo "  $svc: $STATUS"
done

echo ""
echo "Services started! Access:"
echo "  Frontend:    http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  MinIO:       http://localhost:9001"
echo ""

if [[ "$PROFILE" == "infra" || "$PROFILE" == "all" ]]; then
    echo "  Kafka UI:    http://localhost:8090"
    echo "  Grafana:     http://localhost:3001"
    echo "  Prometheus:  http://localhost:9091"
    echo ""
fi
