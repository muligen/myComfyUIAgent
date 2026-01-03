import json
import os
from flask import send_file
from werkzeug.utils import secure_filename
import requests

# ComfyUI服务配置
COMFYUI_URL = "http://127.0.0.1:8000/prompt"
COMFYUI_WORKSPACE = r"E:\AIDraw\comfyUI"
FLOW_FILE_DIR = r"D:\desktop\comfyui_agent\flow_file"  # 工作流文件目录


def execute_workflow(flow_file: str):
    """执行ComfyUI工作流"""
    # 检查文件是否存在
    if not os.path.exists(flow_file):
        raise FileNotFoundError(f"Flow file not found: {flow_file}")

    # 从文件加载工作流JSON
    with open(flow_file, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # 构造请求体
    payload = {"prompt": workflow}

    # 发送POST请求
    response = requests.post(COMFYUI_URL, json=payload)

    # 处理响应
    if response.status_code == 200:
        result = response.json()
        print("请求成功，任务ID：", result.get("prompt_id"))
        return result
    else:
        print("请求失败，状态码：", response.status_code)
        print("错误信息：", response.text)
        return None


def upload_picture(file):
    """上传图片到ComfyUI input目录"""
    # 检查是否为图片文件
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    if file_ext not in allowed_extensions:
        raise ValueError(f"File type not allowed. Allowed types: {allowed_extensions}")

    # 创建目标目录
    input_dir = os.path.join(COMFYUI_WORKSPACE, "input")
    os.makedirs(input_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(input_dir, filename)
    file.save(file_path)

    return {
        "filename": filename,
        "file_path": file_path
    }


def get_video_list():
    """获取output目录下所有视频文件"""
    output_dir = os.path.join(COMFYUI_WORKSPACE, "output", "video")

    # 检查输出目录是否存在
    if not os.path.exists(output_dir):
        return []

    # 获取所有视频文件
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.gif'}
    video_files = []

    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if (
            os.path.isfile(file_path)
            and os.path.splitext(filename)[1].lower() in video_extensions
        ):
            video_files.append(
                {
                    "filename": filename,
                    "file_path": file_path,
                    "file_size": os.path.getsize(file_path),
                }
            )

    return video_files


def get_video_file(video_path: str):
    """流式返回视频文件"""
    # 安全检查：确保路径在允许的目录内
    allowed_dirs = [
        os.path.join(COMFYUI_WORKSPACE, "output"),
        os.path.join(COMFYUI_WORKSPACE, "output", "video"),
        os.path.join(COMFYUI_WORKSPACE, "input")
    ]

    # 规范化路径
    video_path = os.path.normpath(video_path)

    # 检查路径是否在允许的目录内
    is_allowed = False
    for allowed_dir in allowed_dirs:
        allowed_dir = os.path.normpath(allowed_dir)
        if video_path.startswith(allowed_dir):
            is_allowed = True
            break

    if not is_allowed:
        return {"error": "Access denied: path not allowed"}, 403

    # 检查文件是否存在
    if not os.path.exists(video_path):
        return {"error": f"Video file not found: {video_path}"}, 404

    # 检查是否为文件
    if not os.path.isfile(video_path):
        return {"error": "Path is not a file"}, 400

    # 检查是否为视频文件
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.gif'}
    file_ext = os.path.splitext(video_path)[1].lower()

    if file_ext not in video_extensions:
        return {"error": f"File type not allowed. Allowed types: {video_extensions}"}, 400

    # 流式返回视频文件
    return send_file(
        video_path,
        as_attachment=False,  # 不作为附件，直接在浏览器中播放
        mimetype=None,  # 让Flask自动检测MIME类型
        conditional=True,  # 支持范围请求（断点续传）
        download_name=os.path.basename(video_path)  # 设置下载文件名
    )


def get_workflow_list():
    """获取flow_file目录下所有工作流文件名"""
    # 检查目录是否存在
    if not os.path.exists(FLOW_FILE_DIR):
        return []

    # 获取所有JSON文件
    workflow_files = []
    for filename in os.listdir(FLOW_FILE_DIR):
        file_path = os.path.join(FLOW_FILE_DIR, filename)
        if os.path.isfile(file_path) and filename.endswith('.json'):
            workflow_files.append(filename)

    return workflow_files


def get_workflow_content(filename: str):
    """根据文件名读取工作流文件内容"""
    # 安全检查：确保文件名只包含合法字符
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename")

    # 构建文件路径
    file_path = os.path.join(FLOW_FILE_DIR, filename)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {filename}")

    # 检查是否为JSON文件
    if not filename.endswith('.json'):
        raise ValueError("File must be a JSON file")

    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    return {
        "filename": filename,
        "file_path": file_path,
        "content": content
    }
