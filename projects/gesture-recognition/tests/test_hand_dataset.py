"""
Tests for Hand Dataset

测试覆盖：
1. 合成数据生成测试
2. 数据集接口测试
3. DataLoader测试
4. 各手势关键点测试
"""

import pytest
import torch
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gesture_recognition.data.hand_dataset import HandDataset, create_synthetic_dataset


class TestHandDataset:
    """手部数据集测试"""

    def test_init_synthetic(self):
        """测试合成数据初始化"""
        dataset = HandDataset(num_samples=70, num_classes=7)
        assert len(dataset) == 70

    def test_init_custom_samples(self):
        """测试自定义样本数（允许少量舍入误差）"""
        dataset = HandDataset(num_samples=100, num_classes=7)
        # 由于整数除法，实际样本数可能略少
        assert len(dataset) >= 95
        assert len(dataset) <= 105

    def test_getitem(self, synthetic_dataset):
        """测试获取单个样本"""
        features, label = synthetic_dataset[0]

        assert isinstance(features, torch.Tensor)
        assert isinstance(label, int)
        assert 0 <= label < 7

    def test_features_shape(self, synthetic_dataset):
        """测试特征形状"""
        features, _ = synthetic_dataset[0]
        assert features.dim() == 1
        assert len(features) == 66  # 特征维度

    def test_class_balance(self):
        """测试类别平衡"""
        dataset = HandDataset(num_samples=70, num_classes=7)

        # 统计各类别数量
        labels = [sample["gesture"] for sample in dataset.data]
        for cls in range(7):
            count = labels.count(cls)
            assert count == 10  # 每类10个样本

    def test_dataloader(self, synthetic_dataset):
        """测试DataLoader"""
        dataloader = synthetic_dataset.get_dataloader(batch_size=8, shuffle=True)

        batch_features, batch_labels = next(iter(dataloader))
        assert batch_features.shape == (8, 66)
        assert batch_labels.shape == (8,)

    def test_create_synthetic_dataset(self):
        """测试便捷创建函数"""
        train_loader, val_loader = create_synthetic_dataset(
            num_train=70, num_val=14, batch_size=7
        )

        assert len(train_loader.dataset) == 70
        assert len(val_loader.dataset) == 14

    def test_base_keypoints_fist(self, synthetic_dataset):
        """测试拳头关键点生成"""
        keypoints = synthetic_dataset._get_base_keypoints(0)

        assert keypoints.shape == (21, 2)
        # 关键点应该在合理范围内
        assert keypoints.min() >= 0
        assert keypoints.max() <= 1

    def test_base_keypoints_open_palm(self, synthetic_dataset):
        """测试张开手掌关键点生成"""
        keypoints = synthetic_dataset._get_base_keypoints(1)

        assert keypoints.shape == (21, 2)

    def test_base_keypoints_peace(self, synthetic_dataset):
        """测试剪刀手关键点生成"""
        keypoints = synthetic_dataset._get_base_keypoints(2)

        assert keypoints.shape == (21, 2)

    def test_base_keypoints_thumbs_up(self, synthetic_dataset):
        """测试竖大拇指关键点生成"""
        keypoints = synthetic_dataset._get_base_keypoints(3)

        assert keypoints.shape == (21, 2)

    def test_all_gesture_types(self, synthetic_dataset):
        """测试所有手势类型"""
        for gesture_id in range(7):
            keypoints = synthetic_dataset._get_base_keypoints(gesture_id)
            assert keypoints.shape == (21, 2)
            assert not np.isnan(keypoints).any()
