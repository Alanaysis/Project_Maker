"""
鸢尾花分类示例
=============

使用 SVM 对鸢尾花 (Iris) 数据集进行分类。
鸢尾花数据集包含 3 个类别，每个类别 50 个样本，共 150 个样本，
每个样本有 4 个特征 (花萼长度、花萼宽度、花瓣长度、花瓣宽度)。

本示例演示:
1. 数据加载和预处理
2. 使用 One-vs-Rest 和 One-vs-One 多分类策略
3. 不同核函数的对比
4. 模型评估 (准确率、精确率、召回率、F1、混淆矩阵)
"""

import sys
import os
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.svm import SVM
from src.multiclass import OneVsRestSVM, OneVsOneSVM
from src.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def load_iris_data():
    """
    加载鸢尾花数据集 (手动实现，不依赖 sklearn)

    数据来源: Fisher's Iris 数据集
    特征: 花萼长度、花萼宽度、花瓣长度、花瓣宽度
    类别: setosa (0), versicolor (1), virginica (2)
    """
    # 鸢尾花数据集 (部分样本，用于演示)
    # 格式: [花萼长度, 花萼宽度, 花瓣长度, 花瓣宽度]
    data = np.array([
        # Setosa (类别 0)
        [5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2], [4.7, 3.2, 1.3, 0.2],
        [4.6, 3.1, 1.5, 0.2], [5.0, 3.6, 1.4, 0.2], [5.4, 3.9, 1.7, 0.4],
        [4.6, 3.4, 1.4, 0.3], [5.0, 3.4, 1.5, 0.2], [4.4, 2.9, 1.4, 0.2],
        [4.9, 3.1, 1.5, 0.1], [5.4, 3.7, 1.5, 0.2], [4.8, 3.4, 1.6, 0.2],
        [4.8, 3.0, 1.4, 0.1], [4.3, 3.0, 1.1, 0.1], [5.8, 4.0, 1.2, 0.2],
        [5.7, 4.4, 1.5, 0.4], [5.4, 3.9, 1.3, 0.4], [5.1, 3.5, 1.4, 0.3],
        [5.7, 3.8, 1.7, 0.3], [5.1, 3.8, 1.5, 0.3],
        # Versicolor (类别 1)
        [7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5], [6.9, 3.1, 4.9, 1.5],
        [5.5, 2.3, 4.0, 1.3], [6.5, 2.8, 4.6, 1.5], [5.7, 2.8, 4.5, 1.3],
        [6.3, 3.3, 4.7, 1.6], [4.9, 2.4, 3.3, 1.0], [6.6, 2.9, 4.6, 1.3],
        [5.2, 2.7, 3.9, 1.4], [5.0, 2.0, 3.5, 1.0], [5.9, 3.0, 4.2, 1.5],
        [6.0, 2.2, 4.0, 1.0], [6.1, 2.9, 4.7, 1.4], [5.6, 2.9, 3.6, 1.3],
        [6.7, 3.1, 4.4, 1.4], [5.6, 3.0, 4.5, 1.5], [5.8, 2.7, 4.1, 1.0],
        [6.2, 2.2, 4.5, 1.5], [5.6, 2.5, 3.9, 1.1],
        # Virginica (类别 2)
        [6.3, 3.3, 6.0, 2.5], [5.8, 2.7, 5.1, 1.9], [7.1, 3.0, 5.9, 2.1],
        [6.3, 2.9, 5.6, 1.8], [6.5, 3.0, 5.8, 2.2], [7.6, 3.0, 6.6, 2.1],
        [4.9, 2.5, 4.5, 1.7], [7.3, 2.9, 6.3, 1.8], [6.7, 2.5, 5.8, 1.8],
        [7.2, 3.6, 6.1, 2.5], [6.5, 3.2, 5.1, 2.0], [6.4, 2.7, 5.3, 1.9],
        [6.8, 3.0, 5.5, 2.1], [5.7, 2.5, 5.0, 2.0], [5.8, 2.8, 5.1, 2.4],
        [6.4, 3.2, 5.3, 2.3], [6.5, 3.0, 5.5, 1.8], [7.7, 3.8, 6.7, 2.2],
        [7.7, 2.6, 6.9, 2.3], [6.0, 2.2, 5.0, 1.5],
    ])

    labels = np.array([0] * 20 + [1] * 20 + [2] * 20)

    return data, labels


