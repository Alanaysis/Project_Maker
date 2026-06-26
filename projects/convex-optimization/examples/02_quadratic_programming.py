"""
Example 2: Quadratic Programming (二次规划)

Solves a quadratic programming problem.

问题:
    min (1/2) * x^T * P * x + q^T * x
    s.t.  Ax <= b
          x >= 0

QP is a fundamental class of convex optimization problems.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convexity_checker import is_positive_semidefinite, quadratic_form
from src.gradient_descent import gradient_descent
from src.newton_method import newton_method


def example_quadratic_programming():
    """
    Solve a quadratic programming problem.

    Problem:
        min (1/2) * x^T * P * x + q^T * x
        s.t.  x1 + x2 <= 3
              x1 + x3 <= 4
              x1, x2, x3 >= 0

    The optimal solution can be found analytically using KKT conditions.
    """
    print("=" * 60)
    print("Example 2: Quadratic Programming (二次规划)")
    print("=" * 60)

    # Problem data
    P = np.array([
        [4.0, 1.0, 0.0],
        [1.0, 2.0, 1.0],
        [0.0, 1.0, 3.0],
    ])
    q = np.array([-1.0, -2.0, -3.0])
    n = len(q)

    # Verify P is positive definite
    is_psd = is_positive_semidefinite(P)
    print(f"\nP is positive definite: {is_psd}")

    # Objective: f(x) = (1/2) * x^T * P * x + q^T * x
    def f0(x):
        return 0.5 * x @ P @ x + q @ x

    def grad_f0(x):
        return P @ x + q

    def hess_f0(x):
        return P

    # Constraints
    A_ub = np.array([
        [1.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
    ])
    b_ub = np.array([3.0, 4.0])

    constraints = []
    for i in range(A_ub.shape[0]):
        def make_ineq(a_row, b_val):
            return lambda x, _a=a_row, _b=b_val: _a @ x - _b
        constraints.append(make_ineq(A_ub[i], b_ub[i]))

    for i in range(n):
        def make_nonneg(idx):
            return lambda x, _idx=idx: -x[_idx]
        constraints.append(make_nonneg(i))

    # Initial point
    x0 = np.ones(n) * 0.5

    print("\nProblem:")
    print(f"  min (1/2) * x^T * P * x + q^T * x")
    print(f"  s.t.  Ax <= b")
    print(f"       x >= 0")
    print(f"\nP =\n{P}")
    print(f"q = {q}")
    print(f"A_ub =\n{A_ub}")
    print(f"b_ub = {b_ub}")

    # Method 1: Gradient descent with barrier
    print("\n--- Method 1: Gradient Descent with Barrier ---")

    mu = 0.1
    def f_barrier(x):
        val = f0(x)
        for c_fn in constraints:
            ci = c_fn(x)
            if ci >= 0:
                val += 1e6
            else:
                val -= mu * np.log(-ci)
        return val

    def grad_barrier(x):
        val = grad_f0(x).copy()
        for c_fn in constraints:
            ci = c_fn(x)
            if ci < 0:
                ci_grad = np.zeros(n)
                h = 1e-5
                for j in range(n):
                    x_jp = x.copy()
                    x_jp[j] += h
                    x_jm = x.copy()
                    x_jm[j] -= h
                    ci_grad[j] = (c_fn(x_jp) - c_fn(x_jm)) / (2 * h)
                val -= mu * ci_grad / ci
        return val

    result1 = gradient_descent(
        f_barrier, x0,
        grad=grad_barrier,
        max_iter=3000,
        tol=1e-8,
        step_size=0.001,
        line_search=True,
        verbose=True,
    )

    print(f"\nGradient Descent solution: x* = {result1.x_opt}")
    print(f"Optimal value: f(x*) = {result1.f_opt:.6f}")

    # Method 2: Newton's method (for unconstrained version)
    print("\n--- Method 2: Newton's Method (unconstrained) ---")

    # Unconstrained minimum: P*x + q = 0 => x = -P^{-1}*q
    x_unconstrained = -np.linalg.solve(P, q)
    f_unconstrained = f0(x_unconstrained)
    print(f"Unconstrained minimum: x = {x_unconstrained}")
    print(f"Unconstrained optimal value: f = {f_unconstrained:.6f}")

    # Check if unconstrained solution is feasible
    is_feasible = True
    for c_fn in constraints:
        if c_fn(x_unconstrained) > 1e-6:
            is_feasible = False
            break
    print(f"Unconstrained solution is feasible: {is_feasible}")

    # Method 3: Using scipy for verification
    try:
        from scipy.optimize import minimize
        print("\n--- Method 3: Scipy SLSQP ---")

        def f0_simple(x):
            return 0.5 * x @ P @ x + q @ x

        def grad_f0_simple(x):
            return P @ x + q

        cons = []
        for i in range(A_ub.shape[0]):
            cons.append({
                'type': 'ineq',
                'fun': lambda x, _i=i: b_ub[_i] - A_ub[_i] @ x
            })
        for i in range(n):
            cons.append({
                'type': 'ineq',
                'fun': lambda x, _i=i: x[_i]
            })

        scip_result = minimize(
            f0_simple, x0,
            method='SLSQP',
            jac=grad_f0_simple,
            constraints=cons,
            options={'ftol': 1e-12, 'maxiter': 100}
        )

        print(f"Scipy solution: x = {scip_result.x}")
        print(f"Scipy optimal value: {scip_result.fun:.6f}")
        print(f"Scipy success: {scip_result.success}")

    except ImportError:
        print("\nScipy not available for comparison.")

    # Compare results
    print("\n--- Results Comparison ---")
    print(f"Our GD solution: f = {result1.f_opt:.6f}")
    print(f"Scipy solution:   f = {scip_result.fun:.6f}" if 'scip_result' in dir() else "Scipy not available")

    return result1


if __name__ == "__main__":
    example_quadratic_programming()
