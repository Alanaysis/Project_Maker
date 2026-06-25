"""
PCA 去噪演示

展示使用 PCA 进行数据去噪的方法。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pca import PCA


def create_noisy_data(n_samples=200, n_features=50, n_components=5, noise_level=0.5):
    """创建带噪声的数据"""
    np.random.seed(42)

    # 生成低维信号
    np.random.seed(42)
    W = np.random.randn(n_components, n_features)
    Z = np.random.randn(n_samples, n_components)
    signal = Z @ W

    # 添加噪声
    noise = noise_level * np.random.randn(n_samples, n_features)
    X_noisy = signal + noise

    return X_noisy, signal


def demo_denoising():
    """去噪演示"""
    print("=== PCA 去噪演示 ===\n")

    # 创建数据
    X_noisy, X_clean = create_noisy_data(200, 50, 5, noise_level=0.5)
    print(f"数据形状: {X_noisy.shape}")
    print(f"真实信号维度: 5")

    # 不同主成分数量的去噪效果
    n_components_list = [3, 5, 7, 10, 20]

    print("\n不同主成分数量的去噪效果:")
    print("-" * 50)

    for n_comp in n_components_list:
        pca = PCA(n_components=n_comp)
        X_transformed = pca.fit_transform(X_noisy)
        X_denoised = pca.inverse_transform(X_transformed)

        # 计算误差
        mse_noisy = np.mean((X_noisy - X_clean) ** 2)
        mse_denoised = np.mean((X_denoised - X_clean) ** 2)

        improvement = (mse_noisy - mse_denoised) / mse_noisy * 100

        print(f"n_components={n_comp:2d}: "
              f"MSE={mse_denoised:.4f}, "
              f"改善={improvement:.1f}%")

    print()


def demo_variance_threshold():
    """基于方差阈值的去噪"""
    print("=== 基于方差阈值的去噪 ===\n")

    X_noisy, X_clean = create_noisy_data(200, 50, 5, noise_level=0.5)

    # 使用方差比例选择主成分
    thresholds = [0.80, 0.85, 0.90, 0.95, 0.99]

    print("不同方差阈值的去噪效果:")
    print("-" * 60)

    for threshold in thresholds:
        pca = PCA(n_components=threshold)
        X_transformed = pca.fit_transform(X_noisy)
        X_denoised = pca.inverse_transform(X_transformed)

        mse_denoised = np.mean((X_denoised - X_clean) ** 2)
        n_comp = pca.n_components_

        print(f"阈值={threshold:.2f}: "
              f"n_components={n_comp:2d}, "
              f"MSE={mse_denoised:.4f}")

    print()


def demo_noise_level_impact():
    """噪声水平对去噪效果的影响"""
    print("=== 噪声水平对去噪效果的影响 ===\n")

    noise_levels = [0.1, 0.3, 0.5, 1.0, 2.0]
    n_comp = 5

    print(f"固定主成分数量: {n_comp}")
    print("-" * 50)

    for noise_level in noise_levels:
        X_noisy, X_clean = create_noisy_data(200, 50, 5, noise_level)

        pca = PCA(n_components=n_comp)
        X_transformed = pca.fit_transform(X_noisy)
        X_denoised = pca.inverse_transform(X_transformed)

        mse_noisy = np.mean((X_noisy - X_clean) ** 2)
        mse_denoised = np.mean((X_denoised - X_clean) ** 2)

        print(f"噪声水平={noise_level:.1f}: "
              f"噪声MSE={mse_noisy:.4f}, "
              f"去噪后MSE={mse_denoised:.4f}")

    print()


if __name__ == '__main__':
    demo_denoising()
    demo_variance_threshold()
    demo_noise_level_impact()
    print("去噪演示完成！")
