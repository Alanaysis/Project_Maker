"""
Damped Line Search (阻尼线搜索)

This module implements advanced line search strategies for optimization algorithms.

阻尼线搜索模块实现优化算法的高级线搜索策略。

Key Concepts / 关键概念:
- Line search finds a step size alpha that provides sufficient decrease:
  线搜索寻找提供足够下降的步长 alpha:
    f(x + alpha*d) <= f(x) + c1 * alpha * grad^T * d    (Armijo/Wolfe)
    |grad(x + alpha*d)^T * d| <= c2 * |grad(x)^T * d|   (Strong Wolfe)

- Backtracking line search: simple, starts with alpha=1 and reduces.
  回溯线搜索：简单，从 alpha=1 开始递减。

- Wolfe conditions ensure good convergence properties.
  Wolfe 条件保证良好的收敛性质。

- Damped Newton method uses line search to ensure global convergence.
  阻尼牛顿法使用线搜索确保全局收敛。
"""

import numpy as np


class LineSearchResult:
    """
    Container for line search results.
    线搜索结果的容器。
    """
    def __init__(self):
        self.alpha = None
        self.f_new = None
        self.evaluations = 0
        self.success = False
        self.reason = ""


def backtracking_line_search(
    f,
    x,
    d,
    grad_f,
    c1=1e-4,
    rho=0.5,
    alpha_init=1.0,
    alpha_max=1e10,
    max_iter=50,
    verbose=False,
):
    """
    Backtracking line search with Armijo condition.

    Finds alpha in {alpha_0, alpha_0*rho, alpha_0*rho^2, ...} such that:
        f(x + alpha*d) <= f(x) + c1 * alpha * grad^T * d

    This is the simplest and most commonly used line search method.
    这是最简单和最常用的线搜索方法。

    Parameters
    ----------
    f : callable
        Objective function.
    x : ndarray
        Current point.
    d : ndarray
        Search direction (must be a descent direction: grad^T*d < 0).
    grad_f : callable
        Gradient function.
    c1 : float
        Armijo parameter (typically 1e-4). Controls sufficient decrease.
    rho : float
        Reduction factor (typically 0.5).
    alpha_init : float
        Initial step size guess.
    alpha_max : float
        Maximum step size.
    max_iter : int
        Maximum backtracking iterations.
    verbose : bool
        Print details.

    Returns
    -------
    alpha : float
        Step size satisfying Armijo condition.
    """
    x = np.asarray(x, dtype=float)
    d = np.asarray(d, dtype=float)

    fx = f(x)
    g = grad_f(x)
    slope = np.dot(g, d)

    # Check descent direction
    if slope >= 0:
        return alpha_init

    alpha = alpha_init
    evaluations = 0

    for i in range(max_iter):
        f_new = f(x + alpha * d)
        evaluations += 1

        if f_new > fx + c1 * alpha * slope:
            alpha *= rho
        else:
            if verbose:
                print(f"Backtracking: alpha = {alpha:.6e}, "
                      f"f_new = {f_new:.6e}, f + c1*slope = {fx + c1*alpha*slope:.6e}")
            return alpha

        if alpha < 1e-30:
            break

    if verbose:
        print(f"Backtracking: max_iter reached, alpha = {alpha:.6e}")

    return alpha


def wolfe_line_search(
    f,
    x,
    d,
    grad_f,
    c1=1e-4,
    c2=0.9,
    alpha_init=1.0,
    alpha_max=1e10,
    max_iter=50,
):
    """
    Line search satisfying Wolfe conditions.

    Conditions:
        1. Armijo: f(x + alpha*d) <= f(x) + c1 * alpha * grad^T * d
        2. Curvature: grad(x + alpha*d)^T * d >= c2 * grad^T * d

    The strong Wolfe condition replaces condition 2 with:
        |grad(x + alpha*d)^T * d| <= c2 * |grad^T * d|

    Parameters
    ----------
    f : callable
        Objective function.
    x : ndarray
        Current point.
    d : ndarray
        Search direction.
    grad_f : callable
        Gradient function.
    c1 : float
        Armijo parameter.
    c2 : float
        Curvature parameter (typically 0.9 for strong Wolfe).
    alpha_init : float
        Initial step size.
    alpha_max : float
        Maximum step size.
    max_iter : int
        Maximum iterations.

    Returns
    -------
    result : LineSearchResult
        Line search result.
    """
    result = LineSearchResult()
    x = np.asarray(x, dtype=float)
    d = np.asarray(d, dtype=float)

    fx = f(x)
    g = grad_f(x)
    slope = np.dot(g, d)

    if slope >= 0:
        result.reason = "Not a descent direction"
        return result

    alpha_lo = 0.0
    alpha_hi = alpha_max

    alpha = alpha_init
    evaluations = 0

    for i in range(max_iter):
        f_new = f(x + alpha * d)
        evaluations += 1

        # Armijo condition
        if f_new > fx + c1 * alpha * slope:
            # Zoom in
            alpha_hi = alpha
            alpha = 0.5 * (alpha_lo + alpha_hi)
            continue

        g_new = grad_f(x + alpha * d)
        curv = np.dot(g_new, d)

        # Curvature condition
        if curv < c2 * slope:
            # Step size too small
            alpha_lo = alpha
            alpha = max(alpha_hi, alpha)
            alpha = 0.5 * (alpha_lo + alpha_hi)
            continue

        # Strong Wolfe: check gradient magnitude
        if abs(curv) > -c2 * slope:
            alpha_hi = alpha
            alpha = 0.5 * (alpha_lo + alpha_hi)
            continue

        # All conditions satisfied
        result.alpha = alpha
        result.f_new = f_new
        result.evaluations = evaluations
        result.success = True
        result.reason = "Wolfe conditions satisfied"
        return result

        # Recompute for next iteration
        g_new = grad_f(x + alpha * d)
        curv = np.dot(g_new, d)

        if curv <= 0:
            alpha_hi = alpha
        else:
            alpha_lo = alpha
        alpha = 0.5 * (alpha_lo + alpha_hi)

    # Return best alpha found
    result.alpha = alpha
    result.f_new = f(x + alpha * d)
    result.evaluations = evaluations
    result.success = False
    result.reason = "Max iterations reached"

    return result


