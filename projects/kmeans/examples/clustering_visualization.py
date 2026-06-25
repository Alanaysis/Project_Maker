"""
数据聚类可视化示例

展示 K-Means 聚类算法在不同类型数据集上的效果，
以及各种可视化方法的使用。
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KMeans, MiniBatchKMeans
from src.utils import (
    generate_clustered_data,
    compute_silhouette_score_fast,
    compute_calinski_harabasz,
    find_optimal_k_elbow,
    evaluate_clustering
)
from src.visualization import (
    plot_clusters,
    plot_elbow,
    plot_silhouette,
    plot_2d_clusters,
    plot_3d_clusters,
    plot_cluster_distribution,
    plot_convergence
)


def generate_datasets():
    """
    生成多种类型的测试数据集

    返回:
        datasets: 数据集字典
    """
    datasets = {}

    # 1. 球形簇（标准情况）
    X1, y1 = generate_clustered_data(
        n_samples=300, n_clusters=4, n_features=2,
        cluster_std=0.8, random_state=42
    )
    datasets['Spherical Clusters'] = (X1, y1)

    # 2. 不同大小的簇
    rng = np.random.RandomState(42)
    X2 = np.vstack([
        rng.randn(200, 2) * 0.5 + [0, 0],
        rng.randn(100, 2) * 1.0 + [5, 5],
        rng.randn(50, 2) * 0.3 + [10, 0]
    ])
    y2 = np.array([0] * 200 + [1] * 100 + [2] * 50)
    datasets['Different Sizes'] = (X2, y2)

    # 3. 不同密度的簇
    X3 = np.vstack([
        rng.randn(300, 2) * 0.3 + [0, 0],
        rng.randn(100, 2) * 1.5 + [5, 5],
        rng.randn(200, 2) * 0.5 + [10, 0]
    ])
    y3 = np.array([0] * 300 + [1] * 100 + [2] * 200)
    datasets['Different Densities'] = (X3, y3)

    # 4. 非球形簇（月牙形）
    from sklearn.datasets import make_moons
    X4, y4 = make_moons(n_samples=300, noise=0.1, random_state=42)
    datasets['Non-Spherical (Moons)'] = (X4, y4)

    # 5. 3D 数据
    X5, y5 = generate_clustered_data(
        n_samples=300, n_clusters=3, n_features=3,
        cluster_std=1.0, random_state=42
    )
    datasets['3D Data'] = (X5, y5)

    # 6. 高维数据
    X6, y6 = generate_clustered_data(
        n_samples=300, n_clusters=4, n_features=10,
        cluster_std=1.5, random_state=42
    )
    datasets['High Dimensional (10D)'] = (X6, y6)

    return datasets


def visualize_basic_clustering(X, labels, centers, title, ax):
    """
    基本聚类可视化

    参数:
        X: 数据矩阵
        labels: 簇标签
        centers: 簇中心
        title: 标题
        ax: matplotlib 轴对象
    """
    n_clusters = len(np.unique(labels))
    colors = plt.get_cmap('viridis', n_clusters)

    for i in range(n_clusters):
        mask = labels == i
        ax.scatter(X[mask, 0], X[mask, 1],
                   c=[colors(i)], label=f'Cluster {i}',
                   alpha=0.6, s=50)

    # 绘制簇中心
    if centers is not None and centers.shape[1] >= 2:
        ax.scatter(centers[:, 0], centers[:, 1],
                   c='red', marker='X', s=200,
                   linewidths=2, edgecolors='black',
                   label='Centroids')

    ax.set_title(title, fontsize=12)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def visualize_decision_boundary(X, labels, centers, title, ax, resolution=100):
    """
    可视化决策边界

    参数:
        X: 数据矩阵（2D）
        labels: 簇标签
        centers: 簇中心
        title: 标题
        ax: matplotlib 轴对象
        resolution: 网格分辨率
    """
    # 创建网格
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, resolution),
                         np.linspace(y_min, y_max, resolution))

    # 预测网格点的标签
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    from src.distance import pairwise_distances
    distances = pairwise_distances(grid_points, centers)
    grid_labels = np.argmin(distances, axis=1)
    grid_labels = grid_labels.reshape(xx.shape)

    # 绘制决策边界
    ax.contourf(xx, yy, grid_labels, alpha=0.3, cmap='viridis')

    # 绘制数据点
    n_clusters = len(np.unique(labels))
    colors = plt.get_cmap('viridis', n_clusters)

    for i in range(n_clusters):
        mask = labels == i
        ax.scatter(X[mask, 0], X[mask, 1],
                   c=[colors(i)], label=f'Cluster {i}',
                   alpha=0.7, s=50, edgecolors='black', linewidth=0.5)

    # 绘制簇中心
    ax.scatter(centers[:, 0], centers[:, 1],
               c='red', marker='X', s=200,
               linewidths=2, edgecolors='black',
               label='Centroids')

    ax.set_title(title, fontsize=12)
    ax.legend(fontsize=8)


def compare_initialization_methods(X, n_clusters=4):
    """
    比较不同初始化方法

    参数:
        X: 数据矩阵
        n_clusters: 簇数量

    返回:
        fig: matplotlib 图形对象
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 随机初始化
    kmeans_random = KMeans(n_clusters=n_clusters, init='random', random_state=42)
    labels_random = kmeans_random.fit_predict(X)
    centers_random = kmeans_random.cluster_centers_

    visualize_decision_boundary(X, labels_random, centers_random,
                                f'Random Init (WCSS: {kmeans_random.inertia_:.2f})',
                                axes[0])

    # K-Means++ 初始化
    kmeans_pp = KMeans(n_clusters=n_clusters, init='kmeans++', random_state=42)
    labels_pp = kmeans_pp.fit_predict(X)
    centers_pp = kmeans_pp.cluster_centers_

    visualize_decision_boundary(X, labels_pp, centers_pp,
                                f'K-Means++ Init (WCSS: {kmeans_pp.inertia_:.2f})',
                                axes[1])

    # Mini-Batch K-Means
    minibatch = MiniBatchKMeans(n_clusters=n_clusters, batch_size=50, random_state=42)
    labels_mb = minibatch.fit_predict(X)
    centers_mb = minibatch.cluster_centers_

    visualize_decision_boundary(X, labels_mb, centers_mb,
                                f'Mini-Batch (WCSS: {minibatch.inertia_:.2f})',
                                axes[2])

    plt.suptitle('Comparison of Initialization Methods', fontsize=14)
    plt.tight_layout()
    return fig


