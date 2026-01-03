from flask import Flask

from src.comfyui import comfyui_bp

app = Flask(__name__)

# 注册ComfyUI蓝图
app.register_blueprint(comfyui_bp, url_prefix="/comfyui")


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
    app.run(debug=True, host="0.0.0.0", port=5001)
