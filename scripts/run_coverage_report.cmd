@echo off
chcp 65001 >nul
echo ===========================================
echo 百姓助手 - 测试覆盖率报告汇总
echo ===========================================
echo.

setlocal

REM 设置项目根目录
set PROJECT_ROOT=%~dp0

REM 设置颜色输出
for /f %%A in ('echo prompt $E ^| cmd') do set "ESC=%%A"

REM 检查参数
set REPORT_TYPE=html
if "%1"=="" set REPORT_TYPE=html
if "%1"=="console" set REPORT_TYPE=console
if "%1"=="json" set REPORT_TYPE=json
if "%1"=="lcov" set REPORT_TYPE=lcov

echo %ESC%[33m[*]%ESC%[0m 生成测试覆盖率报告...
echo.

REM 创建报告目录
if not exist "%PROJECT_ROOT%coverage_reports" mkdir "%PROJECT_ROOT%coverage_reports"

REM 运行后端覆盖率测试
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  后端测试覆盖率%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

cd "%PROJECT_ROOT%backend"
echo 运行后端测试并生成覆盖率报告...

if "%REPORT_TYPE%"=="html" (
    py -m pytest --cov=app --cov-report=term-missing --cov-report=html:coverage_html 2>&1 | tee "%PROJECT_ROOT%coverage_reports\backend_coverage.txt"
) else if "%REPORT_TYPE%"=="console" (
    py -m pytest --cov=app --cov-report=term-missing 2>&1 | tee "%PROJECT_ROOT%coverage_reports\backend_coverage.txt"
) else if "%REPORT_TYPE%"=="json" (
    py -m pytest --cov=app --cov-report=json --cov-report=term-missing 2>&1 | tee "%PROJECT_ROOT%coverage_reports\backend_coverage.txt"
) else if "%REPORT_TYPE%"=="lcov" (
    py -m pytest --cov=app --cov-report=lcov --cov-report=term-missing 2>&1 | tee "%PROJECT_ROOT%coverage_reports\backend_coverage.txt"
)

cd "%PROJECT_ROOT%"

echo.
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  前端测试覆盖率%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

REM 运行前端覆盖率测试
cd "%PROJECT_ROOT%frontend"
echo 运行前端测试并生成覆盖率报告...

if "%REPORT_TYPE%"=="html" (
    npx vitest run --coverage --reporter=verbose 2>&1 | tee "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt"
) else if "%REPORT_TYPE%"=="console" (
    npx vitest run --coverage --reporter=verbose 2>&1 | tee "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt"
) else (
    npx vitest run --coverage 2>&1 | tee "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt"
)

cd "%PROJECT_ROOT%"

echo.
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo %ESC%[36m  覆盖率报告汇总%ESC%[0m
echo %ESC%[36m═══════════════════════════════════════%ESC%[0m
echo.

REM 生成汇总报告
set BACKEND_COVERAGE=0
set FRONTEND_COVERAGE=0

REM 提取后端覆盖率
if exist "%PROJECT_ROOT%coverage_reports\backend_coverage.txt" (
    findstr /C:"TOTAL" "%PROJECT_ROOT%coverage_reports\backend_coverage.txt" >nul
    if not errorlevel 1 (
        for /f "tokens=6" %%a in ('findstr /C:"TOTAL" "%PROJECT_ROOT%coverage_reports\backend_coverage.txt"') do set "BACKEND_COVERAGE=%%a"
    )
)

REM 提取前端覆盖率
if exist "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt" (
    findstr /C:"All files" "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt" >nul
    if not errorlevel 1 (
        for /f "tokens=12" %%a in ('findstr /C:"All files" "%PROJECT_ROOT%coverage_reports\frontend_coverage.txt"') do set "FRONTEND_COVERAGE=%%a"
    )
)

echo 后端测试覆盖率: %BACKEND_COVERAGE%
echo 前端测试覆盖率: %FRONTEND_COVERAGE%
echo.

echo %ESC%[33m[*]%ESC%[0m 报告文件位置:
echo   - 后端: %PROJECT_ROOT%coverage_reports\backend_coverage.txt
echo   - 前端: %PROJECT_ROOT%coverage_reports\frontend_coverage.txt
if exist "%PROJECT_ROOT%backend\coverage_html" (
    echo   - 后端 HTML: %PROJECT_ROOT%backend\coverage_html\index.html
)
if exist "%PROJECT_ROOT%frontend\coverage" (
    echo   - 前端 HTML: %PROJECT_ROOT%frontend\coverage\index.html
)
echo.

REM 计算平均覆盖率
set /a AVG_COVERAGE=(%BACKEND_COVERAGE:~0,2% + %FRONTEND_COVERAGE:~0,2%) / 2
echo 平均测试覆盖率: %AVG_COVERAGE%%

echo.
if %AVG_COVERAGE% GEQ 70 (
    echo %ESC%[32m✓ 覆盖率达标 (>= 70%%)%ESC%[0m
) else (
    echo %ESC%[31m⚠ 覆盖率偏低，建议增加测试用例%ESC%[0m
)

endlocal
