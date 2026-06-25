"""Gram 矩阵可视化演示

演示 Gram 矩阵的计算和可视化。
"""

import torch
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import gram_matrix


def create_texture_features(texture_type: str, channels: int = 8, size: int = 16) -> torch.Tensor:
    """创建不同纹理的特征图

    Args:
        texture_type: 纹理类型（horizontal/vertical/diagonal/random）
        channels: 通道数
        size: 特征图大小

    Returns:
        特征图张量
    """
    features = torch.zeros(1, channels, size, size)

    if texture_type == "horizontal":
        # 水平条纹纹理
        for i in range(size):
            features[0, :, i, :] = torch.sin(torch.tensor(i * 0.5))

    elif texture_type == "vertical":
        # 垂直条纹纹理
        for i in range(size):
            features[0, :, :, i] = torch.sin(torch.tensor(i * 0.5))

    elif texture_type == "diagonal":
        # 对角线纹理
        for i in range(size):
            for j in range(size):
                features[0, :, i, j] = torch.sin(torch.tensor((i + j) * 0.5))

    elif texture_type == "random":
        # 随机纹理
        features = torch.randn(1, channels, size, size)

    elif texture_type == "checkerboard":
        # 棋盘格纹理
        for i in range(size):
            for j in range(size):
                if (i + j) % 2 == 0:
                    features[0, :, i, j] = 1.0

    return features


def visualize_gram_matrices():
    """可视化不同纹理的 Gram 矩阵"""
    print("=" * 60)
    print("Gram 矩阵可视化")
    print("=" * 60)

    # 创建不同纹理
    texture_types = ["horizontal", "vertical", "diagonal", "checkerboard", "random"]

    fig, axes = plt.subplots(2, len(texture_types), figsize=(4 * len(texture_types), 8))

    for idx, texture_type in enumerate(texture_types):
        print(f"\n处理纹理: {texture_type}")

        # 创建特征图
        features = create_texture_features(texture_type, channels=8, size=16)

        # 计算 Gram 矩阵
        gram = gram_matrix(features, normalize=True)

        # 可视化特征图（取第一个通道）
        axes[0, idx].imshow(features[0, 0].numpy(), cmap="viridis")
        axes[0, idx].set_title(f"{texture_type}\nFeature Map")
        axes[0, idx].axis("off")

        # 可视化 Gram 矩阵
        im = axes[1, idx].imshow(gram[0].numpy(), cmap="hot", vmin=0, vmax=gram.max().item())
        axes[1, idx].set_title(f"Gram Matrix")
        axes[1, idx].axis("off")

        # 打印 Gram 矩阵统计信息
        print(f"  Gram 矩阵形状: {gram.shape}")
        print(f"  对角线均值: {gram[0].diag().mean().item():.4f}")
        print(f"  非对角线均值: {(gram[0].sum() - gram[0].diag().sum()).item() / (8*7):.4f}")

    plt.tight_layout()

    # 保存图像
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / "gram_matrices.png", dpi=150, bbox_inches="tight")
    print(f"\n图像已保存到: {output_dir / 'gram_matrices.png'}")

    plt.show()


