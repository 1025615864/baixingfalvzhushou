#!/bin/bash
# ============================================
# 微服务联调测试脚本
# ============================================

set -e

BASE_URL="${BASE_URL:-http://localhost}"
PASS=0
FAIL=0

echo "=========================================="
echo "微服务联调测试"
echo "=========================================="

# 测试函数
test_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        echo "✓ PASS (HTTP $response)"
        ((PASS++))
    else
        echo "✗ FAIL (HTTP $response, expected $expected_code)"
        ((FAIL++))
    fi
}

# 测试后端主服务
echo ""
echo "--- 后端主服务 (8000) ---"
test_service "Backend Health" "$BASE_URL:8000/health"
test_service "Backend API v1" "$BASE_URL:8000/api/v1/home/recommendations" "404"

echo ""
echo "--- 用户服务 (8001) ---"
test_service "User Service Health" "$BASE_URL:8001/health"
test_service "User Service Auth" "$BASE_URL:8001/api/v1/auth/login" "422"

echo ""
echo "--- 支付通道服务 (8002) ---"
test_service "Payment Channel Service Health" "$BASE_URL:8002/health"
test_service "Payment Channel Service Orders" "$BASE_URL:8002/api/v1/payment/orders" "422"

echo ""
echo "--- 向量嵌入服务 (8003) ---"
test_service "Embedding Service Health" "$BASE_URL:8003/health"

echo ""
echo "--- 订单服务 (8004) ---"
test_service "Order Service Health" "$BASE_URL:8004/health"

echo ""
echo "--- AI服务 (8005) ---"
test_service "AI Service Health" "$BASE_URL:8005/health"
test_service "AI Service Chat" "$BASE_URL:8005/api/v1/ai/chat" "422"

echo ""
echo "--- 新闻服务 (8006) ---"
test_service "News Service Health" "$BASE_URL:8006/health"
test_service "News Service List" "$BASE_URL:8006/api/v1/news" "422"

echo ""
echo "--- 社区服务 (8007) ---"
test_service "Community Service Health" "$BASE_URL:8007/health"
test_service "Community Service Posts" "$BASE_URL:8007/api/v1/community/posts" "422"

echo ""
echo "--- 法律服务 (8008) ---"
test_service "Legal Service Health" "$BASE_URL:8008/health"
test_service "Legal Service Lawyers" "$BASE_URL:8008/api/v1/legal/lawyers" "422"

echo ""
echo "--- 搜索服务 (8009) ---"
test_service "Search Service Health" "$BASE_URL:8009/health"
test_service "Search Service Global" "$BASE_URL:8009/api/v1/search" "422"

echo ""
echo "--- 推荐服务 (8010) ---"
test_service "Recommendation Service Health" "$BASE_URL:8010/health"

echo ""
echo "--- 通知服务 (8011) ---"
test_service "Notification Service Health" "$BASE_URL:8011/health"

echo ""
echo "--- 积分服务 (8012) ---"
test_service "Points Service Health" "$BASE_URL:8012/health"

# 测试前端代理
echo ""
echo "--- 前端代理 (通过nginx/dev server) ---"
test_service "Frontend API Root" "$BASE_URL:5173/api" "404" # 预期404但服务正常
test_service "Frontend API v1" "$BASE_URL:5173/api/v1" "404" # 预期404但服务正常

echo ""
echo "=========================================="
echo "测试结果: $PASS 通过, $FAIL 失败"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
exit 0
