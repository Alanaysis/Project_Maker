"""
增量 PCA 演示

展示增量 PCA 处理大数据集的能力。
"""

import numpy as np
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.incremental_pca import IncrementalPCA
from src.pca import PCA


def demo_basic_incremental():
    """基本增量 PCA 演示"""
    print("=== 基本增量 PCA 演示 ===\n")

    np.random.seed(42)
    X = np.random.randn(1000, 20)

    # 标准 PCA
    pca = PCA(n_components=5)
    X_pca = pca.fit_transform(X)

    # 增量 PCA
    ipca = IncrementalPCA(n_components=5, batch_size=100)
    X_ipca = ipca.fit_transform(X)

    print(f"原始数据形状: {X.shape}")
    print(f"标准 PCA 输出: {X_pca.shape}")
    print(f"增量 PCA 输出: {X_ipca.shape}")

    # 比较结果
    print("\n解释方差比例:")
    print(f"  标准 PCA: {pca.explained_variance_ratio_}")
    print(f"  增量 PCA: {ipca.explained_variance_ratio_}")

    print()


def demo_partial_fit():
    """增量更新演示"""
    print("=== 增量更新演示 ===\n")

    np.random.seed(42)
    ipca = IncrementalPCA(n_components=3)

    # 模拟流式数据
    n_batches = 5
    batch_size = 200

    for i in range(n_batches):
        X_batch = np.random.randn(batch_size, 10)
        ipca.partial_fit(X_batch)
        print(f"批次 {i + 1}: 已处理 {ipca.n_samples_seen_} 个样本")

    # 转换数据
    X_test = np.random.randn(100, 10)
    X_transformed = ipca.transform(X_test)
    print(f"\n转换测试数据: {X_test.shape} -> {X_transformed.shape}")

    print()


def demo_memory_efficiency():
    """内存效率演示"""
    print("=== 内存效率演示 ===\n")

    n_samples = 10000
    n_features = 50
    batch_size = 500

    print(f"数据集大小: {n_samples} x {n_features}")
    print(f"批次大小: {batch_size}")
    print(f"批次数量: {n_samples // batch_size}")

    # 模拟处理
    ipca = IncrementalPCA(n_components=10, batch_size=batch_size)

    start_time = time.time()
    for i in range(0, n_samples, batch_size):
        X_batch = np.random.randn(batch_size, n_features)
        ipca.partial_fit(X_batch)

    elapsed = time.time() - start_time
    print(f"\n处理时间: {elapsed:.3f} 秒")
    print(f"最终样本数: {ipca.n_samples_seen_}")
    print(f"主成分形状: {ipca.components_.shape}")

    print()


def demo_reconstruction():
    """重建演示"""
    print("=== 重建演示 ===\n")

    np.random.seed(42)
    X = np.random.randn(500, 15)

    ipca = IncrementalPCA(n_components=5, batch_size=100)
    X_transformed = ipca.fit_transform(X)
    X_reconstructed = ipca.inverse_transform(X_transformed)

    # 计算重建误差
    mse = np.mean((X - X_reconstructed) ** 2)
    print(f"原始数据形状: {X.shape}")
    print(f"降维后形状: {X_transformed.shape}")
    print(f"重建后形状: {X_reconstructed.shape}")
    print(f"重建 MSE: {mse:.6f}")

    print()


if __name__ == '__main__':
    demo_basic_incremental()
    demo_partial_fit()
    demo_memory_efficiency()
    demo_reconstruction()
    print("增量 PCA 演示完成！")
