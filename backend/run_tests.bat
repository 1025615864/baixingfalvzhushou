@echo off
chcp 65001 >nul
echo ========================================
echo 百姓助手 - 测试运行脚本
echo ========================================

cd /d "%~dp0"

echo [INFO] 检查测试环境...
py -m pytest --version

echo.
echo [1/4] 运行快速测试 (排除慢速测试)...
py -m pytest tests/ -v --tb=short -m "not slow" --timeout=60 --ignore=tests/e2e

echo.
echo [2/4] 运行核心测试...
py -m pytest tests/test_app_config.py tests/test_cache_service.py tests/test_calculator_tool.py -v --tb=short --timeout=60

echo.
echo [3/4] 运行 AI 模块测试...
py -m pytest tests/test_ai_*.py -v --tb=short --timeout=60

echo.
echo [4/4] 运行 Router 测试...
py -m pytest tests/test_*_router.py -v --tb=short --timeout=60

echo.
echo ========================================
echo 测试完成！
echo ========================================
pause