def adamijo_strong_wolfe_line_search(
    f,
    x,
    d,
    grad_f,
    c1=1e-4,
    c2=0.9,
    alpha_init=1.0,
    max_iter=50,
):
    """
    Combined Armijo + Strong Wolfe line search with zoom phase.

    Implements the standard line search algorithm:
        1. Function value check (Armijo)
        2. Curvature check
        3. Zoom phase to satisfy strong Wolfe conditions

    Parameters
    ----------
    f : callable
        Objective function.
    x : ndarray
        Current point.
    d : ndarray
        Search direction.
    grad_f : callable
        Gradient function.
    c1 : float
        Armijo parameter.
    c2 : float
        Curvature parameter.
    alpha_init : float
        Initial step size.
    max_iter : int
        Maximum iterations.

    Returns
    -------
    result : LineSearchResult
        Line search result.
    """
    result = LineSearchResult()
    x = np.asarray(x, dtype=float)
    d = np.asarray(d, dtype=float)

    fx = f(x)
    g = grad_f(x)
    dg = np.dot(g, d)

    if dg >= 0:
        result.reason = "Not a descent direction"
        return result

    alpha = alpha_init
    evaluations = 0

    # Initial function value check
    f_new = f(x + alpha * d)
    evaluations += 1

    if f_new > fx + c1 * alpha * dg:
        alpha = _zoom(f, x, d, fx, dg, c1, c2, grad_f, alpha, alpha_init, max_iter, result)
        if result.success:
            return result

    # Check curvature condition
    g_new = grad_f(x + alpha * d)
    dg_new = np.dot(g_new, d)
    evaluations += 1

    if abs(dg_new) > -c2 * dg:
        alpha = _zoom(f, x, d, fx, dg, c1, c2, grad_f, alpha, alpha_init, max_iter, result)
        if result.success:
            return result

    result.alpha = alpha
    result.f_new = f(x + alpha * d)
    result.evaluations = evaluations
    result.success = True
    result.reason = "Sufficient decrease"

    return result


def _zoom(f, x, d, fx, dg, c1, c2, grad_f, alpha_lo, alpha_hi, max_iter, result):
    """
    Zoom phase of line search.
    线搜索的缩放阶段。

    Finds alpha in [alpha_lo, alpha_hi] satisfying strong Wolfe conditions.
    在 [alpha_lo, alpha_hi] 中寻找满足强 Wolfe 条件的 alpha。
    """
    max_iter_zoom = 20
    for _ in range(max_iter_zoom):
        alpha = 0.5 * (alpha_lo + alpha_hi)
        f_new = f(x + alpha * d)

        if f_new > fx + c1 * alpha * dg or f_new >= f(x + alpha_lo * d):
            alpha_hi = alpha
        else:
            g_new = grad_f(x + alpha * d)
            dg_new = np.dot(g_new, d)
            if abs(dg_new) <= -c2 * dg:
                result.alpha = alpha
                result.f_new = f_new
                result.success = True
                result.reason = "Zoom satisfied"
                return alpha
            if dg_new * (alpha_hi - alpha_lo) >= 0:
                alpha_hi = alpha_lo
            alpha_lo = alpha

        if alpha_hi - alpha_lo < 1e-16:
            break

    result.alpha = 0.5 * (alpha_lo + alpha_hi)
    result.f_new = f(x + result.alpha * d)
    result.success = False
    result.reason = "Zoom failed"
    return result.alpha
