"""
Convexity Checker (凸性检测器)

This module provides tools to verify whether a given function is convex.
A function f is convex if its Hessian matrix is positive semidefinite (PSD)
everywhere in its domain.

凸性检测器提供验证给定函数是否为凸函数的工具。
如果函数 f 的 Hessian 矩阵在其定义域内处处半正定，则该函数为凸函数。

Key Concepts / 关键概念:
- A function f: R^n -> R is convex if for all x, y in domain and theta in [0,1]:
  f(theta*x + (1-theta)*y) <= theta*f(x) + (1-theta)*f(y)
  函数 f 是凸的当且仅当对定义域内任意 x, y 和 theta in [0,1] 满足上述不等式

- If f is twice differentiable, f is convex iff its Hessian matrix is PSD:
  If f 二阶可微，f 是凸的当且仅当其 Hessian 矩阵半正定
  f''(x) >= 0 (for scalar case)
  Hessian(f)(x) >= 0 (for multivariate case)

- Common convex functions:
  常见凸函数:
  - Linear: f(x) = a^T*x (both convex and concave)
  - Quadratic: f(x) = x^T*P*x + q^T*x (convex iff P >= 0)
  - Exponential: f(x) = exp(a^T*x)
  - Log-sum-exp: f(x) = log(sum(exp(x_i)))
  - Negative entropy: f(x) = sum(x*log(x)) for x > 0
  - Norm: f(x) = ||x||_p for p >= 1
"""

import numpy as np
from scipy.optimize import approx_fprime
from scipy.linalg import eigvalsh


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
        Numerical Hessian matrix of shape (n, n).

    Notes
    -----
    Uses the central difference formula:
    f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h^2
    For multivariate case, uses:
    d²f/dx_i dx_j ≈ (f(x+he_i+he_j) - f(x+he_i-he_j) - f(x-he_i+he_j) + f(x-he_i-he_j)) / (4h²)
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    H = np.zeros((n, n))
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

            x_im = x.copy()
            x_im[i] -= h
            f_im = f(x_im)

            x_jm = x.copy()
            x_jm[j] -= h
            f_jm = f(x_jm)

            x_ijm = x.copy()
            x_ijm[i] -= h
            x_ijm[j] -= h
            f_ijm = f(x_ijm)

            x_ijp_m = x.copy()
            x_ijp_m[i] += h
            x_ijp_m[j] -= h
            f_ijp_m = f(x_ijp_m)

            x_im_jp = x.copy()
            x_im_jp[i] -= h
            x_im_jp[j] += h
            f_im_jp = f(x_im_jp)

            H[i, j] = (f_ijp - f_ijp_m - f_im_jp + f_ijm) / (4 * h * h)
            H[j, i] = H[i, j]

    return H


def is_positive_semidefinite(M, tol=1e-10):
    """
    Check if a symmetric matrix is positive semidefinite.
    检查对称矩阵是否半正定。

    A matrix M is PSD if all its eigenvalues are non-negative.
    矩阵 M 半正定当且仅当其所有特征值非负。

    Parameters
    ----------
    M : ndarray
        Symmetric matrix to check.
    tol : float
        Tolerance for considering eigenvalues as non-negative.

    Returns
    -------
    bool
        True if M is positive semidefinite.
    """
    M = np.asarray(M)
    if M.ndim != 2 or M.shape[0] != M.shape[1]:
        raise ValueError("Input must be a square matrix.")

    # Use eigvalsh for symmetric matrices (more efficient and accurate)
    eigenvalues = eigvalsh(M)
    return np.all(eigenvalues >= -tol)


def is_positive_definite(M, tol=1e-10):
    """
    Check if a symmetric matrix is positive definite.
    检查对称矩阵是否正定。

    A matrix M is PD if all its eigenvalues are strictly positive.
    矩阵 M 正定当且仅当其所有特征值严格为正。

    Parameters
    ----------
    M : ndarray
        Symmetric matrix to check.
    tol : float
        Tolerance for considering eigenvalues as positive.

    Returns
    -------
    bool
        True if M is positive definite.
    """
    M = np.asarray(M)
    if M.ndim != 2 or M.shape[0] != M.shape[1]:
        raise ValueError("Input must be a square matrix.")

    eigenvalues = eigvalsh(M)
    return np.all(eigenvalues > -tol)


def check_convexity(f, x_samples, tol=1e-8):
    """
    Check if a function is convex by verifying Hessian PSD at sample points.
    通过在采样点验证 Hessian 矩阵的半正定性来检查函数的凸性。

    This is a necessary condition: if the Hessian is not PSD at any sample
    point, the function is not convex.

    这是必要条件：如果在任何采样点 Hessian 不是 PSD，则函数不是凸的。

    Parameters
    ----------
    f : callable
        Scalar-valued function f: R^n -> R.
    x_samples : list of array-like
        Sample points to check convexity.
    tol : float
        Tolerance for PSD check.

    Returns
    -------
    is_convex : bool
        True if Hessian is PSD at all sample points.
    details : list
        List of (point, min_eigenvalue, is_psd) tuples.
    """
    details = []
    is_convex = True

    for x in x_samples:
        x = np.asarray(x, dtype=float)
        H = numerical_hessian(f, x)
        eigenvalues = eigvalsh(H)
        min_eig = np.min(eigenvalues)
        psd = min_eig >= -tol
        details.append((x, min_eig, psd))
        if not psd:
            is_convex = False

    return is_convex, details


