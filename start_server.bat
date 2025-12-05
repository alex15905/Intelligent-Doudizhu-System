@echo off
REM ================================
REM 启动 DouDiZhuAI 后端服务（Windows）
REM ================================

REM 切换到脚本所在目录
cd /d "%~dp0"

IF NOT EXIST "backend" (
    echo [ERROR] backend 目录不存在，请确认目录结构。
    pause
    exit /b 1
)

cd backend

REM 检查 Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] 未检测到 python，请先在系統中安裝 Python 並配置環境變量。
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
IF NOT EXIST "venv" (
    echo [INFO] 正在创建 Python 虚拟环境 venv ...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [ERROR] 虚拟环境创建失败。
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
IF EXIST "requirements.txt" (
    echo [INFO] 正在安装/更新依赖 ...
    pip install --upgrade pip
    pip install -r requirements.txt
) ELSE (
    echo [ERROR] 未找到 requirements.txt
    pause
    exit /b 1
)

REM 启动开发服务器
echo [INFO] 正在启动 DouDiZhuAI 后端服务 ...
call run_dev.bat

REM 关闭时保持窗口
pause
