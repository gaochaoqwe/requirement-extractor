@echo off
echo ======================================
echo  启动Caddy Web服务器
echo ======================================

echo 1. 检查dist目录...
if not exist dist (
    echo ❌ dist目录不存在，请先运行 npm run build 构建项目
    pause
    exit /b 1
)

echo 2. 创建日志目录...
if not exist logs mkdir logs

echo 3. 停止已运行的Caddy进程...
taskkill /f /im caddy.exe 2>nul || echo 没有找到正在运行的Caddy进程

echo 4. 启动Caddy服务器...
echo.
echo 🚀 服务器启动中...
echo 📱 访问地址: http://localhost:8085
echo 📋 API代理: http://localhost:8085/api/* → http://localhost:5002/*
echo 📝 日志文件: logs/caddy.log
echo.
echo ⏹️  按 Ctrl+C 停止服务器
echo.

./caddy.exe run --config Caddyfile --adapter caddyfile 