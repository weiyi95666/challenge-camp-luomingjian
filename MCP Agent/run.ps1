# 项目启动脚本
$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   MCP Agent 项目启动器" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 激活虚拟环境
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
    Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "✗ 虚拟环境未找到，请先运行 start_all.bat" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "请选择运行模式：" -ForegroundColor Yellow
Write-Host "1. CLI 命令行客户端" -ForegroundColor White
Write-Host "2. 桌面聊天应用" -ForegroundColor White
Write-Host "3. API 服务器" -ForegroundColor White
Write-Host "4. 测试 API" -ForegroundColor White
Write-Host "Q. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-4 或 Q)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "启动 CLI 客户端..." -ForegroundColor Cyan
        Write-Host "输入您的问题（例如：天气 北京），Ctrl+C 退出" -ForegroundColor Gray
        Write-Host ""
        python client.py
    }
    "2" {
        Write-Host ""
        Write-Host "启动桌面聊天应用..." -ForegroundColor Cyan
        python desktop_chat.py
    }
    "3" {
        Write-Host ""
        Write-Host "启动 API 服务器..." -ForegroundColor Cyan
        Write-Host "API 地址: http://127.0.0.1:5001" -ForegroundColor Gray
        python api_server.py
    }
    "4" {
        Write-Host ""
        Write-Host "运行 API 测试..." -ForegroundColor Cyan
        python test_api.py
    }
    "Q" {
        Write-Host ""
        Write-Host "再见！" -ForegroundColor Cyan
    }
    default {
        Write-Host ""
        Write-Host "无效的选项" -ForegroundColor Red
    }
}
