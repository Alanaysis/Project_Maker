"""
逻辑回归基本使用示例

本示例展示如何使用自定义逻辑回归进行二分类任务
"""

import sys
import os
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import LogisticRegression, classification_report


def generate_dataset(n_samples=200, random_state=42):
    """
    生成二分类数据集

    创建两个高斯分布的簇，用于二分类任务
    """
    np.random.seed(random_state)

    # 正类：均值为(2, 2)
    X_pos = np.random.randn(n_samples // 2, 2) + np.array([2, 2])
    y_pos = np.ones(n_samples // 2)

    # 负类：均值为(-2, -2)
    X_neg = np.random.randn(n_samples // 2, 2) + np.array([-2, -2])
    y_neg = np.zeros(n_samples // 2)

    X = np.vstack([X_pos, X_neg])
    y = np.hstack([y_pos, y_neg])

    # 打乱数据
    indices = np.random.permutation(n_samples)
    return X[indices], y[indices]


def train_test_split(X, y, test_ratio=0.2):
    """手动实现训练测试集划分"""
    n = len(X)
    n_test = int(n * test_ratio)

    X_test = X[:n_test]
    y_test = y[:n_test]
    X_train = X[n_test:]
    y_train = y[n_test:]

    return X_train, X_test, y_train, y_test


def main():
    print("=" * 60)
    print("逻辑回归二分类示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n1. 生成数据集...")
    X, y = generate_dataset(n_samples=200)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   正类数量: {int(np.sum(y))}")
    print(f"   负类数量: {int(np.sum(1 - y))}")

    # 2. 划分数据集
    print("\n2. 划分训练/测试集...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_ratio=0.2)
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 3. 创建并训练模型
    print("\n3. 训练逻辑回归模型...")
    model = LogisticRegression(
        learning_rate=0.1,
        n_iterations=500,
        regularization=0.01,
        verbose=True
    )
    model.fit(X_train, y_train)

    # 4. 查看训练结果
    print("\n4. 训练结果:")
    print(f"   最终损失: {model.losses[-1]:.6f}")
    print(f"   权重: {model.weights}")
    print(f"   偏置: {model.bias:.4f}")

    # 5. 模型评估
    print("\n5. 模型评估:")
    y_pred = model.predict(X_test)

    print(classification_report(y_test, y_pred))

    # 6. 预测新样本
    print("6. 预测新样本:")
    new_samples = np.array([
        [3, 3],    # 应该预测为正类
        [-3, -3],  # 应该预测为负类
        [0, 0],    # 边界附近
    ])

    predictions = model.predict(new_samples)
    probabilities = model.predict_proba(new_samples)

    for i, (sample, pred, prob) in enumerate(zip(new_samples, predictions, probabilities)):
        label = "正类" if pred == 1 else "负类"
        print(f"   样本 {sample} -> 预测: {label}, 概率: {prob:.4f}")

    # 7. 绘制损失曲线（如果有matplotlib）
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 4))

        # 损失曲线
        plt.subplot(1, 2, 1)
        plt.plot(model.losses)
        plt.xlabel('迭代次数')
        plt.ylabel('损失值')
        plt.title('训练损失曲线')
        plt.grid(True)

        # 决策边界
        plt.subplot(1, 2, 2)

        # 绘制数据点
        plt.scatter(X[y == 0][:, 0], X[y == 0][:, 1], c='red', label='负类', alpha=0.5)
        plt.scatter(X[y == 1][:, 0], X[y == 1][:, 1], c='blue', label='正类', alpha=0.5)

        # 绘制决策边界
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100),
                            np.linspace(y_min, y_max, 100))
        Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        plt.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')

        plt.xlabel('特征1')
        plt.ylabel('特征2')
        plt.title('决策边界')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.savefig('logistic_regression_result.png', dpi=150)
        print("\n7. 可视化结果已保存到 'logistic_regression_result.png'")

    except ImportError:
        print("\n7. 未安装matplotlib，跳过可视化")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