def train_test_split(X, y, test_ratio=0.3, seed=42):
    """简单的训练测试集划分"""
    np.random.seed(seed)
    n = len(y)
    indices = np.random.permutation(n)
    test_size = int(n * test_ratio)

    test_idx = indices[:test_size]
    train_idx = indices[test_size:]

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def normalize(X_train, X_test):
    """特征标准化"""
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1  # 避免除以零
    return (X_train - mean) / std, (X_test - mean) / std


def main():
    print("=" * 60)
    print("鸢尾花分类示例 - SVM 多分类")
    print("=" * 60)

    # 1. 加载数据
    X, y = load_iris_data()
    print(f"\n数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"类别: {np.unique(y)} (0=setosa, 1=versicolor, 2=virginica)")

    # 2. 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_ratio=0.3)
    print(f"训练集: {X_train.shape[0]} 样本")
    print(f"测试集: {X_test.shape[0]} 样本")

    # 3. 特征标准化
    X_train, X_test = normalize(X_train, X_test)

    # 4. 不同核函数对比
    kernels = ["linear", "rbf", "polynomial"]
    results = {}

    print("\n" + "-" * 60)
    print("不同核函数对比 (One-vs-Rest)")
    print("-" * 60)

    for kernel in kernels:
        print(f"\n--- {kernel.upper()} 核 ---")

        ovr = OneVsRestSVM(kernel=kernel, C=1.0, gamma=1.0, max_passes=50)
        ovr.fit(X_train, y_train)

        y_pred = ovr.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='macro')
        rec = recall_score(y_test, y_pred, average='macro')
        f1 = f1_score(y_test, y_pred, average='macro')

        results[kernel] = {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1,
        }

        print(f"  准确率:   {acc:.4f}")
        print(f"  精确率:   {prec:.4f}")
        print(f"  召回率:   {rec:.4f}")
        print(f"  F1 分数:  {f1:.4f}")

    # 5. One-vs-Rest vs One-vs-One 对比
    print("\n" + "-" * 60)
    print("One-vs-Rest vs One-vs-One 对比 (RBF 核)")
    print("-" * 60)

    for strategy_name, StrategyClass in [
        ("One-vs-Rest", OneVsRestSVM),
        ("One-vs-One", OneVsOneSVM),
    ]:
        print(f"\n--- {strategy_name} ---")

        clf = StrategyClass(kernel="rbf", C=1.0, gamma=1.0, max_passes=50)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        print(f"  准确率: {acc:.4f}")
        print(f"  分类器数量: {len(clf.classifiers)}")

    # 6. 最佳模型的混淆矩阵
    print("\n" + "-" * 60)
    print("最佳模型混淆矩阵 (RBF 核, One-vs-Rest)")
    print("-" * 60)

    best_clf = OneVsRestSVM(kernel="rbf", C=1.0, gamma=1.0, max_passes=50)
    best_clf.fit(X_train, y_train)
    y_pred = best_clf.predict(X_test)

    cm = confusion_matrix(y_test, y_pred)
    class_names = ["setosa", "versicolor", "virginica"]

    print("\n混淆矩阵:")
    print(f"{'':>12}", end="")
    for name in class_names:
        print(f"{name:>12}", end="")
    print()

    for i, name in enumerate(class_names):
        print(f"{name:>12}", end="")
        for j in range(len(class_names)):
            print(f"{cm[i, j]:>12d}", end="")
        print()

    # 7. 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("\n各核函数性能对比:")
    print(f"{'核函数':<15} {'准确率':<10} {'精确率':<10} {'召回率':<10} {'F1':<10}")
    print("-" * 55)
    for kernel, metrics in results.items():
        print(
            f"{kernel:<15} "
            f"{metrics['accuracy']:<10.4f} "
            f"{metrics['precision']:<10.4f} "
            f"{metrics['recall']:<10.4f} "
            f"{metrics['f1']:<10.4f}"
        )


if __name__ == "__main__":
    main()
