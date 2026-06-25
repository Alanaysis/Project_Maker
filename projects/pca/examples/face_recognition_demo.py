"""
人脸识别（特征脸）演示

展示使用 PCA 进行人脸识别的特征脸方法。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pca import PCA


def create_synthetic_faces(n_subjects=10, n_images_per_subject=5, image_size=32):
    """创建合成人脸数据（不依赖 scipy，使用向量化平滑）"""
    np.random.seed(42)

    # 为每个主体创建基础脸
    base_faces = []
    for i in range(n_subjects):
        # 创建基础特征
        face = np.random.randn(image_size, image_size)
        # 向量化平滑化（简单均值滤波）
        smoothed = np.zeros_like(face)
        smoothed[1:-1, 1:-1] = (
            face[:-2, :-2] + face[:-2, 1:-1] + face[:-2, 2:] +
            face[1:-1, :-2] + face[1:-1, 1:-1] + face[1:-1, 2:] +
            face[2:, :-2] + face[2:, 1:-1] + face[2:, 2:]
        ) / 9.0
        # 复制边缘
        smoothed[0, :] = face[0, :]
        smoothed[-1, :] = face[-1, :]
        smoothed[:, 0] = face[:, 0]
        smoothed[:, -1] = face[:, -1]
        base_faces.append(smoothed.flatten())

    base_faces = np.array(base_faces)

    # 为每个主体生成多张图片（加噪声和轻微变换）
    X = []
    y = []

    for i in range(n_subjects):
        for j in range(n_images_per_subject):
            # 添加噪声和变换
            face = base_faces[i].copy()
            face += 0.1 * np.random.randn(image_size * image_size)
            # 轻微缩放
            scale = 1 + 0.05 * np.random.randn()
            face *= scale

            X.append(face)
            y.append(i)

    return np.array(X), np.array(y)


def demo_eigenfaces():
    """特征脸演示"""
    print("=== 特征脸演示 ===\n")

    # 简化版本（不依赖 scipy）
    np.random.seed(42)
    n_subjects = 10
    n_images = 5
    image_size = 16  # 使用更小的图像大小

    X = []
    y = []
    for i in range(n_subjects):
        base = np.random.randn(image_size * image_size)
        for j in range(n_images):
            face = base + 0.2 * np.random.randn(image_size * image_size)
            X.append(face)
            y.append(i)

    X = np.array(X)
    y = np.array(y)

    print(f"数据形状: {X.shape}")
    print(f"主体数量: {len(np.unique(y))}")
    print(f"每主体图片数: {len(y) // len(np.unique(y))}")

    # 计算特征脸
    n_components = 20
    pca = PCA(n_components=n_components)
    X_transformed = pca.fit_transform(X)

    print(f"\n主成分数量: {n_components}")
    print(f"解释方差比例: {pca.explained_variance_ratio_[:5]}...")
    print(f"累积解释方差: {np.sum(pca.explained_variance_ratio_):.3f}")

    # 获取特征脸
    eigenfaces = pca.components_
    print(f"\n特征脸形状: {eigenfaces.shape}")

    print()


def demo_face_reconstruction():
    """人脸重建演示"""
    print("=== 人脸重建演示 ===\n")

    np.random.seed(42)
    image_size = 16  # 使用更小的图像大小
    n_images = 50

    # 创建模拟人脸数据
    X = np.random.randn(n_images, image_size * image_size)

    # 不同主成分数量的重建
    n_components_list = [5, 10, 20, 40]

    print("不同主成分数量的重建效果:")
    print("-" * 50)

    for n_comp in n_components_list:
        pca = PCA(n_components=n_comp)
        X_transformed = pca.fit_transform(X)
        X_reconstructed = pca.inverse_transform(X_transformed)

        mse = np.mean((X - X_reconstructed) ** 2)
        compression = n_comp / (image_size * image_size) * 100

        print(f"n_components={n_comp:2d}: "
              f"MSE={mse:.4f}, "
              f"压缩率={compression:.1f}%")

    print()


def demo_face_matching():
    """人脸匹配演示"""
    print("=== 人脸匹配演示 ===\n")

    np.random.seed(42)

    # 创建 5 个主体，每个 4 张图片
    n_subjects = 5
    n_images = 4
    image_size = 16  # 使用更小的图像大小

    X = []
    y = []

    for i in range(n_subjects):
        base = np.random.randn(image_size * image_size)
        for j in range(n_images):
            face = base + 0.1 * np.random.randn(image_size * image_size)
            X.append(face)
            y.append(i)

    X = np.array(X)
    y = np.array(y)

    # 使用 PCA 降维
    n_components = 10
    pca = PCA(n_components=n_components)
    X_transformed = pca.fit_transform(X)

    print(f"数据形状: {X.shape} -> {X_transformed.shape}")

    # 计算距离矩阵
    n = len(X_transformed)
    distances = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            distances[i, j] = np.linalg.norm(X_transformed[i] - X_transformed[j])

    # 测试匹配
    test_idx = 0  # 第一张图片
    distances_to_test = distances[test_idx].copy()
    distances_to_test[test_idx] = np.inf  # 排除自己

    # 找到最近的匹配
    best_match = np.argmin(distances_to_test)
    true_label = y[test_idx]
    match_label = y[best_match]

    print(f"\n查询图片: 主体 {true_label}")
    print(f"最佳匹配: 主体 {match_label} (距离: {distances_to_test[best_match]:.3f})")
    print(f"匹配正确: {true_label == match_label}")

    print()


if __name__ == '__main__':
    demo_eigenfaces()
    demo_face_reconstruction()
    demo_face_matching()
    print("人脸识别演示完成！")
