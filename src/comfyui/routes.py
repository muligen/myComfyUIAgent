import time
from functools import wraps
from flask import Blueprint, jsonify, request, send_file
from .service import execute_workflow, upload_picture, get_video_list, get_workflow_list, get_workflow_content, execute_task, get_history

comfyui_bp = Blueprint('comfyui', __name__)

# 允许的IP地址
ALLOWED_IP = "8.148.242.1"


def ip_restricted(f):
    """IP访问限制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端真实IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR',
                                       request.environ.get('HTTP_X_REAL_IP', request.remote_addr))

        # 如果是通过代理访问，可能包含多个IP，取第一个
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # if client_ip != ALLOWED_IP:
        #     return jsonify({'error': 'Access denied: IP not allowed'}), 403

        return f(*args, **kwargs)
    return decorated_function


@comfyui_bp.route("/execute", methods=["POST"])
@ip_restricted
def execute_flow():
    """执行ComfyUI工作流"""
    try:
        data = request.get_json()
        if not data or "flow_file" not in data:
            return jsonify({"error": "flow_file parameter is required"}), 400

        flow_file = data["flow_file"]
        result = execute_workflow(flow_file)

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


@comfyui_bp.route("/upload_pic", methods=["POST"])
@ip_restricted
def upload_picture_route():
    """上传图片到ComfyUI工作目录"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        result = upload_picture(file)

        return jsonify(
            {
                "success": True,
                "message": "File uploaded successfully",
                "filename": result["filename"],
                "file_path": result["file_path"],
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/videos", methods=["GET"])
@ip_restricted
def get_videos_route():
    """获取所有视频文件列表"""
    try:
        videos = get_video_list()

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(videos)} video files",
                "videos": videos,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/get_video", methods=["GET"])
@ip_restricted
def get_video_route():
    """流式返回视频文件"""
    from .service import get_video_file

    try:
        video_path = request.args.get('video_path')

        if not video_path:
            return jsonify({"error": "video_path parameter is required"}), 400

        return get_video_file(video_path)

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/workflows", methods=["GET"])
@ip_restricted
def get_workflows_route():
    """获取所有工作流文件列表"""
    try:
        workflows = get_workflow_list()

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(workflows)} workflow files",
                "workflows": workflows,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/workflows/<filename>", methods=["GET"])
@ip_restricted
def get_workflow_by_name_route(filename):
    """根据文件名获取工作流内容"""
    try:
        result = get_workflow_content(filename)

        return jsonify(
            {
                "success": True,
                "filename": result["filename"],
                "file_path": result["file_path"],
                "content": result["content"],
            }
        ), 200

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/tasks", methods=["POST"])
@ip_restricted
def create_task():
    """根据提供的工作流数据触发ComfyUI任务"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # 检查是否包含工作流数据
        if "params" not in data:
            return jsonify({"error": "params field is required"}), 400

        workflow_data = data["params"]

        # 可选：检查是否包含client_id（用于WebSocket推送）
        client_id = data.get("client_id")

        # 执行任务
        result = execute_task(workflow_data)
        print("Executing task result:", result)

        if result:
            response_data = {
                "status": "success",
                "task_id": result.get("prompt_id"),
                "queue_position": result.get("number", -1),
                "node_errors": result.get("node_errors", {}),
                "estimated_time": time.time()
            }

            # 如果提供了client_id，添加到响应中
            if client_id:
                response_data["client_id"] = client_id

            return jsonify(response_data), 200
        else:
            return jsonify({"error": "Failed to create task"}), 500

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@comfyui_bp.route("/history", methods=["GET"])
@ip_restricted
def get_history_route():
    """获取ComfyUI的历史记录"""
    try:
        history = get_history()

        if history is not None:
            return jsonify(
                {
                    "status": "success",
                    "message": "History retrieved successfully",
                    "data": history
                }
            ), 200
        else:
            return jsonify({"error": "Failed to retrieve history"}), 500

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

