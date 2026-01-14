from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import time
import os
import shutil
from pathlib import Path
import sys
import json
import socket
from fastapi import Request

app = FastAPI(title="信发系统后端API", description="用于管理设备和推送图片的API服务")

# --- 数据模型 ---

class DeviceStatus(BaseModel):
    """设备状态模型"""
    last_seen: float
    status: str = "online"
    current_task: Optional[str] = None # 当前正在显示的图片URL（在设备领取任务时更新）
    current_program_name: Optional[str] = None # 当前播放的节目名称或文件名
    name: Optional[str] = None # 设备可自定义名称

class PushTask(BaseModel):
    """推送任务模型"""
    image_url: str
    timestamp: float

# --- 内存存储 (简化版，生产环境应使用数据库) ---

# 存储设备信息: {device_id: DeviceStatus}
devices: Dict[str, DeviceStatus] = {}

# 存储待推送任务: {device_id: PushTask}
pending_tasks: Dict[str, PushTask] = {}

# 设备排序列表（按顺序存储device_id）
device_order: List[str] = []

# 离线与清理阈值（可按需调整）
OFFLINE_THRESHOLD_SECONDS = 60   # 超过该秒数未心跳 -> 标记离线
PRUNE_THRESHOLD_SECONDS = 600    # 超过该秒数未心跳 -> 从列表中移除

# 存储图片信息
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path("static")
# 设备信息持久化文件
DATA_DIR = Path(".")
DEVICES_DB = DATA_DIR / "devices.json"

def load_devices_from_disk() -> None:
    if DEVICES_DB.exists():
        try:
            with open(DEVICES_DB, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for device_id, info in raw.items():
                if device_id.startswith("_"):  # 跳过元数据
                    continue
                devices[device_id] = DeviceStatus(
                    last_seen=info.get("last_seen", time.time()),
                    status=info.get("status", "offline"),
                    current_task=info.get("current_task"),
                    current_program_name=info.get("current_program_name"),
                    name=info.get("name")
                )
            # 加载设备排序
            global device_order
            device_order = raw.get("_device_order", [])
            # 确保排序列表包含所有现有设备
            for device_id in devices.keys():
                if device_id not in device_order:
                    device_order.append(device_id)
        except Exception:
            # 读取失败则忽略，保持内存默认
            pass

def save_devices_to_disk() -> None:
    try:
        serialized = {
            device_id: {
                "last_seen": status.last_seen,
                "status": status.status,
                "current_task": status.current_task,
                "current_program_name": status.current_program_name,
                "name": status.name,
            }
            for device_id, status in devices.items()
        }
        # 保存设备排序
        serialized["_device_order"] = device_order
        with open(DEVICES_DB, "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)
    except Exception:
        # 写盘失败不抛出，避免影响接口
        pass
# 使用相对路径提供图片URL，避免硬编码主机与端口

# 默认图片URL
DEFAULT_IMAGE_FILENAME = "default.jpg"
DEFAULT_IMAGE_URL = f"/images/{DEFAULT_IMAGE_FILENAME}"

# --- API 路由 ---

@app.get("/api")
def read_root():
    """API根路径，用于健康检查"""
    return {"message": "信发系统API运行中"}

@app.get("/")
def serve_display():
    """提供客户端显示界面 (显示端)"""
    client_path = STATIC_DIR / "client.html"
    return FileResponse(str(client_path))

@app.get("/admin")
def serve_admin():
    """提供管理界面 (发布端)"""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path))

# 1. 客户端 (安卓电视) 接口

@app.post("/api/v1/device/heartbeat/{device_id}")
def device_heartbeat(device_id: str):
    """
    安卓电视客户端定时发送心跳，并注册设备。
    """
    current_time = time.time()
    # 如果设备已存在，仅更新心跳；否则初始化并设置默认图片
    existing = devices.get(device_id)
    if existing:
        existing.last_seen = current_time
        existing.status = "online"
    else:
        devices[device_id] = DeviceStatus(
            last_seen=current_time,
            status="online",
            current_task=DEFAULT_IMAGE_URL,
            name=device_id
        )
    save_devices_to_disk()
    return {"message": "Heartbeat received", "device_id": device_id, "name": devices[device_id].name}

