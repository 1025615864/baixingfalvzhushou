# 安全扫描脚本（Windows PowerShell）

$ErrorActionPreference = "Continue"

Write-Host "Starting security scan..."

# 运行bandit安全扫描
Write-Host "Running bandit security scan..."
try {
    bandit -r backend -f json -o bandit_report.json | Out-Null
    bandit -r backend -f txt -o bandit_report.txt | Out-Null
} catch {
    Write-Host "Bandit scan failed: $_"
}

# 运行safety依赖安全扫描
Write-Host "Running safety dependency scan..."
try {
    safety check --json > safety_report.json | Out-Null
    safety check > safety_report.txt | Out-Null
} catch {
    Write-Host "Safety scan failed: $_"
}

# 检查结果
if (Test-Path bandit_report.txt) {
    Write-Host "=== Bandit Report ==="
    Get-Content bandit_report.txt
}

if (Test-Path safety_report.txt) {
    Write-Host "=== Safety Report ==="
    Get-Content safety_report.txt
}

Write-Host "Security scan completed"
