"""
基础优化示例

演示梯度下降、牛顿法、BFGS 的使用。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.functions.test_functions import QuadraticFunction
from src.optimizers.gradient_descent import GradientDescent
from src.optimizers.newton_method import NewtonMethod
from src.optimizers.bfgs import BFGS


def main():
    print("=" * 60)
    print("凸优化基础示例")
    print("=" * 60)

    # 创建二次函数 f(x) = x^T A x
    A = np.array([[2, 0], [0, 2]])
    f = QuadraticFunction(A)
    x0 = np.array([10.0, 10.0])

    print(f"\n目标函数: f(x) = x^T A x")
    print(f"A = \n{A}")
    print(f"初始点: x0 = {x0}")
    print(f"理论最优解: x* = [0, 0]")

    # 1. 梯度下降
    print("\n" + "-" * 40)
    print("1. 梯度下降")
    print("-" * 40)

    gd = GradientDescent(learning_rate=0.1, max_iter=1000, verbose=True)
    result_gd = gd.optimize(f, f.gradient, x0)

    print(f"最优解: {result_gd.x}")
    print(f"最优值: {result_gd.fun:.6e}")
    print(f"迭代次数: {result_gd.nit}")
    print(f"收敛: {result_gd.success}")

    # 2. 牛顿法
    print("\n" + "-" * 40)
    print("2. 牛顿法")
    print("-" * 40)

    newton = NewtonMethod(max_iter=10, verbose=True)
    result_newton = newton.optimize(f, f.gradient, x0, f.hessian)

    print(f"最优解: {result_newton.x}")
    print(f"最优值: {result_newton.fun:.6e}")
    print(f"迭代次数: {result_newton.nit}")
    print(f"收敛: {result_newton.success}")

    # 3. BFGS
    print("\n" + "-" * 40)
    print("3. BFGS")
    print("-" * 40)

    bfgs = BFGS(max_iter=100, verbose=True)
    result_bfgs = bfgs.optimize(f, f.gradient, x0)

    print(f"最优解: {result_bfgs.x}")
    print(f"最优值: {result_bfgs.fun:.6e}")
    print(f"迭代次数: {result_bfgs.nit}")
    print(f"收敛: {result_bfgs.success}")

    # 对比
    print("\n" + "=" * 60)
    print("算法对比")
    print("=" * 60)
    print(f"{'算法':<15} {'迭代次数':<10} {'最优值':<15} {'收敛'}")
    print("-" * 50)
    print(f"{'梯度下降':<15} {result_gd.nit:<10} {result_gd.fun:<15.6e} {result_gd.success}")
    print(f"{'牛顿法':<15} {result_newton.nit:<10} {result_newton.fun:<15.6e} {result_newton.success}")
    print(f"{'BFGS':<15} {result_bfgs.nit:<10} {result_bfgs.fun:<15.6e} {result_bfgs.success}")


if __name__ == "__main__":
    main()
