"""
图像颜色压缩示例

使用 K-Means 聚类算法对图像进行颜色压缩，
将图像中的颜色数量减少到指定的 K 种颜色。

原理:
    1. 将图像的每个像素视为一个数据点（RGB 三维向量）
    2. 使用 K-Means 对所有像素进行聚类
    3. 用聚类中心的颜色替换原始像素颜色
    4. 重建压缩后的图像
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KMeans, MiniBatchKMeans


def compress_image(image, n_colors, use_minibatch=False, random_state=42):
    """
    使用 K-Means 压缩图像颜色

    参数:
        image: 输入图像，形状 (height, width, 3)，值范围 [0, 1] 或 [0, 255]
        n_colors: 压缩后的颜色数量
        use_minibatch: 是否使用 Mini-Batch K-Means
        random_state: 随机种子

    返回:
        compressed_image: 压缩后的图像
        labels: 每个像素的簇标签
        centers: 颜色中心
    """
    # 获取图像尺寸
    height, width, channels = image.shape

    # 将图像转换为像素矩阵
    pixels = image.reshape(-1, channels)

    # 归一化到 [0, 1] 范围
    if pixels.max() > 1:
        pixels = pixels / 255.0

    # 选择 K-Means 算法
    if use_minibatch:
        kmeans = MiniBatchKMeans(
            n_clusters=n_colors,
            batch_size=1000,
            random_state=random_state
        )
    else:
        kmeans = KMeans(
            n_clusters=n_colors,
            random_state=random_state,
            init='kmeans++'
        )

    # 训练模型
    kmeans.fit(pixels)

    # 获取标签和中心
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    # 用中心颜色替换原始像素
    compressed_pixels = centers[labels]

    # 重建图像
    compressed_image = compressed_pixels.reshape(height, width, channels)

    return compressed_image, labels, centers


def create_sample_image(size=100):
    """
    创建一个示例图像用于测试

    参数:
        size: 图像大小

    返回:
        image: 示例图像
    """
    # 创建一个渐变图像
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)

    # 创建 RGB 通道
    R = np.sin(2 * np.pi * X) * 0.5 + 0.5
    G = np.cos(2 * np.pi * Y) * 0.5 + 0.5
    B = np.sin(2 * np.pi * (X + Y)) * 0.5 + 0.5

    image = np.stack([R, G, B], axis=2)

    return image


def visualize_compression(original, compressed, n_colors, centers):
    """
    可视化压缩结果

    参数:
        original: 原始图像
        compressed: 压缩后的图像
        n_colors: 颜色数量
        centers: 颜色中心
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 原始图像
    axes[0].imshow(original)
    axes[0].set_title('Original Image', fontsize=14)
    axes[0].axis('off')

    # 压缩后的图像
    axes[1].imshow(compressed)
    axes[1].set_title(f'Compressed ({n_colors} colors)', fontsize=14)
    axes[1].axis('off')

    # 颜色调色板
    palette = centers.reshape(1, -1, 3)
    palette = np.repeat(palette, 30, axis=0)
    axes[2].imshow(palette)
    axes[2].set_title('Color Palette', fontsize=14)
    axes[2].axis('off')

    plt.tight_layout()
    return fig


def compare_compression_levels(image, color_levels=[2, 4, 8, 16, 32]):
    """
    比较不同压缩级别

    参数:
        image: 原始图像
        color_levels: 颜色数量列表
    """
    n_levels = len(color_levels)
    fig, axes = plt.subplots(2, n_levels, figsize=(4 * n_levels, 8))

    for i, n_colors in enumerate(color_levels):
        # 压缩图像
        compressed, labels, centers = compress_image(image, n_colors)

        # 显示压缩后的图像
        axes[0, i].imshow(compressed)
        axes[0, i].set_title(f'{n_colors} Colors', fontsize=12)
        axes[0, i].axis('off')

        # 显示颜色分布
        unique_labels, counts = np.unique(labels, return_counts=True)
        axes[1, i].bar(range(n_colors), counts[unique_labels] / len(labels),
                       color=centers[unique_labels])
        axes[1, i].set_xlabel('Color Index')
        axes[1, i].set_ylabel('Proportion')
        axes[1, i].set_ylim(0, 1)

    plt.suptitle('Image Color Compression Comparison', fontsize=16)
    plt.tight_layout()
    return fig


def main():
    """主函数"""
    print("=" * 60)
    print("图像颜色压缩示例")
    print("=" * 60)

    # 创建示例图像
    print("\n1. 创建示例图像...")
    image = create_sample_image(size=100)
    print(f"   图像尺寸: {image.shape}")

    # 测试不同压缩级别
    color_levels = [2, 4, 8, 16]

    print("\n2. 测试不同压缩级别...")
    for n_colors in color_levels:
        # 标准 K-Means
        compressed, labels, centers = compress_image(image, n_colors)
        print(f"   {n_colors} 颜色 - 像素数: {len(labels)}, 唯一标签: {len(np.unique(labels))}")

    # 比较标准 K-Means 和 Mini-Batch K-Means
    print("\n3. 比较标准 K-Means 和 Mini-Batch K-Means...")
    n_colors = 8

    # 标准 K-Means
    compressed_std, labels_std, centers_std = compress_image(
        image, n_colors, use_minibatch=False
    )

    # Mini-Batch K-Means
    compressed_mb, labels_mb, centers_mb = compress_image(
        image, n_colors, use_minibatch=True
    )

    print(f"   标准 K-Means: {len(np.unique(labels_std))} 种颜色")
    print(f"   Mini-Batch K-Means: {len(np.unique(labels_mb))} 种颜色")

    # 可视化结果
    print("\n4. 生成可视化...")
    fig1 = visualize_compression(image, compressed_std, n_colors, centers_std)
    fig1.suptitle('Standard K-Means Compression', fontsize=16)

    fig2 = visualize_comparison(image, compressed_std, compressed_mb, n_colors)

    print("\n5. 保存结果...")
    fig1.savefig('image_compression_standard.png', dpi=150, bbox_inches='tight')
    fig2.savefig('image_compression_comparison.png', dpi=150, bbox_inches='tight')

    print("\n完成! 图像已保存。")
    plt.show()


def visualize_comparison(original, compressed_std, compressed_mb, n_colors):
    """
    可视化标准 K-Means 和 Mini-Batch K-Means 的比较

    参数:
        original: 原始图像
        compressed_std: 标准 K-Means 压缩结果
        compressed_mb: Mini-Batch K-Means 压缩结果
        n_colors: 颜色数量
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(original)
    axes[0].set_title('Original', fontsize=14)
    axes[0].axis('off')

    axes[1].imshow(compressed_std)
    axes[1].set_title(f'Standard K-Means ({n_colors} colors)', fontsize=14)
    axes[1].axis('off')

    axes[2].imshow(compressed_mb)
    axes[2].set_title(f'Mini-Batch K-Means ({n_colors} colors)', fontsize=14)
    axes[2].axis('off')

    plt.suptitle('K-Means vs Mini-Batch K-Means', fontsize=16)
    plt.tight_layout()
    return fig


if __name__ == '__main__':
    main()
