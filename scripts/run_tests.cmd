@echo off
chcp 65001 >nul
echo ===========================================
echo 百姓助手 - 完整测试套件
echo ===========================================
echo.

setlocal

REM 设置项目根目录
set PROJECT_ROOT=%~dp0

REM 设置颜色输出
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"

REM 检查参数
set ACTION=help
if "%1"=="" set ACTION=help
if "%1"=="help" set ACTION=help
if "%1"=="backend" set ACTION=backend
if "%1"=="frontend" set ACTION=frontend
if "%1"=="all" set ACTION=all
if "%1"=="coverage" set ACTION=coverage
if "%1"=="quick" set ACTION=quick
if "%1"=="e2e" set ACTION=e2e
if "%1"=="unit" set ACTION=unit

if "%ACTION%"=="help" (
    echo 用法: run_tests.bat [命令]
    echo.
    echo 命令:
    echo   help      显示此帮助信息 (默认)
    echo   backend   运行后端单元测试 (pytest)
    echo   frontend  运行前端测试 (E2E + Unit)
    echo   all       运行所有测试 (后端 + 前端)
    echo   coverage  运行所有测试并生成覆盖率报告
    echo   quick     快速测试 (跳过覆盖率)
    echo   e2e       仅运行前端 E2E 测试
    echo   unit      仅运行单元测试 (后端 + 前端)
    echo.
    echo 示例:
    echo   run_tests.bat all          ^&^& 运行所有测试
    echo   run_tests.bat coverage     ^&^& 运行测试并生成覆盖率
    echo   run_tests.bat quick        ^&^& 快速测试
    echo.
    exit /b 0
)

