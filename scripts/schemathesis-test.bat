@echo off
REM Schemathesis Quick Test Script for Windows
REM 快速测试 API 的脚本 - 基于 OpenAPI Schema

setlocal enabledelayedexpansion

REM 配置
set SCHEMATHESIS_SOURCE=http://localhost:8080/openapi.json
set BASE_URL=http://localhost:8080
set OUTPUT_DIR=test-results
set CHECKS=all

REM 颜色输出 (Windows CMD 不支持 ANSI 颜色，使用简单标记)
echo [INFO] 检查依赖...

REM 检查 schemathesis 是否安装
where schemathesis >nul 2>&1
if errorlevel 1 (
    echo [ERROR] schemathesis 未安装，请运行: pip install schemathesis
    exit /b 1
)

echo [INFO] schemathesis 已安装

REM 检查服务器是否运行
echo [INFO] 检查服务器可用性: %BASE_URL%
curl -s -o nul -w "%%{http_code}" %BASE_URL%/health >nul 2>&1
if errorlevel 200 (
    echo [INFO] 服务器运行正常
) else (
    echo [WARN] 服务器可能未运行或 /health 端点不可用，尝试直接测试...
)

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 运行完整测试
echo [INFO] 运行完整 Schemathesis 测试...
echo [INFO] Schema 来源: %SCHEMATHESIS_SOURCE%

schemathesis run "%SCHEMATHESIS_SOURCE%" --checks "%CHECKS%" --base-url "%BASE_URL%" --validate-schema --verbosity verbose --output-format cli --junit-xml "%OUTPUT_DIR%\schemathesis-junit.xml" --json "%OUTPUT_DIR%\schemathesis-report.json"

endlocal
