"""
客户分群示例

使用 K-Means 聚类算法对客户进行分群，
基于客户的消费行为特征将其分为不同的群体。

应用场景:
    - 精准营销
    - 客户价值分析
    - 个性化推荐
    - 客户流失预警
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KMeans, MiniBatchKMeans
from src.utils import (
    compute_silhouette_score_fast,
    compute_calinski_harabasz,
    find_optimal_k_elbow,
    normalize_data,
    evaluate_clustering
)
from src.visualization import plot_clusters, plot_elbow, plot_silhouette


def generate_customer_data(n_customers=1000, random_state=42):
    """
    生成模拟客户数据

    特征:
        - 年消费金额 (Annual Spending)
        - 消费频率 (Purchase Frequency)
        - 平均订单金额 (Average Order Value)
        - 客户年龄 (Customer Age)
        - 会员时长 (Membership Duration in months)

    参数:
        n_customers: 客户数量
        random_state: 随机种子

    返回:
        X: 特征矩阵
        feature_names: 特征名称
        true_segments: 真实分群标签（用于验证）
    """
    rng = np.random.RandomState(random_state)

    # 定义客户分群原型
    segments = {
        'High-Value': {
            'annual_spending': (5000, 2000),
            'frequency': (20, 8),
            'avg_order': (300, 100),
            'age': (35, 10),
            'membership': (36, 12)
        },
        'Medium-Value': {
            'annual_spending': (2000, 800),
            'frequency': (10, 4),
            'avg_order': (200, 60),
            'age': (30, 8),
            'membership': (24, 10)
        },
        'Low-Value': {
            'annual_spending': (500, 300),
            'frequency': (3, 2),
            'avg_order': (150, 50),
            'age': (25, 6),
            'membership': (12, 6)
        },
        'New Customers': {
            'annual_spending': (300, 200),
            'frequency': (2, 1),
            'avg_order': (100, 40),
            'age': (22, 4),
            'membership': (3, 2)
        }
    }

    X_list = []
    true_segments = []
    feature_names = ['Annual Spending', 'Purchase Frequency', 'Average Order Value',
                     'Customer Age', 'Membership Duration']

    samples_per_segment = n_customers // len(segments)

    for i, (segment_name, params) in enumerate(segments.items()):
        n = samples_per_segment if i < len(segments) - 1 else n_customeres - len(X_list)

        # 生成特征
        annual_spending = rng.normal(params['annual_spending'][0],
                                     params['annual_spending'][1], n)
        frequency = rng.normal(params['frequency'][0],
                               params['frequency'][1], n)
        avg_order = rng.normal(params['avg_order'][0],
                               params['avg_order'][1], n)
        age = rng.normal(params['age'][0],
                         params['age'][1], n)
        membership = rng.normal(params['membership'][0],
                                params['membership'][1], n)

        # 组合特征
        segment_data = np.column_stack([
            annual_spending, frequency, avg_order, age, membership
        ])

        X_list.append(segment_data)
        true_segments.extend([i] * n)

    X = np.vstack(X_list)
    true_segments = np.array(true_segments)

    # 确保所有值为正
    X = np.abs(X)

    # 随机打乱
    indices = rng.permutation(len(X))
    X = X[indices]
    true_segments = true_segments[indices]

    return X, feature_names, true_segments


def preprocess_data(X):
    """
    数据预处理

    参数:
        X: 原始特征矩阵

    返回:
        X_normalized: 标准化后的特征矩阵
        mean: 均值
        std: 标准差
    """
    # 标准化
    X_normalized, mean, std = normalize_data(X)

    return X_normalized, mean, std


def find_optimal_k(X, max_k=10):
    """
    寻找最优 K 值

    使用肘部法则和轮廓系数

    参数:
        X: 特征矩阵
        max_k: 最大 K 值

    返回:
        optimal_k: 最优 K 值
        results: 评估结果
    """
    # 肘部法则
    optimal_k_elbow, k_range, wcss_list = find_optimal_k_elbow(X, max_k=max_k)

    # 计算不同 K 值的轮廓系数
    silhouette_scores = []
    calinski_scores = []

    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(X)

        sil_score = compute_silhouette_score_fast(X, labels)
        cal_score = compute_calinski_harabasz(X, labels)

        silhouette_scores.append(sil_score)
        calinski_scores.append(cal_score)

    # 找到轮廓系数最大的 K
    optimal_k_silhouette = np.argmax(silhouette_scores) + 2

    # 综合考虑选择 K
    optimal_k = optimal_k_elbow  # 默认使用肘部法则

    results = {
        'k_range': k_range,
        'wcss_list': wcss_list,
        'optimal_k_elbow': optimal_k_elbow,
        'optimal_k_silhouette': optimal_k_silhouette,
        'silhouette_scores': silhouette_scores,
        'calinski_scores': calinski_scores
    }

    return optimal_k, results


def perform_segmentation(X, n_clusters, method='kmeans'):
    """
    执行客户分群

    参数:
        X: 特征矩阵
        n_clusters: 簇数量
        method: 聚类方法 ('kmeans' 或 'minibatch')

    返回:
        labels: 分群标签
        centers: 簇中心
        metrics: 评估指标
    """
    if method == 'kmeans':
        kmeans = KMeans(n_clusters=n_clusters, init='kmeans++', random_state=42)
    elif method == 'minibatch':
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, batch_size=100, random_state=42)
    else:
        raise ValueError(f"不支持的方法: {method}")

    # 训练模型
    kmeans.fit(X)

    # 获取结果
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    # 评估聚类质量
    metrics = evaluate_clustering(X, labels)

    return labels, centers, metrics


def analyze_segments(X, labels, centers, feature_names):
    """
    分析客户分群结果

    参数:
        X: 特征矩阵
        labels: 分群标签
        centers: 簇中心
        feature_names: 特征名称

    返回:
        segment_analysis: 分群分析结果
    """
    n_clusters = len(np.unique(labels))
    segment_analysis = {}

    for k in range(n_clusters):
        # 获取当前簇的数据
        cluster_mask = labels == k
        cluster_data = X[cluster_mask]

        # 计算统计信息
        segment_info = {
            'size': len(cluster_data),
            'proportion': len(cluster_data) / len(X),
            'center': centers[k],
            'feature_means': np.mean(cluster_data, axis=0),
            'feature_stds': np.std(cluster_data, axis=0)
        }

        # 为每个特征添加分析
        for i, feature_name in enumerate(feature_names):
            segment_info[f'{feature_name}_mean'] = cluster_data[:, i].mean()
            segment_info[f'{feature_name}_std'] = cluster_data[:, i].std()

        segment_analysis[f'Segment {k}'] = segment_info

    return segment_analysis


def visualize_segmentation_results(X, labels, centers, feature_names, results):
    """
    可视化分群结果

    参数:
        X: 特征矩阵
        labels: 分群标签
        centers: 簇中心
        feature_names: 特征名称
        results: 寻找最优 K 的结果
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. 聚类结果（使用前两个特征）
    ax1 = axes[0, 0]
    scatter = ax1.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', alpha=0.6, s=50)
    ax1.scatter(centers[:, 0], centers[:, 1], c='red', marker='X', s=200,
                linewidths=2, edgecolors='black', label='Centroids')
    ax1.set_xlabel(feature_names[0], fontsize=12)
    ax1.set_ylabel(feature_names[1], fontsize=12)
    ax1.set_title('Customer Segments', fontsize=14)
    ax1.legend()
    plt.colorbar(scatter, ax=ax1)

    # 2. 肘部法则
    ax2 = axes[0, 1]
    ax2.plot(results['k_range'], results['wcss_list'], 'bo-', linewidth=2, markersize=8)
    ax2.axvline(x=results['optimal_k_elbow'], color='r', linestyle='--',
                label=f'Optimal K (Elbow): {results["optimal_k_elbow"]}')
    ax2.set_xlabel('Number of Clusters (K)', fontsize=12)
    ax2.set_ylabel('WCSS', fontsize=12)
    ax2.set_title('Elbow Method', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. 轮廓系数
    ax3 = axes[0, 2]
    k_range_sil = range(2, 2 + len(results['silhouette_scores']))
    ax3.plot(k_range_sil, results['silhouette_scores'], 'go-', linewidth=2, markersize=8)
    ax3.axvline(x=results['optimal_k_silhouette'], color='r', linestyle='--',
                label=f'Optimal K (Silhouette): {results["optimal_k_silhouette"]}')
    ax3.set_xlabel('Number of Clusters (K)', fontsize=12)
    ax3.set_ylabel('Silhouette Score', fontsize=12)
    ax3.set_title('Silhouette Analysis', fontsize=14)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Calinski-Harabasz 指数
    ax4 = axes[1, 0]
    ax4.plot(k_range_sil, results['calinski_scores'], 'mo-', linewidth=2, markersize=8)
    ax4.set_xlabel('Number of Clusters (K)', fontsize=12)
    ax4.set_ylabel('Calinski-Harabasz Score', fontsize=12)
    ax4.set_title('Calinski-Harabasz Index', fontsize=14)
    ax4.grid(True, alpha=0.3)

    # 5. 簇大小分布
    ax5 = axes[1, 1]
    unique_labels, counts = np.unique(labels, return_counts=True)
    colors = plt.get_cmap('viridis', len(unique_labels))
    bars = ax5.bar(unique_labels, counts, color=[colors(i) for i in range(len(unique_labels))])
    ax5.set_xlabel('Segment ID', fontsize=12)
    ax5.set_ylabel('Number of Customers', fontsize=12)
    ax5.set_title('Segment Size Distribution', fontsize=14)
    ax5.grid(True, alpha=0.3, axis='y')

    # 添加数值标签
    for bar, count in zip(bars, counts):
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                 str(count), ha='center', va='bottom')

    # 6. 特征重要性（簇中心热图）
    ax6 = axes[1, 2]
    centers_normalized = (centers - centers.min(axis=0)) / (centers.max(axis=0) - centers.min(axis=0) + 1e-8)
    im = ax6.imshow(centers_normalized.T, cmap='YlOrRd', aspect='auto')
    ax6.set_yticks(range(len(feature_names)))
    ax6.set_yticklabels(feature_names, fontsize=10)
    ax6.set_xlabel('Segment ID', fontsize=12)
    ax6.set_title('Feature Importance by Segment', fontsize=14)
    plt.colorbar(im, ax=ax6)

    plt.suptitle('Customer Segmentation Analysis', fontsize=16, y=1.02)
    plt.tight_layout()
    return fig


