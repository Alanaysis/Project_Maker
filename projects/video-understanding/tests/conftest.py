"""测试配置和共享 fixtures"""

import numpy as np
import pytest
import torch


@pytest.fixture
def sample_frames():
    """生成合成视频帧 (T, C, H, W)"""
    return torch.randn(8, 3, 224, 224)


@pytest.fixture
def sample_frames_batch():
    """生成 batch 视频帧 (B, T, C, H, W)"""
    return torch.randn(2, 8, 3, 224, 224)


@pytest.fixture
def sample_numpy_frames():
    """生成合成 numpy 帧列表"""
    return [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(10)]


@pytest.fixture
def small_frames():
    """小尺寸帧，用于快速测试"""
    return torch.randn(4, 3, 64, 64)
