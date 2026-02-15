#!/bin/bash
# 安全扫描脚本

set -e

echo "Starting security scan..."

# 运行bandit安全扫描
echo "Running bandit security scan..."
bandit -r backend -f json -o bandit_report.json || true
bandit -r backend -f txt -o bandit_report.txt || true

# 运行safety依赖安全扫描
echo "Running safety dependency scan..."
safety check --json > safety_report.json || true
safety check > safety_report.txt || true

# 检查结果
if [ -f bandit_report.txt ]; then
    echo "=== Bandit Report ==="
    cat bandit_report.txt
fi

if [ -f safety_report.txt ]; then
    echo "=== Safety Report ==="
    cat safety_report.txt
fi

echo "Security scan completed"
