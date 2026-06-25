"""视频数据集测试"""

import os
import tempfile

import pytest
import torch

from video_understanding.data.video_dataset import SyntheticVideoDataset, VideoDataset


class TestSyntheticVideoDataset:
    """SyntheticVideoDataset 测试类"""

    def test_init(self):
        """测试初始化"""
        dataset = SyntheticVideoDataset(num_samples=50, num_classes=5)
        assert len(dataset) == 50

    def test_getitem(self):
        """测试获取样本"""
        dataset = SyntheticVideoDataset(num_samples=10, num_frames=8, num_classes=5)
        frames, label = dataset[0]
        assert frames.shape == (8, 3, 224, 224)
        assert 0 <= label < 5

    def test_different_sizes(self):
        """测试不同尺寸"""
        dataset = SyntheticVideoDataset(
            num_samples=5, num_frames=4, frame_size=(112, 112)
        )
        frames, _ = dataset[0]
        assert frames.shape == (4, 3, 112, 112)

    def test_reproducibility(self):
        """测试可重复性"""
        ds1 = SyntheticVideoDataset(num_samples=5, seed=42)
        ds2 = SyntheticVideoDataset(num_samples=5, seed=42)
        _, label1 = ds1[0]
        _, label2 = ds2[0]
        assert label1 == label2


class TestVideoDataset:
    """VideoDataset 测试类"""

    def test_init_empty_dir(self):
        """测试空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = VideoDataset(tmpdir)
            assert len(dataset) == 0

    def test_init_nonexistent_dir(self):
        """测试不存在的目录"""
        dataset = VideoDataset("/nonexistent/path")
        assert len(dataset) == 0

    def test_repr(self):
        """测试字符串表示"""
        dataset = SyntheticVideoDataset(num_samples=10)
        assert "10" in repr(dataset)
