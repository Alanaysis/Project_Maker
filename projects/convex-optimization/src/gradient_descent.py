"""
Gradient Descent Optimizer (梯度下降优化器)

This module implements gradient descent and its variants for unconstrained
and constrained convex optimization.

梯度下降优化器实现无约束和有约束凸优化的梯度下降及其变体。

Key Concepts / 关键概念:
- Gradient descent: x_{k+1} = x_k - alpha_k * grad(f)(x_k)
  梯度下降: x_{k+1} = x_k - alpha_k * grad(f)(x_k)

- The negative gradient direction is the steepest descent direction.
  负梯度方向是最速下降方向。

- Step size selection is critical:
  步长选择至关重要:
  - Fixed step size: simple but may not converge
  - Line search: adaptive, more robust
  - Armijo condition: sufficient decrease guarantee

- Convergence rate for strongly convex functions: O(1/k) for gradient descent
  强凸函数的收敛速度: O(1/k)

- For L-smooth functions, step size alpha <= 1/L guarantees convergence.
  对于 L-光滑函数，步长 alpha <= 1/L 保证收敛。
"""

import numpy as np
from scipy.optimize import line_search


class GradientDescentResult:
    """
    Container for gradient descent optimization results.
    梯度下降优化结果的容器。
    """
    def __init__(self):
        self.x_opt = None
        self.f_opt = None
        self.n_iter = 0
        self.converged = False
        self.history = {
            'x': [],
            'f': [],
            'grad_norm': [],
            'step_size': [],
        }