def verify_convexity_1d(f, x_range, n_points=100, tol=1e-8):
    """
    Verify convexity of a univariate function by checking second derivative.
    通过检查二阶导数验证一元函数的凸性。

    For a univariate function f: R -> R, f is convex iff f''(x) >= 0 everywhere.
    对于一元函数 f，f 是凸的当且仅当 f''(x) >= 0 处处成立。

    Parameters
    ----------
    f : callable
        Scalar function f: R -> R.
    x_range : tuple
        (x_min, x_max) range to check.
    n_points : int
        Number of sample points.
    tol : float
        Tolerance for non-negativity check.

    Returns
    -------
    is_convex : bool
        True if f''(x) >= 0 at all sample points.
    min_second_deriv : float
        Minimum second derivative value found.
    """
    x_min, x_max = x_range
    x_samples = np.linspace(x_min, x_max, n_points)
    min_second_deriv = np.inf

    for x in x_samples:
        # Central difference for second derivative
        h = 1e-5
        f_pp = (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)
        if f_pp < min_second_deriv:
            min_second_deriv = f_pp

    return min_second_deriv >= -tol, min_second_deriv


def check_jensen_inequality(f, x_samples, n_trials=100, tol=1e-6):
    """
    Verify Jensen's inequality for a convex function.
    验证凸函数的 Jensen 不等式。

    For a convex function f:
    f(E[X]) <= E[f(X)]

    This is a fundamental characterization of convex functions.
    这是凸函数的基本特征。

    Parameters
    ----------
    f : callable
        Scalar-valued function to check.
    x_samples : list of array-like
        Points to use in Jensen's inequality check.
    n_trials : int
        Number of random convex combination trials.
    tol : float
        Tolerance for inequality violation.

    Returns
    -------
    is_convex : bool
        True if Jensen's inequality holds for all trials.
    max_violation : float
        Maximum violation of Jensen's inequality found.
    """
    x_samples = [np.asarray(x, dtype=float) for x in x_samples]
    n = len(x_samples[0])
    max_violation = 0.0

    for _ in range(n_trials):
        # Random convex combination
        weights = np.random.dirichlet(np.ones(len(x_samples)))
        x_comb = sum(w * x for w, x in zip(weights, x_samples))

        f_comb = f(x_comb)
        f_expected = sum(w * f(x) for w, x in zip(weights, x_samples))

        violation = f_expected - f_comb
        max_violation = max(max_violation, violation)

    # For convex function, f(E[X]) <= E[f(X)], so violation should be >= 0
    return max_violation >= -tol, max_violation


# Predefined convex functions for testing / learning
# 预定义的凸函数用于测试和学习

def linear_function(x, a=None, b=0):
    """
    Linear function: f(x) = a^T*x + b
    线性函数: f(x) = a^T*x + b

    Linear functions are both convex and concave.
    线性函数既是凸函数也是凹函数。
    """
    a = np.array(a) if a is not None else np.ones(len(x))
    return np.dot(a, x) + b


def quadratic_form(x, P=None, q=None, r=0):
    """
    Quadratic function: f(x) = x^T*P*x + q^T*x + r
    二次函数: f(x) = x^T*P*x + q^T*x + r

    This function is convex if and only if P is positive semidefinite.
    当且仅当 P 半正定时，此函数是凸函数。
    """
    P = np.array(P) if P is not None else np.eye(len(x))
    q = np.array(q) if q is not None else np.zeros(len(x))
    return x @ P @ x + q @ x + r


def exponential_function(x, a=None):
    """
    Exponential function: f(x) = sum(exp(a_i * x_i))
    指数函数: f(x) = sum(exp(a_i * x_i))

    This is convex for any vector a.
    对任意向量 a，此函数是凸的。
    """
    a = np.array(a) if a is not None else np.ones(len(x))
    return np.sum(np.exp(a * x))


def log_sum_exp(x, alpha=1.0):
    """
    Log-sum-exp function: f(x) = (1/alpha) * log(sum(exp(alpha * x_i)))
    对数指数和函数: f(x) = (1/alpha) * log(sum(exp(alpha * x_i)))

    This is a smooth approximation of the maximum function.
    这是最大值函数的平滑近似。
    """
    alpha = float(alpha)
    return (1.0 / alpha) * np.log(np.sum(np.exp(alpha * x)))


def negative_entropy(x, eps=1e-12):
    """
    Negative entropy function: f(x) = sum(x_i * log(x_i)) for x_i > 0
    负熵函数: f(x) = sum(x_i * log(x_i)) for x_i > 0

    Domain: x_i > 0 for all i.
    定义域: x_i > 0 for all i.
    """
    x = np.asarray(x, dtype=float)
    x = np.maximum(x, eps)
    return np.sum(x * np.log(x))


def huber_loss(x, delta=1.0):
    """
    Huber loss: robust loss function combining L1 and L2 properties.
    Huber 损失: 结合 L1 和 L2 性质的鲁棒损失函数。

    f(x) = 0.5 * x^2           for |x| <= delta
    f(x) = delta * (|x| - 0.5*delta)  for |x| > delta

    This is convex for any delta > 0.
    对任意 delta > 0，此函数是凸的。
    """
    x = np.asarray(x, dtype=float)
    abs_x = np.abs(x)
    result = np.where(abs_x <= delta, 0.5 * x ** 2, delta * (abs_x - 0.5 * delta))
    return float(np.sum(result))


def log_barrier(x, eps=1e-12):
    """
    Log barrier function: f(x) = -sum(log(x_i))
    对数障碍函数: f(x) = -sum(log(x_i))

    Domain: x_i > 0 for all i.
    定义域: x_i > 0 for all i.

    Used in interior point methods to keep iterates strictly feasible.
    在内点法中用于保持迭代点严格可行。
    """
    x = np.asarray(x, dtype=float)
    x = np.maximum(x, eps)
    return -np.sum(np.log(x))
