@echo off
chcp 65001 >nul
setlocal

REM 创建虚拟环境（如果不存在）
if not exist .venv (
  python -m venv .venv
)

REM 激活虚拟环境并安装依赖
call .venv\Scripts\activate
pip install -r requirements.txt

REM 启动后端（在新窗口或后台）
start "MCP API" python api_server.py

REM 等待后端启动，再打开桌面前端
timeout /t 1 >nul
python desktop_chat.py

endlocal
