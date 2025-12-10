@echo off
echo ========================================
echo 启动 Easy Dataset 开发环境
echo ========================================
echo.

echo [1/3] 检查并清理端口冲突...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1717 ^| findstr LISTENING') do (
    echo 发现占用 1717 端口的进程 PID: %%a，正在停止...
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo [2/3] 清理 Next.js 缓存...
if exist .next (
    echo 删除 .next 目录...
    rmdir /s /q .next >nul 2>&1
)

echo.
echo [3/3] 启动 Next.js 开发服务器...
echo 请确保 Django 后端已启动在 http://127.0.0.1:8000
echo.
pnpm dev

