"""
鸢尾花分类示例

使用 KNN 分类器对鸢尾花数据集进行分类。
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KNNClassifier, CrossValidator, train_test_split, accuracy_score


def load_iris_data():
    """
    加载鸢尾花数据集（简化版本，无需外部依赖）

    返回 150 个样本，3 个类别，4 个特征。
    """
    # 使用 NumPy 生成模拟的鸢尾花数据
    np.random.seed(42)

    # 类别 0: 山鸢尾 (Setosa)
    # 特征: 花萼长度, 花萼宽度, 花瓣长度, 花瓣宽度
    setosa = np.random.randn(50, 4) * [0.35, 0.38, 0.17, 0.10] + [5.0, 3.4, 1.5, 0.2]

    # 类别 1: 变色鸢尾 (Versicolor)
    versicolor = np.random.randn(50, 4) * [0.51, 0.31, 0.47, 0.20] + [5.9, 2.8, 4.3, 1.3]

    # 类别 2: 维吉尼亚鸢尾 (Virginica)
    virginica = np.random.randn(50, 4) * [0.64, 0.32, 0.55, 0.27] + [6.6, 3.0, 5.5, 2.0]

    # 合并数据
    X = np.vstack([setosa, versicolor, virginica])
    y = np.array([0] * 50 + [1] * 50 + [2] * 50)

    # 打乱数据
    indices = np.random.permutation(150)
    return X[indices], y[indices]


def main():
    """运行鸢尾花分类示例"""
    print("=" * 60)
    print("鸢尾花分类示例 - KNN 分类器")
    print("=" * 60)

    # 1. 加载数据
    print("\n1. 加载数据...")
    X, y = load_iris_data()
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   类别数量: {len(np.unique(y))}")
    print(f"   类别分布: {dict(zip(*np.unique(y, return_counts=True)))}")

    # 2. 划分数据集
    print("\n2. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 3. 使用不同 K 值训练模型
    print("\n3. 测试不同 K 值...")
    k_values = [1, 3, 5, 7, 9, 11, 13, 15]
    results = []

    for k in k_values:
        knn = KNNClassifier(k=k, metric='euclidean', weights='uniform')
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        results.append((k, accuracy))
        print(f"   K={k:2d}: 准确率 = {accuracy:.4f}")

    # 4. 使用不同距离度量
    print("\n4. 测试不同距离度量...")
    metrics = ['euclidean', 'manhattan', 'cosine']

    for metric in metrics:
        knn = KNNClassifier(k=5, metric=metric, weights='uniform')
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        print(f"   {metric:10s}: 准确率 = {accuracy:.4f}")

    # 5. 使用不同权重策略
    print("\n5. 测试不同权重策略...")
    for weights in ['uniform', 'distance']:
        knn = KNNClassifier(k=5, metric='euclidean', weights=weights)
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        print(f"   {weights:10s}: 准确率 = {accuracy:.4f}")

    # 6. 交叉验证选择最优 K
    print("\n6. 交叉验证选择最优 K...")
    cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)
    cv_results = cv.select_k(
        X, y,
        k_range=[1, 3, 5, 7, 9, 11, 13, 15],
        metric='euclidean',
        task='classification'
    )
    print(f"   最优 K: {cv_results['best_k']}")
    print(f"   最优准确率: {cv_results['best_score']:.4f}")

    # 7. 使用最优 K 训练最终模型
    print("\n7. 使用最优 K 训练最终模型...")
    best_knn = KNNClassifier(
        k=cv_results['best_k'],
        metric='euclidean',
        weights='distance'
    )
    best_knn.fit(X_train, y_train)

    # 8. 评估最终模型
    print("\n8. 最终模型评估...")
    train_accuracy = best_knn.score(X_train, y_train)
    test_accuracy = best_knn.score(X_test, y_test)
    print(f"   训练集准确率: {train_accuracy:.4f}")
    print(f"   测试集准确率: {test_accuracy:.4f}")

    # 9. 预测示例
    print("\n9. 预测示例...")
    sample = X_test[:5]
    predictions = best_knn.predict(sample)
    probabilities = best_knn.predict_proba(sample)

    class_names = ['Setosa', 'Versicolor', 'Virginica']
    for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
        print(f"   样本 {i+1}: 预测 = {class_names[pred]} "
              f"(概率: {dict(zip(class_names, [f'{p:.3f}' for p in proba]))})")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
