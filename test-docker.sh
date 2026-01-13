#!/bin/bash

# 信发系统 Docker 测试脚本

echo "========================================="
echo "信发系统 Docker 环境测试"
echo "========================================="

# 检查 Docker 是否安装
echo -n "检查 Docker 安装... "
if command -v docker &> /dev/null; then
    echo "✓"
    docker --version
else
    echo "✗"
    echo "错误: 未安装 Docker，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
echo -n "检查 Docker Compose 安装... "
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "✓"
    docker compose version 2>/dev/null || docker-compose --version
else
    echo "✗"
    echo "错误: 未安装 Docker Compose"
    exit 1
fi

# 检查端口 8000 是否被占用
echo -n "检查端口 8000... "
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✗"
    echo "警告: 端口 8000 已被占用，请修改 docker-compose.yml 中的端口配置"
else
    echo "✓"
fi

# 检查必要文件
echo -n "检查项目文件... "
required_files=("main.py" "requirements.txt" "Dockerfile" "docker-compose.yml" "static/index.html" "static/client.html")
all_exist=true

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ] && [ ! -d "$file" ]; then
        echo "✗"
        echo "错误: 缺少文件 $file"
        all_exist=false
    fi
done

if $all_exist; then
    echo "✓"
fi

echo ""
echo "========================================="
echo "环境检查完成！"
echo "========================================="
echo ""
echo "下一步操作:"
echo "  1. 构建并启动: docker-compose up -d"
echo "  2. 查看日志:   docker-compose logs -f"
echo "  3. 停止服务:   docker-compose down"
