"""
Interior Point Method (内点法)

This module implements the interior point method for solving convex
optimization problems with inequality constraints.

内点法模块用于求解带不等式约束的凸优化问题。

Key Concepts / 关键概念:
- Interior point methods solve a sequence of barrier problems:
  内点法求解一系列障碍问题:
    min f_0(x) - mu * sum(log(-c_i(x)))
  where c_i(x) <= 0 are inequality constraints and mu > 0 is the barrier parameter.

- The central path is the trajectory of optimal solutions as mu -> 0.
  中心路径是 mu -> 0 时最优解的轨迹。

- Primal-dual interior point methods solve the KKT conditions directly
  using Newton's method on the perturbed KKT system.

  原对偶内点法直接通过 Newton 法求解扰动后的 KKT 条件。

- Convergence: Typically 10-50 iterations regardless of problem size
  (polynomial time complexity).

  收敛性：通常 10-50 次迭代（多项式时间复杂度）。

- Log barrier function transforms constrained problems into unconstrained ones:
  对数障碍函数将约束问题转化为无约束问题:
    phi(x) = -sum(log(-c_i(x)))  for c_i(x) < 0
"""

import numpy as np
from scipy.optimize import line_search
from src.gradient_descent import numerical_gradient
from src.newton_method import _backtracking_line_search


class InteriorPointResult:
    """
    Container for interior point method results.
    内点法结果的容器。
    """
    def __init__(self):
        self.x_opt = None
        self.f_opt = None
        self.n_iter = 0
        self.converged = False
        self.history = {
            'x': [],
            'f': [],
            'mu': [],
            'dual_gap': [],
            'primal_residual': [],
            'dual_residual': [],
        }


def log_barrier_function(constraints, x):
    """
    Compute the log barrier value for given constraints.
    计算给定约束的对数障碍值。

    phi(x) = -sum(log(-c_i(x))) where c_i(x) < 0

    Parameters
    ----------
    constraints : list of callable
        List of constraint functions c_i(x) <= 0.
    x : ndarray
        Current point (must be strictly feasible).

    Returns
    -------
    phi : float
        Log barrier value.
    """
    phi = 0.0
    for c in constraints:
        ci = c(x)
        if ci >= 0:
            raise ValueError(f"Point is not strictly feasible: c(x) = {ci} >= 0")
        phi -= np.log(-ci)
    return phi


def log_barrier_gradient(constraints, x):
    """
    Compute the gradient of the log barrier function.
    计算对数障碍函数的梯度。

    grad(phi)(x) = -sum( grad(c_i)(x) / c_i(x) )

    Parameters
    ----------
    constraints : list of callable
        List of constraint functions.
    x : ndarray
        Current point.

    Returns
    -------
    grad : ndarray
        Gradient of the log barrier.
    """
    n = len(x)
    grad = np.zeros(n)
    for c in constraints:
        ci = c(x)
        # Numerical gradient of constraint
        h = 1e-5
        for i in range(n):
            x_plus = x.copy()
            x_plus[i] += h
            x_minus = x.copy()
            x_minus[i] -= h
            ci_grad = (c(x_plus) - c(x_minus)) / (2 * h)
            grad[i] -= ci_grad / ci
    return grad


def log_barrier_hessian(constraints, x):
    """
    Compute the Hessian of the log barrier function.
    计算对数障碍函数的 Hessian。

    Hessian(phi)(x) = -sum( [Hess(c_i)(x) * c_i(x) - grad(c_i)(x) * grad(c_i)(x)^T] / c_i(x)^2 )

    Parameters
    ----------
    constraints : list of callable
        List of constraint functions.
    x : ndarray
        Current point.

    Returns
    -------
    H : ndarray
        Hessian of the log barrier.
    """
    n = len(x)
    H = np.zeros((n, n))
    for c in constraints:
        ci = c(x)
        # Numerical gradient
        h = 1e-5
        grad_ci = np.zeros(n)
        for i in range(n):
            x_plus = x.copy()
            x_plus[i] += h
            x_minus = x.copy()
            x_minus[i] -= h
            grad_ci[i] = (c(x_plus) - c(x_minus)) / (2 * h)

        # Numerical Hessian of constraint
        fi = c(x)
        for i in range(n):
            for j in range(i, n):
                x_ip = x.copy()
                x_ip[i] += h
                f_ip = c(x_ip)
                x_jp = x.copy()
                x_jp[j] += h
                f_jp = c(x_jp)
                x_ijp = x.copy()
                x_ijp[i] += h
                x_ijp[j] += h
                f_ijp = c(x_ijp)
                Hessian_ci = (f_ijp - f_ip - f_jp + fi) / (h * h)
                H[i, j] -= (Hessian_ci * ci - grad_ci[i] * grad_ci[j]) / (ci ** 2)
                H[j, i] = H[i, j]
    return H


