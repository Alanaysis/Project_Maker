"""视频数据集加载模块

提供 PyTorch Dataset 接口，用于加载视频数据。
"""

import os
from typing import Callable, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from video_understanding.data.frame_sampler import FrameSampler
from video_understanding.utils.video_utils import extract_frames, frames_to_tensor


class VideoDataset(Dataset):
    """视频数据集

    支持从目录结构加载视频文件，返回采样后的帧张量和标签。

    目录结构:
        root/
        ├── class1/
        │   ├── video1.mp4
        │   └── video2.mp4
        └── class2/
            ├── video3.mp4
            └── video4.mp4

    Args:
        root: 数据根目录
        sampler: 帧采样器
        frame_size: 帧的目标大小 (H, W)
        transform: 可选的数据增强变换
        extensions: 支持的视频文件扩展名
    """

    def __init__(
        self,
        root: str,
        sampler: Optional[FrameSampler] = None,
        frame_size: Tuple[int, int] = (224, 224),
        transform: Optional[Callable] = None,
        extensions: Tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv"),
    ):
        self.root = root
        self.sampler = sampler or FrameSampler()
        self.frame_size = frame_size
        self.transform = transform
        self.extensions = extensions

        self.samples: List[Tuple[str, int]] = []
        self.classes: List[str] = []
        self.class_to_idx: dict = {}

        self._scan_directory()

    def _scan_directory(self):
        """扫描目录，收集视频路径和标签"""
        if not os.path.isdir(self.root):
            return

        classes = sorted(
            d for d in os.listdir(self.root)
            if os.path.isdir(os.path.join(self.root, d))
        )
        self.classes = classes
        self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}

        for cls in classes:
            cls_dir = os.path.join(self.root, cls)
            for fname in sorted(os.listdir(cls_dir)):
                if any(fname.lower().endswith(ext) for ext in self.extensions):
                    path = os.path.join(cls_dir, fname)
                    self.samples.append((path, self.class_to_idx[cls]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """获取一个视频样本

        Args:
            idx: 样本索引

        Returns:
            (frames_tensor, label) - frames_tensor 形状为 (T, C, H, W)
        """
        video_path, label = self.samples[idx]

        # 采样帧
        frames = extract_frames(video_path, method=self.sampler.method, num_frames=self.sampler.num_frames)

        # 转为张量
        tensor = frames_to_tensor(frames, size=self.frame_size)

        # 应用变换
        if self.transform:
            tensor = self.transform(tensor)

        return tensor, label

    def get_class_names(self) -> List[str]:
        """获取类别名称列表"""
        return self.classes

    def __repr__(self) -> str:
        return (
            f"VideoDataset(root='{self.root}', samples={len(self)}, "
            f"classes={len(self.classes)}, sampler={self.sampler})"
        )


class SyntheticVideoDataset(Dataset):
    """合成视频数据集（用于测试和调试）

    生成随机视频帧张量和标签，无需真实视频文件。

    Args:
        num_samples: 样本数量
        num_frames: 每个视频的帧数
        num_classes: 类别数
        frame_size: 帧大小 (H, W)
        seed: 随机种子
    """

    def __init__(
        self,
        num_samples: int = 100,
        num_frames: int = 16,
        num_classes: int = 10,
        frame_size: Tuple[int, int] = (224, 224),
        seed: int = 42,
    ):
        self.num_samples = num_samples
        self.num_frames = num_frames
        self.num_classes = num_classes
        self.frame_size = frame_size
        self.rng = np.random.RandomState(seed)

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        frames = torch.randn(self.num_frames, 3, *self.frame_size)
        label = self.rng.randint(0, self.num_classes)
        return frames, label

    def __repr__(self) -> str:
        return (
            f"SyntheticVideoDataset(num_samples={self.num_samples}, "
            f"num_frames={self.num_frames}, num_classes={self.num_classes})"
        )