def print_segment_report(segment_analysis, feature_names):
    """
    打印分群报告

    参数:
        segment_analysis: 分群分析结果
        feature_names: 特征名称
    """
    print("\n" + "=" * 80)
    print("客户分群报告")
    print("=" * 80)

    for segment_name, info in segment_analysis.items():
        print(f"\n{segment_name}:")
        print(f"  客户数量: {info['size']} ({info['proportion']:.1%})")
        print(f"  特征均值:")
        for i, feature_name in enumerate(feature_names):
            print(f"    - {feature_name}: {info['feature_means'][i]:.2f} (±{info['feature_stds'][i]:.2f})")

    print("\n" + "=" * 80)


def main():
    """主函数"""
    print("=" * 60)
    print("客户分群示例")
    print("=" * 60)

    # 1. 生成客户数据
    print("\n1. 生成模拟客户数据...")
    X, feature_names, true_segments = generate_customer_data(n_customers=500)
    print(f"   数据形状: {X.shape}")
    print(f"   特征: {feature_names}")

    # 2. 数据预处理
    print("\n2. 数据预处理...")
    X_normalized, mean, std = preprocess_data(X)
    print(f"   标准化完成")

    # 3. 寻找最优 K
    print("\n3. 寻找最优 K 值...")
    optimal_k, results = find_optimal_k(X_normalized, max_k=8)
    print(f"   肘部法则最优 K: {results['optimal_k_elbow']}")
    print(f"   轮廓系数最优 K: {results['optimal_k_silhouette']}")

    # 4. 执行分群
    print("\n4. 执行客户分群...")
    labels, centers, metrics = perform_segmentation(X_normalized, optimal_k, method='kmeans')
    print(f"   聚类完成，共 {optimal_k} 个分群")
    print(f"   轮廓系数: {metrics['silhouette_score']:.4f}")
    print(f"   Calinski-Harabasz: {metrics['calinski_harabasz']:.4f}")

    # 5. 分析分群结果
    print("\n5. 分析分群结果...")
    segment_analysis = analyze_segments(X_normalized, labels, centers, feature_names)
    print_segment_report(segment_analysis, feature_names)

    # 6. 可视化
    print("\n6. 生成可视化...")
    fig = visualize_segmentation_results(X_normalized, labels, centers, feature_names, results)
    fig.savefig('customer_segmentation.png', dpi=150, bbox_inches='tight')
    print("   图表已保存: customer_segmentation.png")

    # 7. 比较标准 K-Means 和 Mini-Batch K-Means
    print("\n7. 比较标准 K-Means 和 Mini-Batch K-Means...")
    labels_mb, centers_mb, metrics_mb = perform_segmentation(
        X_normalized, optimal_k, method='minibatch'
    )
    print(f"   Mini-Batch 轮廓系数: {metrics_mb['silhouette_score']:.4f}")
    print(f"   Mini-Batch Calinski-Harabasz: {metrics_mb['calinski_harabasz']:.4f}")

    print("\n完成!")
    plt.show()


if __name__ == '__main__':
    main()
