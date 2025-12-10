@echo off
echo 正在清理占用 1717 端口的进程...

echo.
echo 查找占用 1717 端口的进程...
netstat -ano | findstr :1717

echo.
echo 正在停止这些进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1717 ^| findstr LISTENING') do (
    echo 停止进程 PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo 清理完成！现在可以重新启动 Next.js 开发服务器了。
echo 请运行: pnpm dev
pause

