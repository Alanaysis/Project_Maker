"""
手写数字识别示例
===============

使用 SVM 对手写数字数据集进行分类。
本示例使用简化版的手写数字数据 (8x8 像素)，包含 10 个类别 (0-9)。

本示例演示:
1. 手写数字数据的加载和预处理
2. 多分类 SVM 的训练
3. 模型评估和混淆矩阵分析
4. 错误样本分析
"""

import sys
import os
import numpy as np

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


def generate_digit_data(n_per_class=50, seed=42):
    """
    生成简化版手写数字数据

    每个数字用 8x8 的像素矩阵表示 (64 维特征)。
    通过为每个数字生成特征模板，添加随机噪声来模拟手写变体。

    参数:
        n_per_class: 每个类别的样本数
        seed: 随机种子

    返回:
        X: 特征矩阵 (n_samples, 64)
        y: 标签 (n_samples,)
    """
    np.random.seed(seed)

    # 每个数字的特征模板 (简化版)
    # 每个模板是一个 8x8 的矩阵，值越大表示像素越亮
    templates = {
        0: np.array([
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 0],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [0, 1, 0, 0, 0, 0, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
        ], dtype=float),
        1: np.array([
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
        2: np.array([
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
        ], dtype=float),
        3: np.array([
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
        4: np.array([
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 1, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
        ], dtype=float),
        5: np.array([
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
        6: np.array([
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 1, 1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
        7: np.array([
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
        ], dtype=float),
        8: np.array([
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
            [1, 0, 0, 0, 0, 0, 1, 0],
            [1, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
        9: np.array([
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
        ], dtype=float),
    }

    X_list = []
    y_list = []

    for digit, template in templates.items():
        # 展平模板
        flat_template = template.flatten()

        # 生成带噪声的样本
        for _ in range(n_per_class):
            noise = np.random.randn(64) * 0.3
            sample = flat_template + noise
            sample = np.clip(sample, 0, 1)  # 限制在 [0, 1]
            X_list.append(sample)
            y_list.append(digit)

    X = np.array(X_list)
    y = np.array(y_list)

    # 打乱顺序
    indices = np.random.permutation(len(y))
    return X[indices], y[indices]


def train_test_split(X, y, test_ratio=0.3, seed=42):
    """划分训练集和测试集"""
    np.random.seed(seed)
    n = len(y)
    indices = np.random.permutation(n)
    test_size = int(n * test_ratio)

    test_idx = indices[:test_size]
    train_idx = indices[test_size:]

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def main():
    print("=" * 60)
    print("手写数字识别示例 - SVM 多分类")
    print("=" * 60)

    # 1. 生成数据
    X, y = generate_digit_data(n_per_class=50, seed=42)
    print(f"\n数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"类别: {np.unique(y)} (0-9)")

    # 2. 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_ratio=0.3)
    print(f"训练集: {X_train.shape[0]} 样本")
    print(f"测试集: {X_test.shape[0]} 样本")

    # 3. 特征标准化
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1
    X_train = (X_train - mean) / std
    X_test = (X_test - mean) / std

    # 4. 训练模型
    print("\n" + "-" * 60)
    print("训练 One-vs-Rest SVM (RBF 核)")
    print("-" * 60)

    clf = OneVsRestSVM(kernel="rbf", C=10.0, gamma=0.1, max_passes=50)
    print("训练中...")
    clf.fit(X_train, y_train)
    print("训练完成!")

    # 5. 评估
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='macro')
    rec = recall_score(y_test, y_pred, average='macro')
    f1 = f1_score(y_test, y_pred, average='macro')

    print(f"\n评估结果:")
    print(f"  准确率:   {acc:.4f}")
    print(f"  精确率:   {prec:.4f}")
    print(f"  召回率:   {rec:.4f}")
    print(f"  F1 分数:  {f1:.4f}")

    # 6. 混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n混淆矩阵:")
    print(f"{'':>6}", end="")
    for d in range(10):
        print(f"{d:>6}", end="")
    print()

    for i in range(10):
        print(f"{i:>6}", end="")
        for j in range(10):
            print(f"{cm[i, j]:>6d}", end="")
        print()

    # 7. 每个数字的准确率
    print(f"\n每个数字的准确率:")
    print("-" * 30)
    for digit in range(10):
        mask = y_test == digit
        if np.sum(mask) > 0:
            digit_acc = accuracy_score(y_test[mask], y_pred[mask])
            print(f"  数字 {digit}: {digit_acc:.4f} ({np.sum(y_pred[mask] == digit)}/{np.sum(mask)})")

    # 8. 错误分析
    errors = np.where(y_pred != y_test)[0]
    print(f"\n错误分析:")
    print(f"  总错误数: {len(errors)}")
    if len(errors) > 0:
        print(f"  错误率: {len(errors)/len(y_test):.4f}")
        print(f"\n  前 5 个错误样本:")
        for idx in errors[:5]:
            print(f"    样本 {idx}: 真实={y_test[idx]}, 预测={y_pred[idx]}")


if __name__ == "__main__":
    main()
