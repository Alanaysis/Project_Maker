"""视频处理工具函数"""

from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch


def load_video(video_path: str, max_frames: Optional[int] = None) -> List[np.ndarray]:
    """加载视频并提取所有帧

    Args:
        video_path: 视频文件路径
        max_frames: 最大帧数限制

    Returns:
        帧列表，每帧为 (H, W, 3) 的 numpy 数组（BGR格式）
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频文件: {video_path}")

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if max_frames and len(frames) >= max_frames:
            break

    cap.release()
    return frames


def get_video_info(video_path: str) -> dict:
    """获取视频基本信息

    Args:
        video_path: 视频文件路径

    Returns:
        包含视频信息的字典
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频文件: {video_path}")

    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0

    cap.release()
    return info


def extract_frames(
    video_path: str,
    method: str = "uniform",
    num_frames: int = 16,
    max_frames: Optional[int] = None,
) -> List[np.ndarray]:
    """从视频中按策略提取帧

    Args:
        video_path: 视频文件路径
        method: 采样方法 ('uniform', 'random', 'dense')
        num_frames: 采样帧数
        max_frames: 最大读取帧数

    Returns:
        采样后的帧列表
    """
    all_frames = load_video(video_path, max_frames=max_frames)
    if len(all_frames) == 0:
        return []

    if method == "uniform":
        indices = np.linspace(0, len(all_frames) - 1, num_frames, dtype=int)
    elif method == "random":
        indices = sorted(np.random.choice(len(all_frames), min(num_frames, len(all_frames)), replace=False))
    elif method == "dense":
        step = max(1, len(all_frames) // num_frames)
        indices = list(range(0, len(all_frames), step))[:num_frames]
    else:
        raise ValueError(f"未知采样方法: {method}")

    return [all_frames[i] for i in indices]


def frames_to_tensor(
    frames: List[np.ndarray],
    size: Tuple[int, int] = (224, 224),
    normalize: bool = True,
) -> torch.Tensor:
    """将帧列表转换为 PyTorch 张量

    Args:
        frames: 帧列表，每帧为 (H, W, 3) 的 numpy 数组
        size: 目标大小 (H, W)
        normalize: 是否归一化到 [0, 1]

    Returns:
        形状为 (T, C, H, W) 的张量
    """
    tensors = []
    for frame in frames:
        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # resize
        frame_resized = cv2.resize(frame_rgb, (size[1], size[0]))
        # HWC -> CHW
        frame_chw = frame_resized.transpose(2, 0, 1)
        tensors.append(frame_chw)

    tensor = np.stack(tensors, axis=0).astype(np.float32)
    if normalize:
        tensor = tensor / 255.0

    return torch.from_numpy(tensor)


def compute_histogram(frame: np.ndarray, bins: int = 64) -> np.ndarray:
    """计算帧的颜色直方图

    Args:
        frame: 输入帧 (H, W, 3)
        bins: 直方图 bin 数

    Returns:
        归一化的直方图向量
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [bins, bins], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten()
