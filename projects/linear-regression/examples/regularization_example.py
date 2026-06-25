#!/usr/bin/env python3
"""正则化示例

演示 L1 (Lasso)、L2 (Ridge)、Elastic Net 正则化的效果。
展示正则化如何防止过拟合和进行特征选择。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import RidgeRegression, LassoRegression, ElasticNet
from src.evaluation import mean_squared_error, r2_score
from src.utils import generate_linear_data, train_test_split, print_evaluation_report


def demo_ridge_regression():
    """演示岭回归 (L2 正则化)"""
    print("=" * 60)
    print("  Demo 1: Ridge Regression (L2 Regularization)")
    print("=" * 60)

    # 生成高维数据（特征数 > 样本数，容易过拟合）
    np.random.seed(42)
    n_samples = 50
    n_features = 20

    # 只有前 5 个特征是真正有用的
    true_weights = np.zeros(n_features)
    true_weights[:5] = np.array([3.0, -2.0, 1.5, 0.5, -1.0])

    X, y = generate_linear_data(
        n_samples=n_samples,
        n_features=n_features,
        noise=1.0,
        true_weights=true_weights,
        true_bias=2.0,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    print(f"\n  Data: {n_samples} samples, {n_features} features")
    print(f"  Only first 5 features are relevant")

    # 测试不同的 alpha 值
    alphas = [0.0, 0.01, 0.1, 1.0, 10.0]
    print(f"\n  {'Alpha':<10} {'Train R2':<12} {'Test R2':<12} {'Weight Norm':<12}")
    print(f"  {'-'*46}")

    for alpha in alphas:
        model = RidgeRegression(alpha=alpha, learning_rate=0.01, n_iterations=2000)
        model.fit(X_train, y_train)

        train_r2 = r2_score(y_train, model.predict(X_train))
        test_r2 = r2_score(y_test, model.predict(X_test))
        weight_norm = np.sqrt(np.sum(model.weights ** 2))

        print(f"  {alpha:<10.2f} {train_r2:<12.4f} {test_r2:<12.4f} {weight_norm:<12.4f}")

    print("\n  Observation: As alpha increases, weights shrink (smaller norm)")
    print("  Moderate alpha helps prevent overfitting")


def demo_lasso_regression():
    """演示 Lasso 回归 (L1 正则化) - 特征选择"""
    print("\n" + "=" * 60)
    print("  Demo 2: Lasso Regression (L1 Regularization)")
    print("=" * 60)

    # 生成高维稀疏数据
    np.random.seed(42)
    n_samples = 100
    n_features = 20

    # 只有前 3 个特征是真正有用的
    true_weights = np.zeros(n_features)
    true_weights[:3] = np.array([5.0, -3.0, 2.0])

    X, y = generate_linear_data(
        n_samples=n_samples,
        n_features=n_features,
        noise=0.5,
        true_weights=true_weights,
        true_bias=1.0,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    print(f"\n  Data: {n_samples} samples, {n_features} features")
    print(f"  Only first 3 features are relevant (sparse)")

    # 测试不同的 alpha 值
    alphas = [0.0, 0.01, 0.1, 1.0, 5.0]
    print(f"\n  {'Alpha':<10} {'Train R2':<12} {'Test R2':<12} {'Non-zero W':<12}")
    print(f"  {'-'*46}")

    for alpha in alphas:
        model = LassoRegression(alpha=alpha, learning_rate=0.01, n_iterations=3000)
        model.fit(X_train, y_train)

        train_r2 = r2_score(y_train, model.predict(X_train))
        test_r2 = r2_score(y_test, model.predict(X_test))
        n_nonzero = int(np.sum(np.abs(model.weights) > 1e-3))

        print(f"  {alpha:<10.2f} {train_r2:<12.4f} {test_r2:<12.4f} {n_nonzero:<12}")

    print("\n  Observation: Lasso drives irrelevant feature weights to exactly 0")
    print("  This performs automatic feature selection!")


def demo_elastic_net():
    """演示 Elastic Net（L1+L2 混合正则化）"""
    print("\n" + "=" * 60)
    print("  Demo 3: Elastic Net (L1 + L2 Regularization)")
    print("=" * 60)

    # 生成有相关特征的数据
    np.random.seed(42)
    n_samples = 100
    n_features = 10

    true_weights = np.array([3.0, -2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    X, y = generate_linear_data(
        n_samples=n_samples,
        n_features=n_features,
        noise=0.5,
        true_weights=true_weights,
        true_bias=2.0,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    print(f"\n  Data: {n_samples} samples, {n_features} features")
    print(f"  Only first 3 features are relevant")

    # 测试不同的 l1_ratio
    l1_ratios = [0.0, 0.25, 0.5, 0.75, 1.0]
    alpha = 0.5

    print(f"\n  Alpha = {alpha}")
    print(f"  {'l1_ratio':<10} {'Train R2':<12} {'Test R2':<12} {'Non-zero W':<12}")
    print(f"  {'-'*46}")

    for l1_ratio in l1_ratios:
        model = ElasticNet(
            alpha=alpha, l1_ratio=l1_ratio, learning_rate=0.01, n_iterations=3000
        )
        model.fit(X_train, y_train)

        train_r2 = r2_score(y_train, model.predict(X_train))
        test_r2 = r2_score(y_test, model.predict(X_test))
        n_nonzero = int(np.sum(np.abs(model.weights) > 1e-3))

        label = f"{l1_ratio:.2f}"
        if l1_ratio == 0.0:
            label += " (Ridge)"
        elif l1_ratio == 1.0:
            label += " (Lasso)"

        print(f"  {label:<10} {train_r2:<12.4f} {test_r2:<12.4f} {n_nonzero:<12}")

    print("\n  Observation: l1_ratio controls the L1/L2 balance")
    print("  l1_ratio=1 is pure Lasso, l1_ratio=0 is pure Ridge")


def main():
    print("\n" + "#" * 60)
    print("#  Regularization Examples")
    print("#" * 60)

    demo_ridge_regression()
    demo_lasso_regression()
    demo_elastic_net()

    print("\n" + "#" * 60)
    print("#  All regularization examples completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
