#!/usr/bin/env python3
"""
PCA 实际应用示例

演示 PCA 在实际场景中的应用：
1. 数据压缩：减少存储空间
2. 噪声过滤：去除低方差成分
3. 特征工程：为机器学习准备数据
4. 数据探索：发现数据结构
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pca import PCA


def demo_data_compression():
    """演示数据压缩应用。"""
    print("\n" + "=" * 60)
    print("应用1：数据压缩")
    print("=" * 60)

    np.random.seed(42)

    # 模拟高维数据（如图像特征）
    n_samples = 100
    n_features = 50

    # 创建有冗余的数据
    base = np.random.randn(n_samples, 5)
    noise = np.random.randn(n_samples, n_features) * 0.1
    X = np.hstack([base, base, base, base, base, base, base, base, base, base]) + noise

    print(f"\n原始数据形状: {X.shape}")
    print(f"原始数据大小: {X.nbytes} bytes")

    # 不同压缩比
    print("\n压缩比分析:")
    print("-" * 50)
    print(f"{'保留成分数':<12} {'压缩比':<15} {'重建误差(MSE)':<15}")
    print("-" * 50)

    for n_comp in [2, 5, 10, 20]:
        pca = PCA(n_components=n_comp)
        X_reduced = pca.fit_transform(X)
        X_reconstructed = pca.inverse_transform(X_reduced)

        compression_ratio = n_comp / n_features
        mse = np.mean((X - X_reconstructed) ** 2)

        print(f"{n_comp:<12} {compression_ratio:<15.2%} {mse:<15.6f}")

    print("\n结论：即使只保留 5 个成分（压缩比 10%），重建误差也很小。")


def demo_noise_filtering():
    """演示噪声过滤应用。"""
    print("\n" + "=" * 60)
    print("应用2：噪声过滤")
    print("=" * 60)

    np.random.seed(42)

    # 创建带噪声的数据
    n_samples = 200
    n_features = 10

    # 干净信号：低秩结构
    signal = np.random.randn(n_samples, 3) @ np.random.randn(3, n_features)

    # 添加噪声
    noise_level = 0.5
    noise = np.random.randn(n_samples, n_features) * noise_level
    X_noisy = signal + noise

    print(f"\n数据形状: {X_noisy.shape}")
    print(f"噪声水平: {noise_level}")

    # PCA 去噪：保留主要成分
    pca = PCA(n_components=3)
    X_reduced = pca.fit_transform(X_noisy)
    X_denoised = pca.inverse_transform(X_reduced)

    # 计算去噪效果
    mse_noisy = np.mean((signal - X_noisy) ** 2)
    mse_denoised = np.mean((signal - X_denoised) ** 2)

    print(f"\n去噪前 MSE: {mse_noisy:.6f}")
    print(f"去噪后 MSE: {mse_denoised:.6f}")
    print(f"噪声减少: {(1 - mse_denoised/mse_noisy):.2%}")

    print("\n结论：PCA 可以有效去除噪声，保留信号的主要结构。")


def demo_feature_engineering():
    """演示特征工程应用。"""
    print("\n" + "=" * 60)
    print("应用3：特征工程（为机器学习准备数据）")
    print("=" * 60)

    np.random.seed(42)

    # 创建高维数据
    n_samples = 300
    n_features = 20

    # 创建有结构的数据
    X = np.random.randn(n_samples, n_features)

    # 模拟分类任务的特征
    # 前几个特征有区分度
    X[:100, :3] += 3   # 类别1
    X[100:200, :3] -= 3  # 类别2
    # 其余特征是噪声

    labels = np.array([0]*100 + [1]*100 + [2]*100)

    print(f"\n原始数据形状: {X.shape}")

    # PCA 降维作为特征工程
    pca = PCA(n_components=5)
    X_features = pca.fit_transform(X)

    print(f"降维后形状: {X_features.shape}")
    print(f"解释方差比例: {pca.explained_variance_ratio_}")
    print(f"累积解释方差: {np.sum(pca.explained_variance_ratio_):.2%}")

    # 分析类别可分性
    print("\n类别中心距离分析:")
    for i in range(3):
        for j in range(i+1, 3):
            center_i = np.mean(X_features[labels == i], axis=0)
            center_j = np.mean(X_features[labels == j], axis=0)
            dist = np.linalg.norm(center_i - center_j)
            print(f"   类别{i} vs 类别{j}: {dist:.4f}")

    print("\n结论：PCA 可以将高维特征压缩为更有信息量的低维特征。")


def demo_data_exploration():
    """演示数据探索应用。"""
    print("\n" + "=" * 60)
    print("应用4：数据探索（发现数据结构）")
    print("=" * 60)

    np.random.seed(42)

    # 创建有内在维度的数据
    n_samples = 150

    # 数据实际上只有 2 个内在维度
    t = np.linspace(0, 4*np.pi, n_samples)
    intrinsic = np.column_stack([np.sin(t), np.cos(t)])

    # 嵌入到高维空间
    projection_matrix = np.random.randn(2, 8)
    X = intrinsic @ projection_matrix + np.random.randn(n_samples, 8) * 0.1

    print(f"\n数据形状: {X.shape}")

    # 分析内在维度
    pca = PCA(n_components=8)
    pca.fit(X)

    print("\n各主成分的解释方差比例:")
    cumulative = 0
    for i, ratio in enumerate(pca.explained_variance_ratio_):
        cumulative += ratio
        bar = "#" * int(ratio * 50)
        print(f"   PC{i+1}: {ratio:.4f}  {bar}")

    print(f"\n前2个成分解释了 {np.sum(pca.explained_variance_ratio_[:2]):.2%} 的方差")
    print("\n结论：数据的内在维度约为 2，与生成数据的维度一致。")


def main():
    print("=" * 60)
    print("PCA 实际应用示例")
    print("=" * 60)

    demo_data_compression()
    demo_noise_filtering()
    demo_feature_engineering()
    demo_data_exploration()

    print("\n" + "=" * 60)
    print("所有应用示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
