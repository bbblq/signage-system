#!/bin/bash

# 信发系统 - 开发模式启动脚本

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}信发系统 - 开发模式${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "开发模式特性:"
echo "  ✓ 代码热更新（修改 main.py 自动重启）"
echo "  ✓ 静态文件实时更新（修改 HTML/CSS/JS 立即生效）"
echo "  ✓ 数据持久化"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# 停止生产模式容器（如果在运行）
docker-compose down 2>/dev/null

# 启动开发模式
docker-compose -f docker-compose.dev.yml up -d

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}✗ 启动失败！${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 开发模式已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "访问地址:"
echo -e "  管理端: ${GREEN}http://localhost:8000/admin${NC}"
echo -e "  显示端: ${GREEN}http://localhost:8000/${NC}"
echo ""
echo -e "查看日志: ${BLUE}docker-compose -f docker-compose.dev.yml logs -f${NC}"
echo -e "停止服务: ${BLUE}docker-compose -f docker-compose.dev.yml down${NC}"
echo ""
echo "提示: 现在修改代码文件会自动生效！"
echo "  - 修改 main.py 会自动重启服务"
echo "  - 修改 static/ 下的文件会立即生效"
echo ""
