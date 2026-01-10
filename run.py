import subprocess
import sys
import threading

from flask import Flask

from src.comfyui import comfyui_bp

app = Flask(__name__)

# 注册ComfyUI蓝图
app.register_blueprint(comfyui_bp, url_prefix="/comfyui")


def start_thumbnail_generator():
    """
    启动缩略图生成器子进程
    """
    print("正在启动缩略图生成器子进程...")
    # 使用 subprocess 启动独立的子进程
    process = subprocess.Popen(
        [sys.executable, "-m", "src.thumbnail_generator"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 定义一个函数在后台读取子进程输出
    def log_subprocess_output():
        for line in process.stdout:
            print(f"[缩略图生成器] {line}", end="")
        for line in process.stderr:
            print(f"[缩略图生成器错误] {line}", end="")

    # 启动线程读取输出
    log_thread = threading.Thread(target=log_subprocess_output, daemon=True)
    log_thread.start()

    return process


@app.route("/")
def index():
    return """
    <h1>ComfyUI Agent API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li>POST /comfyui/execute - 执行ComfyUI工作流</li>
        <li>POST /comfyui/upload_pic - 上传图片</li>
        <li>GET /comfyui/videos - 获取视频列表</li>
        <li>GET /comfyui/get_video - 获取视频文件</li>
    </ul>
    """


if __name__ == "__main__":
    # 启动缩略图生成器子进程
    thumbnail_process = start_thumbnail_generator()

    try:
        # 启动Flask服务器
        print("启动Flask服务器...")
        app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)
    finally:
        # 退出时终止子进程
        if thumbnail_process:
            print("正在停止缩略图生成器...")
            thumbnail_process.terminate()
            thumbnail_process.wait()
