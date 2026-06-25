"""
Video frame sampling strategies.

Provides multiple sampling strategies for extracting frames from videos:
- Uniform: evenly spaced frames
- Random: randomly selected frames
- Dense: every N-th frame
- Temporal jitter: uniform with random offset
"""

import random
from typing import List, Optional

import numpy as np


class FrameSampler:
    """Sample frames from video sequences.

    Args:
        num_frames: Number of frames to sample.
        strategy: Sampling strategy ('uniform', 'random', 'dense', 'temporal_jitter').
        stride: Frame stride for dense sampling.
    """

    STRATEGIES = ("uniform", "random", "dense", "temporal_jitter")

    def __init__(
        self,
        num_frames: int = 16,
        strategy: str = "uniform",
        stride: int = 1,
    ):
        if num_frames <= 0:
            raise ValueError(f"num_frames must be positive, got {num_frames}")
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy '{strategy}'. Choose from: {self.STRATEGIES}"
            )

        self.num_frames = num_frames
        self.strategy = strategy
        self.stride = stride

    def sample(self, total_frames: int) -> List[int]:
        """Sample frame indices from a video.

        Args:
            total_frames: Total number of frames in the video.

        Returns:
            List of sampled frame indices (0-indexed).

        Raises:
            ValueError: If total_frames is less than 1.
        """
        if total_frames < 1:
            raise ValueError(f"total_frames must be >= 1, got {total_frames}")

        if self.strategy == "uniform":
            return self._uniform_sample(total_frames)
        elif self.strategy == "random":
            return self._random_sample(total_frames)
        elif self.strategy == "dense":
            return self._dense_sample(total_frames)
        elif self.strategy == "temporal_jitter":
            return self._temporal_jitter_sample(total_frames)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _uniform_sample(self, total_frames: int) -> List[int]:
        """Evenly spaced frame sampling."""
        if total_frames <= self.num_frames:
            return list(range(total_frames))

        step = total_frames / self.num_frames
        indices = [int(step * i + step / 2) for i in range(self.num_frames)]
        return [min(idx, total_frames - 1) for idx in indices]

    def _random_sample(self, total_frames: int) -> List[int]:
        """Random frame sampling (sorted by index)."""
        if total_frames <= self.num_frames:
            return list(range(total_frames))

        indices = sorted(random.sample(range(total_frames), self.num_frames))
        return indices

    def _dense_sample(self, total_frames: int) -> List[int]:
        """Dense sampling with fixed stride."""
        # Calculate the total span needed
        span = (self.num_frames - 1) * self.stride + 1

        if total_frames <= span:
            # Video is shorter than needed span, use uniform
            return self._uniform_sample(total_frames)

        # Random start position
        max_start = total_frames - span
        start = random.randint(0, max_start)

        indices = [start + i * self.stride for i in range(self.num_frames)]
        return indices

    def _temporal_jitter_sample(self, total_frames: int) -> List[int]:
        """Uniform sampling with random temporal jitter."""
        if total_frames <= self.num_frames:
            return list(range(total_frames))

        step = total_frames / self.num_frames
        jitter = step / 4  # +/- 25% of step size

        indices = []
        for i in range(self.num_frames):
            center = step * i + step / 2
            offset = random.uniform(-jitter, jitter)
            idx = int(center + offset)
            idx = max(0, min(idx, total_frames - 1))
            indices.append(idx)

        return indices

    def __repr__(self) -> str:
        return (
            f"FrameSampler(num_frames={self.num_frames}, "
            f"strategy='{self.strategy}', stride={self.stride})"
        )
