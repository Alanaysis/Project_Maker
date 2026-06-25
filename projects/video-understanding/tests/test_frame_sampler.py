"""帧采样器测试"""

import numpy as np
import pytest

from video_understanding.data.frame_sampler import FrameSampler


class TestFrameSampler:
    """FrameSampler 测试类"""

    def test_init(self):
        """测试初始化"""
        sampler = FrameSampler(num_frames=16, method="uniform")
        assert sampler.num_frames == 16
        assert sampler.method == "uniform"

    def test_uniform_sample(self):
        """测试均匀采样"""
        sampler = FrameSampler(num_frames=5, method="uniform")
        indices = sampler.sample(100)
        assert len(indices) == 5
        assert indices[0] == 0
        assert indices[-1] == 99

    def test_random_sample(self):
        """测试随机采样"""
        sampler = FrameSampler(num_frames=5, method="random", seed=42)
        indices = sampler.sample(100)
        assert len(indices) == 5
        # 随机采样结果应该已排序
        assert all(indices[i] <= indices[i + 1] for i in range(len(indices) - 1))

    def test_dense_sample(self):
        """测试密集采样"""
        sampler = FrameSampler(num_frames=5, method="dense")
        indices = sampler.sample(100)
        assert len(indices) == 5

    def test_sample_more_than_available(self):
        """测试采样数超过总帧数"""
        sampler = FrameSampler(num_frames=100, method="uniform")
        indices = sampler.sample(10)
        assert len(indices) == 10

    def test_zero_frames(self):
        """测试零帧输入"""
        sampler = FrameSampler(num_frames=5, method="uniform")
        indices = sampler.sample(0)
        assert len(indices) == 0

    def test_single_frame(self):
        """测试单帧输入"""
        sampler = FrameSampler(num_frames=5, method="uniform")
        indices = sampler.sample(1)
        assert len(indices) == 1
        assert indices[0] == 0

    def test_invalid_method(self):
        """测试无效采样方法"""
        sampler = FrameSampler(method="invalid")
        with pytest.raises(ValueError):
            sampler.sample(100)

    def test_sample_with_scores(self):
        """测试基于分数的采样"""
        sampler = FrameSampler(num_frames=3, method="uniform")
        scores = np.array([0.1, 0.5, 0.3, 0.9, 0.2])
        indices, selected_scores = sampler.sample_with_scores([], scores, top_k=3)
        assert len(indices) == 3
        assert len(selected_scores) == 3

    def test_random_reproducibility(self):
        """测试随机采样的可重复性"""
        sampler1 = FrameSampler(num_frames=5, method="random", seed=42)
        sampler2 = FrameSampler(num_frames=5, method="random", seed=42)
        assert np.array_equal(sampler1.sample(100), sampler2.sample(100))

    def test_repr(self):
        """测试字符串表示"""
        sampler = FrameSampler(num_frames=16, method="uniform")
        assert "16" in repr(sampler)
        assert "uniform" in repr(sampler)
