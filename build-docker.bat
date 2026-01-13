@echo off
REM 信发系统 Docker 构建和推送脚本 (Windows)

chcp 65001 > nul
setlocal enabledelayedexpansion

REM 配置
set IMAGE_NAME=signage-system
set VERSION=latest
set DOCKER_USERNAME=your-username

echo ========================================
echo 信发系统 Docker 构建脚本
echo ========================================

REM 1. 构建镜像
echo.
echo [1/4] 构建 Docker 镜像...
docker build -t %IMAGE_NAME%:%VERSION% .

if errorlevel 1 (
    echo 构建失败！
    pause
    exit /b 1
)

echo ✓ 镜像构建成功

REM 2. 打标签
echo.
echo [2/4] 为镜像打标签...
docker tag %IMAGE_NAME%:%VERSION% %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%
echo ✓ 标签创建成功: %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%

REM 3. 推送到 Docker Hub
echo.
echo [3/4] 推送镜像到 Docker Hub...
echo 提示: 如果未登录，请先运行 'docker login'
echo.

set /p PUSH_CONFIRM="是否推送到 Docker Hub? (y/n): "
if /i "%PUSH_CONFIRM%"=="y" (
    docker push %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%
    
    if errorlevel 1 (
        echo 推送失败！请检查 Docker Hub 登录状态
        pause
        exit /b 1
    )
    
    echo ✓ 镜像推送成功
) else (
    echo 跳过推送步骤
)

REM 4. 显示镜像信息
echo.
echo [4/4] 镜像信息
docker images | findstr %IMAGE_NAME%

echo.
echo ========================================
echo ✓ 完成！
echo ========================================
echo.
echo 使用方法:
echo   本地运行: docker-compose up -d
echo   拉取镜像: docker pull %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%
echo.
echo 访问地址:
echo   管理端: http://localhost:8000/admin
echo   显示端: http://localhost:8000/
echo.

pause
