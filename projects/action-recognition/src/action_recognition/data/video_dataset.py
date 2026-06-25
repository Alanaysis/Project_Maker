"""
Video dataset for action recognition.

Supports loading videos from directory structures like:
    data_root/
        class1/
            video1.mp4
            video2.mp4
        class2/
            ...

Also supports pre-extracted frame directories and synthetic data for testing.
"""

import os
import random
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from action_recognition.data.frame_sampler import FrameSampler


class VideoDataset(Dataset):
    """Dataset for loading video clips with action labels.

    Supports three data formats:
        - Video files (.mp4, .avi, .mov) via OpenCV
        - Frame directories (one folder per video with numbered frames)
        - Synthetic data (for testing without real videos)

    Args:
        data_root: Root directory containing class subdirectories.
        frame_sampler: FrameSampler instance for frame selection.
        transform: Optional transform applied to each frame.
        frame_size: Target frame size (H, W).
        class_to_idx: Mapping from class name to index. Auto-detected if None.
        synthetic: If True, generate synthetic data for testing.
        num_synthetic_classes: Number of classes for synthetic mode.
    """

    VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

    def __init__(
        self,
        data_root: str = "",
        frame_sampler: Optional[FrameSampler] = None,
        transform: Optional[Callable] = None,
        frame_size: Tuple[int, int] = (224, 224),
        class_to_idx: Optional[Dict[str, int]] = None,
        synthetic: bool = False,
        num_synthetic_classes: int = 10,
        num_synthetic_samples: int = 100,
        num_frames: int = 16,
    ):
        self.data_root = data_root
        self.frame_sampler = frame_sampler or FrameSampler(num_frames=num_frames)
        self.transform = transform
        self.frame_size = frame_size
        self.synthetic = synthetic

        if synthetic:
            self.num_classes = num_synthetic_classes
            self.class_to_idx = {
                f"action_{i}": i for i in range(num_synthetic_classes)
            }
            self.samples = [
                (f"synthetic_{i}", i % num_synthetic_classes)
                for i in range(num_synthetic_samples)
            ]
        else:
            if not data_root or not os.path.isdir(data_root):
                raise ValueError(f"data_root must be a valid directory: {data_root}")
            self.class_to_idx = class_to_idx or self._discover_classes()
            self.num_classes = len(self.class_to_idx)
            self.samples = self._discover_samples()

    def _discover_classes(self) -> Dict[str, int]:
        """Discover class names from directory structure."""
        classes = sorted(
            d for d in os.listdir(self.data_root)
            if os.path.isdir(os.path.join(self.data_root, d))
        )
        return {cls: idx for idx, cls in enumerate(classes)}

    def _discover_samples(self) -> List[Tuple[str, int]]:
        """Discover all video samples with their class labels."""
        samples = []
        for cls_name, cls_idx in self.class_to_idx.items():
            cls_dir = os.path.join(self.data_root, cls_name)
            if not os.path.isdir(cls_dir):
                continue
            for fname in sorted(os.listdir(cls_dir)):
                fpath = os.path.join(cls_dir, fname)
                ext = os.path.splitext(fname)[1].lower()
                if os.path.isfile(fpath) and (
                    ext in self.VIDEO_EXTENSIONS or ext in self.IMAGE_EXTENSIONS
                ):
                    samples.append((fpath, cls_idx))
        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a video clip and its label.

        Args:
            idx: Sample index.

        Returns:
            Tuple of (video_tensor, label).
            video_tensor: (T, C, H, W) float tensor normalized to [0, 1].
            label: Integer class label.
        """
        fpath, label = self.samples[idx]

        if self.synthetic:
            frames = self._generate_synthetic_frames()
        else:
            frames = self._load_frames(fpath)

        if self.transform:
            frames = [self.transform(f) for f in frames]

        video_tensor = torch.stack(frames)  # (T, C, H, W)
        return video_tensor, label

    def _generate_synthetic_frames(self) -> List[torch.Tensor]:
        """Generate random synthetic frames for testing."""
        C, H, W = 3, self.frame_size[0], self.frame_size[1]
        T = self.frame_sampler.num_frames
        frames = torch.rand(T, C, H, W)
        return [frames[i] for i in range(T)]

    def _load_frames(self, fpath: str) -> List[torch.Tensor]:
        """Load frames from video file or frame directory."""
        try:
            import cv2
        except ImportError:
            raise ImportError("OpenCV (cv2) is required for loading videos. "
                              "Install with: pip install opencv-python")

        ext = os.path.splitext(fpath)[1].lower()

        if ext in self.VIDEO_EXTENSIONS:
            return self._load_from_video(fpath)
        else:
            return self._load_from_frames(fpath)

    def _load_from_video(self, video_path: str) -> List[torch.Tensor]:
        """Load frames from a video file using OpenCV."""
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise ValueError(f"Video has no frames: {video_path}")

        indices = self.frame_sampler.sample(total_frames)
        frames = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.frame_size[1], self.frame_size[0]))
                frame_tensor = torch.from_numpy(frame).float().permute(2, 0, 1) / 255.0
                frames.append(frame_tensor)

        cap.release()

        if not frames:
            raise ValueError(f"No frames loaded from: {video_path}")

        return frames

    def _load_from_frames(self, image_path: str) -> List[torch.Tensor]:
        """Load from a single image (repeated for temporal consistency)."""
        import cv2

        frame = cv2.imread(image_path)
        if frame is None:
            raise IOError(f"Cannot read image: {image_path}")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.frame_size[1], self.frame_size[0]))
        frame_tensor = torch.from_numpy(frame).float().permute(2, 0, 1) / 255.0

        # Repeat single frame to create temporal sequence
        return [frame_tensor] * self.frame_sampler.num_frames

    def get_class_names(self) -> List[str]:
        """Return list of class names sorted by index."""
        return sorted(self.class_to_idx, key=self.class_to_idx.get)
