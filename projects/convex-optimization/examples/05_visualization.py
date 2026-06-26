"""
Example 5: Visualization of Optimization Process (优化过程可视化)

Visualizes the optimization trajectory for understanding
how different algorithms converge.

This example demonstrates:
- Gradient descent trajectory
- Newton's method trajectory
- Convergence comparison
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gradient_descent import gradient_descent
from src.newton_method import newton_method


def Rosenbrock_function(x):
    """
    Rosenbrock function: a classic optimization test problem.

    f(x, y) = (a - x)^2 + b * (y - x^2)^2

    With a=1, b=100:
    f(x, y) = (1 - x)^2 + 100 * (y - x^2)^2

    Minimum: f(1, 1) = 0

    The function has a narrow, curved valley making it challenging
    for gradient-based methods.
    """
    a, b = 1.0, 100.0
    return (a - x[0]) ** 2 + b * (x[1] - x[0] ** 2) ** 2


def Rosenbrock_gradient(x):
    """Gradient of Rosenbrock function."""
    a, b = 1.0, 100.0
    dx = -2 * (a - x[0]) - 400 * b * x[0] * (x[1] - x[0] ** 2)
    dy = 200 * b * (x[1] - x[0] ** 2)
    return np.array([dx, dy])


def Rosenbrock_hessian(x):
    """Hessian of Rosenbrock function."""
    a, b = 1.0, 100.0
    hxx = 2 - 400 * b * x[1] + 1200 * b * x[0] ** 2
    hxy = -400 * b * x[0]
    hyy = 200 * b
    return np.array([[hxx, hxy], [hxy, hyy]])


def quadratic_function(x):
    """Simple quadratic function for easy visualization."""
    return x[0] ** 2 + 2 * x[1] ** 2


def quadratic_gradient(x):
    return np.array([2 * x[0], 4 * x[1]])


def quadratic_hessian(x):
    return np.array([[2.0, 0.0], [0.0, 4.0]])


def ellipse_function(x):
    """Elliptic bowl for visualization."""
    return x[0] ** 2 / 4 + x[1] ** 2 + 1


def ellipse_gradient(x):
    return np.array([x[0] / 2, 2 * x[1]])


def ellipse_hessian(x):
    return np.array([[0.5, 0.0], [0.0, 2.0]])


def visualize_optimization(func, grad_func, hess_func, x0, method='gradient'):
    """
    Visualize the optimization process by computing the trajectory.

    Parameters
    ----------
    func : callable
        Objective function.
    grad_func : callable
        Gradient function.
    hess_func : callable
        Hessian function.
    x0 : array-like
        Initial point.
    method : str
        Optimization method ('gradient' or 'newton').

    Returns
    -------
    result : dict
        Contains trajectory and convergence data.
    """
    x0 = np.asarray(x0, dtype=float)

    if method == 'gradient':
        result = gradient_descent(
            func, x0,
            grad=grad_func,
            max_iter=200,
            tol=1e-10,
            step_size=0.001,
            line_search=True,
            verbose=False,
        )
    else:
        result = newton_method(
            func, x0,
            grad=grad_func,
            hess=hess_func,
            max_iter=50,
            tol=1e-10,
            line_search=True,
            verbose=False,
        )

    return {
        'x_opt': result.x_opt,
        'f_opt': result.f_opt,
        'n_iter': result.n_iter,
        'converged': result.converged,
        'history': result.history,
        'method': method,
    }


def compare_methods(func, grad_func, hess_func, x0, methods=['gradient', 'newton']):
    """
    Compare different optimization methods on the same problem.

    Parameters
    ----------
    func : callable
        Objective function.
    grad_func : callable
        Gradient function.
    hess_func : callable
        Hessian function.
    x0 : array-like
        Initial point.
    methods : list of str
        Methods to compare.

    Returns
    -------
    results : dict
        Dictionary of results for each method.
    """
    results = {}
    for method in methods:
        print(f"\n--- {method.title()} Method ---")
        result = visualize_optimization(func, grad_func, hess_func, x0, method)
        results[method] = result
        print(f"  Optimal point: {result['x_opt']}")
        print(f"  Optimal value: {result['f_opt']:.10e}")
        print(f"  Iterations: {result['n_iter']}")
        print(f"  Converged: {result['converged']}")

    return results


def main():
    print("=" * 60)
    print("Example 5: Visualization of Optimization Process")
    print("优化过程可视化")
    print("=" * 60)

    # Test on quadratic function
    print("\n" + "=" * 60)
    print("Test 1: Quadratic Function (二次函数)")
    print("f(x,y) = x^2 + 2y^2")
    print("=" * 60)

    x0_quad = np.array([3.0, 4.0])
    quad_results = compare_methods(
        quadratic_function, quadratic_gradient, quadratic_hessian,
        x0_quad, methods=['gradient', 'newton']
    )

    # Test on Rosenbrock function
    print("\n" + "=" * 60)
    print("Test 2: Rosenbrock Function (Rosenbrock 函数)")
    print("f(x,y) = (1-x)^2 + 100*(y-x^2)^2")
    print("Minimum at (1, 1)")
    print("=" * 60)

    x0_rosen = np.array([-1.5, 1.0])
    rosen_results = compare_methods(
        Rosenbrock_function, Rosenbrock_gradient, Rosenbrock_hessian,
        x0_rosen, methods=['gradient', 'newton']
    )

    # Convergence comparison
    print("\n" + "=" * 60)
    print("Convergence Comparison (收敛比较)")
    print("=" * 60)

    for method in ['gradient', 'newton']:
        history = rosen_results[method]['history']
        f_history = history['f']
        grad_history = history['grad_norm']

        print(f"\n{method.title()} Method:")
        print(f"  Final f value: {f_history[-1]:.10e}")
        print(f"  Final gradient norm: {grad_history[-1]:.2e}")
        print(f"  Iterations: {len(f_history)}")

        # Show convergence history
        print(f"  First 5 iterations:")
        for i in range(min(5, len(f_history))):
            print(f"    Iter {i}: f = {f_history[i]:.6e}, ||grad|| = {grad_history[i]:.2e}")

        print(f"  Last 5 iterations:")
        for i in range(max(0, len(f_history) - 5), len(f_history)):
            print(f"    Iter {i}: f = {f_history[i]:.6e}, ||grad|| = {grad_history[i]:.2e}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary (总结)")
    print("=" * 60)
    print("\nKey Observations / 关键观察:")
    print("  1. Newton's method converges faster (fewer iterations)")
    print("     牛顿法收敛更快（迭代次数更少）")
    print("  2. Gradient descent is simpler but may need more iterations")
    print("     梯度下降更简单但可能需要更多迭代")
    print("  3. For ill-conditioned problems (like Rosenbrock), Newton's")
    print("     method handles curvature better")
    print("     对于病态问题（如 Rosenbrock），牛顿法更好地处理曲率")
    print("  4. Newton's method requires Hessian computation (O(n^3))")
    print("     牛顿法需要计算 Hessian（O(n^3) 复杂度）")

    return rosen_results


if __name__ == "__main__":
    main()
