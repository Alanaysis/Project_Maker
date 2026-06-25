"""帧采样策略模块

实现多种视频帧采样策略，用于从长视频中高效选取代表性帧。
"""

from typing import List, Optional, Tuple

import numpy as np


class FrameSampler:
    """视频帧采样器

    支持多种采样策略：
    - uniform: 均匀采样，等间距选取帧
    - random: 随机采样
    - keyframe: 基于场景变化的关键帧采样
    - dense: 密集采样，每隔固定间隔取帧

    Args:
        num_frames: 目标采样帧数
        method: 采样方法
        seed: 随机种子
    """

    def __init__(
        self,
        num_frames: int = 16,
        method: str = "uniform",
        seed: int = 42,
    ):
        self.num_frames = num_frames
        self.method = method
        self.seed = seed

    def sample(self, total_frames: int) -> np.ndarray:
        """返回采样的帧索引

        Args:
            total_frames: 视频总帧数

        Returns:
            采样帧索引数组
        """
        if total_frames <= 0:
            return np.array([], dtype=int)

        n = min(self.num_frames, total_frames)

        if self.method == "uniform":
            return self._uniform_sample(total_frames, n)
        elif self.method == "random":
            return self._random_sample(total_frames, n)
        elif self.method == "dense":
            return self._dense_sample(total_frames, n)
        else:
            raise ValueError(f"未知采样方法: {self.method}")

    def _uniform_sample(self, total: int, n: int) -> np.ndarray:
        """均匀采样"""
        return np.linspace(0, total - 1, n, dtype=int)

    def _random_sample(self, total: int, n: int) -> np.ndarray:
        """随机采样"""
        rng = np.random.RandomState(self.seed)
        indices = rng.choice(total, size=n, replace=False)
        return np.sort(indices)

    def _dense_sample(self, total: int, n: int) -> np.ndarray:
        """密集采样"""
        step = max(1, total // n)
        indices = list(range(0, total, step))[:n]
        return np.array(indices, dtype=int)

    def sample_with_scores(
        self,
        frames: List[np.ndarray],
        scores: np.ndarray,
        top_k: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """基于分数的采样（用于关键帧提取）

        Args:
            frames: 帧列表
            scores: 每帧的重要性分数
            top_k: 选取前 k 个帧，默认使用 num_frames

        Returns:
            (采样帧索引, 对应分数)
        """
        k = top_k or self.num_frames
        k = min(k, len(scores))
        top_indices = np.argsort(scores)[-k:][::-1]
        top_indices = np.sort(top_indices)
        return top_indices, scores[top_indices]

    def __repr__(self) -> str:
        return f"FrameSampler(num_frames={self.num_frames}, method='{self.method}')"