def visualize_convergence(X, n_clusters=4):
    """
    可视化收敛过程

    参数:
        X: 数据矩阵
        n_clusters: 簇数量

    返回:
        fig: matplotlib 图形对象
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 运行 K-Means 并记录收敛过程
    kmeans = KMeans(n_clusters=n_clusters, max_iter=20, init='kmeans++', random_state=42)

    # 手动迭代以记录历史
    rng = np.random.RandomState(42)
    centroids = kmeans._init_centroids_kmeans_plus_plus(X)

    inertia_history = []
    label_history = []
    center_history = []

    for iteration in range(20):
        # 分配簇
        labels = kmeans._assign_clusters(X, centroids)

        # 更新中心
        centroids_new = kmeans._update_centroids(X, labels)

        # 计算 WCSS
        wcss = kmeans._compute_wcss(X, labels, centroids_new)

        # 记录历史
        inertia_history.append(wcss)
        label_history.append(labels.copy())
        center_history.append(centroids_new.copy())

        # 收敛判断
        centroid_shift = np.max(np.linalg.norm(centroids_new - centroids, axis=1))
        centroids = centroids_new

        if centroid_shift < 1e-4:
            break

    # 可视化不同迭代阶段
    iterations_to_show = [0, 1, 2, 5, len(inertia_history) - 1]
    iterations_to_show = [i for i in iterations_to_show if i < len(inertia_history)]

    for idx, iteration in enumerate(iterations_to_show[:5]):
        ax = axes[idx // 3, idx % 3]
        visualize_decision_boundary(
            X, label_history[iteration], center_history[iteration],
            f'Iteration {iteration + 1} (WCSS: {inertia_history[iteration]:.2f})',
            ax
        )

    # 绘制收敛曲线
    ax = axes[1, 2]
    ax.plot(range(1, len(inertia_history) + 1), inertia_history, 'b-o', linewidth=2)
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('WCSS', fontsize=12)
    ax.set_title('Convergence History', fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.suptitle('K-Means Convergence Process', fontsize=14)
    plt.tight_layout()
    return fig


def evaluate_different_k(X, max_k=10):
    """
    评估不同 K 值的聚类效果

    参数:
        X: 数据矩阵
        max_k: 最大 K 值

    返回:
        fig: matplotlib 图形对象
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 肘部法则
    optimal_k, k_range, wcss_list = find_optimal_k_elbow(X, max_k=max_k)

    axes[0].plot(k_range, wcss_list, 'bo-', linewidth=2, markersize=8)
    axes[0].axvline(x=optimal_k, color='r', linestyle='--',
                    label=f'Optimal K = {optimal_k}')
    axes[0].set_xlabel('Number of Clusters (K)', fontsize=12)
    axes[0].set_ylabel('WCSS', fontsize=12)
    axes[0].set_title('Elbow Method', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 轮廓系数
    silhouette_scores = []
    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(X)
        score = compute_silhouette_score_fast(X, labels)
        silhouette_scores.append(score)

    k_range_sil = range(2, max_k + 1)
    optimal_k_sil = np.argmax(silhouette_scores) + 2

    axes[1].plot(k_range_sil, silhouette_scores, 'go-', linewidth=2, markersize=8)
    axes[1].axvline(x=optimal_k_sil, color='r', linestyle='--',
                    label=f'Optimal K = {optimal_k_sil}')
    axes[1].set_xlabel('Number of Clusters (K)', fontsize=12)
    axes[1].set_ylabel('Silhouette Score', fontsize=12)
    axes[1].set_title('Silhouette Analysis', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Calinski-Harabasz 指数
    calinski_scores = []
    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(X)
        score = compute_calinski_harabasz(X, labels)
        calinski_scores.append(score)

    optimal_k_cal = np.argmax(calinski_scores) + 2

    axes[2].plot(k_range_sil, calinski_scores, 'mo-', linewidth=2, markersize=8)
    axes[2].axvline(x=optimal_k_cal, color='r', linestyle='--',
                    label=f'Optimal K = {optimal_k_cal}')
    axes[2].set_xlabel('Number of Clusters (K)', fontsize=12)
    axes[2].set_ylabel('Calinski-Harabasz Score', fontsize=12)
    axes[2].set_title('Calinski-Harabasz Index', fontsize=12)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('Optimal K Selection', fontsize=14)
    plt.tight_layout()
    return fig


def main():
    """主函数"""
    print("=" * 60)
    print("数据聚类可视化示例")
    print("=" * 60)

    # 1. 生成数据集
    print("\n1. 生成测试数据集...")
    datasets = generate_datasets()
    print(f"   共生成 {len(datasets)} 个数据集")

    # 2. 基本聚类可视化
    print("\n2. 基本聚类可视化...")
    fig1, axes = plt.subplots(2, 3, figsize=(18, 12))

    for idx, (name, (X, y)) in enumerate(datasets.items()):
        if X.shape[1] > 2:
            X_plot = X[:, :2]
        else:
            X_plot = X

        ax = axes[idx // 3, idx % 3]

        # 执行聚类
        n_clusters = len(np.unique(y))
        kmeans = KMeans(n_clusters=n_clusters, init='kmeans++', random_state=42)
        labels = kmeans.fit_predict(X_plot)

        visualize_basic_clustering(X_plot, labels, kmeans.cluster_centers_, name, ax)

    plt.suptitle('K-Means Clustering on Different Datasets', fontsize=16)
    plt.tight_layout()
    fig1.savefig('clustering_basic.png', dpi=150, bbox_inches='tight')

    # 3. 比较初始化方法
    print("\n3. 比较初始化方法...")
    X_test, _ = datasets['Spherical Clusters']
    fig2 = compare_initialization_methods(X_test, n_clusters=4)
    fig2.savefig('clustering_initialization.png', dpi=150, bbox_inches='tight')

    # 4. 可视化收敛过程
    print("\n4. 可视化收敛过程...")
    fig3 = visualize_convergence(X_test, n_clusters=4)
    fig3.savefig('clustering_convergence.png', dpi=150, bbox_inches='tight')

    # 5. 评估不同 K 值
    print("\n5. 评估不同 K 值...")
    fig4 = evaluate_different_k(X_test, max_k=10)
    fig4.savefig('clustering_k_evaluation.png', dpi=150, bbox_inches='tight')

    # 6. 3D 聚类可视化
    print("\n6. 3D 聚类可视化...")
    X_3d, y_3d = datasets['3D Data']
    kmeans_3d = KMeans(n_clusters=3, init='kmeans++', random_state=42)
    labels_3d = kmeans_3d.fit_predict(X_3d)

    fig5 = plot_3d_clusters(X_3d, labels_3d, kmeans_3d.cluster_centers_,
                            title='3D Clustering Result')
    fig5.savefig('clustering_3d.png', dpi=150, bbox_inches='tight')

    # 7. 综合评估
    print("\n7. 综合评估结果...")
    for name, (X, y) in datasets.items():
        if X.shape[1] > 2:
            X_eval = X[:, :2]
        else:
            X_eval = X

        n_clusters = len(np.unique(y))
        kmeans = KMeans(n_clusters=n_clusters, init='kmeans++', random_state=42)
        labels = kmeans.fit_predict(X_eval)

        metrics = evaluate_clustering(X_eval, labels)
        print(f"\n   {name}:")
        print(f"     轮廓系数: {metrics['silhouette_score']:.4f}")
        print(f"     Calinski-Harabasz: {metrics['calinski_harabasz']:.4f}")

    print("\n完成! 图表已保存。")
    plt.show()


if __name__ == '__main__':
    main()