def compare_gram_similarity():
    """比较不同纹理的 Gram 矩阵相似度"""
    print("\n" + "=" * 60)
    print("Gram 矩阵相似度比较")
    print("=" * 60)

    texture_types = ["horizontal", "vertical", "diagonal", "checkerboard", "random"]

    # 计算所有纹理的 Gram 矩阵
    grams = {}
    for texture_type in texture_types:
        features = create_texture_features(texture_type, channels=8, size=16)
        grams[texture_type] = gram_matrix(features, normalize=True)

    # 计算相似度矩阵
    n = len(texture_types)
    similarity_matrix = torch.zeros(n, n)

    for i, type1 in enumerate(texture_types):
        for j, type2 in enumerate(texture_types):
            # 使用 MSE 计算差异，越小越相似
            mse = torch.mean((grams[type1] - grams[type2]) ** 2)
            similarity_matrix[i, j] = mse.item()

    # 打印相似度矩阵
    print("\nGram 矩阵 MSE 差异矩阵:")
    print("（值越小表示越相似）")
    print()

    # 表头
    header = "".ljust(12)
    for t in texture_types:
        header += t[:8].rjust(10)
    print(header)

    # 数据行
    for i, type1 in enumerate(texture_types):
        row = type1.ljust(12)
        for j, type2 in enumerate(texture_types):
            row += f"{similarity_matrix[i, j]:.4f}".rjust(10)
        print(row)

    # 找出最相似和最不相似的纹理对
    min_val = float("inf")
    max_val = 0
    min_pair = ("", "")
    max_pair = ("", "")

    for i in range(n):
        for j in range(i + 1, n):
            val = similarity_matrix[i, j].item()
            if val < min_val:
                min_val = val
                min_pair = (texture_types[i], texture_types[j])
            if val > max_val:
                max_val = val
                max_pair = (texture_types[i], texture_types[j])

    print(f"\n最相似的纹理对: {min_pair[0]} 和 {min_pair[1]} (MSE: {min_val:.4f})")
    print(f"最不相似的纹理对: {max_pair[0]} 和 {max_pair[1]} (MSE: {max_val:.4f})")


def demonstrate_gram_properties():
    """演示 Gram 矩阵的数学性质"""
    print("\n" + "=" * 60)
    print("Gram 矩阵数学性质演示")
    print("=" * 60)

    # 1. 对称性
    print("\n1. 对称性:")
    features = torch.randn(1, 4, 8, 8)
    gram = gram_matrix(features, normalize=False)

    is_symmetric = torch.allclose(gram, gram.transpose(1, 2), atol=1e-6)
    print(f"   Gram 矩阵是否对称: {is_symmetric}")

    # 2. 半正定性
    print("\n2. 半正定性:")
    eigenvalues = torch.linalg.eigvalsh(gram)
    is_positive_semidefinite = torch.all(eigenvalues >= -1e-6)
    print(f"   所有特征值非负: {is_positive_semidefinite}")
    print(f"   特征值范围: [{eigenvalues.min().item():.4f}, {eigenvalues.max().item():.4f}]")

    # 3. 秩
    print("\n3. 秩:")
    rank = torch.linalg.matrix_rank(gram[0])
    print(f"   Gram 矩阵的秩: {rank.item()}")
    print(f"   特征图通道数: {features.shape[1]}")
    print(f"   空间尺寸: {features.shape[2]}x{features.shape[3]}")

    # 4. 归一化效果
    print("\n4. 归一化效果:")
    gram_normalized = gram_matrix(features, normalize=True)
    gram_unnormalized = gram_matrix(features, normalize=False)

    print(f"   未归一化 Gram 矩阵均值: {gram_unnormalized.mean().item():.4f}")
    print(f"   归一化 Gram 矩阵均值: {gram_normalized.mean().item():.4f}")

    # 5. 不同特征的 Gram 矩阵
    print("\n5. 不同特征的 Gram 矩阵:")
    features1 = torch.randn(1, 4, 8, 8)
    features2 = torch.randn(1, 4, 8, 8)

    gram1 = gram_matrix(features1)
    gram2 = gram_matrix(features2)

    mse = torch.mean((gram1 - gram2) ** 2)
    print(f"   两个随机特征的 Gram 矩阵 MSE: {mse.item():.4f}")

    # 相同特征
    mse_same = torch.mean((gram1 - gram1) ** 2)
    print(f"   相同特征的 Gram 矩阵 MSE: {mse_same.item():.4f}")


def main():
    """主函数"""
    print("Gram 矩阵演示")
    print("=" * 60)

    # 可视化 Gram 矩阵
    visualize_gram_matrices()

    # 比较相似度
    compare_gram_similarity()

    # 演示数学性质
    demonstrate_gram_properties()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
