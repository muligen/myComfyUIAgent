"""
缩略图生成器子进程
监控 COMFYUI_INPUT 和 COMFYUI_OUTPUT 文件夹，为新文件生成缩略图
"""

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Set

FFMPEG_PATH = r"D:\xiezuo\resources\ffmpeg\ffmpeg.exe"


class ThumbnailGenerator:
    """缩略图生成器"""

    # 支持的图片和视频格式
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
    VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        input_thumb_dir: str,
        output_thumb_dir: str,
    ):
        """
        初始化缩略图生成器

        Args:
            input_dir: ComfyUI输入文件夹
            output_dir: ComfyUI输出文件夹
            input_thumb_dir: 输入缩略图文件夹
            output_thumb_dir: 输出缩略图文件夹
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_thumb_dir = Path(input_thumb_dir)
        self.output_thumb_dir = Path(output_thumb_dir)

        # 创建缩略图文件夹
        self.input_thumb_dir.mkdir(parents=True, exist_ok=True)
        self.output_thumb_dir.mkdir(parents=True, exist_ok=True)

        # 记录已处理的文件
        self.processed_files: Dict[str, Set[str]] = {
            str(self.input_dir): set(),
            str(self.output_dir): set(),
        }

        # 缩略图尺寸
        self.thumbnail_size = "200x200"  # 视频缩略图尺寸
        self.thumbnail_quality = 85  # 图片质量

    def _is_media_file(self, file_path: Path) -> bool:
        """检查是否是媒体文件"""
        return (
            file_path.suffix.lower() in self.IMAGE_EXTENSIONS
            or file_path.suffix.lower() in self.VIDEO_EXTENSIONS
        )

    def _generate_image_thumbnail(self, input_path: Path, output_path: Path) -> bool:
        """
        使用 ffmpeg 生成图片缩略图

        Args:
            input_path: 输入图片路径
            output_path: 输出缩略图路径

        Returns:
            是否成功生成
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                FFMPEG_PATH,
                "-i",
                str(input_path),
                "-vf",
                f"scale={self.thumbnail_size}:force_original_aspect_ratio=decrease",
                "-q:v",
                str(self.thumbnail_quality),
                "-y",  # 覆盖已存在的文件
                str(output_path),
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"生成图片缩略图失败 {input_path}: {e}")
            return False

    def _generate_video_thumbnail(self, input_path: Path, output_path: Path) -> bool:
        """
        使用 ffmpeg 从视频中提取第一帧作为缩略图

        Args:
            input_path: 输入视频路径
            output_path: 输出缩略图路径

        Returns:
            是否成功生成
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # 提取视频第一帧并缩放
            cmd = [
                FFMPEG_PATH,
                "-i",
                str(input_path),
                "-ss",
                "00:00:00",  # 从开始位置
                "-vframes",
                "1",  # 只提取一帧
                "-vf",
                f"scale={self.thumbnail_size}:force_original_aspect_ratio=decrease",
                "-q:v",
                str(self.thumbnail_quality),
                "-y",  # 覆盖已存在的文件
                str(output_path),
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"生成视频缩略图失败 {input_path}: {e}")
            return False

    def _generate_thumbnail(self, file_path: Path) -> bool:
        """
        为文件生成缩略图

        Args:
            file_path: 文件路径

        Returns:
            是否成功生成
        """
        # 确定源目录和目标缩略图目录
        if file_path.parent == self.input_dir:
            thumb_dir = self.input_thumb_dir
        elif file_path.parent == self.output_dir:
            thumb_dir = self.output_thumb_dir
        else:
            return False

        # 生成缩略图路径
        thumb_path = thumb_dir / f"{file_path.stem}_thumb.jpg"

        # 根据文件类型选择生成方法
        if file_path.suffix.lower() in self.IMAGE_EXTENSIONS:
            return self._generate_image_thumbnail(file_path, thumb_path)
        elif file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
            return self._generate_video_thumbnail(file_path, thumb_path)

        return False

    def _scan_directory(self, directory: Path) -> Set[Path]:
        """
        扫描目录获取所有媒体文件

        Args:
            directory: 目录路径

        Returns:
            媒体文件集合
        """
        if not directory.exists():
            return set()

        media_files = set()
        try:
            for item in directory.iterdir():
                if item.is_file() and self._is_media_file(item):
                    media_files.add(item)
        except PermissionError:
            print(f"没有权限访问目录: {directory}")

        return media_files

    def _process_new_files(self):
        """处理新文件"""
        # 扫描输入和输出目录
        input_files = self._scan_directory(self.input_dir)
        output_files = self._scan_directory(self.output_dir)

        # 检查新文件并生成缩略图
        for file_path in input_files | output_files:
            file_key = str(file_path)
            parent_dir = str(file_path.parent)

            if file_key not in self.processed_files.get(parent_dir, set()):
                print(f"发现新文件: {file_path}")
                if self._generate_thumbnail(file_path):
                    print(f"缩略图生成成功: {file_path}")
                    self.processed_files[parent_dir].add(file_key)
                else:
                    print(f"缩略图生成失败: {file_path}")

    def start(self, check_interval: int = 5):
        """
        启动缩略图生成器

        Args:
            check_interval: 检查间隔（秒）
        """
        print(f"缩略图生成器已启动")
        print(f"监控目录: {self.input_dir}, {self.output_dir}")
        print(f"缩略图目录: {self.input_thumb_dir}, {self.output_thumb_dir}")
        print(f"检查间隔: {check_interval}秒")

        # 首次扫描，生成所有已有文件的缩略图
        print("执行首次扫描...")
        self._process_new_files()

        # 持续监控
        try:
            while True:
                time.sleep(check_interval)
                self._process_new_files()
        except KeyboardInterrupt:
            print("\n缩略图生成器已停止")


def main():
    """主函数"""
    # 配置路径
    COMFYUI_INPUT = r"E:\AIDraw\comfyUI\input"
    COMFYUI_OUTPUT = r"E:\AIDraw\comfyUI\output"
    COMFYUI_INPUT_THUMB = r"E:\AIDraw\comfyUI\input\thumbnails"
    COMFYUI_OUTPUT_THUMB = r"E:\AIDraw\comfyUI\output\thumbnails"

    # 创建并启动生成器
    generator = ThumbnailGenerator(
        input_dir=COMFYUI_INPUT,
        output_dir=COMFYUI_OUTPUT,
        input_thumb_dir=COMFYUI_INPUT_THUMB,
        output_thumb_dir=COMFYUI_OUTPUT_THUMB,
    )

    generator.start(check_interval=5)


if __name__ == "__main__":
    main()
