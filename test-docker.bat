@echo off
REM 信发系统 Docker 测试脚本 (Windows)

chcp 65001 > nul

echo =========================================
echo 信发系统 Docker 环境测试
echo =========================================

REM 检查 Docker 是否安装
echo 检查 Docker 安装...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未安装 Docker，请先安装 Docker Desktop
    pause
    exit /b 1
) else (
    echo ✓ Docker 已安装
    docker --version
)

REM 检查 Docker Compose 是否可用
echo 检查 Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ✗ 错误: Docker Compose 不可用
        pause
        exit /b 1
    ) else (
        echo ✓ Docker Compose 已安装
        docker-compose --version
    )
) else (
    echo ✓ Docker Compose 已安装
    docker compose version
)

REM 检查端口 8000 是否被占用
echo 检查端口 8000...
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if errorlevel 1 (
    echo ✓ 端口 8000 可用
) else (
    echo ✗ 警告: 端口 8000 已被占用，请修改 docker-compose.yml 中的端口配置
)

REM 检查必要文件
echo 检查项目文件...
set ALL_EXIST=1

if not exist "main.py" (
    echo ✗ 缺少文件: main.py
    set ALL_EXIST=0
)
if not exist "requirements.txt" (
    echo ✗ 缺少文件: requirements.txt
    set ALL_EXIST=0
)
if not exist "Dockerfile" (
    echo ✗ 缺少文件: Dockerfile
    set ALL_EXIST=0
)
if not exist "docker-compose.yml" (
    echo ✗ 缺少文件: docker-compose.yml
    set ALL_EXIST=0
)
if not exist "static\index.html" (
    echo ✗ 缺少文件: static\index.html
    set ALL_EXIST=0
)
if not exist "static\client.html" (
    echo ✗ 缺少文件: static\client.html
    set ALL_EXIST=0
)

if %ALL_EXIST%==1 (
    echo ✓ 所有必要文件存在
)

echo.
echo =========================================
echo 环境检查完成！
echo =========================================
echo.
echo 下一步操作:
echo   1. 构建并启动: docker-compose up -d
echo   2. 查看日志:   docker-compose logs -f
echo   3. 停止服务:   docker-compose down
echo.

pause