REM 记录开始时间
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "START_TIME=%%a"
echo %ESC%[32m[%TIME%]%ESC%[0m 开始执行测试...
echo.

REM 创建临时目录用于测试结果
if not exist "%PROJECT_ROOT%test_results" mkdir "%PROJECT_ROOT%test_results"

REM 设置测试结果文件
set BACKEND_RESULT=%PROJECT_ROOT%test_results\backend_test_result.txt
set FRONTEND_RESULT=%PROJECT_ROOT%test_results\frontend_test_result.txt
set COVERAGE_RESULT=%PROJECT_ROOT%test_results\coverage_report.txt

REM 定义成功/失败标志
set BACKEND_PASS=0
set FRONTEND_PASS=0

echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  1. 后端测试 (Python/pytest)%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

if "%ACTION%"=="backend" goto run_backend
if "%ACTION%"=="all" goto run_backend
if "%ACTION%"=="coverage" goto run_backend
if "%ACTION%"=="quick" goto run_backend
if "%ACTION%"=="unit" goto run_backend
echo 跳过后端测试 (使用 frontend/e2e 参数)
goto skip_backend

:run_backend
echo %ESC%[33m[*]%ESC%[0m 检查后端测试环境...

REM 检查 Python
py -V >nul 2>&1
if errorlevel 1 (
    echo %ESC%[31m[错误]%ESC%[0m 未找到 Python，请确保已安装 Python 3.8+
    echo %ESC%[31m[错误]%ESC%[0m 后端测试失败
    set BACKEND_PASS=1
    goto backend_done
)

REM 检查并安装测试依赖
echo %ESC%[33m[*]%ESC%[0m 安装/检查测试依赖...
cd "%PROJECT_ROOT%backend"
if exist requirements-dev.txt (
    echo 安装后端开发依赖...
    py -m pip install -q -r requirements-dev.txt 2>nul
    if errorlevel 1 (
        echo %ESC%[31m[警告]%ESC%[0m 安装依赖时出现问题，继续尝试运行测试...
    )
)

REM 运行后端测试
echo.
echo %ESC%[33m[*]%ESC%[0m 运行后端单元测试...
echo.

if "%ACTION%"=="coverage" (
    echo 生成覆盖率报告...
    py -m pytest -v --cov=app --cov-report=term-missing --cov-report=html:coverage_html -x 2>&1 | tee "%BACKEND_RESULT%"
) else if "%ACTION%"=="quick" (
    py -m pytest -v --tb=short 2>&1 | tee "%BACKEND_RESULT%"
) else (
    py -m pytest -v 2>&1 | tee "%BACKEND_RESULT%"
)

if errorlevel 1 (
    echo.
    echo %ESC%[31m[失败]%ESC%[0m 后端测试未完全通过
    set BACKEND_PASS=1
) else (
    echo.
    echo %ESC%[32m[成功]%ESC%[0m 后端测试通过
    set BACKEND_PASS=0
)

:backend_done
cd "%PROJECT_ROOT%"

:skip_backend
echo.

echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  2. 前端测试 (Playwright E2E + Vitest)%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

if "%ACTION%"=="frontend" goto run_frontend
if "%ACTION%"=="all" goto run_frontend
if "%ACTION%"=="coverage" goto run_frontend
if "%ACTION%"=="quick" goto run_frontend
if "%ACTION%"=="e2e" goto run_frontend
if "%ACTION%"=="unit" goto run_frontend
echo 跳过前端测试 (使用 backend 参数)
goto skip_frontend

:run_frontend
echo %ESC%[33m[*]%ESC%[0m 检查前端测试环境...

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[31m[错误]%ESC%[0m 未找到 Node.js，请确保已安装 Node.js 18+
    echo %ESC%[31m[错误]%ESC%[0m 前端测试失败
    set FRONTEND_PASS=1
    goto frontend_done
)

REM 安装 Playwright 浏览器
echo %ESC%[33m[*]%ESC%[0m 检查/安装 Playwright 浏览器...
cd "%PROJECT_ROOT%frontend"
npm run test:e2e:install >nul 2>&1
if errorlevel 1 (
    echo %ESC%[31m[警告]%ESC%[0m Playwright 浏览器安装出现问题
)

REM 运行前端 E2E 测试
echo.
echo %ESC%[33m[*]%ESC%[0m 运行前端 E2E 测试...
echo.

if "%ACTION%"=="e2e" (
    echo 运行所有 E2E 测试...
    npm run test:e2e 2>&1 | tee "%FRONTEND_RESULT%"
) else if "%ACTION%"=="quick" (
    echo 运行 E2E 测试 (快速模式)...
    npm run test:e2e -- --project=chromium --reporter=line 2>&1 | tee "%FRONTEND_RESULT%"
) else if "%ACTION%"=="unit" (
    echo 运行 Vitest 单元测试...
    npx vitest run --reporter=verbose 2>&1 | tee "%FRONTEND_RESULT%"
) else (
    echo 运行完整前端测试...
    echo.
    echo %ESC%[33m[*]%ESC%[0m E2E 测试...
    npm run test:e2e -- --project=chromium --reporter=line 2>&1 | tee "%FRONTEND_RESULT%"
)

if errorlevel 1 (
    echo.
    echo %ESC%[31m[失败]%ESC%[0m 前端测试未完全通过
    set FRONTEND_PASS=1
) else (
    echo.
    echo %ESC%[32m[成功]%ESC%[0m 前端测试通过
    set FRONTEND_PASS=0
)

:frontend_done
cd "%PROJECT_ROOT%"

:skip_frontend
echo.

REM 生成汇总报告
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  测试结果汇总%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

REM 记录结束时间
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC_END=%%A"
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "END_TIME=%%a"

echo 开始时间: %START_TIME%
echo 结束时间: %END_TIME%
echo.

if "%ACTION%"=="backend" (
    if %BACKEND_PASS%==0 (
        echo %ESC%[32m✓%ESC%[0m 后端测试: 通过
    ) else (
        echo %ESC%[31m✗%ESC%[0m 后端测试: 失败
    )
) else if "%ACTION%"=="frontend" (
    if %FRONTEND_PASS%==0 (
        echo %ESC%[32m✓%ESC%[0m 前端测试: 通过
    ) else (
        echo %ESC%[31m✗%ESC%[0m 前端测试: 失败
    )
) else if "%ACTION%"=="all" (
    if %BACKEND_PASS%==0 (
        echo %ESC%[32m✓%ESC%[0m 后端测试: 通过
    ) else (
        echo %ESC%[31m✗%ESC%[0m 后端测试: 失败
    )
    if %FRONTEND_PASS%==0 (
        echo %ESC%[32m✓%ESC%[0m 前端测试: 通过
    ) else (
        echo %ESC%[31m✗%ESC%[0m 前端测试: 失败
    )
) else if "%ACTION%"=="coverage" (
    echo %ESC%[33m[*]%ESC%[0m 覆盖率报告已生成
    if exist "%PROJECT_ROOT%coverage_html" (
        echo %ESC%[33m[*]%ESC%[0m 查看报告: %PROJECT_ROOT%coverage_html\index.html
    )
)

echo.
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  详细日志%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
if exist "%BACKEND_RESULT%" (
    echo 后端测试日志: %BACKEND_RESULT%
)
if exist "%FRONTEND_RESULT%" (
    echo 前端测试日志: %FRONTEND_RESULT%
)
echo.

REM 计算总体结果
set OVERALL_PASS=0
if "%ACTION%"=="backend" (
    set OVERALL_PASS=%BACKEND_PASS%
) else if "%ACTION%"=="frontend" (
    set OVERALL_PASS=%FRONTEND_PASS%
) else (
    set /a OVERALL_PASS=%BACKEND_PASS% + %FRONTEND_PASS%
)

if %OVERALL_PASS%==0 (
    echo %ESC%[32m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[32m  ✓ 所有测试通过!%ESC%[0m
    echo %ESC%[32m═══════════════════════════════════════%ESC%[0m
    exit /b 0
) else (
    echo %ESC%[31m═══════════════════════════════════════%ESC%[0m
    echo %ESC%[31m  ✗ 部分测试失败!%ESC%[0m
    echo %ESC%[31m═══════════════════════════════════════%ESC%[0m
    exit /b 1
)

endlocal
