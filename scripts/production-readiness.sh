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

TOTAL_CHECKS=8
PASS_COUNT=0
FAIL_COUNT=0

pass_check() {
  echo -e "  ${GREEN}✓ PASS${NC} $1"
  ((PASS_COUNT++))
}

fail_check() {
  echo -e "  ${RED}✗ FAIL${NC} $1"
  ((FAIL_COUNT++))
}

warn_check() {
  echo -e "  ${YELLOW}⚠ WARN${NC} $1"
}

echo "========================================"
echo "  百姓法律助手 - 生产就绪检查"
echo "========================================"
echo ""

echo -e "\e[1mCheck 1: 所有 Dockerfile 是否存在 (14个服务)\e[0m"
DF_MISSING=0
for svc in "${SERVICES[@]}"; do
  if [ "$svc" = "backend" ]; then
    svc_dir="${PROJECT_ROOT}/backend"
  else
    svc_dir="${PROJECT_ROOT}/services/${svc}"
  fi

  if [ -f "${svc_dir}/Dockerfile" ]; then
    echo -e "  ${GREEN}✓${NC} ${svc}/Dockerfile"
  else
    echo -e "  ${RED}✗${NC} ${svc}/Dockerfile 缺失"
    ((DF_MISSING++))
  fi
done

if [ "$DF_MISSING" -eq 0 ]; then
  pass_check "所有 Dockerfile 均存在"
else
  fail_check "缺少 ${DF_MISSING} 个 Dockerfile"
fi
echo ""

echo -e "\e[1mCheck 2: 所有 .env.example 是否存在\e[0m"
ENV_MISSING=0
for svc in "${SERVICES[@]}"; do
  if [ "$svc" = "backend" ]; then
    svc_dir="${PROJECT_ROOT}/backend"
  else
    svc_dir="${PROJECT_ROOT}/services/${svc}"
  fi

  if [ -f "${svc_dir}/.env.example" ]; then
    echo -e "  ${GREEN}✓${NC} ${svc}/.env.example"
  else
    echo -e "  ${RED}✗${NC} ${svc}/.env.example 缺失"
    ((ENV_MISSING++))
  fi
done

if [ "$ENV_MISSING" -eq 0 ]; then
  pass_check "所有 .env.example 均存在"
else
  fail_check "缺少 ${ENV_MISSING} 个 .env.example"
fi
echo ""

echo -e "\e[1mCheck 3: 所有 requirements.txt 是否存在\e[0m"
REQ_MISSING=0
for svc in "${SERVICES[@]}"; do
  if [ "$svc" = "backend" ]; then
    svc_dir="${PROJECT_ROOT}/backend"
  else
    svc_dir="${PROJECT_ROOT}/services/${svc}"
  fi

  if [ -f "${svc_dir}/requirements.txt" ]; then
    if [ -s "${svc_dir}/requirements.txt" ]; then
      echo -e "  ${GREEN}✓${NC} ${svc}/requirements.txt"
    else
      echo -e "  ${YELLOW}⚠${NC} ${svc}/requirements.txt 为空"
      ((REQ_MISSING++))
    fi
  else
    echo -e "  ${RED}✗${NC} ${svc}/requirements.txt 缺失"
    ((REQ_MISSING++))
  fi
done

if [ "$REQ_MISSING" -eq 0 ]; then
  pass_check "所有 requirements.txt 均存在且非空"
else
  fail_check "缺少或为空 ${REQ_MISSING} 个 requirements.txt"
fi
echo ""

echo -e "\e[1mCheck 4: Python 文件中是否存在硬编码密钥\e[0m"
SECRET_PATTERNS=(
  "password\s*=\s*['\"][^'\"]+['\"]"
  "secret_key\s*=\s*['\"][^'\"]+['\"]"
  "api_key\s*=\s*['\"][^'\"]+['\"]"
  "SECRET\s*=\s*['\"][^'\"]+['\"]"
)

SECRET_FOUND=0
for pattern in "${SECRET_PATTERNS[@]}"; do
  matches=$(grep -rnE "$pattern" \
    --include="*.py" \
    "${PROJECT_ROOT}/backend" \
    "${PROJECT_ROOT}/services" \
    2>/dev/null \
    | grep -v '\.env\.example' \
    | grep -v 'test_' \
    | grep -v '__pycache__' \
    | grep -v 'os\.environ' \
    | grep -v 'getenv' \
    | grep -v 'settings\.py' \
    | grep -v 'config\.py' \
    || true)

  if [ -n "$matches" ]; then
    echo -e "  ${RED}✗${NC} 发现匹配模式: ${pattern}"
    echo "$matches" | head -5 | while read -r line; do
      echo -e "    ${RED}${line}${NC}"
    done
    ((SECRET_FOUND++))
  else
    echo -e "  ${GREEN}✓${NC} 模式安全: ${pattern}"
  fi
done

