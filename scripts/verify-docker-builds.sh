#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SERVICES=(
  "backend"
  "user-service"
  "community-service"
  "legal-service"
  "ai-service"
  "embedding-service"
  "news-service"
  "order-service"
  "notification-service"
  "payment-channel-service"
  "points-service"
  "recommendation-service"
  "search-service"
  "knowledge-service"
)

TOTAL_PASS=0
TOTAL_FAIL=0

print_status() {
  local ok=$1
  if [ "$ok" = "1" ]; then
    echo -ne "${GREEN}  OK  ${NC}"
  elif [ "$ok" = "2" ]; then
    echo -ne "${YELLOW}EMPTY${NC}"
  else
    echo -ne "${RED}MISS ${NC}"
  fi
}

echo "========================================"
echo "  Docker 构建验证"
echo "========================================"
echo ""

printf "%-26s| %-10s| %-14s| %-12s\n" "SERVICE" "DOCKERFILE" "REQ.TXT" ".ENV.EXAMPLE"
printf "%-26s+-%-10s+-%-14s+-%-12s\n" "--------------------------" "----------" "--------------" "------------"

for svc in "${SERVICES[@]}"; do
  if [ "$svc" = "backend" ]; then
    svc_dir="${PROJECT_ROOT}/backend"
  else
    svc_dir="${PROJECT_ROOT}/services/${svc}"
  fi

  df_ok=0
  req_ok=0
  env_ok=0

  if [ -f "${svc_dir}/Dockerfile" ]; then
    df_ok=1
    ((TOTAL_PASS++))
  else
    ((TOTAL_FAIL++))
  fi

  if [ -f "${svc_dir}/requirements.txt" ]; then
    if [ -s "${svc_dir}/requirements.txt" ]; then
      req_ok=1
      ((TOTAL_PASS++))
    else
      req_ok=2
      ((TOTAL_FAIL++))
    fi
  else
    ((TOTAL_FAIL++))
  fi

  if [ -f "${svc_dir}/.env.example" ]; then
    env_ok=1
    ((TOTAL_PASS++))
  else
    ((TOTAL_FAIL++))
  fi

  printf "%-26s| " "$svc"
  print_status $df_ok
  printf "| "
  print_status $req_ok
  printf "| "
  print_status $env_ok
  echo ""
done

echo ""
echo "========================================"
echo -e "  Docker Compose 构建检查"
echo "========================================"
echo ""

if [ -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
  echo -e "${YELLOW}执行 docker-compose build...${NC}"
  if docker compose -f "${PROJECT_ROOT}/docker-compose.yml" build 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose build 成功"
    ((TOTAL_PASS++))
  else
    echo -e "${RED}✗${NC} docker-compose build 失败"
    ((TOTAL_FAIL++))
  fi
else
  echo -e "${RED}✗${NC} docker-compose.yml 未找到"
  ((TOTAL_FAIL++))
fi

echo ""
echo "========================================"
echo -e "  总计: ${GREEN}通过 ${TOTAL_PASS}${NC} | ${RED}失败 ${TOTAL_FAIL}${NC}"
echo "========================================"

if [ "$TOTAL_FAIL" -gt 0 ]; then
  exit 1
fi

exit 0
