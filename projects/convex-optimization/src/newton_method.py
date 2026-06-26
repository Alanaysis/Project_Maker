"""
Newton's Method Optimizer (牛顿法优化器)

This module implements Newton's method for unconstrained convex optimization.

牛顿法优化器实现无约束凸优化的牛顿法。

Key Concepts / 关键概念:
- Newton's method uses second-order information (Hessian) for faster convergence.
  牛顿法利用二阶信息（Hessian）实现更快的收敛。

- Update rule:
    x_{k+1} = x_k - H^{-1}(x_k) * grad(f)(x_k)
  where H(x_k) is the Hessian matrix at x_k.

- Local convergence rate: Quadratic (doubles correct digits each iteration)
  局部收敛速度: 二次收敛（每次迭代正确位数翻倍）

- Global convergence requires:
  全局收敛需要:
  1. Line search to ensure sufficient decrease (Armijo condition)
  2. Damped Newton method for guaranteed convergence
  3. Hessian must be positive definite

- For strongly convex functions with Lipschitz continuous Hessian,
  Newton's method converges quadratically near the optimum.
  对于强凸函数且 Hessian Lipschitz 连续，牛顿法在最优解附近二次收敛。

- Computational cost: O(n^3) per iteration for Hessian inversion.
  计算成本: 每次迭代 O(n^3) 用于 Hessian 求逆。
"""

import numpy as np
from scipy.optimize import line_search
from src.gradient_descent import numerical_gradient


class NewtonResult:
    """
    Container for Newton's method optimization results.
    牛顿法优化结果的容器。
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
            'newton_dec': [],  # Newton decrement
            'step_size': [],
        }


def numerical_hessian(f, x, h=1e-5):
    """
    Compute the Hessian matrix numerically using central differences.
    使用中心差分法数值计算 Hessian 矩阵。

    Parameters
    ----------
    f : callable
        Scalar-valued function f: R^n -> R.
    x : array-like
        Point at which to evaluate the Hessian.
    h : float
        Step size for finite differences.

    Returns
    -------
    H : ndarray
        Hessian matrix of shape (n, n).
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    H = np.zeros((n, n))
    fi = f(x)
    for i in range(n):
        for j in range(i, n):
            x_ip = x.copy()
            x_ip[i] += h
            f_ip = f(x_ip)

            x_jp = x.copy()
            x_jp[j] += h
            f_jp = f(x_jp)

            x_ijp = x.copy()
            x_ijp[i] += h
            x_ijp[j] += h
            f_ijp = f(x_ijp)

            H[i, j] = (f_ijp - f_ip - f_jp + fi) / (h * h)
            H[j, i] = H[i, j]
    return H


def newton_method(
    f,
    x0,
    grad=None,
    hess=None,
    max_iter=100,
    tol=1e-8,
    line_search=True,
    regularization=1e-6,
    verbose=False,
):
    """
    Newton's method for unconstrained optimization.

    For a convex function f, Newton's method solves:
        grad(f)(x*) = 0

    At each iteration:
        1. Compute gradient g = grad(f)(x_k)
        2. Compute Hessian H = Hessian(f)(x_k)
        3. Solve H * d = -g for Newton direction d
        4. Update x_{k+1} = x_k + alpha * d (with line search)

    Parameters
    ----------
    f : callable
        Objective function f: R^n -> R.
    x0 : array-like
        Initial point.
    grad : callable, optional
        Gradient function. If None, numerical gradient is used.
    hess : callable, optional
        Hessian function. If None, numerical Hessian is used.
    max_iter : int
        Maximum number of iterations.
    tol : float
        Convergence tolerance on Newton decrement.
    line_search : bool
        Whether to use backtracking line search.
    regularization : float
        Regularization added to Hessian diagonal for numerical stability.
    verbose : bool
        Print progress.

    Returns
    -------
    result : NewtonResult
        Optimization result.
    """
    result = NewtonResult()
    x = np.asarray(x0, dtype=float).copy()
    n = len(x)

    if grad is not None:
        grad_func = grad
    else:
        grad_func = lambda x: numerical_gradient(f, x)

    if hess is not None:
        hess_func = hess
    else:
        hess_func = lambda x: numerical_hessian(f, x)

    for i in range(max_iter):
        g = grad_func(x)
        H = hess_func(x)

        # Regularize Hessian for numerical stability
        H_reg = H + regularization * np.eye(n)

        # Check if Hessian is positive definite
        try:
            # Try Cholesky decomposition
            L = np.linalg.cholesky(H_reg)
            pd = True
        except np.linalg.LinAlgError:
            # If Cholesky fails, add more regularization
            reg = regularization
            while True:
                try:
                    H_reg = H + reg * np.eye(n)
                    L = np.linalg.cholesky(H_reg)
                    pd = True
                    break
                except np.linalg.LinAlgError:
                    reg *= 10
                    if reg > 1e10:
                        pd = False
                        break

        if not pd:
            # Fall back to gradient descent direction
            d = -g
            newton_dec = np.linalg.norm(d)
        else:
            # Solve H * d = -g using Cholesky factorization
            # H = L * L^T
            # L * L^T * d = -g
            # First solve L * y = -g
            y = np.linalg.solve(L, -g)
            # Then solve L^T * d = y
            d = np.linalg.solve(L.T, y)

        # Newton decrement: sqrt(grad^T * H^{-1} * grad)
        # Measures distance to optimality
        newton_dec = np.sqrt(-np.dot(g, d))
        # Ensure real value
        newton_dec = max(0.0, newton_dec)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['grad_norm'].append(np.linalg.norm(g))
        result.history['newton_dec'].append(newton_dec)

        if verbose:
            print(f"Iter {i:3d}: f = {f(x):.10e}, ||grad|| = {np.linalg.norm(g):.2e}, "
                  f"lambda = {newton_dec:.6e}")

        # Check convergence using Newton decrement
        if newton_dec < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.n_iter = i
            if verbose:
                print(f"Converged at iteration {i} with lambda = {newton_dec:.2e}")
            break

        # Line search
        if line_search:
            alpha = _backtracking_line_search(f, x, d, grad_func, max_iter=50)
        else:
            alpha = 1.0

        # Update
        x = x + alpha * d

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


