#!/bin/bash

# 信发系统 Docker 构建和推送脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置
IMAGE_NAME="signage-system"
VERSION="latest"
DOCKER_USERNAME="${DOCKER_USERNAME:-your-username}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}信发系统 Docker 构建脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 构建镜像
echo -e "\n${GREEN}[1/4] 构建 Docker 镜像...${NC}"
docker build -t ${IMAGE_NAME}:${VERSION} .

if [ $? -ne 0 ]; then
    echo -e "${RED}构建失败！${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 镜像构建成功${NC}"

# 2. 打标签
echo -e "\n${GREEN}[2/4] 为镜像打标签...${NC}"
docker tag ${IMAGE_NAME}:${VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
echo -e "${GREEN}✓ 标签创建成功: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"

# 3. 推送到 Docker Hub
echo -e "\n${GREEN}[3/4] 推送镜像到 Docker Hub...${NC}"
echo -e "${BLUE}提示: 如果未登录，请先运行 'docker login'${NC}"

read -p "是否推送到 Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}推送失败！请检查 Docker Hub 登录状态${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 镜像推送成功${NC}"
else
    echo -e "${BLUE}跳过推送步骤${NC}"
fi

# 4. 显示镜像信息
echo -e "\n${GREEN}[4/4] 镜像信息${NC}"
docker images | grep ${IMAGE_NAME}

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n使用方法:"
echo -e "  本地运行: ${GREEN}docker-compose up -d${NC}"
echo -e "  拉取镜像: ${GREEN}docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo -e "\n访问地址:"
echo -e "  管理端: ${GREEN}http://localhost:8000/admin${NC}"
echo -e "  显示端: ${GREEN}http://localhost:8000/${NC}"
