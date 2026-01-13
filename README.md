# 信发系统 - 局域网数字标牌管理系统

一个基于 FastAPI 的局域网数字标牌管理系统，支持多设备管理、图片推送和轮播功能。

## 🚀 快速开始

### 使用 Docker（推荐）

#### 🔧 开发模式（支持代码热更新）

**适用场景**：需要修改代码或前端文件时使用

**Windows 用户：**
```cmd
start-dev.bat
```

**Linux/Mac 用户：**
```bash
bash start-dev.sh
```

**或手动启动：**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**开发模式特性：**
- ✅ 修改 `main.py` 会自动重启服务
- ✅ 修改 `static/` 下的 HTML/CSS/JS 文件会立即生效
- ✅ 无需重新构建镜像
- ✅ 数据持久化

#### 🚀 生产模式（稳定运行）

**适用场景**：部署到服务器或不需要修改代码时使用

1. **构建并启动服务**
```bash
docker-compose up -d
```

2. **访问服务**
- 管理端：http://localhost:8000/admin
- 显示端：http://localhost:8000/
- 显示端可以去 https://www.appcreator24.com/ 打包一个andorid tv的 apk 固定访问网址就可以了

3. **查看日志**
```bash
docker-compose logs -f
```

4. **停止服务**
```bash
docker-compose down
```

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **启动服务**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```



## 📦 Docker 镜像发布与部署

### 1. 构建并推送到 Docker Hub
如果你想自己构建镜像并发布：

```bash
# 构建镜像
docker build -t bbblq/signage-system:latest .

# 推送镜像
docker login
docker push bbblq/signage-system:latest
```

### 2. 使用 Docker Compose 部署 (使用已发布的镜像)
无需下载源码，只需创建一个 `docker-compose.yml` 文件即可运行：

```yaml
version: '3'
services:
  signage-system:
    image: bbblq/signage-system:latest
    container_name: signage-system
    ports:
      - "8000:8000"
    volumes:
      - ./images:/app/images
      - ./devices.json:/app/devices.json
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
```

启动服务：
```bash
docker-compose up -d
```

## 🏗️ 项目结构

```
.
├── main.py              # FastAPI 主应用
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像构建文件
├── docker-compose.yml  # Docker Compose 配置
├── .dockerignore       # Docker 构建忽略文件
├── static/             # 前端静态文件
│   ├── index.html      # 管理端页面
│   └── client.html     # 显示端页面
├── images/             # 图片存储目录（持久化）
└── devices.json        # 设备信息（持久化）
```

## 🔧 环境变量

可以通过环境变量配置以下参数：

- `TZ`: 时区设置（默认：Asia/Shanghai）

在 `docker-compose.yml` 中修改：
```yaml
environment:
  - TZ=Asia/Shanghai
```

## 📱 功能特性

- ✅ 设备自动注册与心跳检测
- ✅ 在线/离线状态监控
- ✅ 图片上传管理
- ✅ 单设备图片推送
- ✅ 批量设备图片推送
- ✅ 图片轮播功能
- ✅ 设备自定义命名
- ✅ 设备手动删除
- ✅ 设备拖拽排序管理
- ✅ 数据持久化

## 🌐 API 端点

### 设备端
- `POST /api/v1/device/heartbeat/{device_id}` - 设备心跳
- `GET /api/v1/device/check_task/{device_id}` - 检查任务

### 管理端
- `GET /api/v1/manager/devices` - 获取设备列表
- `POST /api/v1/manager/upload_image` - 上传图片
- `GET /api/v1/manager/images` - 获取图片列表
- `POST /api/v1/manager/push_image` - 推送图片
- `POST /api/v1/manager/push_image_bulk` - 批量推送
- `POST /api/v1/manager/start_slideshow` - 启动轮播
- `POST /api/v1/manager/stop_slideshow` - 停止轮播
- `POST /api/v1/manager/set_device_name` - 设置设备名称
- `DELETE /api/v1/manager/delete_device/{device_id}` - 删除设备
- `POST /api/v1/manager/update_device_order` - 更新设备排序

### 系统
- `GET /api/v1/server/info` - 获取服务器信息

## 📝 注意事项

1. **数据持久化**：`images/` 目录和 `devices.json` 文件通过 Docker 卷挂载实现持久化
2. **端口配置**：默认使用 8000 端口，可在 `docker-compose.yml` 中修改
3. **网络访问**：确保防火墙允许 8000 端口访问
4. **局域网部署**：建议在局域网内使用，如需外网访问请配置反向代理和 HTTPS

## 🛠️ 故障排查

### 容器无法启动
```bash
# 查看日志
docker-compose logs

# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

### 数据丢失
确保 `docker-compose.yml` 中的卷挂载配置正确：
```yaml
volumes:
  - ./images:/app/images
  - ./devices.json:/app/devices.json
```

## 📄 许可证

MIT License
