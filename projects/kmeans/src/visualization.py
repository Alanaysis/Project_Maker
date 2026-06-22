"""
可视化模块

提供 K-Means 聚类结果的可视化工具。
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_clusters(X, labels, centroids, title="K-Means Clustering", figsize=(10, 8)):
    """
    绘制聚类结果

    参数:
        X: 数据矩阵，形状 (n_samples, n_features)
        labels: 簇标签数组
        centroids: 簇中心矩阵
        title: 图表标题
        figsize: 图表大小
    """
    X = np.asarray(X)
    labels = np.asarray(labels)
    centroids = np.asarray(centroids)

    n_features = X.shape[1]
    n_clusters = len(np.unique(labels))

    if n_features == 2:
        return plot_2d_clusters(X, labels, centroids, title, figsize)
    elif n_features == 3:
        return plot_3d_clusters(X, labels, centroids, title, figsize)
    else:
        # 对于高维数据，使用前两个特征进行可视化
        print(f"数据维度为 {n_features}，仅显示前两个特征")
        return plot_2d_clusters(X[:, :2], labels, centroids[:, :2], title, figsize)


def plot_2d_clusters(X, labels, centroids, title="K-Means Clustering", figsize=(10, 8)):
    """
    2D 聚类可视化

    参数:
        X: 数据矩阵，形状 (n_samples, 2)
        labels: 簇标签数组
        centroids: 簇中心矩阵，形状 (n_clusters, 2)
        title: 图表标题
        figsize: 图表大小
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 获取唯一标签
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    # 使用颜色映射
    colors = plt.get_cmap('viridis', n_clusters)

    # 绘制每个簇的数据点
    for i, label in enumerate(unique_labels):
        mask = labels == label
        ax.scatter(X[mask, 0], X[mask, 1],
                   c=[colors(i)],
                   label=f'Cluster {label}',
                   alpha=0.6,
                   s=50)

    # 绘制簇中心
    ax.scatter(centroids[:, 0], centroids[:, 1],
               c='red',
               marker='X',
               s=200,
               linewidths=2,
               edgecolors='black',
               label='Centroids')

    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Feature 1', fontsize=12)
    ax.set_ylabel('Feature 2', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_3d_clusters(X, labels, centroids, title="K-Means Clustering", figsize=(12, 10)):
    """
    3D 聚类可视化

    参数:
        X: 数据矩阵，形状 (n_samples, 3)
        labels: 簇标签数组
        centroids: 簇中心矩阵，形状 (n_clusters, 3)
        title: 图表标题
        figsize: 图表大小
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')

    # 获取唯一标签
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    # 使用颜色映射
    colors = plt.get_cmap('viridis', n_clusters)

    # 绘制每个簇的数据点
    for i, label in enumerate(unique_labels):
        mask = labels == label
        ax.scatter(X[mask, 0], X[mask, 1], X[mask, 2],
                   c=[colors(i)],
                   label=f'Cluster {label}',
                   alpha=0.6,
                   s=50)

    # 绘制簇中心
    ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2],
               c='red',
               marker='X',
               s=200,
               linewidths=2,
               edgecolors='black',
               label='Centroids')

    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Feature 1', fontsize=12)
    ax.set_ylabel('Feature 2', fontsize=12)
    ax.set_zlabel('Feature 3', fontsize=12)
    ax.legend()

    plt.tight_layout()
    return fig


def plot_elbow(wcss_list, k_range, title="Elbow Method", figsize=(10, 6)):
    """
    绘制肘部法则图

    参数:
        wcss_list: 不同 K 值对应的 WCSS 列表
        k_range: K 值范围
        title: 图表标题
        figsize: 图表大小
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(k_range, wcss_list, 'bo-', linewidth=2, markersize=8)
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Number of Clusters (K)', fontsize=12)
    ax.set_ylabel('Within-Cluster Sum of Squares (WCSS)', fontsize=12)
    ax.set_xticks(k_range)
    ax.grid(True, alpha=0.3)

    # 标记最小值点
    min_idx = np.argmin(wcss_list)
    ax.scatter(k_range[min_idx], wcss_list[min_idx],
               c='red', s=100, zorder=5,
               label=f'Min WCSS (K={k_range[min_idx]})')

    ax.legend()

    plt.tight_layout()
    return fig


def plot_silhouette(X, labels, title="Silhouette Analysis", figsize=(10, 6)):
    """
    绘制轮廓系数图

    参数:
        X: 数据矩阵
        labels: 簇标签数组
        title: 图表标题
        figsize: 图表大小
    """
    from sklearn.metrics import silhouette_samples, silhouette_score

    fig, ax = plt.subplots(figsize=figsize)

    # 计算轮廓系数
    silhouette_avg = silhouette_score(X, labels)
    sample_silhouette_values = silhouette_samples(X, labels)

    n_clusters = len(np.unique(labels))
    y_lower = 10

    colors = plt.get_cmap('viridis', n_clusters)

    for i in range(n_clusters):
        # 获取当前簇的轮廓系数
        cluster_silhouette_values = sample_silhouette_values[labels == i]
        cluster_silhouette_values.sort()

        size_cluster = cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster

        ax.fill_betweenx(np.arange(y_lower, y_upper),
                          0, cluster_silhouette_values,
                          facecolor=colors(i), edgecolor=colors(i), alpha=0.7)

        ax.text(-0.05, y_lower + 0.5 * size_cluster, str(i))
        y_lower = y_upper + 10

    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Silhouette Coefficient', fontsize=12)
    ax.set_ylabel('Cluster Label', fontsize=12)

    # 添加平均轮廓系数线
    ax.axvline(x=silhouette_avg, color="red", linestyle="--",
               label=f'Average: {silhouette_avg:.3f}')

    ax.legend()
    ax.set_yticks([])

    plt.tight_layout()
    return fig


def plot_cluster_distribution(labels, title="Cluster Distribution", figsize=(10, 6)):
    """
    绘制簇分布图

    参数:
        labels: 簇标签数组
        title: 图表标题
        figsize: 图表大小
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    unique_labels, counts = np.unique(labels, return_counts=True)

    # 柱状图
    bars = ax1.bar(unique_labels, counts, color=plt.get_cmap('viridis', len(unique_labels))(range(len(unique_labels))))
    ax1.set_title(title, fontsize=16)
    ax1.set_xlabel('Cluster Label', fontsize=12)
    ax1.set_ylabel('Number of Samples', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='y')

    # 在柱状图上添加数值标签
    for bar, count in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 str(count), ha='center', va='bottom')

    # 饼图
    ax2.pie(counts, labels=[f'Cluster {i}' for i in unique_labels],
            autopct='%1.1f%%', startangle=90,
            colors=plt.get_cmap('viridis', len(unique_labels))(range(len(unique_labels))))
    ax2.set_title('Cluster Proportion', fontsize=16)

    plt.tight_layout()
    return fig


def plot_convergence(inertia_history, title="Convergence History", figsize=(10, 6)):
    """
    绘制收敛历史图

    参数:
        inertia_history: 每次迭代的 WCSS 列表
        title: 图表标题
        figsize: 图表大小
    """
    fig, ax = plt.subplots(figsize=figsize)

    iterations = range(1, len(inertia_history) + 1)
    ax.plot(iterations, inertia_history, 'b-', linewidth=2)
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Within-Cluster Sum of Squares (WCSS)', fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig