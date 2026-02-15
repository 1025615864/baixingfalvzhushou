@echo off
REM ============================================
REM 百姓助手 - 本地开发环境一键启动脚本
REM ============================================
setlocal

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set FRONTEND_DIR=%SCRIPT_DIR%frontend

echo ============================================
echo 百姓助手 - 本地开发环境启动
echo ============================================

REM 检查 Python
py -V >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装，请先安装 Python 3.10+
    exit /b 1
)

REM 检查 Node.js
node -v >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js 18+
    exit /b 1
)

REM 创建后端虚拟环境
set VENV_DIR=%BACKEND_DIR%\.venv
set VENV_PY=%VENV_DIR%\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo [INFO] 创建后端虚拟环境...
    py -m venv "%VENV_DIR%"
) else (
    echo [INFO] 后端虚拟环境已存在
)

REM 安装后端依赖
echo [INFO] 安装后端依赖...
"%VENV_PY%" -m pip install -U pip >nul 2>&1
"%VENV_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt" >nul 2>&1
if errorlevel 1 (
    echo [WARN] 后端依赖安装可能有警告，继续尝试启动...
)

REM 安装前端依赖
set NODE_MODULES=%FRONTEND_DIR%\node_modules
if not exist "%NODE_MODULES%" (
    echo [INFO] 安装前端依赖...
    cd /d "%FRONTEND_DIR%"
    npm install
    cd /d "%SCRIPT_DIR%"
) else (
    echo [INFO] 前端依赖已存在
)

REM 检查配置文件
if not exist "%BACKEND_DIR%\.env" (
    echo [INFO] 创建环境变量配置文件...
    copy "%BACKEND_DIR%\env.example" "%BACKEND_DIR%\.env" >nul
    echo [WARN] 请编辑 %BACKEND_DIR%\.env 配置数据库连接等信息
)

echo ============================================
echo 启动服务...
echo ============================================
echo 后端: http://localhost:8000
echo Swagger文档: http://localhost:8000/docs
echo 前端: http://localhost:5173
echo ============================================

REM 启动后端服务
echo [INFO] 启动后端服务...
start "Baixing Backend" cmd /c "%VENV_PY% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 5 /nobreak >nul

REM 启动前端服务
echo [INFO] 启动前端服务...
cd /d "%FRONTEND_DIR%"
start "Baixing Frontend" cmd /c "npm run dev -- --host 0.0.0.0 --port 5173"

cd /d "%SCRIPT_DIR%"

echo ============================================
echo 启动完成！
echo ============================================
echo 请访问:
echo   - API: http://localhost:8000/api
echo   - Swagger: http://localhost:8000/docs
echo   - 前端: http://localhost:5173
echo ============================================
echo 关闭所有窗口或按 Ctrl+C 停止服务

endlocal
