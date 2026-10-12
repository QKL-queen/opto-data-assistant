@echo off
chcp 65001 >nul
title 光电实验数据处理助手
cd /d "%~dp0"

echo ============================================
echo   光电实验数据处理助手  启动中...
echo ============================================

if not exist "venv\Scripts\python.exe" (
    echo [首次运行] 正在创建虚拟环境并安装依赖，请耐心等待...
    python -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [启动] 正在打开浏览器（http://127.0.0.1:7860）...
venv\Scripts\python.exe app.py
pause