def primal_dual_interior_point(
    f0,
    grad_f0,
    hess_f0,
    constraints,
    x0,
    max_iter=100,
    tol=1e-8,
    mu_init=1.0,
    mu_min=1e-12,
    verbose=False,
):
    """
    Primal-dual interior point method for convex optimization.

    Solves:
        min f0(x)
        s.t.  c_i(x) <= 0,  i = 1, ..., m

    The method solves the KKT conditions of the barrier problem:
        grad(f0)(x) - sum(lambda_i * grad(c_i)(x)) = 0
        lambda_i * c_i(x) = -mu,  i = 1, ..., m
        lambda_i > 0, c_i(x) < 0

    Parameters
    ----------
    f0 : callable
        Objective function f0: R^n -> R.
    grad_f0 : callable
        Gradient of objective function.
    hess_f0 : callable
        Hessian of objective function.
    constraints : list of callable
        List of inequality constraint functions c_i(x) <= 0.
    x0 : array-like
        Strictly feasible initial point (c_i(x0) < 0 for all i).
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    mu_init : float
        Initial barrier parameter.
    mu_min : float
        Minimum barrier parameter.
    verbose : bool
        Print progress.

    Returns
    -------
    result : InteriorPointResult
        Optimization result.
    """
    result = InteriorPointResult()
    x = np.asarray(x0, dtype=float).copy()
    n = len(x)
    m = len(constraints)

    # Initialize dual variables
    lam = np.ones(m)

    mu = mu_init

    for i in range(max_iter):
        # Compute barrier-augmented objective
        # f_bar(x) = f0(x) - mu * sum(log(-c_i(x)))
        grad_bar = grad_f0(x).copy()
        hess_bar = hess_f0(x).copy()

        for j, c in enumerate(constraints):
            cj = c(x)
            if cj >= 0:
                raise ValueError(f"Iteration {i}: Point infeasible, c_{j}(x) = {cj} >= 0")

            # Gradient contribution
            grad_cj = numerical_gradient(c, x)
            grad_bar -= mu * grad_cj / cj

            # Hessian contribution
            h = 1e-5
            fi = c(x)
            for a in range(n):
                for b in range(a, n):
                    x_ab = x.copy()
                    x_ab[a] += h
                    x_ab[b] += h
                    f_ab = c(x_ab)
                    x_a = x.copy()
                    x_a[a] += h
                    f_a = c(x_a)
                    x_b = x.copy()
                    x_b[b] += h
                    f_b = c(x_b)
                    hess_cj = (f_ab - f_a - f_b + fi) / (h * h)
                    grad_cj_a = (c(x.copy() + h * np.eye(n)[a]) - c(x.copy() - h * np.eye(n)[a])) / (2 * h)
                    grad_cj_b = (c(x.copy() + h * np.eye(n)[b]) - c(x.copy() - h * np.eye(n)[b])) / (2 * h)
                    hess_bar[a, b] -= mu * (hess_cj * cj - grad_cj_a * grad_cj_b) / (cj ** 2)
                    hess_bar[b, a] = hess_bar[a, b]

        # Newton step: solve KKT system
        # [H_bar  -J^T] [dx]   [-(grad_f0 - J^T lam)]
        # [J       D  ] [dlam] = [diag(lam) * c(x) + mu*1]
        # where J = Jacobian of constraints, D = diag(lam)

        J = np.zeros((m, n))
        for j, c in enumerate(constraints):
            J[j] = numerical_gradient(c, x)

        # Right-hand side
        rhs_x = -grad_bar
        rhs_lam = (lam * np.array([c(x) for c in constraints]) + mu)

        # Solve the KKT system
        # Form augmented system
        A = np.block([
            [hess_bar, -J.T],
            [J, np.zeros((m, m))]
        ])
        b = np.concatenate([rhs_x, rhs_lam])

        try:
            step = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            # Fallback to gradient descent on barrier problem
            dx = -grad_bar
            dlam = np.zeros(m)
        else:
            dx = step[:n]
            dlam = step[n:]

        # Compute residuals
        primal_res = np.linalg.norm(grad_bar)
        dual_res = np.linalg.norm(lam * np.array([c(x) for c in constraints]) + mu)
        dual_gap = np.dot(lam, np.array([c(x) for c in constraints])) + n * mu

        result.history['x'].append(x.copy())
        result.history['f'].append(f0(x))
        result.history['mu'].append(mu)
        result.history['dual_gap'].append(dual_gap)
        result.history['primal_residual'].append(primal_res)
        result.history['dual_residual'].append(dual_res)

        if verbose:
            print(f"Iter {i:3d}: f = {f0(x):.6e}, mu = {mu:.2e}, "
                  f"dual_gap = {dual_gap:.2e}, primal_res = {primal_res:.2e}")

        # Check convergence
        if dual_gap < tol and primal_res < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f0(x)
            result.n_iter = i
            if verbose:
                print(f"Converged at iteration {i}")
            break

        # Line search
        alpha = _backtracking_line_search(f0, x, dx, grad_f0, max_iter=50)

        # Ensure strict feasibility
        x_new = x + alpha * dx
        min_c = min(c(x_new) for c in constraints)
        if min_c >= 0:
            # Reduce step size to maintain feasibility
            for alpha_try in [alpha * 0.5 ** k for k in range(1, 20)]:
                if all(c(x + alpha_try * dx) < 0 for c in constraints):
                    alpha = alpha_try
                    break
            else:
                alpha = 1e-8

        x = x + alpha * dx

        # Update dual variables
        lam = -mu / np.array([c(x) for c in constraints])
        lam = np.maximum(lam, 1e-12)

        # Reduce barrier parameter
        mu *= 0.3
        mu = max(mu, mu_min)

    result.x_opt = x.copy()
    result.f_opt = f0(x)
    result.n_iter = i + 1

    final_primal_res = np.linalg.norm(grad_f0(x))
    if final_primal_res < tol:
        result.converged = True

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result


