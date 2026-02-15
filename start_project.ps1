# 百姓助手启动脚本
param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

function Start-Project {
    Write-Host "🚀 启动百姓助手项目..." -ForegroundColor Green
    
    # 检查Docker
    $dockerRunning = docker ps 2>$null
    if (-not $dockerRunning) {
        Write-Host "⚠️ Docker未运行，尝试启动..." -ForegroundColor Yellow
        # 尝试启动Docker Desktop
        & "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>$null
        Start-Sleep -Seconds 10
    }
    
    # 启动Docker服务
    Write-Host "🐳 启动Docker服务..." -ForegroundColor Cyan
    docker compose up -d db redis
    Start-Sleep -Seconds 5
    
    # 初始化数据库
    Write-Host "🗄️ 初始化数据库..." -ForegroundColor Cyan
    cd backend
    .venv\Scripts\python -m alembic upgrade head
    cd ..
    
    # 启动后端
    Write-Host "🔧 启动后端服务..." -ForegroundColor Cyan
    Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd backend; .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Hidden
    
    # 启动前端
    Write-Host "🎨 启动前端服务..." -ForegroundColor Cyan
    Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd frontend-v2; npm run dev" -WindowStyle Hidden
    
    Write-Host "✅ 项目已启动！" -ForegroundColor Green
    Write-Host "📱 前端: http://localhost:5173" -ForegroundColor Yellow
    Write-Host "🔌 后端API: http://localhost:8000" -ForegroundColor Yellow
    Write-Host "📊 监控: http://localhost:3001 (Grafana)" -ForegroundColor Yellow
}

function Stop-Project {
    Write-Host "🛑 停止百姓助手项目..." -ForegroundColor Red
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" } | Stop-Process -Force
    docker compose down
    Write-Host "✅ 项目已停止" -ForegroundColor Green
}

switch ($Action) {
    "start" { Start-Project }
    "stop" { Stop-Project }
    "restart" { Stop-Project; Start-Project }
    default { Write-Host "用法: .\start_project.ps1 [start|stop|restart]" }
}
