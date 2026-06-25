"""
图像采样模块测试
================

测试图像降采样、上采样等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.image_sampling import (
    ImageSampler,
    downsample_image,
    upsample_image,
    demonstrate_image_aliasing,
)


class TestImageSampler:
    """图像采样器测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)
        assert sampler.image.shape == (100, 100)

    def test_invalid_image(self):
        """测试无效图像"""
        with pytest.raises(ValueError):
            ImageSampler(np.random.rand(100, 100, 3))  # 3D 数组


class TestDownsample:
    """降采样测试"""

    def test_basic_downsample(self):
        """测试基本降采样"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        result = sampler.downsample(2, anti_aliasing=False)

        assert result.shape == (50, 50)

    def test_downsample_factor_4(self):
        """测试 4 倍降采样"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        result = sampler.downsample(4, anti_aliasing=False)

        assert result.shape == (25, 25)

    def test_with_anti_aliasing(self):
        """测试带抗混叠的降采样"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        result = sampler.downsample(2, anti_aliasing=True)

        assert result.shape == (50, 50)

    def test_average_method(self):
        """测试平均法降采样"""
        image = np.ones((100, 100)) * 0.5
        sampler = ImageSampler(image)

        result = sampler.downsample(2, method='average', anti_aliasing=False)

        assert np.allclose(result, 0.5)

    def test_subsample_method(self):
        """测试抽取法降采样"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        result = sampler.downsample(2, method='subsample', anti_aliasing=False)

        assert result.shape == (50, 50)
        # 验证抽取正确
        assert np.allclose(result, image[::2, ::2])

    def test_invalid_factor(self):
        """测试无效因子"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        with pytest.raises(ValueError):
            sampler.downsample(0)
        with pytest.raises(ValueError):
            sampler.downsample(-1)

    def test_invalid_method(self):
        """测试无效方法"""
        image = np.random.rand(100, 100)
        sampler = ImageSampler(image)

        with pytest.raises(ValueError):
            sampler.downsample(2, method='invalid')


class TestUpsample:
    """上采样测试"""

    def test_nearest(self):
        """测试最近邻上采样"""
        image = np.random.rand(25, 25)
        sampler = ImageSampler(image)

        result = sampler.upsample(2, method='nearest')

        assert result.shape == (50, 50)

    def test_bilinear(self):
        """测试双线性上采样"""
        image = np.random.rand(25, 25)
        sampler = ImageSampler(image)

        result = sampler.upsample(2, method='bilinear')

        assert result.shape == (50, 50)

    def test_bicubic(self):
        """测试双三次上采样"""
        image = np.random.rand(25, 25)
        sampler = ImageSampler(image)

        result = sampler.upsample(2, method='bicubic')

        assert result.shape == (50, 50)

    def test_constant_image(self):
        """测试常数图像上采样"""
        image = np.ones((25, 25)) * 0.5
        sampler = ImageSampler(image)

        result = sampler.upsample(2, method='bilinear')

        # 常数图像上采样后应保持常数
        assert np.allclose(result, 0.5, atol=1e-10)

    def test_invalid_factor(self):
        """测试无效因子"""
        image = np.random.rand(25, 25)
        sampler = ImageSampler(image)

        with pytest.raises(ValueError):
            sampler.upsample(0)
        with pytest.raises(ValueError):
            sampler.upsample(-1)

    def test_invalid_method(self):
        """测试无效方法"""
        image = np.random.rand(25, 25)
        sampler = ImageSampler(image)

        with pytest.raises(ValueError):
            sampler.upsample(2, method='invalid')


class TestDownsampleImage:
    """降采样便捷函数测试"""

    def test_basic(self):
        """测试基本降采样"""
        image = np.random.rand(100, 100)

        result = downsample_image(image, 2)

        assert result.shape == (50, 50)

    def test_no_anti_aliasing(self):
        """测试无抗混叠"""
        image = np.random.rand(100, 100)

        result = downsample_image(image, 2, anti_aliasing=False)

        assert result.shape == (50, 50)


class TestUpsampleImage:
    """上采样便捷函数测试"""

    def test_basic(self):
        """测试基本上采样"""
        image = np.random.rand(25, 25)

        result = upsample_image(image, 2)

        assert result.shape == (50, 50)

    def test_nearest(self):
        """测试最近邻"""
        image = np.random.rand(25, 25)

        result = upsample_image(image, 2, method='nearest')

        assert result.shape == (50, 50)


class TestDemonstrateImageAliasing:
    """图像混叠演示测试"""

    def test_basic(self):
        """测试基本演示"""
        result = demonstrate_image_aliasing(size=64, downsample_factor=2)

        assert "original" in result
        assert "downsampled_with_aa" in result
        assert "downsampled_without_aa" in result
        assert "upsampled_nearest" in result
        assert "upsampled_bilinear" in result

    def test_shapes(self):
        """测试输出形状"""
        size = 64
        factor = 2
        result = demonstrate_image_aliasing(size=size, downsample_factor=factor)

        assert result["original"].shape == (size, size)
        assert result["downsampled_with_aa"].shape == (size // factor, size // factor)
        assert result["downsampled_without_aa"].shape == (size // factor, size // factor)
        assert result["upsampled_nearest"].shape == (size, size)
        assert result["upsampled_bilinear"].shape == (size, size)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
