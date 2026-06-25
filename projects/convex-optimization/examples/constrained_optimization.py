"""
约束优化示例

演示拉格朗日对偶、KKT 条件、内点法的使用。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.constrained.lagrangian import Lagrangian, AugmentedLagrangian
from src.constrained.kkt import KKTChecker, verify_kkt_for_qp
from src.constrained.interior_point import BarrierMethod


def example_lagrangian():
    """拉格朗日函数示例"""
    print("=" * 60)
    print("1. 拉格朗日函数示例")
    print("=" * 60)

    # 问题: min x^2 + y^2
    # s.t. x + y = 1
    # 最优解: x = y = 0.5

    objective = lambda x: x[0] ** 2 + x[1] ** 2
    eq_constraint = lambda x: x[0] + x[1] - 1

    L = Lagrangian(objective, eq_constraints=[eq_constraint])

    x = np.array([0.5, 0.5])
    nu = np.array([-1.0])  # 最优乘子

    print(f"问题: min x^2 + y^2, s.t. x + y = 1")
    print(f"最优解: x = {x}")
    print(f"最优乘子: nu = {nu}")
    print(f"拉格朗日函数值: L(x, nu) = {L(x, nu_eq=nu):.4f}")


def example_kkt():
    """KKT 条件示例"""
    print("\n" + "=" * 60)
    print("2. KKT 条件检验示例")
    print("=" * 60)

    # 问题: min 0.5*x^2 + 0.5*y^2
    # s.t. x + y = 1
    # 最优解: x = y = 0.5, nu = -1

    grad_obj = lambda x: x
    eq_constraints = [lambda x: x[0] + x[1] - 1]
    grad_eq = [lambda x: np.array([1.0, 1.0])]

    checker = KKTChecker(
        grad_obj=grad_obj,
        grad_eq=grad_eq,
        eq_constraints=eq_constraints,
    )

    x = np.array([0.5, 0.5])
    nu = np.array([-1.0])

    result = checker.check(x, np.array([]), nu)

    print(f"最优解: x = {x}")
    print(f"最优乘子: nu = {nu}")
    print(f"KKT 条件检验:")
    print(f"  平稳性: {result.stationarity}")
    print(f"  原始可行性: {result.primal_feasibility}")
    print(f"  对偶可行性: {result.dual_feasibility}")
    print(f"  互补松弛性: {result.complementary_slackness}")
    print(f"  总违背: {result.violation:.2e}")
    print(f"  满足 KKT: {result.is_satisfied}")


def example_interior_point():
    """内点法示例"""
    print("\n" + "=" * 60)
    print("3. 内点法示例")
    print("=" * 60)

    # 问题: min x^2
    # s.t. x ≥ 1 (即 -x + 1 ≤ 0)
    # 最优解: x = 1

    objective = lambda x: x[0] ** 2
    grad_obj = lambda x: np.array([2 * x[0]])
    ineq_constraints = [lambda x: -x[0] + 1]
    grad_ineq = [lambda x: np.array([-1.0])]

    barrier = BarrierMethod(
        objective=objective,
        grad_obj=grad_obj,
        ineq_constraints=ineq_constraints,
        grad_ineq=grad_ineq,
        t0=1.0,
        mu=10.0,
        max_iter=20,
        verbose=True,
    )

    x0 = np.array([2.0])
    result = barrier.solve(x0)

    print(f"\n问题: min x^2, s.t. x ≥ 1")
    print(f"初始点: x0 = {x0}")
    print(f"最优解: x = {result.x}")
    print(f"最优值: f(x) = {result.fun:.4f}")
    print(f"迭代次数: {result.nit}")
    print(f"收敛: {result.success}")


def example_qp_kkt():
    """二次规划 KKT 条件示例"""
    print("\n" + "=" * 60)
    print("4. 二次规划 KKT 条件示例")
    print("=" * 60)

    # 问题: min 0.5*x^2 + 0.5*y^2
    # s.t. x + y = 1
    # 最优解: x = y = 0.5

    Q = np.array([[1, 0], [0, 1]])
    c = np.array([0, 0])
    A = np.array([[1, 1]])
    b = np.array([1])

    x = np.array([0.5, 0.5])
    nu = np.array([-0.5])

    result = verify_kkt_for_qp(Q, c, A, b, x=x, nu_eq=nu)

    print(f"问题: min 0.5*x^2 + 0.5*y^2, s.t. x + y = 1")
    print(f"最优解: x = {x}")
    print(f"最优乘子: nu = {nu}")
    print(f"KKT 条件检验:")
    print(f"  平稳性: {result.stationarity}")
    print(f"  原始可行性: {result.primal_feasibility}")
    print(f"  满足 KKT: {result.is_satisfied}")


def main():
    print("凸优化 - 约束优化示例")
    print("=" * 60)

    example_lagrangian()
    example_kkt()
    example_interior_point()
    example_qp_kkt()


if __name__ == "__main__":
    main()