def numerical_gradient(f, x, h=1e-7):
    """
    Compute the gradient numerically using central differences.
    使用中心差分法数值计算梯度。

    Parameters
    ----------
    f : callable
        Scalar-valued function f: R^n -> R.
    x : array-like
        Point at which to compute the gradient.
    h : float
        Step size for finite differences.

    Returns
    -------
    grad : ndarray
        Numerical gradient vector.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    grad = np.zeros(n)
    f_x = f(x)
    for i in range(n):
        x_plus = x.copy()
        x_plus[i] += h
        x_minus = x.copy()
        x_minus[i] -= h
        grad[i] = (f(x_plus) - f(x_minus)) / (2 * h)
    return grad


def exact_gradient(f, x):
    """
    Compute the gradient using scipy's approx_fprime if available.
    使用 scipy 的 approx_fprime 计算梯度。

    Parameters
    ----------
    f : callable
        Scalar-valued function f: R^n -> R.
    x : array-like
        Point at which to compute the gradient.

    Returns
    -------
    grad : ndarray
        Gradient vector.
    """
    x = np.asarray(x, dtype=float)
    return approx_fprime(x, f, 1e-7)


def gradient_descent(
    f,
    x0,
    grad=None,
    max_iter=1000,
    tol=1e-8,
    step_size=0.01,
    line_search=True,
    step_size_bounds=(1e-10, 1e10),
    verbose=False,
):
    """
    Gradient descent optimization.

    Gradient descent iteratively updates:
        x_{k+1} = x_k - alpha_k * grad(f)(x_k)

    Parameters
    ----------
    f : callable
        Objective function f: R^n -> R.
    x0 : array-like
        Initial point.
    grad : callable, optional
        Gradient function. If None, numerical gradient is used.
    max_iter : int
        Maximum number of iterations.
    tol : float
        Convergence tolerance on gradient norm.
    step_size : float
        Initial step size (used with fixed step size mode).
    line_search : bool
        If True, use backtracking line search for adaptive step size.
    step_size_bounds : tuple
        (min, max) bounds for step size in line search.
    verbose : bool
        If True, print progress information.

    Returns
    -------
    result : GradientDescentResult
        Optimization result container.
    """
    result = GradientDescentResult()
    x = np.asarray(x0, dtype=float).copy()
    n = len(x)

    # Choose gradient function
    if grad is not None:
        grad_func = grad
    else:
        grad_func = lambda x: numerical_gradient(f, x)

    # Backtracking line search parameters
    alpha_init = step_size
    rho = 0.5
    c = 1e-4
    alpha = alpha_init

    for i in range(max_iter):
        g = grad_func(x)
        grad_norm = np.linalg.norm(g)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['grad_norm'].append(grad_norm)
        result.history['step_size'].append(alpha)

        if verbose:
            print(f"Iter {i:4d}: f = {f(x):.10e}, ||grad|| = {grad_norm:.2e}, "
                  f"alpha = {alpha:.6e}")

        # Check convergence
        if grad_norm < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.n_iter = i
            if verbose:
                print(f"Converged at iteration {i} with ||grad|| = {grad_norm:.2e}")
            break

        # Compute descent direction (negative gradient)
        d = -g

        # Step size selection
        if line_search:
            # Backtracking line search with Armijo condition
            # Find alpha such that: f(x + alpha*d) <= f(x) + c*alpha*grad^T*d
            alpha = alpha_init
            fx = f(x)
            for _ in range(50):
                if f(x + alpha * d) <= fx + c * alpha * np.dot(g, d):
                    break
                alpha *= rho
            alpha = np.clip(alpha, step_size_bounds[0], step_size_bounds[1])
        else:
            alpha = step_size

        # Update
        x = x + alpha * d

    # Final evaluation
    result.x_opt = x.copy()
    result.f_opt = f(x)
    result.n_iter = i + 1

    # Check final convergence
    final_grad_norm = np.linalg.norm(grad_func(x))
    if final_grad_norm < tol:
        result.converged = True

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}, ||grad|| = {final_grad_norm:.2e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result


def momentum_gradient_descent(
    f,
    x0,
    grad=None,
    max_iter=1000,
    tol=1e-8,
    step_size=0.01,
    momentum=0.9,
    line_search=True,
    verbose=False,
):
    """
    Gradient descent with momentum.

    Updates:
        v_{k+1} = mu * v_k - alpha * grad(f)(x_k)
        x_{k+1} = x_k + v_{k+1}

    Momentum accelerates convergence by accumulating velocity in the
    direction of persistent descent. It helps dampen oscillations in
    directions with high curvature.

    带动量的梯度下降通过累积持续下降方向的加速度来加速收敛。
    它有助于减弱高曲率方向上的振荡。

    Parameters
    ----------
    f : callable
        Objective function f: R^n -> R.
    x0 : array-like
        Initial point.
    grad : callable, optional
        Gradient function.
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    step_size : float
        Base step size.
    momentum : float
        Momentum coefficient (0 <= mu < 1).
    line_search : bool
        Whether to use line search.
    verbose : bool
        Print progress.

    Returns
    -------
    result : GradientDescentResult
        Optimization result.
    """
    result = GradientDescentResult()
    x = np.asarray(x0, dtype=float).copy()
    v = np.zeros_like(x)

    if grad is not None:
        grad_func = grad
    else:
        grad_func = lambda x: numerical_gradient(f, x)

    alpha = step_size

    for i in range(max_iter):
        g = grad_func(x)
        grad_norm = np.linalg.norm(g)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['grad_norm'].append(grad_norm)
        result.history['step_size'].append(alpha)

        if verbose:
            print(f"Iter {i:4d}: f = {f(x):.10e}, ||grad|| = {grad_norm:.2e}")

        if grad_norm < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.n_iter = i
            break

        # Momentum update
        v = momentum * v - alpha * g
        x = x + v

    result.x_opt = x.copy()
    result.f_opt = f(x)
    result.n_iter = i + 1

    final_grad_norm = np.linalg.norm(grad_func(x))
    if final_grad_norm < tol:
        result.converged = True

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}, ||grad|| = {final_grad_norm:.2e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result


def adagrad_gradient_descent(
    f,
    x0,
    grad=None,
    max_iter=1000,
    tol=1e-8,
    step_size=0.01,
    eps=1e-8,
    line_search=True,
    verbose=False,
):
    """
    AdaGrad gradient descent with adaptive per-coordinate learning rates.

    Updates:
        G_k = G_{k-1} + grad(f)(x_k)^2
        x_{k+1} = x_k - (alpha / sqrt(G_k + eps)) * grad(f)(x_k)

    AdaGrad adapts step sizes per coordinate based on historical gradient magnitudes,
    making it suitable for sparse problems.

    AdaGrad 根据历史梯度幅度自适应调整每个坐标的步长，
    适用于稀疏问题。

    Parameters
    ----------
    f : callable
        Objective function.
    x0 : array-like
        Initial point.
    grad : callable, optional
        Gradient function.
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    step_size : float
        Initial learning rate.
    eps : float
            Numerical stability constant.
    line_search : bool
        Whether to use line search.
    verbose : bool
        Print progress.

    Returns
    -------
    result : GradientDescentResult
        Optimization result.
    """
    result = GradientDescentResult()
    x = np.asarray(x0, dtype=float).copy()
    n = len(x)
    G = np.zeros(n)  # Accumulated squared gradients

    if grad is not None:
        grad_func = grad
    else:
        grad_func = lambda x: numerical_gradient(f, x)

    alpha = step_size

    for i in range(max_iter):
        g = grad_func(x)
        grad_norm = np.linalg.norm(g)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['grad_norm'].append(grad_norm)
        result.history['step_size'].append(alpha)

        if verbose:
            print(f"Iter {i:4d}: f = {f(x):.10e}, ||grad|| = {grad_norm:.2e}")

        if grad_norm < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.n_iter = i
            break

        # Accumulate squared gradients
        G += g ** 2

        # Adaptive step size per coordinate
        adaptive_alpha = alpha / (np.sqrt(G) + eps)

        # Element-wise update
        x = x - adaptive_alpha * g

    result.x_opt = x.copy()
    result.f_opt = f(x)
    result.n_iter = i + 1

    final_grad_norm = np.linalg.norm(grad_func(x))
    if final_grad_norm < tol:
        result.converged = True

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}, ||grad|| = {final_grad_norm:.2e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result
