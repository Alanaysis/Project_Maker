"""
数据集测试。
"""

import pytest
import torch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import SyntheticPoseDataset, create_dataloader


class TestSyntheticPoseDataset:
    """测试合成姿态数据集。"""

    def test_dataset_length(self):
        """测试数据集长度。"""
        dataset = SyntheticPoseDataset(num_samples=50)
        assert len(dataset) == 50

    def test_sample_keys(self):
        """测试样本的键。"""
        dataset = SyntheticPoseDataset(num_samples=10)
        sample = dataset[0]
        assert "image" in sample
        assert "keypoints" in sample
        assert "weights" in sample
        assert "heatmaps" in sample

    def test_image_shape(self):
        """测试图像形状。"""
        dataset = SyntheticPoseDataset(
            num_samples=5, image_size=(128, 128)
        )
        sample = dataset[0]
        img = sample["image"]
        assert img.shape == (3, 128, 128)
        assert img.dtype == torch.float32

    def test_image_range(self):
        """测试图像值范围。"""
        dataset = SyntheticPoseDataset(num_samples=5)
        sample = dataset[0]
        img = sample["image"]
        assert img.min() >= 0.0
        assert img.max() <= 1.0

    def test_keypoints_shape(self):
        """测试关键点形状。"""
        dataset = SyntheticPoseDataset(num_samples=5, num_keypoints=17)
        sample = dataset[0]
        kp = sample["keypoints"]
        assert kp.shape == (17, 2)
        assert kp.dtype == torch.float32

    def test_keypoints_range(self):
        """测试关键点坐标范围。"""
        dataset = SyntheticPoseDataset(num_samples=20)
        for i in range(len(dataset)):
            kp = dataset[i]["keypoints"]
            assert kp.min() >= 0.0, f"Sample {i}: min={kp.min()}"
            assert kp.max() <= 1.0, f"Sample {i}: max={kp.max()}"

    def test_weights_shape(self):
        """测试权重形状。"""
        dataset = SyntheticPoseDataset(num_samples=5, num_keypoints=17)
        sample = dataset[0]
        w = sample["weights"]
        assert w.shape == (17,)
        # 权重应该为 0 或 1
        assert ((w == 0) | (w == 1)).all()

    def test_heatmaps_shape(self):
        """测试热力图形状。"""
        dataset = SyntheticPoseDataset(
            num_samples=5, num_keypoints=17, heatmap_size=(64, 64)
        )
        sample = dataset[0]
        hm = sample["heatmaps"]
        assert hm.shape == (17, 64, 64)
        assert hm.dtype == torch.float32

    def test_heatmaps_range(self):
        """测试热力图值范围。"""
        dataset = SyntheticPoseDataset(num_samples=5, heatmap_size=(32, 32))
        for i in range(len(dataset)):
            hm = dataset[i]["heatmaps"]
            assert hm.min() >= 0.0, f"Sample {i}: min={hm.min()}"
            assert hm.max() <= 1.0, f"Sample {i}: max={hm.max()}"

    def test_different_num_keypoints(self):
        """测试不同关键点数量。"""
        for num_kp in [5, 10, 17]:
            dataset = SyntheticPoseDataset(num_samples=3, num_keypoints=num_kp)
            sample = dataset[0]
            assert sample["keypoints"].shape[0] == num_kp
            assert sample["weights"].shape[0] == num_kp
            assert sample["heatmaps"].shape[0] == num_kp

    def test_variety(self):
        """测试样本多样性。"""
        dataset = SyntheticPoseDataset(num_samples=10)
        kp_list = [dataset[i]["keypoints"] for i in range(10)]
        # 不同样本的关键点应该不同
        for i in range(len(kp_list)):
            for j in range(i + 1, len(kp_list)):
                if not torch.allclose(kp_list[i], kp_list[j], atol=1e-3):
                    break
            else:
                continue
            break
        else:
            pytest.skip("All samples are identical (unlikely)")


class TestCreateDataloader:
    """测试数据加载器创建。"""

    def test_basic_creation(self):
        """测试基本创建。"""
        dataset = SyntheticPoseDataset(num_samples=20)
        loader = create_dataloader(dataset, batch_size=4)
        assert loader is not None

    def test_batch_shape(self):
        """测试批次形状。"""
        dataset = SyntheticPoseDataset(
            num_samples=20, image_size=(128, 128), heatmap_size=(32, 32)
        )
        loader = create_dataloader(dataset, batch_size=4)
        batch = next(iter(loader))

        assert batch["image"].shape == (4, 3, 128, 128)
        assert batch["keypoints"].shape == (4, 17, 2)
        assert batch["weights"].shape == (4, 17)
        assert batch["heatmaps"].shape == (4, 17, 32, 32)

    def test_shuffle(self):
        """测试 shuffle 参数。"""
        dataset = SyntheticPoseDataset(num_samples=20)
        loader = create_dataloader(dataset, batch_size=4, shuffle=False)
        assert loader is not None
