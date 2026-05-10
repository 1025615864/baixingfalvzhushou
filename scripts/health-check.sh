#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICES=(
  "backend:8000:/health"
  "user-service:8001:/health"
  "community-service:8003:/health"
  "legal-service:8004:/health"
  "ai-service:8005:/health"
  "embedding-service:8006:/health"
  "news-service:8007:/health"
  "order-service:8008:/health"
  "notification-service:8009:/health"
  "payment-channel-service:8010:/health"
  "points-service:8011:/health"
  "recommendation-service:8012:/health"
  "search-service:8013:/health"
  "knowledge-service:8006:/api/health"
)

ENDPOINTS=("/health" "/health/live" "/health/ready")

FAIL_COUNT=0
DEGRADED_COUNT=0

check_endpoint() {
  local name=$1
  local port=$2
  local path=$3
  local url="http://localhost:${port}${path}"

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)

  if [ "$http_code" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} ${name} ${path} (HTTP ${http_code})"
    return 0
  elif [ "$http_code" = "503" ] || [ "$http_code" = "000" ]; then
    echo -e "  ${RED}✗${NC} ${name} ${path} (HTTP ${http_code})"
    return 1
  else
    echo -e "  ${YELLOW}⚠${NC} ${name} ${path} (HTTP ${http_code})"
    return 2
  fi
}

echo "========================================"
echo "  百姓法律助手 - 微服务健康检查"
echo "========================================"
echo ""

for svc in "${SERVICES[@]}"; do
  IFS=':' read -r name port base_path <<< "$svc"
  echo -e "\e[1m${name} (port ${port})\e[0m"

  for ep in "${ENDPOINTS[@]}"; do
    check_endpoint "$name" "$port" "$ep"
    case $? in
      1) ((FAIL_COUNT++)) ;;
      2) ((DEGRADED_COUNT++)) ;;
    esac
  done
  echo ""
done

echo "========================================"
echo -e "  结果: ${GREEN}通过${NC} | ${YELLOW}降级: ${DEGRADED_COUNT}${NC} | ${RED}失败: ${FAIL_COUNT}${NC}"
echo "========================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi

exit 0
