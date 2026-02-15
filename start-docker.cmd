@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==========================================
echo    百姓法律助手 - 开发环境启动 (Windows)
echo ==========================================
echo.

:: 检查 Docker 是否运行
docker info > nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查 .env.docker 文件
if not exist ".env.docker" (
    echo [警告] .env.docker 文件不存在
)

echo.
echo [步骤 1/5] 停止旧容器...
docker compose -f docker-compose.dev.yml --env-file .env.docker down 2>nul

echo.
echo [步骤 2/5] 构建镜像...
docker compose -f docker-compose.dev.yml --env-file .env.docker build
if errorlevel 1 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)

echo.
echo [步骤 3/5] 启动服务...
docker compose -f docker-compose.dev.yml --env-file .env.docker up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)

echo.
echo [步骤 4/5] 等待服务就绪...
echo 等待数据库启动...
timeout /t 5 /nobreak > nul

echo 等待后端服务启动...
set /a count=0
:wait_backend
curl -s http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if !count! geq 30 (
        echo [警告] 后端服务启动超时，请检查日志
        goto :continue
    )
    timeout /t 2 /nobreak > nul
    goto :wait_backend
)
echo [OK] 后端服务已就绪

:continue
echo.
echo [步骤 5/5] 初始化数据库...
echo 运行数据库迁移...
docker compose -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic upgrade head 2>nul
if errorlevel 1 (
    echo [提示] 数据库迁移可能已经完成
)

echo.
echo ==========================================
echo ✅ 开发环境启动完成！
echo ==========================================
echo.
echo 服务地址:
echo   - 前端:     http://localhost:3000
echo   - 后端API:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
echo 数据库:
echo   - PostgreSQL: localhost:5433
echo   - Redis:      localhost:16379
echo.
echo 常用命令:
echo   - 查看日志:   docker compose -f docker-compose.dev.yml logs -f
echo   - 停止服务:   docker compose -f docker-compose.dev.yml down
echo   - 重启服务:   docker compose -f docker-compose.dev.yml restart
echo.
pause