def barrier_method(
    f0,
    grad_f0,
    hess_f0,
    constraints,
    x0,
    max_iter=100,
    tol=1e-8,
    mu_init=1.0,
    mu_factor=10.0,
    verbose=False,
):
    """
    Classical barrier method (exterior sequence of unconstrained problems).

    Solves a sequence of unconstrained problems:
        min f0(x) - mu_k * sum(log(-c_i(x)))

    where mu_k decreases geometrically: mu_{k+1} = mu_k / tau

    Parameters
    ----------
    f0 : callable
        Objective function.
    grad_f0 : callable
        Gradient of objective.
    hess_f0 : callable
        Hessian of objective.
    constraints : list of callable
        Inequality constraints c_i(x) <= 0.
    x0 : array-like
        Strictly feasible starting point.
    max_iter : int
        Maximum total iterations across all barrier problems.
    tol : float
        Convergence tolerance.
    mu_init : float
        Initial barrier parameter.
    mu_factor : float
        Factor by which mu increases each subproblem.
    verbose : bool
        Print progress.

    Returns
    -------
    result : InteriorPointResult
        Optimization result.
    """
    result = InteriorPointResult()
    x = np.asarray(x0, dtype=float).copy()
    mu = mu_init

    total_iter = 0
    outer_iter = 0

    while mu < 1e12 and total_iter < max_iter:
        # Define barrier-augmented objective
        def f_bar(x_local, mu_val=mu):
            val = f0(x_local)
            val -= mu_val * log_barrier_function(constraints, x_local)
            return val

        def grad_f_bar(x_local, mu_val=mu):
            val = grad_f0(x_local).copy()
            val -= mu_val * log_barrier_gradient(constraints, x_local)
            return val

        def hess_f_bar(x_local, mu_val=mu):
            val = hess_f0(x_local).copy()
            val -= mu_val * log_barrier_hessian(constraints, x_local)
            return val

        # Solve subproblem using Newton's method
        from src.newton_method import newton_method

        sub_result = newton_method(
            f_bar, x,
            grad=grad_f_bar,
            hess=hess_f_bar,
            max_iter=min(50, max_iter - total_iter),
            tol=tol,
            verbose=False,
        )

        x = sub_result.x_opt
        total_iter += sub_result.n_iter
        outer_iter += 1

        # Compute dual gap as stopping criterion
        lam = mu / np.array([-c(x) for c in constraints])
        dual_gap = n * mu if 'n' in dir() else 0  # Will be set below

        result.history['x'].append(x.copy())
        result.history['f'].append(f0(x))
        result.history['mu'].append(mu)

        # Compute dual gap properly
        n = len(x)
        lam = mu / np.array([-c(x) for c in constraints])
        dual_gap = n * mu

        if dual_gap < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f0(x)
            result.n_iter = total_iter
            if verbose:
                print(f"Barrier method converged at outer iter {outer_iter}")
            break

        if verbose:
            print(f"Barrier iter {outer_iter}: mu = {mu:.2e}, f = {f0(x):.6e}, "
                  f"dual_gap = {dual_gap:.2e}")

        mu *= mu_factor

    if not result.converged:
        result.x_opt = x.copy()
        result.f_opt = f0(x)
        result.n_iter = total_iter

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}")
        print(f"Barrier iterations: {outer_iter}, Total Newton iters: {total_iter}")

    return result
