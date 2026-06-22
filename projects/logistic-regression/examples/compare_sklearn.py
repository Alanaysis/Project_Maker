"""
与scikit-learn逻辑回归对比

对比自定义实现与sklearn的性能差异
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import LogisticRegression, accuracy_score


def generate_dataset(n_samples=200, random_state=42):
    """生成数据集"""
    np.random.seed(random_state)

    X_pos = np.random.randn(n_samples // 2, 2) + np.array([2, 2])
    y_pos = np.ones(n_samples // 2)

    X_neg = np.random.randn(n_samples // 2, 2) + np.array([-2, -2])
    y_neg = np.zeros(n_samples // 2)

    X = np.vstack([X_pos, X_neg])
    y = np.hstack([y_pos, y_neg])

    indices = np.random.permutation(n_samples)
    return X[indices], y[indices]


def main():
    print("=" * 60)
    print("自定义逻辑回归 vs scikit-learn")
    print("=" * 60)

    # 生成数据
    X, y = generate_dataset(n_samples=300)

    # 划分数据集
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"\n训练集: {len(X_train)} 样本")
    print(f"测试集: {len(X_test)} 样本")

    # 1. 自定义实现
    print("\n" + "-" * 40)
    print("1. 自定义逻辑回归:")
    print("-" * 40)

    custom_model = LogisticRegression(
        learning_rate=0.1,
        n_iterations=1000,
        regularization=0.01
    )
    custom_model.fit(X_train, y_train)

    custom_pred = custom_model.predict(X_test)
    custom_acc = accuracy_score(y_test, custom_pred)

    print(f"   准确率: {custom_acc:.4f}")
    print(f"   权重: {custom_model.weights}")
    print(f"   偏置: {custom_model.bias:.4f}")

    # 2. scikit-learn实现
    try:
        from sklearn.linear_model import LogisticRegression as SklearnLR
        from sklearn.metrics import accuracy_score as sklearn_acc

        print("\n" + "-" * 40)
        print("2. scikit-learn逻辑回归:")
        print("-" * 40)

        sklearn_model = SklearnLR(
            C=1.0,  # 正则化强度的倒数
            max_iter=1000,
            random_state=42
        )
        sklearn_model.fit(X_train, y_train)

        sklearn_pred = sklearn_model.predict(X_test)
        sklearn_accuracy = sklearn_acc(y_test, sklearn_pred)

        print(f"   准确率: {sklearn_accuracy:.4f}")
        print(f"   权重: {sklearn_model.coef_[0]}")
        print(f"   偏置: {sklearn_model.intercept_[0]:.4f}")

        # 对比
        print("\n" + "-" * 40)
        print("3. 对比结果:")
        print("-" * 40)
        print(f"   自定义实现准确率: {custom_acc:.4f}")
        print(f"   sklearn准确率:    {sklearn_accuracy:.4f}")
        print(f"   差异:            {abs(custom_acc - sklearn_accuracy):.4f}")

    except ImportError:
        print("\n未安装scikit-learn，跳过对比")
        print("安装命令: pip install scikit-learn")

    print("\n" + "=" * 60)
    print("对比完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
