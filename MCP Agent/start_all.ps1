# 启动脚本（PowerShell）
Param()

# 允许当前进程加载本地脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# 创建虚拟环境（如不存在）
if (-not (Test-Path -Path .venv)) {
    python -m venv .venv
}

# 激活虚拟环境
. .\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 启动后端
Start-Process -NoNewWindow -FilePath python -ArgumentList "api_server.py"
Start-Sleep -Seconds 1

# 启动桌面前端（阻塞，以便用户关闭后可一并关闭后端）
python desktop_chat.py
