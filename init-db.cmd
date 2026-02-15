@echo off
chcp 65001 > nul

echo ==========================================
echo    百姓法律助手 - 数据库初始化 (Windows)
echo ==========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

echo 1. 运行数据库迁移...
docker compose -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic upgrade head
if errorlevel 1 (
    echo [错误] 数据库迁移失败
    pause
    exit /b 1
)

echo.
echo 2. 检查迁移状态...
docker compose -f docker-compose.dev.yml --env-file .env.docker exec -T backend alembic current

echo.
echo ==========================================
echo ✅ 数据库初始化完成！
echo ==========================================
pause
