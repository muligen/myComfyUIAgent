### 开发文档

#### 一、本地调用comfyui生成视频。

##### 测试调用生成完成

    测试通过： 
        comfyui似乎围绕其根目录下的各个目录来工作。不需要在prompt中填入绝对路径定位工作文件。
        首先需要把工作流导出api，
        其次，修改其中的输入和输出。在输入的图片，只能填图片名，然后确保comfyui\input里面有这个图片。
        另外为了获得比较固定的输出文件名，可以修改prompt中的filename_prefix，然后输出的产物只会在comfyui\output文件夹，
        会以这个前缀输出最终文件，以此来检索本次生成的video。


#### 二、agent服务器功能
1. post /comfyui/execute，接受flow_file路径参数,调用main方法
2. post /comfyui/upload_pic, 接受图片资源，并将其存在{{COMFYUI_WORKSPACE}}/input
3. get  /comfyui/videos, 返回{{COMFYUI_WORKSPACE}}/output所有视频路径
4. get  /comfyui/get_video, 接受传入的视频路径，流式返回视频