@app.get("/api/v1/device/check_task/{device_id}")
def check_task(device_id: str):
    """
    安卓电视客户端定时轮询，检查是否有新的推送任务或轮播任务。
    """
    # 检查设备是否在线
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not registered")

    # 1. 优先处理推送任务
    if device_id in pending_tasks:
        task = pending_tasks.pop(device_id)
        devices[device_id].current_task = task.image_url
        save_devices_to_disk()
        return {"task_available": True, "image_url": task.image_url}
    
    # 2. 处理轮播任务
    if device_id in slideshow_tasks:
        slideshow = slideshow_tasks[device_id]
        current_time = time.time()
        
        # 计算当前应该显示的图片索引
        elapsed = current_time - slideshow.timestamp
        image_index = int(elapsed / slideshow.interval_seconds) % len(slideshow.image_filenames)
        current_image = slideshow.image_filenames[image_index]
        current_image_url = f"/images/{current_image}"
        
        # 更新设备当前任务
        devices[device_id].current_task = current_image_url
        save_devices_to_disk()
        
        return {"task_available": True, "image_url": current_image_url}

    # 3. 无新任务时返回当前设备应显示的图片（若已存在）
    current = devices[device_id].current_task if device_id in devices else None
    return {"task_available": False, "image_url": current}

# 2. 管理端 (前端) 接口

@app.get("/api/v1/manager/devices")
def get_devices():
    """
    获取所有注册设备的列表和状态。
    """
    current_time = time.time()
    online_or_recent_devices: Dict[str, DeviceStatus] = {}
    to_delete: List[str] = []

    for device_id, status in devices.items():
        delta = current_time - status.last_seen
        if delta < OFFLINE_THRESHOLD_SECONDS:
            # 在线
            status.status = "online"
            online_or_recent_devices[device_id] = status
        elif delta < PRUNE_THRESHOLD_SECONDS:
            # 离线但保留一段时间显示
            status.status = "offline"
            online_or_recent_devices[device_id] = status
        else:
            # 长时间未心跳，但重命名过的设备不自动删除
            if status.name and status.name != device_id:
                # 重命名过的设备，标记为离线但不删除
                status.status = "offline"
                online_or_recent_devices[device_id] = status
            else:
                # 未重命名的设备，长时间未心跳则移除
                to_delete.append(device_id)

    if to_delete:
        for device_id in to_delete:
            devices.pop(device_id, None)
            pending_tasks.pop(device_id, None)
        save_devices_to_disk()

    # 按排序返回设备列表
    ordered_devices = {}
    for device_id in device_order:
        if device_id in online_or_recent_devices:
            ordered_devices[device_id] = online_or_recent_devices[device_id]
    # 添加不在排序列表中的设备
    for device_id, status in online_or_recent_devices.items():
        if device_id not in ordered_devices:
            ordered_devices[device_id] = status
            device_order.append(device_id)  # 自动添加到排序列表
    
    return ordered_devices

