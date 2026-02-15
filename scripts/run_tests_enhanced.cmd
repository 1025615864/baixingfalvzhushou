@echo off
chcp 65001 >nul
echo ===========================================
echo 百姓助手 - 增强测试套件 (支持详细测试场景)
echo ===========================================
echo.

setlocal

REM 设置项目根目录
set PROJECT_ROOT=%~dp0

REM 设置颜色输出
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"

REM 检查参数
set TEST_TYPE=all
if "%1"=="" set TEST_TYPE=all
if "%1"=="api" set TEST_TYPE=api
if "%1"=="services" set TEST_TYPE=services
if "%1"=="auth" set TEST_TYPE=auth
if "%1"=="payment" set TEST_TYPE=payment
if "%1%2"=="forum posts" set TEST_TYPE=forum
if "%1%2"=="news comments" set TEST_TYPE=news
if "%1"=="database" set TEST_TYPE=database
if "%1"=="cache" set TEST_TYPE=cache
if "%1"=="security" set TEST_TYPE=security
if "%1"=="integration" set TEST_TYPE=integration
if "%1"=="frontend-smoke" set TEST_TYPE=frontend-smoke
if "%1"=="frontend-full" set TEST_TYPE=frontend-full

if "%TEST_TYPE%"=="all" (
    echo 用法: run_tests_enhanced.bat [测试类型]
    echo.
    echo 后端测试类型:
    echo   api          API 接口测试 (用户、论坛、新闻等)
    echo   services     服务层单元测试
    echo   auth         认证授权测试
    echo   payment      支付相关测试
    echo   forum        论坛功能测试
    echo   news         新闻和评论测试
    echo   database     数据库操作测试
    echo   cache        缓存服务测试
    echo   security     安全相关测试
    echo   integration  集成测试
    echo.
    echo 前端测试类型:
    echo   frontend-smoke  前端冒烟测试
    echo   frontend-full   前端完整测试
    echo.
    echo 综合测试类型:
    echo   all           所有测试 (默认)
    echo.
    echo 示例:
    echo   run_tests_enhanced.bat api           ^&^& 运行 API 测试
    echo   run_tests_enhanced.bat payment       ^&^& 运行支付测试
    echo   run_tests_enhanced.bat forum         ^&^& 运行论坛测试
    echo   run_tests_enhanced.bat frontend-smoke ^&^& 运行前端冒烟测试
    echo.
    exit /b 0
)

echo %ESC%[33m[*]%ESC%[0m 开始执行 [%TEST_TYPE%] 测试...
echo.

REM 记录开始时间
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "START_TIME=%%a"

REM 创建临时目录
if not exist "%PROJECT_ROOT%test_results" mkdir "%PROJECT_ROOT%test_results"
set TEST_LOG=%PROJECT_ROOT%test_results\%TEST_TYPE%_test_log.txt

REM 根据测试类型执行相应测试
if "%TEST_TYPE%"=="api" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  API 接口测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_api.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="services" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  服务层单元测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_user_service.py tests/test_forum_service.py tests/test_news_service.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="auth" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  认证授权测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_api.py::TestUserAPI -v --tb=short 2>&1 | tee "%TEST_LOG%"
    py -m pytest tests/test_auth*.py -v --tb=short 2>&1 | tee -a "%TEST_LOG%"
)

if "%TEST_TYPE%"=="payment" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  支付相关测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_payment*.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
    py -m pytest tests/test_settlement*.py -v --tb=short 2>&1 | tee -a "%TEST_LOG%"
)

if "%TEST_TYPE%"=="forum" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  论坛功能测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_api.py::TestForumAPI -v --tb=short 2>&1 | tee "%TEST_LOG%"
    py -m pytest tests/test_forum*.py -v --tb=short 2>&1 | tee -a "%TEST_LOG%"
)

if "%TEST_TYPE%"=="news" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  新闻和评论测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_api.py::TestNewsAPI -v --tb=short 2>&1 | tee "%TEST_LOG%"
    py -m pytest tests/test_news*.py -v --tb=short 2>&1 | tee -a "%TEST_LOG%"
)

if "%TEST_TYPE%"=="database" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  数据库操作测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_database.py tests/test_db_migration_gate.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="cache" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  缓存服务测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_cache*.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="security" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  安全相关测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_pii.py tests/test_permissions.py tests/test_system_secrets.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
    py -m pytest tests/test_rate_limit*.py -v --tb=short 2>&1 | tee -a "%TEST_LOG%"
)

if "%TEST_TYPE%"=="integration" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  集成测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%backend"
    py -m pytest tests/test_orders_pay_integration.py tests/test_lawyer_consultation*.py -v --tb=short 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="frontend-smoke" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  前端冒烟测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%frontend"
    echo 运行关键 E2E 测试...
    npm run test:e2e -- --grep "auth|smoke" --project=chromium 2>&1 | tee "%TEST_LOG%"
)

if "%TEST_TYPE%"=="frontend-full" (
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[36m  前端完整测试%ESC%[0m
    echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
    cd "%PROJECT_ROOT%frontend"
    echo 安装 Playwright 浏览器...
    npm run test:e2e:install >nul 2>&1
    echo 运行所有 E2E 测试...
    npm run test:e2e -- --project=chromium 2>&1 | tee "%TEST_LOG%"
)

REM 记录结束时间
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "END_TIME=%%a"

echo.
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  测试完成%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.
echo 开始时间: %START_TIME%
echo 结束时间: %END_TIME%
echo.
if exist "%TEST_LOG%" (
    echo 详细日志: %TEST_LOG%
)

endlocal
