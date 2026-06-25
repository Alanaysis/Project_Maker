"""
手写数字识别示例

使用 KNN 分类器对手写数字数据集进行识别。
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KNNClassifier, CrossValidator, train_test_split, accuracy_score


def generate_digit_data(n_samples_per_class=50):
    """
    生成模拟的手写数字数据集

    每个数字用 8x8 的像素矩阵表示（64 维特征）。

    Args:
        n_samples_per_class: 每个数字的样本数

    Returns:
        X: 特征矩阵 (n_samples, 64)
        y: 标签 (n_samples,)
    """
    np.random.seed(42)

    # 定义每个数字的基础模式（8x8 矩阵的简化表示）
    # 这里用随机生成来模拟不同数字的特征
    digit_patterns = {
        0: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     1, 0, 0, 0, 0, 0, 0, 1,
                     1, 0, 0, 0, 0, 0, 0, 1,
                     1, 0, 0, 0, 0, 0, 0, 1,
                     1, 0, 0, 0, 0, 0, 0, 1,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        1: np.array([0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 1, 1, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        2: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 1, 0, 0,
                     0, 0, 0, 0, 1, 0, 0, 0,
                     0, 0, 0, 1, 0, 0, 0, 0,
                     0, 0, 1, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 0], dtype=float),
        3: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 1, 1, 1, 0, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        4: np.array([0, 0, 0, 0, 1, 0, 0, 0,
                     0, 0, 0, 1, 1, 0, 0, 0,
                     0, 0, 1, 0, 1, 0, 0, 0,
                     0, 1, 0, 0, 1, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 1, 0, 0, 0,
                     0, 0, 0, 0, 1, 0, 0, 0,
                     0, 0, 0, 0, 1, 0, 0, 0], dtype=float),
        5: np.array([0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 0, 0, 0, 0, 0, 0,
                     0, 1, 0, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 0, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        6: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        7: np.array([0, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 1, 0, 0,
                     0, 0, 0, 0, 1, 0, 0, 0,
                     0, 0, 0, 1, 0, 0, 0, 0,
                     0, 0, 0, 1, 0, 0, 0, 0,
                     0, 0, 0, 1, 0, 0, 0, 0,
                     0, 0, 0, 1, 0, 0, 0, 0], dtype=float),
        8: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float),
        9: np.array([0, 0, 1, 1, 1, 1, 0, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 0, 0, 0, 0, 0, 1, 0,
                     0, 1, 0, 0, 0, 0, 1, 0,
                     0, 0, 1, 1, 1, 1, 0, 0], dtype=float)
    }

    X_list = []
    y_list = []

    for digit, pattern in digit_patterns.items():
        # 为每个数字生成多个变体
        for _ in range(n_samples_per_class):
            # 添加随机噪声模拟手写变异
            noise = np.random.randn(64) * 0.15
            sample = np.clip(pattern + noise, 0, 1)
            X_list.append(sample)
            y_list.append(digit)

    X = np.array(X_list)
    y = np.array(y_list)

    # 打乱数据
    indices = np.random.permutation(len(y))
    return X[indices], y[indices]


def visualize_digit(sample, title="Digit"):
    """
    简单的数字可视化（文本模式）

    Args:
        sample: 64 维特征向量
        title: 标题
    """
    print(f"\n{title}:")
    print("+" + "-" * 16 + "+")
    for i in range(8):
        row = "|"
        for j in range(8):
            val = sample[i * 8 + j]
            if val > 0.5:
                row += "##"
            elif val > 0.2:
                row += ".."
            else:
                row += "  "
        row += "|"
        print(row)
    print("+" + "-" * 16 + "+")


def main():
    """运行手写数字识别示例"""
    print("=" * 60)
    print("手写数字识别示例 - KNN 分类器")
    print("=" * 60)

    # 1. 加载数据
    print("\n1. 加载数据...")
    X, y = generate_digit_data(n_samples_per_class=50)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   类别数量: {len(np.unique(y))} (数字 0-9)")

    # 2. 可视化几个样本
    print("\n2. 可视化样本...")
    for digit in [0, 1, 2]:
        idx = np.where(y == digit)[0][0]
        visualize_digit(X[idx], f"数字 {digit}")

    # 3. 划分数据集
    print("\n3. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 4. 测试不同 K 值
    print("\n4. 测试不同 K 值...")
    k_values = [1, 3, 5, 7, 9, 11]
    best_accuracy = 0
    best_k = 1

    for k in k_values:
        knn = KNNClassifier(k=k, metric='euclidean', weights='uniform')
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        print(f"   K={k:2d}: 准确率 = {accuracy:.4f}")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_k = k

    # 5. 测试不同距离度量
    print("\n5. 测试不同距离度量...")
    metrics = ['euclidean', 'manhattan', 'cosine']

    for metric in metrics:
        knn = KNNClassifier(k=best_k, metric=metric, weights='uniform')
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        print(f"   {metric:10s}: 准确率 = {accuracy:.4f}")

    # 6. 测试距离加权
    print("\n6. 测试距离加权...")
    for weights in ['uniform', 'distance']:
        knn = KNNClassifier(k=best_k, metric='euclidean', weights=weights)
        knn.fit(X_train, y_train)
        accuracy = knn.score(X_test, y_test)
        print(f"   {weights:10s}: 准确率 = {accuracy:.4f}")

    # 7. 交叉验证
    print("\n7. 交叉验证...")
    cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)
    cv_results = cv.select_k(
        X, y,
        k_range=[1, 3, 5, 7, 9, 11],
        metric='euclidean',
        task='classification'
    )
    print(f"   最优 K: {cv_results['best_k']}")
    print(f"   最优准确率: {cv_results['best_score']:.4f}")

    # 8. 训练最终模型
    print("\n8. 训练最终模型...")
    final_model = KNNClassifier(
        k=cv_results['best_k'],
        metric='euclidean',
        weights='distance'
    )
    final_model.fit(X_train, y_train)

    # 9. 评估最终模型
    print("\n9. 最终模型评估...")
    train_accuracy = final_model.score(X_train, y_train)
    test_accuracy = final_model.score(X_test, y_test)
    print(f"   训练集准确率: {train_accuracy:.4f}")
    print(f"   测试集准确率: {test_accuracy:.4f}")

    # 10. 预测示例
    print("\n10. 预测示例...")
    predictions = final_model.predict(X_test[:5])
    true_labels = y_test[:5]

    for i, (pred, true) in enumerate(zip(predictions, true_labels)):
        status = "正确" if pred == true else "错误"
        print(f"    样本 {i+1}: 预测 = {pred}, 真实 = {true} [{status}]")

    # 11. 混淆矩阵（简化版）
    print("\n11. 各数字识别准确率...")
    all_predictions = final_model.predict(X_test)
    for digit in range(10):
        mask = y_test == digit
        if np.sum(mask) > 0:
            digit_accuracy = np.mean(all_predictions[mask] == digit)
            print(f"    数字 {digit}: {digit_accuracy:.4f} "
                  f"({np.sum(all_predictions[mask] == digit)}/{np.sum(mask)})")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