@app.post("/api/v1/manager/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片文件到服务器。
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image.")

    file_path = IMAGE_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        await file.close()

    return {"filename": file.filename, "url": f"/images/{file.filename}", "message": "Image uploaded successfully"}

@app.get("/api/v1/manager/images")
def get_images():
    """
    获取所有已上传的图片列表。
    """
    images = []
    for item in IMAGE_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            images.append({
                "filename": item.name,
                "url": f"/images/{item.name}"
            })
    return images

@app.delete("/api/v1/manager/delete_image/{filename}")
def delete_image(filename: str):
    """删除图片文件"""
    file_path = IMAGE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")
    return {"message": f"Image {filename} deleted"}

@app.post("/api/v1/manager/push_image")
def push_image(device_id: str = Body(..., embed=True), image_filename: str = Body(..., embed=True)):
    """
    向指定的设备推送指定的图片。
    """
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found or not registered")

    image_path = IMAGE_DIR / image_filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found on server")

    image_url = f"/images/{image_filename}"
    
    # 创建推送任务
    task = PushTask(image_url=image_url, timestamp=time.time())
    pending_tasks[device_id] = task
    
    # 立即更新设备状态中的当前节目名
    devices[device_id].current_program_name = image_filename
    devices[device_id].current_task = image_url
    save_devices_to_disk()
    
    return {"message": f"Push command sent to device {device_id}", "image_url": image_url}

@app.post("/api/v1/manager/push_image_bulk")
def push_image_bulk(device_ids: List[str] = Body(..., embed=True), image_filename: str = Body(..., embed=True)):
    """
    批量向多个设备推送同一图片。
    """
    image_path = IMAGE_DIR / image_filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found on server")

    image_url = f"/images/{image_filename}"
    created_for: List[str] = []
    for device_id in device_ids:
        if device_id not in devices:
            # 跳过未注册设备
            continue
        pending_tasks[device_id] = PushTask(image_url=image_url, timestamp=time.time())
        # 立即更新设备状态中的当前节目名
        devices[device_id].current_program_name = image_filename
        devices[device_id].current_task = image_url
        created_for.append(device_id)
    save_devices_to_disk()
    return {"message": f"Push command sent to {len(created_for)} devices", "image_url": image_url, "device_ids": created_for}

class SetNamePayload(BaseModel):
    device_id: str
    name: str

@app.post("/api/v1/manager/set_device_name")
def set_device_name(payload: SetNamePayload):
    """
    设置设备自定义名称，持久化保存。
    """
    device_id = payload.device_id
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found or not registered")
    devices[device_id].name = payload.name
    save_devices_to_disk()
    return {"message": "Device name updated", "device_id": device_id, "name": payload.name}

@app.delete("/api/v1/manager/delete_device/{device_id}")
def delete_device(device_id: str):
    """删除设备（手动移除）"""
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 从内存中移除
    devices.pop(device_id, None)
    pending_tasks.pop(device_id, None)
    if device_id in device_order:
        device_order.remove(device_id)
    
    save_devices_to_disk()
    return {"message": f"Device {device_id} deleted successfully"}

class SlideshowTask(BaseModel):
    """轮播任务模型"""
    image_filenames: List[str]
    interval_seconds: int = 10
    timestamp: float

# 存储轮播任务: {device_id: SlideshowTask}
slideshow_tasks: Dict[str, SlideshowTask] = {}

@app.post("/api/v1/manager/start_slideshow")
def start_slideshow(device_id: str = Body(..., embed=True), 
                    image_filenames: List[str] = Body(..., embed=True), 
                    interval_seconds: int = Body(..., embed=True),
                    program_name: str = Body("轮播节目", embed=True)):
    """为指定设备启动轮播任务"""
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 验证图片文件存在
    valid_images = []
    for filename in image_filenames:
        if (IMAGE_DIR / filename).exists():
            valid_images.append(filename)
    
    if not valid_images:
        raise HTTPException(status_code=400, detail="No valid images found")
    
    # 按文件名排序
    valid_images.sort()
    
    slideshow_tasks[device_id] = SlideshowTask(
        image_filenames=valid_images,
        interval_seconds=max(5, interval_seconds),  # 最少5秒间隔
        timestamp=time.time()
    )
    
    # 更新设备状态中的当前节目名
    devices[device_id].current_program_name = program_name
    if valid_images:
        devices[device_id].current_task = f"/images/{valid_images[0]}"
    save_devices_to_disk()
    
    return {"message": f"Slideshow started for device {device_id}", "images": valid_images, "interval": interval_seconds}

@app.post("/api/v1/manager/stop_slideshow")
def stop_slideshow(device_id: str = Body(..., embed=True)):
    """停止指定设备的轮播任务"""
    if device_id in slideshow_tasks:
        slideshow_tasks.pop(device_id)
        return {"message": f"Slideshow stopped for device {device_id}"}
    return {"message": "No slideshow task found"}

@app.post("/api/v1/manager/update_device_order")
def update_device_order(new_order: List[str] = Body(..., embed=True)):
    """更新设备排序"""
    global device_order
    # 验证所有设备ID都存在
    valid_order = [device_id for device_id in new_order if device_id in devices]
    device_order = valid_order
    save_devices_to_disk()
    return {"message": "Device order updated", "order": device_order}

# 3. 静态文件服务 (用于提供图片和前端页面)
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 启动时尝试加载设备信息
load_devices_from_disk()

def get_local_ips() -> List[str]:
    ips: List[str] = []
    # 方法1: UDP 探测主要出口IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and primary_ip != "127.0.0.1":
            ips.append(primary_ip)
    except Exception:
        pass
    # 方法2: 解析主机名得到的本机IP
    try:
        hostname = socket.gethostname()
        for res in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = res[4][0]
            if ip and ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        ips.append("127.0.0.1")
    return ips

@app.get("/api/v1/server/info")
def server_info(request: Request):
    """返回本机可用局域网IP与端口，便于在页面展示访问地址。"""
    try:
        port = request.url.port or (443 if request.url.scheme == "https" else 80)
    except Exception:
        port = 8000
    ips = get_local_ips()
    return {
        "ips": ips,
        "port": port,
        "admin_urls": [f"http://{ip}:{port}/admin" for ip in ips],
        "display_urls": [f"http://{ip}:{port}/" for ip in ips],
    }

# 运行说明：
# Docker方式: docker-compose up -d
# 本地开发: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

