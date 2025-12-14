import requests
import json

# ComfyUI服务地址
COMFYUI_URL = "http://127.0.0.1:8000/prompt"

# 从文件加载工作流JSON（或直接写在代码中）
with open(r"test\video_wan2_2_5B_ti2v.json", "r", encoding="utf-8") as f:
    workflow = json.load(f )

# 构造请求体
payload = {"prompt": workflow}

# 发送POST请求
response = requests.post(COMFYUI_URL, json=payload)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(result)
    print("请求成功，任务ID：", result.get("prompt_id"))  # 用于查询结果
else:
    print("请求失败，状态码：", response.status_code)
    print("错误信息：", response.text)
