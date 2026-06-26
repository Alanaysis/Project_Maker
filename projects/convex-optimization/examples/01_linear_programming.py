"""
Example 1: Linear Programming (线性规划)

Solves a linear programming problem using interior point method.

问题:
    min c^T * x
    s.t.  Ax <= b
          x >= 0

This demonstrates how interior point methods solve LP problems.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convexity_checker import is_positive_semidefinite
from src.interior_point import barrier_method
from src.gradient_descent import gradient_descent


def example_linear_programming():
    """
    Solve a linear programming problem.

    Problem formulation:
        min  2*x1 + 3*x2 + x3
        s.t. x1 + x2 + x3 <= 6
             2*x1 + x2 + x3 <= 8
             x1, x2, x3 >= 0
    """
    print("=" * 60)
    print("Example 1: Linear Programming (线性规划)")
    print("=" * 60)

    # Problem data
    c = np.array([2.0, 3.0, 1.0])  # Objective coefficients
    A = np.array([
        [1.0, 1.0, 1.0],
        [2.0, 1.0, 1.0],
    ])
    b = np.array([6.0, 8.0])

    n = len(c)

    # Objective: f(x) = c^T * x
    def f0(x):
        return c @ x

    def grad_f0(x):
        return c.copy()

    def hess_f0(x):
        return np.zeros((n, n))

    # Inequality constraints: Ax <= b  =>  Ax - b <= 0
    # And x >= 0  =>  -x <= 0
    constraints = []

    for i in range(A.shape[0]):
        def make_ineq(a_row, b_val):
            return lambda x, _a=a_row, _b=b_val: _a @ x - _b
        constraints.append(make_ineq(A[i], b[i]))

    for i in range(n):
        def make_nonneg(idx):
            return lambda x, _idx=idx: -x[_idx]
        constraints.append(make_nonneg(i))

    # Strictly feasible starting point
    x0 = np.ones(n) * 0.1  # x = (0.1, 0.1, 0.1)

    print("\nProblem:")
    print(f"  min {c}^T * x")
    print(f"  s.t. Ax <= b")
    print(f"       x >= 0")
    print(f"\nA =\n{A}")
    print(f"b = {b}")

    # Solve using gradient descent (since LP has linear objective,
    # we use it as a demonstration)
    print("\n--- Solving with gradient descent (simple LP) ---")

    def f_aug(x):
        val = f0(x)
        for c_fn in constraints:
            ci = c_fn(x)
            # Log barrier for inequality constraints
            if ci >= 0:
                val += 1e6  # Penalty for infeasibility
            else:
                val -= 0.1 * np.log(-ci)
        return val

    result = gradient_descent(
        f_aug, x0,
        max_iter=2000,
        tol=1e-8,
        step_size=0.001,
        line_search=True,
        verbose=True,
    )

    print(f"\nOptimal solution: x* = {result.x_opt}")
    print(f"Optimal value: f(x*) = {result.f_opt:.6f}")

    # Verify constraints
    print(f"\nConstraint verification:")
    for i, c_fn in enumerate(constraints):
        val = c_fn(result.x_opt)
        print(f"  c_{i}(x*) = {val:.6e} (should be <= 0)")

    # Compare with scipy
    try:
        from scipy.optimize import linprog
        res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, None)] * n, method='highs')
        print(f"\nScipy linprog solution: x = {res.x}")
        print(f"Scipy optimal value: {res.fun:.6f}")
    except ImportError:
        print("\nScipy not available for comparison.")

    return result


if __name__ == "__main__":
    example_linear_programming()
