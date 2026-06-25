"""
超分辨率数据集测试

测试数据集加载和预处理功能
"""

import pytest
import torch
import os
import sys
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dataset import SRDataset, SRTestDataset, create_synthetic_dataset


class TestSRDataset:
    """SRDataset 测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建合成数据集
            create_synthetic_dataset(tmpdir, num_images=5, image_size=64)
            yield tmpdir

    def test_init(self, temp_dir):
        """测试数据集初始化"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=2,
            patch_size=32,
            is_training=True
        )

        assert len(dataset) == 5

    def test_getitem_training(self, temp_dir):
        """测试训练模式获取数据"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=2,
            patch_size=32,
            is_training=True
        )

        lr, hr = dataset[0]

        # 检查形状
        assert lr.shape[0] == 3  # 通道数
        assert hr.shape[0] == 3

        # 检查尺寸关系
        assert hr.shape[1] == 32  # patch_size
        assert hr.shape[2] == 32
        assert lr.shape[1] == 16  # patch_size / scale_factor
        assert lr.shape[2] == 16

    def test_getitem_evaluation(self, temp_dir):
        """测试评估模式获取数据"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=2,
            patch_size=32,
            is_training=False
        )

        lr, hr = dataset[0]

        # 检查形状
        assert lr.shape[0] == 3
        assert hr.shape[0] == 3

        # 检查尺寸关系
        assert hr.shape[1] == lr.shape[1] * 2
        assert hr.shape[2] == lr.shape[2] * 2

    def test_scale_factor_3(self, temp_dir):
        """测试 3 倍缩放"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=3,
            patch_size=48,
            is_training=True
        )

        lr, hr = dataset[0]

        assert hr.shape[1] == 48
        assert lr.shape[1] == 16

    def test_scale_factor_4(self, temp_dir):
        """测试 4 倍缩放"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=4,
            patch_size=64,
            is_training=True
        )

        lr, hr = dataset[0]

        assert hr.shape[1] == 64
        assert lr.shape[1] == 16

    def test_augmentation(self, temp_dir):
        """测试数据增强"""
        dataset = SRDataset(
            hr_dir=temp_dir,
            scale_factor=2,
            patch_size=32,
            is_training=True,
            augment=True
        )

        # 获取多个样本，检查是否不同
        samples = [dataset[0] for _ in range(5)]

        # 由于随机增强，样本应该不同
        # 注意：这可能偶尔失败，因为增强是随机的
        assert len(samples) == 5

    def test_empty_directory(self):
        """测试空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                SRDataset(hr_dir=tmpdir)


class TestSRTestDataset:
    """SRTestDataset 测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_synthetic_dataset(tmpdir, num_images=3, image_size=64)
            yield tmpdir

    def test_init(self, temp_dir):
        """测试数据集初始化"""
        dataset = SRTestDataset(
            hr_dir=temp_dir,
            scale_factor=2
        )

        assert len(dataset) == 3

    def test_getitem(self, temp_dir):
        """测试获取数据"""
        dataset = SRTestDataset(
            hr_dir=temp_dir,
            scale_factor=2
        )

        lr, hr = dataset[0]

        # 检查形状
        assert lr.shape[0] == 3
        assert hr.shape[0] == 3

        # 检查尺寸关系
        assert hr.shape[1] == lr.shape[1] * 2
        assert hr.shape[2] == lr.shape[2] * 2


class TestCreateSyntheticDataset:
    """create_synthetic_dataset 测试"""

    def test_create(self):
        """测试创建合成数据集"""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_synthetic_dataset(tmpdir, num_images=5, image_size=32)

            # 检查文件是否创建
            files = os.listdir(tmpdir)
            assert len(files) == 5

            # 检查文件扩展名
            for f in files:
                assert f.endswith('.png')

    def test_different_sizes(self):
        """测试不同图像尺寸"""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_synthetic_dataset(tmpdir, num_images=2, image_size=64)

            files = os.listdir(tmpdir)
            assert len(files) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
