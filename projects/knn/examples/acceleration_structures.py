"""
加速结构示例

比较暴力搜索、KD-Tree 和 Ball Tree 的性能。
"""

import numpy as np
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KDTree, BallTree, KNNClassifier


def benchmark_search(X_train, y_train, X_test, k=5):
    """
    基准测试不同搜索方法

    Args:
        X_train: 训练数据
        y_train: 训练标签
        X_test: 测试数据
        k: 近邻数量

    Returns:
        results: 各方法的耗时结果
    """
    results = {}

    # 1. 暴力搜索
    print("   测试暴力搜索...")
    start = time.time()
    knn_brute = KNNClassifier(k=k, metric='euclidean', weights='uniform')
    knn_brute.fit(X_train, y_train)
    predictions_brute = knn_brute.predict(X_test)
    time_brute = time.time() - start
    results['brute_force'] = time_brute

    # 2. KD-Tree
    print("   测试 KD-Tree...")
    start = time.time()
    kd_tree = KDTree(metric='euclidean')
    kd_tree.build(X_train, y_train)
    predictions_kd = []
    for x in X_test:
        indices, distances = kd_tree.query(x, k=k)
        labels = y_train[indices]
        unique_labels, counts = np.unique(labels, return_counts=True)
        predictions_kd.append(unique_labels[np.argmax(counts)])
    predictions_kd = np.array(predictions_kd)
    time_kd = time.time() - start
    results['kd_tree'] = time_kd

    # 3. Ball Tree
    print("   测试 Ball Tree...")
    start = time.time()
    ball_tree = BallTree(metric='euclidean', leaf_size=10)
    ball_tree.build(X_train, y_train)
    predictions_ball = []
    for x in X_test:
        indices, distances = ball_tree.query(x, k=k)
        labels = y_train[indices]
        unique_labels, counts = np.unique(labels, return_counts=True)
        predictions_ball.append(unique_labels[np.argmax(counts)])
    predictions_ball = np.array(predictions_ball)
    time_ball = time.time() - start
    results['ball_tree'] = time_ball

    # 验证结果一致性
    results['consistent_kd'] = np.array_equal(predictions_brute, predictions_kd)
    results['consistent_ball'] = np.array_equal(predictions_brute, predictions_ball)

    return results


def main():
    """运行加速结构示例"""
    print("=" * 60)
    print("加速结构示例 - KD-Tree vs Ball Tree")
    print("=" * 60)

    # 测试不同数据规模
    sizes = [100, 500, 1000, 2000]
    n_features_list = [2, 5, 10]
    k = 5

    print("\n1. 不同数据规模的性能比较")
    print("-" * 60)

    for n_features in n_features_list:
        print(f"\n特征维度: {n_features}")
        print(f"{'样本数':<10} {'暴力搜索':<15} {'KD-Tree':<15} {'Ball Tree':<15}")
        print("-" * 55)

        for n_samples in sizes:
            # 生成随机数据
            np.random.seed(42)
            X_train = np.random.randn(n_samples, n_features)
            y_train = np.random.randint(0, 3, n_samples)
            X_test = np.random.randn(20, n_features)

            results = benchmark_search(X_train, y_train, X_test, k=k)

            print(f"{n_samples:<10} "
                  f"{results['brute_force']:<15.4f} "
                  f"{results['kd_tree']:<15.4f} "
                  f"{results['ball_tree']:<15.4f}")

    # 测试不同特征维度
    print("\n\n2. 不同特征维度的性能比较")
    print("-" * 60)

    n_samples = 1000
    feature_dims = [2, 3, 5, 10, 20]

    print(f"样本数: {n_samples}")
    print(f"{'特征维度':<10} {'暴力搜索':<15} {'KD-Tree':<15} {'Ball Tree':<15}")
    print("-" * 55)

    for n_features in feature_dims:
        np.random.seed(42)
        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randint(0, 3, n_samples)
        X_test = np.random.randn(20, n_features)

        results = benchmark_search(X_train, y_train, X_test, k=k)

        print(f"{n_features:<10} "
              f"{results['brute_force']:<15.4f} "
              f"{results['kd_tree']:<15.4f} "
              f"{results['ball_tree']:<15.4f}")

    # 测试不同 K 值
    print("\n\n3. 不同 K 值的性能比较")
    print("-" * 60)

    n_samples = 1000
    n_features = 5
    k_values = [1, 3, 5, 10, 20]

    print(f"样本数: {n_samples}, 特征维度: {n_features}")
    print(f"{'K 值':<10} {'暴力搜索':<15} {'KD-Tree':<15} {'Ball Tree':<15}")
    print("-" * 55)

    for k in k_values:
        np.random.seed(42)
        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randint(0, 3, n_samples)
        X_test = np.random.randn(20, n_features)

        results = benchmark_search(X_train, y_train, X_test, k=k)

        print(f"{k:<10} "
              f"{results['brute_force']:<15.4f} "
              f"{results['kd_tree']:<15.4f} "
              f"{results['ball_tree']:<15.4f}")

    # 测试半径搜索
    print("\n\n4. 半径搜索示例")
    print("-" * 60)

    np.random.seed(42)
    X = np.random.randn(500, 2)
    y = np.random.randint(0, 3, 500)
    query_point = np.array([0.5, 0.5])
    radius = 0.5

    # KD-Tree 半径搜索
    kd_tree = KDTree(metric='euclidean')
    kd_tree.build(X, y)
    kd_indices, kd_distances = kd_tree.query_radius(query_point, radius)
    print(f"KD-Tree 半径搜索 (radius={radius}):")
    print(f"   找到 {len(kd_indices)} 个点")

    # Ball Tree 半径搜索
    ball_tree = BallTree(metric='euclidean', leaf_size=10)
    ball_tree.build(X, y)
    ball_indices, ball_distances = ball_tree.query_radius(query_point, radius)
    print(f"Ball Tree 半径搜索 (radius={radius}):")
    print(f"   找到 {len(ball_indices)} 个点")

    # 树的统计信息
    print("\n\n5. 树的统计信息")
    print("-" * 60)

    X = np.random.randn(1000, 5)
    y = np.random.randint(0, 3, 1000)

    kd_tree = KDTree(metric='euclidean')
    kd_tree.build(X, y)
    print(f"KD-Tree:")
    print(f"   节点数: {kd_tree.get_size()}")
    print(f"   树深度: {kd_tree.get_depth()}")

    ball_tree = BallTree(metric='euclidean', leaf_size=10)
    ball_tree.build(X, y)
    print(f"Ball Tree:")
    print(f"   节点数: {ball_tree.get_size()}")
    print(f"   树深度: {ball_tree.get_depth()}")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
