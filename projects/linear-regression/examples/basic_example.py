#!/usr/bin/env python3
"""线性回归基础示例

演示如何使用线性回归模型进行训练和预测。
涵盖简单线性回归、多元线性回归和正规方程法。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression
from src.evaluation import mean_squared_error, root_mean_squared_error
from src.evaluation import mean_absolute_error, r2_score
from src.utils import generate_linear_data, train_test_split, print_evaluation_report


def demo_simple_linear_regression():
    """演示简单线性回归（单特征）"""
    print("=" * 60)
    print("  Demo 1: Simple Linear Regression (Single Feature)")
    print("=" * 60)

    # 生成数据: y = 3x + 4 + noise
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=1,
        noise=0.5,
        true_weights=np.array([3.0]),
        true_bias=4.0,
        random_state=42,
    )
    print(f"\n  Data: y = 3x + 4 + noise")
    print(f"  Samples: {X.shape[0]}, Features: {X.shape[1]}")

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")

    # 训练模型（梯度下降法）
    model = LinearRegression(learning_rate=0.1, n_iterations=500, verbose=False)
    model.fit(X_train, y_train)

    # 评估
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    print_evaluation_report(y_train, y_train_pred, "Train")
    print_evaluation_report(y_test, y_test_pred, "Test")

    # 查看参数
    print(f"  Learned weight: {model.weights[0]:.4f} (true: 3.0)")
    print(f"  Learned bias:   {model.bias:.4f} (true: 4.0)")


def demo_multiple_linear_regression():
    """演示多元线性回归（多特征）"""
    print("\n" + "=" * 60)
    print("  Demo 2: Multiple Linear Regression (Multiple Features)")
    print("=" * 60)

    # 生成数据: y = 2*x1 + 3*x2 - 1*x3 + 5 + noise
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=200,
        n_features=3,
        noise=1.0,
        true_weights=np.array([2.0, 3.0, -1.0]),
        true_bias=5.0,
        random_state=42,
    )
    print(f"\n  Data: y = 2*x1 + 3*x2 - 1*x3 + 5 + noise")
    print(f"  Samples: {X.shape[0]}, Features: {X.shape[1]}")

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 训练模型
    model = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model.fit(X_train, y_train)

    # 评估
    y_test_pred = model.predict(X_test)
    print_evaluation_report(y_test, y_test_pred, "Test")

    # 查看参数
    print(f"  Learned weights: {model.weights}")
    print(f"  True weights:    [2.0, 3.0, -1.0]")
    print(f"  Learned bias:    {model.bias:.4f} (true: 5.0)")


def demo_normal_equation():
    """演示正规方程法"""
    print("\n" + "=" * 60)
    print("  Demo 3: Normal Equation Method")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=2,
        noise=0.5,
        true_weights=np.array([1.5, -2.0]),
        true_bias=3.0,
        random_state=42,
    )
    print(f"\n  Data: y = 1.5*x1 - 2.0*x2 + 3 + noise")

    # 正规方程法
    model_ne = LinearRegression(method="normal_equation")
    model_ne.fit(X, y)

    # 梯度下降法
    model_gd = LinearRegression(learning_rate=0.01, n_iterations=1000, method="gradient_descent")
    model_gd.fit(X, y)

    print(f"\n  Normal Equation:")
    print(f"    Weights: {model_ne.weights}")
    print(f"    Bias:    {model_ne.bias:.4f}")

    print(f"\n  Gradient Descent (1000 iterations):")
    print(f"    Weights: {model_gd.weights}")
    print(f"    Bias:    {model_gd.bias:.4f}")

    print(f"\n  True: weights=[1.5, -2.0], bias=3.0")


def main():
    """主函数"""
    print("\n" + "#" * 60)
    print("#  Linear Regression - Basic Examples")
    print("#" * 60)

    demo_simple_linear_regression()
    demo_multiple_linear_regression()
    demo_normal_equation()

    print("\n" + "#" * 60)
    print("#  All basic examples completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
