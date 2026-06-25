"""
核 PCA 演示

展示核 PCA 进行非线性降维的能力。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kernel_pca import KernelPCA


def create_swiss_roll(n_samples=1000, noise=0.1):
    """创建瑞士卷数据集"""
    t = 1.5 * np.pi * (1 + 2 * np.random.rand(n_samples))
    x = t * np.cos(t)
    y = 21 * np.random.rand(n_samples)
    z = t * np.sin(t)

    X = np.column_stack([x, y, z]) + noise * np.random.randn(n_samples, 3)
    return X, t


def demo_rbf_kernel():
    """RBF 核 PCA 演示"""
    print("=== RBF 核 PCA 演示 ===\n")

    # 创建瑞士卷数据
    X, colors = create_swiss_roll(500, noise=0.1)
    print(f"原始数据形状: {X.shape}")

    # 不同 gamma 值
    gammas = [0.01, 0.1, 1.0]

    for gamma in gammas:
        kpca = KernelPCA(n_components=2, kernel='rbf', gamma=gamma)
        X_transformed = kpca.fit_transform(X)
        print(f"gamma={gamma}: 输出形状 {X_transformed.shape}")

    print()


def demo_different_kernels():
    """不同核函数比较"""
    print("=== 不同核函数比较 ===\n")

    np.random.seed(42)
    n = 200
    t = np.linspace(0, 4 * np.pi, n)
    X = np.column_stack([
        np.cos(t) + 0.1 * np.random.randn(n),
        np.sin(t) + 0.1 * np.random.randn(n),
        t / (4 * np.pi) + 0.1 * np.random.randn(n),
    ])

    kernels = ['linear', 'rbf', 'poly', 'sigmoid']

    for kernel in kernels:
        kpca = KernelPCA(n_components=2, kernel=kernel)
        X_transformed = kpca.fit_transform(X)
        print(f"{kernel:8s} 核: 输出形状 {X_transformed.shape}")

    print()


def demo_transform_new_data():
    """转换新数据演示"""
    print("=== 转换新数据演示 ===\n")

    np.random.seed(42)
    X_train = np.random.randn(100, 5)

    kpca = KernelPCA(n_components=2, kernel='rbf')
    X_train_transformed = kpca.fit_transform(X_train)

    # 转换新数据
    X_new = np.random.randn(20, 5)
    X_new_transformed = kpca.transform(X_new)

    print(f"训练数据形状: {X_train.shape} -> {X_train_transformed.shape}")
    print(f"新数据形状: {X_new.shape} -> {X_new_transformed.shape}")

    print()


if __name__ == '__main__':
    demo_rbf_kernel()
    demo_different_kernels()
    demo_transform_new_data()
    print("核 PCA 演示完成！")