if [ "$SECRET_FOUND" -eq 0 ]; then
  pass_check "未发现硬编码密钥"
else
  fail_check "发现 ${SECRET_FOUND} 种硬编码密钥模式"
fi
echo ""

echo -e "\e[1mCheck 5: .gitignore 是否排除 .env 文件\e[0m"
GITIGNORE="${PROJECT_ROOT}/.gitignore"

if [ -f "$GITIGNORE" ]; then
  if grep -qE '^\.env$' "$GITIGNORE" || grep -qE '^\.env\b' "$GITIGNORE"; then
    echo -e "  ${GREEN}✓${NC} .gitignore 包含 .env 排除规则"
    pass_check ".gitignore 正确排除 .env 文件"
  else
    echo -e "  ${RED}✗${NC} .gitignore 未排除 .env 文件"
    fail_check ".gitignore 未排除 .env 文件"
  fi
else
  echo -e "  ${RED}✗${NC} .gitignore 文件不存在"
  fail_check ".gitignore 文件不存在"
fi
echo ""

echo -e "\e[1mCheck 6: docker-compose.prod.yml 是否存在且有效\e[0m"
PROD_COMPOSE="${PROJECT_ROOT}/docker-compose.prod.yml"

if [ -f "$PROD_COMPOSE" ]; then
  echo -e "  ${GREEN}✓${NC} docker-compose.prod.yml 存在"

  if docker compose -f "$PROD_COMPOSE" config --quiet 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} docker-compose.prod.yml 语法有效"
    pass_check "docker-compose.prod.yml 存在且有效"
  else
    if command -v docker &>/dev/null; then
      echo -e "  ${RED}✗${NC} docker-compose.prod.yml 语法无效"
      fail_check "docker-compose.prod.yml 语法无效"
    else
      echo -e "  ${YELLOW}⚠${NC} Docker 未安装，跳过语法验证"
      warn_check "Docker 未安装，无法验证 docker-compose.prod.yml 语法"
      pass_check "docker-compose.prod.yml 存在（语法未验证）"
    fi
  fi
else
  echo -e "  ${RED}✗${NC} docker-compose.prod.yml 不存在"
  fail_check "docker-compose.prod.yml 不存在"
fi
echo ""

echo -e "\e[1mCheck 7: Kubernetes Helm Chart 是否存在\e[0m"
HELM_DIR="${PROJECT_ROOT}/helm/baixing-assistant"

if [ -f "${HELM_DIR}/Chart.yaml" ]; then
  echo -e "  ${GREEN}✓${NC} ${HELM_DIR}/Chart.yaml 存在"
else
  echo -e "  ${RED}✗${NC} Chart.yaml 不存在"
fi

if [ -f "${HELM_DIR}/values.yaml" ]; then
  echo -e "  ${GREEN}✓${NC} ${HELM_DIR}/values.yaml 存在"
else
  echo -e "  ${RED}✗${NC} values.yaml 不存在"
fi

if [ -f "${HELM_DIR}/Chart.yaml" ] && [ -f "${HELM_DIR}/values.yaml" ]; then
  pass_check "Helm Chart 文件完整"
else
  fail_check "Helm Chart 文件不完整"
fi
echo ""

echo -e "\e[1mCheck 8: 监控配置是否存在 (Prometheus / Grafana)\e[0m"
PROM_DIR="${PROJECT_ROOT}/prometheus"
GRAFANA_DIR="${PROJECT_ROOT}/backend/grafana"

MONITORING_OK=true

if [ -f "${PROM_DIR}/prometheus.yml" ]; then
  echo -e "  ${GREEN}✓${NC} prometheus/prometheus.yml 存在"
else
  echo -e "  ${RED}✗${NC} prometheus/prometheus.yml 缺失"
  MONITORING_OK=false
fi

if [ -f "${PROM_DIR}/alerts.yml" ]; then
  echo -e "  ${GREEN}✓${NC} prometheus/alerts.yml 存在"
else
  echo -e "  ${RED}✗${NC} prometheus/alerts.yml 缺失"
  MONITORING_OK=false
fi

if [ -f "${GRAFANA_DIR}/baixing_dashboard.json" ]; then
  echo -e "  ${GREEN}✓${NC} backend/grafana/baixing_dashboard.json 存在"
else
  echo -e "  ${RED}✗${NC} backend/grafana/baixing_dashboard.json 缺失"
  MONITORING_OK=false
fi

if [ "$MONITORING_OK" = true ]; then
  pass_check "监控配置完整"
else
  fail_check "监控配置不完整"
fi
echo ""

echo "========================================"
echo -e "  生产就绪检查结果"
echo "========================================"
echo -e "  检查项: ${TOTAL_CHECKS}"
echo -e "  ${GREEN}通过: ${PASS_COUNT}${NC}"
echo -e "  ${RED}失败: ${FAIL_COUNT}${NC}"
echo "========================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi

exit 0