def damped_newton_method(
    f,
    x0,
    grad=None,
    hess=None,
    max_iter=100,
    tol=1e-8,
    mu=0.5,
    verbose=False,
):
    """
    Damped Newton method with guaranteed global convergence.

    The damped Newton method uses a fixed step size of alpha = 1 when
    the Newton decrement is small (< 1), and uses backtracking line search
    when the decrement is large.

    阻尼牛顿法在牛顿减量小时使用固定步长 alpha=1，
    在减量较大时使用回溯线搜索，保证全局收敛。

    Theorem: If f is convex and has Lipschitz-continuous Hessian,
    the damped Newton method converges globally.

    定理：如果 f 是凸函数且具有 Lipschitz 连续的 Hessian，
    阻尼牛顿法全局收敛。

    Parameters
    ----------
    f : callable
        Objective function (must be convex).
    x0 : array-like
        Initial point.
    grad : callable, optional
        Gradient function.
    hess : callable, optional
        Hessian function.
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    mu : float
        Parameter for self-concordance check (typically 0.5).
    verbose : bool
        Print progress.

    Returns
    -------
    result : NewtonResult
        Optimization result.
    """
    result = NewtonResult()
    x = np.asarray(x0, dtype=float).copy()
    n = len(x)

    if grad is not None:
        grad_func = grad
    else:
        grad_func = lambda x: numerical_gradient(f, x)

    if hess is not None:
        hess_func = hess
    else:
        hess_func = lambda x: numerical_hessian(f, x)

    for i in range(max_iter):
        g = grad_func(x)
        H = hess_func(x)

        # Regularize Hessian
        H_reg = H + 1e-8 * np.eye(n)

        try:
            L = np.linalg.cholesky(H_reg)
            y = np.linalg.solve(L, g)
            newton_dec = np.linalg.norm(y)
        except np.linalg.LinAlgError:
            newton_dec = np.inf

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['grad_norm'].append(np.linalg.norm(g))
        result.history['newton_dec'].append(newton_dec)

        if verbose:
            print(f"Iter {i:3d}: f = {f(x):.10e}, lambda = {newton_dec:.6e}")

        # Check convergence
        if newton_dec < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.n_iter = i
            if verbose:
                print(f"Converged at iteration {i} with lambda = {newton_dec:.2e}")
            break

        # Solve for Newton direction
        try:
            L = np.linalg.cholesky(H_reg)
            y = np.linalg.solve(L, -g)
            d = np.linalg.solve(L.T, y)
        except np.linalg.LinAlgError:
            d = -g  # Fallback to gradient direction

        # Damping rule
        if newton_dec < 1.0 / (4 * mu):
            alpha = 1.0  # Pure Newton step
        else:
            alpha = _backtracking_line_search(f, x, d, grad_func, max_iter=50)

        x = x + alpha * d

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


def _backtracking_line_search(f, x, d, grad_func, c=1e-4, rho=0.5, max_iter=50):
    """
    Backtracking line search with Armijo condition.
    带 Armijo 条件的回溯线搜索。

    Finds the largest alpha in {alpha_0, alpha_0*rho, alpha_0*rho^2, ...}
    such that: f(x + alpha*d) <= f(x) + c*alpha*grad^T*d

    在集合 {alpha_0, alpha_0*rho, alpha_0*rho^2, ...} 中寻找最大的 alpha，
    使得: f(x + alpha*d) <= f(x) + c*alpha*grad^T*d

    Parameters
    ----------
    f : callable
        Objective function.
    x : ndarray
        Current point.
    d : ndarray
        Search direction (should be descent direction).
    grad_func : callable
        Gradient function.
    c : float
        Sufficient decrease parameter (typically 1e-4).
    rho : float
        Reduction factor (typically 0.5).
    max_iter : int
        Maximum number of backtracking steps.

    Returns
    -------
    alpha : float
        Step size satisfying Armijo condition.
    """
    alpha = 1.0
    fx = f(x)
    g = grad_func(x)
    for _ in range(max_iter):
        if f(x + alpha * d) <= fx + c * alpha * np.dot(g, d):
            return alpha
        alpha *= rho
    return alpha
