@echo off
REM 信发系统 - 开发模式启动脚本

chcp 65001 > nul

echo ========================================
echo 信发系统 - 开发模式
echo ========================================
echo.
echo 开发模式特性:
echo   ✓ 代码热更新（修改 main.py 自动重启）
echo   ✓ 静态文件实时更新（修改 HTML/CSS/JS 立即生效）
echo   ✓ 数据持久化
echo.
echo ========================================
echo.

REM 停止生产模式容器（如果在运行）
docker-compose down 2>nul

REM 启动开发模式
docker-compose -f docker-compose.dev.yml up -d

if errorlevel 1 (
    echo.
    echo ✗ 启动失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ 开发模式已启动！
echo ========================================
echo.
echo 访问地址:
echo   管理端: http://localhost:8000/admin
echo   显示端: http://localhost:8000/
echo.
echo 查看日志: docker-compose -f docker-compose.dev.yml logs -f
echo 停止服务: docker-compose -f docker-compose.dev.yml down
echo.
echo 提示: 现在修改代码文件会自动生效！
echo   - 修改 main.py 会自动重启服务
echo   - 修改 static/ 下的文件会立即生效
echo.

pause
