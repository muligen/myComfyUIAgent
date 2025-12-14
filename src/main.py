import json
import os
from functools import wraps

import requests
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

# ComfyUI服务地址
COMFYUI_URL = "http://127.0.0.1:8000/prompt"
COMFYUI_WORKSPACE = r"E:\AIDraw\comfyUI"

# 允许的IP地址
ALLOWED_IP = "8.148.242.1"

app = Flask(__name__)

def ip_restricted(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端真实IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('HTTP_X_REAL_IP', request.remote_addr))

        # 如果是通过代理访问，可能包含多个IP，取第一个
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # if client_ip != ALLOWED_IP:
        #     return jsonify({'error': 'Access denied: IP not allowed'}), 403

        return f(*args, **kwargs)
    return decorated_function


def main(flow_file: str):
    # 从文件加载工作流JSON（或直接写在代码中）
    with open(flow_file, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # 构造请求体
    payload = {"prompt": workflow}

    # 发送POST请求
    response = requests.post(COMFYUI_URL, json=payload)

    # 处理响应
    if response.status_code == 200:
        result = response.json()
        print(result)
        print("请求成功，任务ID：", result.get("prompt_id"))  # 用于查询结果
        return result
    else:
        print("请求失败，状态码：", response.status_code)
        print("错误信息：", response.text)
        return None


@app.route("/comfyui/execute", methods=["POST"])
@ip_restricted
def execute_flow():
    try:
        data = request.get_json()
        if not data or "flow_file" not in data:
            return jsonify({"error": "flow_file parameter is required"}), 400

        flow_file = data["flow_file"]

        # 检查文件是否存在
        if not os.path.exists(flow_file):
            return jsonify({"error": f"Flow file not found: {flow_file}"}), 404

        # 调用main方法
        result = main(flow_file)

        if result:
            return jsonify(
                {
                    "success": True,
                    "message": "Workflow executed successfully",
                    "prompt_id": result.get("prompt_id"),
                    "result": result,
                }
            ), 200
        else:
            return jsonify({"error": "Failed to execute workflow"}), 500

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/comfyui/upload_pic", methods=["POST"])
@ip_restricted
def upload_picture():
    try:
        # 检查是否有文件被上传
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # 检查是否为图片文件
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

        if file_ext not in allowed_extensions:
            return jsonify(
                {"error": f"File type not allowed. Allowed types: {allowed_extensions}"}
            ), 400

        # 创建目标目录
        input_dir = os.path.join(COMFYUI_WORKSPACE, "input")
        os.makedirs(input_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(input_dir, filename)
        file.save(file_path)

        return jsonify(
            {
                "success": True,
                "message": "File uploaded successfully",
                "filename": filename,
                "file_path": file_path,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/comfyui/videos", methods=["GET"])
@ip_restricted
def get_videos():
    try:
        output_dir = os.path.join(COMFYUI_WORKSPACE, "output", "video")

        # 检查输出目录是否存在
        if not os.path.exists(output_dir):
            return jsonify(
                {
                    "success": True,
                    "message": "Output directory does not exist",
                    "videos": [],
                }
            ), 200

        # 获取所有视频文件
        video_extensions = {
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".mkv",
            ".gif",
        }
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

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(video_files)} video files",
                "videos": video_files,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/comfyui/get_video", methods=["GET"])
@ip_restricted
def get_video():
    try:
        # 获取视频路径参数
        video_path = request.args.get('video_path')

        if not video_path:
            return jsonify({"error": "video_path parameter is required"}), 400

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
            return jsonify({"error": "Access denied: path not allowed"}), 403

        # 检查文件是否存在
        if not os.path.exists(video_path):
            return jsonify({"error": f"Video file not found: {video_path}"}), 404

        # 检查是否为文件
        if not os.path.isfile(video_path):
            return jsonify({"error": "Path is not a file"}), 400

        # 检查是否为视频文件
        video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.gif'}
        file_ext = os.path.splitext(video_path)[1].lower()

        if file_ext not in video_extensions:
            return jsonify({"error": f"File type not allowed. Allowed types: {video_extensions}"}), 400

        # 流式返回视频文件
        return send_file(
            video_path,
            as_attachment=False,  # 不作为附件，直接在浏览器中播放
            mimetype=None,  # 让Flask自动检测MIME类型
            conditional=True,  # 支持范围请求（断点续传）
            download_name=os.path.basename(video_path)  # 设置下载文件名
        )

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
