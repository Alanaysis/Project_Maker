"""
深度估计数据集测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import (
    SyntheticDepthDataset,
    create_dataloader,
    generate_random_batch,
)


class TestSyntheticDepthDataset:
    """合成深度数据集测试"""

    def test_basic(self):
        """测试基本功能"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        assert len(dataset) == 10

    def test_getitem(self):
        """测试获取样本"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        image, depth, mask = dataset[0]

        assert image.shape == (3, 64, 64)
        assert depth.shape == (1, 64, 64)
        assert mask.shape == (1, 64, 64)

    def test_image_range(self):
        """测试图像值范围"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        image, _, _ = dataset[0]

        assert image.min() >= 0
        assert image.max() <= 1

    def test_depth_range(self):
        """测试深度值范围"""
        dataset = SyntheticDepthDataset(
            num_samples=10,
            image_size=(64, 64),
            depth_range=(0.5, 5.0),
            add_noise=False,
        )
        _, depth, _ = dataset[0]

        assert depth.min() >= 0.5
        assert depth.max() <= 5.0

    def test_different_scenes(self):
        """测试不同场景类型"""
        for scene in ["plane", "slope", "stairs", "sphere"]:
            dataset = SyntheticDepthDataset(
                num_samples=1,
                image_size=(64, 64),
                scene_types=[scene],
            )
            image, depth, mask = dataset[0]
            assert image.shape == (3, 64, 64)
            assert depth.shape == (1, 64, 64)

    def test_custom_depth_range(self):
        """测试自定义深度范围"""
        dataset = SyntheticDepthDataset(
            num_samples=5,
            image_size=(32, 32),
            depth_range=(1.0, 20.0),
        )
        _, depth, mask = dataset[0]

        assert depth.shape == (1, 32, 32)
        assert mask.shape == (1, 32, 32)


class TestCreateDataloader:
    """数据加载器测试"""

    def test_basic(self):
        """测试基本功能"""
        dataset = SyntheticDepthDataset(num_samples=20, image_size=(64, 64))
        loader = create_dataloader(dataset, batch_size=4)

        images, depths, masks = next(iter(loader))
        assert images.shape == (4, 3, 64, 64)
        assert depths.shape == (4, 1, 64, 64)
        assert masks.shape == (4, 1, 64, 64)

    def test_shuffle(self):
        """测试打乱"""
        dataset = SyntheticDepthDataset(num_samples=20, image_size=(64, 64))
        loader = create_dataloader(dataset, batch_size=4, shuffle=True)

        batches = []
        for images, _, _ in loader:
            batches.append(images[0])

        # 打乱后批次应该不同
        assert not torch.equal(batches[0], batches[1])


class TestGenerateRandomBatch:
    """随机批量生成测试"""

    def test_basic(self):
        """测试基本功能"""
        images, depths, masks = generate_random_batch(batch_size=4, image_size=(64, 64))

        assert images.shape == (4, 3, 64, 64)
        assert depths.shape == (4, 1, 64, 64)
        assert masks.shape == (4, 1, 64, 64)

    def test_depth_range(self):
        """测试深度范围"""
        _, depths, _ = generate_random_batch(
            batch_size=2,
            image_size=(32, 32),
            depth_range=(1.0, 5.0),
        )

        assert depths.min() >= 1.0
        assert depths.max() <= 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
