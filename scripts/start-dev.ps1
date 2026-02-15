param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [string]$FrontendHost = "127.0.0.1",
  [switch]$SkipInstall,
  [switch]$UseDocker,
  [string]$DockerComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

$venvDir = Join-Path $backendDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $backendDir)) { throw "backend directory not found: $backendDir" }
if (-not (Test-Path $frontendDir)) { throw "frontend directory not found: $frontendDir" }

Write-Host "=========================================="
Write-Host "百姓助手开发环境启动"
Write-Host "=========================================="
Write-Host "Repo: $repoRoot"
Write-Host "Backend: http://${BackendHost}:${BackendPort}"
Write-Host "Frontend: http://${FrontendHost}:${FrontendPort}"
Write-Host "Mode: $(if ($UseDocker) { 'Docker Compose' } else { 'Local' })"
Write-Host "=========================================="

# Docker Compose 模式
if ($UseDocker) {
  Write-Host "检查 Docker Desktop 状态..." -ForegroundColor Cyan

  # 检查 Docker Desktop 是否运行
  $dockerStatus = docker info 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: Docker Desktop 未运行，请启动 Docker Desktop 后重试" -ForegroundColor Yellow
    Write-Host "或者使用本地模式: .\start-dev.ps1 -SkipInstall" -ForegroundColor Yellow
    exit 1
  }

  Write-Host "Docker 运行正常，启动服务..." -ForegroundColor Green

  # 启动 Docker Compose 服务
  $composeCmd = "docker compose -f $DockerComposeFile up -d"
  Write-Host "执行: $composeCmd" -ForegroundColor Cyan

  # 检查 docker compose 版本 (v2 vs v1)
  $dockerComposeVersion = docker compose version 2>&1
  if ($LASTEXITCODE -eq 0) {
    # 使用 docker compose v2
    docker compose -f $DockerComposeFile up -d --build
  } else {
    # 使用 docker-compose v1
    docker-compose -f $DockerComposeFile up -d --build
  }

  Write-Host ""
  Write-Host "服务启动完成！" -ForegroundColor Green
  Write-Host ""
  Write-Host "访问地址:" -ForegroundColor Cyan
  Write-Host "  - 前端: http://localhost:3000"
  Write-Host "  - 后端: http://localhost:8000"
  Write-Host "  - API文档: http://localhost:8000/docs"
  Write-Host "  - Grafana: http://localhost:3001 (admin/admin123)"
  Write-Host "  - Prometheus: http://localhost:19090"
  Write-Host ""
  Write-Host "停止服务: docker compose -f $DockerComposeFile down" -ForegroundColor Yellow
  Write-Host "查看日志: docker compose -f $DockerComposeFile logs -f" -ForegroundColor Yellow

  exit 0
}

# 本地开发模式
if (-not $SkipInstall) {
  if (-not (Test-Path $venvPython)) {
    Write-Host "创建 backend venv: $venvDir" -ForegroundColor Cyan
    & py -m venv $venvDir
  }

  Write-Host "安装 backend 依赖..." -ForegroundColor Cyan
  & $venvPython -m pip install -U pip
  & $venvPython -m pip install -r (Join-Path $backendDir "requirements.txt")

  $nodeModules = Join-Path $frontendDir "node_modules"
  if (-not (Test-Path $nodeModules)) {
    Write-Host "安装 frontend 依赖..." -ForegroundColor Cyan
    & npm --prefix $frontendDir install
  }
}

$proxyTarget = "http://${BackendHost}:${BackendPort}"
$wsProxyTarget = $proxyTarget -replace '^http', 'ws'

$backendCmd = "& '${venvPython}' -m uvicorn app.main:app --reload --host ${BackendHost} --port ${BackendPort}"
$frontendCmd = "`$env:VITE_PROXY_TARGET='${proxyTarget}'; `$env:VITE_WS_PROXY_TARGET='${wsProxyTarget}'; npm --prefix '${frontendDir}' run dev -- --host ${FrontendHost} --port ${FrontendPort}"

Write-Host ""
Write-Host "启动 backend..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
  "-NoExit",
  "-Command",
  $backendCmd
) -WorkingDirectory $backendDir

Write-Host "启动 frontend..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList @(
  "-NoExit",
  "-Command",
  $frontendCmd
) -WorkingDirectory $repoRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "开发环境启动完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "关闭两个弹出窗口即可停止服务" -ForegroundColor Yellow
Write-Host ""
Write-Host "使用 Docker 模式:" -ForegroundColor Cyan
Write-Host "  .\start-dev.ps1 -UseDocker" -ForegroundColor White
Write-Host "  .\start-dev.ps1 -UseDocker -DockerComposeFile docker-compose.prod.yml" -ForegroundColor White
