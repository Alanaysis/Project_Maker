#!/usr/bin/env python3
"""
PCA 基本使用示例

演示如何使用 PCA 进行降维，包括：
1. 创建数据
2. 拟合 PCA 模型
3. 降维和可视化
4. 分析解释方差
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pca import PCA


def main():
    print("=" * 60)
    print("PCA 主成分分析 - 基本使用示例")
    print("=" * 60)

    # 1. 创建示例数据
    print("\n[1] 创建示例数据...")
    np.random.seed(42)

    # 创建具有相关性的数据
    n_samples = 200
    x = np.random.randn(n_samples)
    y = 0.5 * x + np.random.randn(n_samples) * 0.3
    z = 0.3 * x + 0.2 * y + np.random.randn(n_samples) * 0.2
    w = np.random.randn(n_samples) * 0.1
    v = np.random.randn(n_samples) * 0.05

    X = np.column_stack([x, y, z, w, v])
    print(f"   数据形状: {X.shape} ({X.shape[0]} 个样本, {X.shape[1]} 个特征)")

    # 2. 拟合 PCA 模型
    print("\n[2] 拟合 PCA 模型...")
    pca = PCA(n_components=3)
    X_reduced = pca.fit_transform(X)
    print(f"   降维后形状: {X_reduced.shape}")

    # 3. 分析解释方差
    print("\n[3] 解释方差分析:")
    print("-" * 50)
    print(f"   {'主成分':<10} {'特征值':<15} {'方差比例':<15} {'累积比例':<15}")
    print("-" * 50)

    cumulative = 0.0
    for i in range(pca.n_components_):
        var = pca.explained_variance_[i]
        ratio = pca.explained_variance_ratio_[i]
        cumulative += ratio
        print(f"   PC{i+1:<8} {var:<15.4f} {ratio:<15.4%} {cumulative:<15.4%}")

    # 4. 主成分方向
    print("\n[4] 主成分方向（特征向量）:")
    feature_names = ["x", "y", "z", "w", "v"]
    for i in range(pca.n_components_):
        print(f"   PC{i+1}: {pca.components_[i]}")

    # 5. 重建误差
    print("\n[5] 重建误差分析:")
    for n_comp in range(1, X.shape[1] + 1):
        pca_temp = PCA(n_components=n_comp)
        pca_temp.fit(X)
        error = pca_temp.reconstruction_error(X)
        print(f"   n_components={n_comp}: MSE = {error:.6f}")

    # 6. 数据预览
    print("\n[6] 降维后数据预览（前5个样本）:")
    print(f"   {X_reduced[:5]}")

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
