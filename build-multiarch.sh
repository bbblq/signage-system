#!/bin/bash

# 信发系统 - 多架构 Docker 镜像构建脚本
# 支持 amd64 和 arm64 架构

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 配置
IMAGE_NAME="signage-system"
VERSION="latest"
DOCKER_USERNAME="${DOCKER_USERNAME:-your-username}"
PLATFORMS="linux/amd64,linux/arm64"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}信发系统 多架构 Docker 构建脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查 Docker buildx
echo -e "\n${GREEN}检查 Docker buildx...${NC}"
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}错误: Docker buildx 未安装${NC}"
    echo -e "${BLUE}请升级到 Docker 19.03+ 版本${NC}"
    exit 1
fi

# 创建并使用 buildx builder
echo -e "\n${GREEN}创建 buildx builder...${NC}"
docker buildx create --name signage-builder --use 2>/dev/null || docker buildx use signage-builder

# 启动 builder
echo -e "${GREEN}启动 builder...${NC}"
docker buildx inspect --bootstrap

# 构建多架构镜像
echo -e "\n${GREEN}构建多架构镜像...${NC}"
echo -e "${BLUE}平台: ${PLATFORMS}${NC}"

read -p "是否推送到 Docker Hub? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 构建并推送
    docker buildx build \
        --platform ${PLATFORMS} \
        --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
        --push \
        .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}构建失败！${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 多架构镜像构建并推送成功${NC}"
else
    # 仅构建到本地
    docker buildx build \
        --platform ${PLATFORMS} \
        --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
        --load \
        .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}构建失败！${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 多架构镜像构建成功（本地）${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n镜像信息:"
echo -e "  名称: ${GREEN}${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo -e "  架构: ${GREEN}${PLATFORMS}${NC}"
