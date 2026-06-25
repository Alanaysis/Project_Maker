"""
最小二乘示例

演示最小二乘、岭回归、Lasso 回归的使用。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications.least_squares import (
    LeastSquares,
    RidgeRegression,
    LassoRegression,
)


def example_least_squares():
    """普通最小二乘示例"""
    print("=" * 60)
    print("1. 普通最小二乘")
    print("=" * 60)

    # 创建超定系统
    np.random.seed(42)
    n, m = 20, 5
    A = np.random.randn(n, m)
    x_true = np.array([1, 2, 3, 4, 5])
    b = A @ x_true + 0.1 * np.random.randn(n)

    ls = LeastSquares(A, b)

    # 不同求解方法
    methods = {
        "解析解": ls.solve_analytical,
        "正规方程": ls.solve_normal_equations,
        "QR 分解": ls.solve_qr,
        "SVD 分解": ls.solve_svd,
        "梯度下降": lambda: ls.solve_gradient_descent(max_iter=10000, learning_rate=0.001),
    }

    print(f"真实参数: {x_true}")
    print()

    for name, method in methods.items():
        x = method()
        residual = np.linalg.norm(ls.residual(x))
        error = np.linalg.norm(x - x_true)
        print(f"{name}:")
        print(f"  解: {x}")
        print(f"  残差: {residual:.6e}")
        print(f"  误差: {error:.6e}")
        print()


def example_ridge_regression():
    """岭回归示例"""
    print("=" * 60)
    print("2. 岭回归 (L2 正则化)")
    print("=" * 60)

    # 创建病态问题
    np.random.seed(42)
    n, m = 20, 10
    A = np.random.randn(n, m)
    # 添加相关性
    A[:, 5:] = A[:, :5] + 0.01 * np.random.randn(n, 5)
    x_true = np.zeros(m)
    x_true[:5] = [1, 2, 3, 4, 5]
    b = A @ x_true + 0.1 * np.random.randn(n)

    print(f"真实参数: {x_true}")
    print()

    # 不同正则化参数
    lambdas = [0, 0.01, 0.1, 1.0]
    for lambda_ in lambdas:
        ridge = RidgeRegression(A, b, lambda_=lambda_)
        x = ridge.solve_analytical()
        error = np.linalg.norm(x - x_true)
        norm = np.linalg.norm(x)

        print(f"lambda = {lambda_}:")
        print(f"  解: {x}")
        print(f"  误差: {error:.6e}")
        print(f"  范数: {norm:.6e}")
        print()


def example_lasso():
    """Lasso 回归示例"""
    print("=" * 60)
    print("3. Lasso 回归 (L1 正则化)")
    print("=" * 60)

    # 创建稀疏信号
    np.random.seed(42)
    n, m = 50, 20
    A = np.random.randn(n, m)
    x_true = np.zeros(m)
    x_true[:3] = [1, 2, 3]
    b = A @ x_true + 0.1 * np.random.randn(n)

    print(f"真实参数: {x_true}")
    print(f"非零元素: {np.sum(x_true != 0)}")
    print()

    # 不同正则化参数
    lambdas = [0.01, 0.1, 1.0]
    for lambda_ in lambdas:
        lasso = LassoRegression(A, b, lambda_=lambda_)
        x = lasso.solve_coordinate_descent()
        error = np.linalg.norm(x - x_true)
        n_nonzero = np.sum(np.abs(x) > 1e-6)

        print(f"lambda = {lambda_}:")
        print(f"  解: {x}")
        print(f"  误差: {error:.6e}")
        print(f"  非零元素: {n_nonzero}")
        print()


def main():
    print("凸优化 - 最小二乘示例")
    print("=" * 60)

    example_least_squares()
    example_ridge_regression()
    example_lasso()


if __name__ == "__main__":
    main()
