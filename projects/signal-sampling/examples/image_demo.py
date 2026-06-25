"""
图像采样演示
=============

演示图像的降采样和上采样。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.image_sampling import (
    ImageSampler,
    downsample_image,
    upsample_image,
    demonstrate_image_aliasing,
)


def demo_downsampling():
    """降采样演示"""
    print("=" * 60)
    print("图像降采样演示")
    print("=" * 60)

    # 创建测试图像
    size = 128
    image = _create_test_image(size)

    sampler = ImageSampler(image)

    print(f"原始图像大小: {image.shape}")
    print()

    # 不同降采样因子
    factors = [2, 4, 8]

    print("降采样因子 | 输出大小      | 像素数比")
    print("-" * 45)

    for factor in factors:
        result = sampler.downsample(factor, anti_aliasing=True)
        ratio = result.size / image.size
        print(f"     {factor}      | {str(result.shape):14s} | {ratio:.4f}")


def demo_upsampling():
    """上采样演示"""
    print("\n" + "=" * 60)
    print("图像上采样演示")
    print("=" * 60)

    # 创建小图像
    size = 32
    image = _create_test_image(size)

    sampler = ImageSampler(image)

    print(f"原始图像大小: {image.shape}")
    print()

    # 不同插值方法
    methods = ['nearest', 'bilinear', 'bicubic']

    print("插值方法 | 输出大小      | 特点")
    print("-" * 55)

    for method in methods:
        result = sampler.upsample(4, method=method)

        if method == 'nearest':
            desc = "速度最快，质量最差"
        elif method == 'bilinear':
            desc = "速度较快，质量一般"
        else:
            desc = "速度较慢，质量较好"

        print(f"{method:9s} | {str(result.shape):14s} | {desc}")


def demo_aliasing_in_images():
    """图像混叠演示"""
    print("\n" + "=" * 60)
    print("图像混叠演示")
    print("=" * 60)

    size = 128
    factor = 4

    print(f"原始图像大小: {size}x{size}")
    print(f"降采样因子: {factor}")
    print()

    result = demonstrate_image_aliasing(size=size, downsample_factor=factor)

    print("降采样结果:")
    print(f"  带抗混叠: {result['downsampled_with_aa'].shape}")
    print(f"  不带抗混叠: {result['downsampled_without_aa'].shape}")
    print()
    print("上采样结果:")
    print(f"  最近邻: {result['upsampled_nearest'].shape}")
    print(f"  双线性: {result['upsampled_bilinear'].shape}")
    print()
    print("混叠效果:")
    print("  - 不带抗混叠: 产生锯齿和摩尔纹")
    print("  - 带抗混叠: 图像更平滑，但可能模糊")


def demo_anti_aliasing_importance():
    """抗混叠重要性演示"""
    print("\n" + "=" * 60)
    print("抗混叠重要性演示")
    print("=" * 60)

    # 创建高频纹理图像
    size = 128
    x = np.linspace(0, 8 * np.pi, size)
    y = np.linspace(0, 8 * np.pi, size)
    X, Y = np.meshgrid(x, y)
    image = (np.sin(X * 4) * np.sin(Y * 4) + 1) / 2

    print(f"高频纹理图像: {size}x{size}")
    print()

    sampler = ImageSampler(image)

    # 带抗混叠降采样
    with_aa = sampler.downsample(4, anti_aliasing=True)
    without_aa = sampler.downsample(4, anti_aliasing=False)

    print("降采样 4 倍:")
    print(f"  带抗混叠: 标准差 = {np.std(with_aa):.4f}")
    print(f"  不带抗混叠: 标准差 = {np.std(without_aa):.4f}")
    print()
    print("分析:")
    print("  - 不带抗混叠: 高频成分产生混叠，出现摩尔纹")
    print("  - 带抗混叠: 高频成分被滤除，图像更平滑")
    print("  - 抗混叠滤波是降采样的必要步骤")


def demo_image_pyramid():
    """图像金字塔演示"""
    print("\n" + "=" * 60)
    print("图像金字塔演示")
    print("=" * 60)

    size = 128
    image = _create_test_image(size)

    print(f"原始图像: {size}x{size}")
    print()

    # 构建金字塔
    pyramid = [image]
    current = image

    for level in range(4):
        sampler = ImageSampler(current)
        downsampled = sampler.downsample(2, anti_aliasing=True)
        pyramid.append(downsampled)
        current = downsampled
        print(f"Level {level + 1}: {current.shape}")

    print()
    print("图像金字塔用途:")
    print("  - 多尺度图像分析")
    print("  - 图像压缩")
    print("  - 目标检测 (不同尺度)")
    print("  - 图像融合")


def _create_test_image(size: int) -> np.ndarray:
    """创建测试图像"""
    # 棋盘格 + 渐变
    image = np.zeros((size, size))
    block_size = size // 8

    for i in range(size):
        for j in range(size):
            if (i // block_size + j // block_size) % 2 == 0:
                image[i, j] = 1.0

    # 添加渐变
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)
    gradient = 0.3 * (X + Y) / 2

    image = image + gradient
    image = np.clip(image, 0, 1)

    return image


if __name__ == "__main__":
    demo_downsampling()
    demo_upsampling()
    demo_aliasing_in_images()
    demo_anti_aliasing_importance()
    demo_image_pyramid()
