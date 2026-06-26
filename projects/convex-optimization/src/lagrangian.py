"""
Lagrangian Multiplier Method (拉格朗日乘子法)

This module implements the method of Lagrange multipliers for handling
equality and inequality constraints in optimization.

拉格朗日乘子法模块用于处理优化中的等式和不等式约束。

Key Concepts / 关键概念:
- For constrained optimization:
  对于约束优化:
    min f(x)
    s.t.  h_i(x) = 0,  i = 1, ..., p
          g_j(x) <= 0,  j = 1, ..., q

- The Lagrangian is:
  拉格朗日函数:
    L(x, lambda, nu) = f(x) + sum(lambda_j * g_j(x)) + sum(nu_i * h_i(x))

- The dual function is:
  对偶函数:
    g(lambda, nu) = inf_x L(x, lambda, nu)

- The dual problem is:
  对偶问题:
    max g(lambda, nu)
    s.t.  lambda >= 0

- Weak duality: g(lambda, nu) <= f(x*) for any feasible x and lambda >= 0.
  弱对偶性：g(lambda, nu) <= f(x*) 对任意可行 x 和 lambda >= 0 成立。

- Strong duality holds when there is no duality gap (e.g., Slater's condition).
  强对偶性在无对偶间隙时成立（例如 Slater 条件）。
"""

import numpy as np
from src.gradient_descent import numerical_gradient


class LagrangianResult:
    """
    Container for Lagrangian multiplier method results.
    拉格朗日乘子法结果的容器。
    """
    def __init__(self):
        self.x_opt = None
        self.lambda_opt = None  # Inequality multipliers
        self.nu_opt = None     # Equality multipliers
        self.f_opt = None
        self.converged = False
        self.n_iter = 0
        self.history = {
            'x': [],
            'f': [],
            'lambda': [],
            'nu': [],
            'primal_residual': [],
            'dual_residual': [],
        }


def lagrangian(f, equality_constraints, inequality_constraints, x, nu=None, lam=None):
    """
    Compute the Lagrangian value.
    计算拉格朗日函数值。

    L(x, lam, nu) = f(x) + sum(lam_j * g_j(x)) + sum(nu_i * h_i(x))

    Parameters
    ----------
    f : callable
        Objective function.
    equality_constraints : list of callable
        Equality constraints h_i(x) = 0.
    inequality_constraints : list of callable
        Inequality constraints g_j(x) <= 0.
    x : ndarray
        Current point.
    nu : array-like, optional
        Equality multiplier values.
    lam : array-like, optional
        Inequality multiplier values.

    Returns
    -------
    L : float
        Lagrangian value.
    """
    L = f(x)

    if equality_constraints:
        if nu is None:
            nu = np.zeros(len(equality_constraints))
        for i, h in enumerate(equality_constraints):
            L += nu[i] * h(x)

    if inequality_constraints:
        if lam is None:
            lam = np.zeros(len(inequality_constraints))
        for j, g in enumerate(inequality_constraints):
            L += lam[j] * g(x)

    return L


def lagrangian_gradient(f, equality_constraints, inequality_constraints, x, nu=None, lam=None):
    """
    Compute the gradient of the Lagrangian with respect to x.
    计算拉格朗日函数关于 x 的梯度。

    grad_x L = grad(f)(x) + sum(nu_i * grad(h_i)(x)) + sum(lam_j * grad(g_j)(x))

    Parameters
    ----------
    f : callable
        Objective function.
    equality_constraints : list of callable
        Equality constraints.
    inequality_constraints : list of callable
        Inequality constraints.
    x : ndarray
        Current point.
    nu : array-like, optional
        Equality multipliers.
    lam : array-like, optional
        Inequality multipliers.

    Returns
    -------
    grad_L : ndarray
        Gradient of Lagrangian.
    """
    grad_L = numerical_gradient(f, x)

    if equality_constraints:
        if nu is None:
            nu = np.zeros(len(equality_constraints))
        for i, h in enumerate(equality_constraints):
            grad_L += nu[i] * numerical_gradient(h, x)

    if inequality_constraints:
        if lam is None:
            lam = np.zeros(len(inequality_constraints))
        for j, g in enumerate(inequality_constraints):
            grad_L += lam[j] * numerical_gradient(g, x)

    return grad_L


def augmented_lagrangian(
    f,
    equality_constraints,
    inequality_constraints,
    x,
    nu=None,
    lam=None,
    rho=1.0,
):
    """
    Compute the augmented Lagrangian value.
    计算增广拉格朗日函数值。

    For equality constraints h_i(x) = 0:
        L_A(x) = f(x) + sum(nu_i * h_i(x)) + (rho/2) * sum(h_i(x)^2)

    For inequality constraints g_j(x) <= 0:
        L_A(x) = f(x) + sum(max(0, lam_j + rho*g_j(x))^2 - lam_j^2) / (2*rho)

    The augmented Lagrangian adds a quadratic penalty term to improve
    conditioning compared to the standard Lagrangian.

    增广拉格朗日函数添加了二次惩罚项，改善了条件数。

    Parameters
    ----------
    f : callable
        Objective function.
    equality_constraints : list of callable
        Equality constraints h_i(x) = 0.
    inequality_constraints : list of callable
        Inequality constraints g_j(x) <= 0.
    x : ndarray
        Current point.
    nu : array-like, optional
        Equality multipliers.
    lam : array-like, optional
        Inequality multipliers.
    rho : float
        Penalty parameter.

    Returns
    -------
    L_A : float
        Augmented Lagrangian value.
    """
    L_A = f(x)

    if equality_constraints:
        if nu is None:
            nu = np.zeros(len(equality_constraints))
        for i, h in enumerate(equality_constraints):
            hi = h(x)
            L_A += nu[i] * hi + (rho / 2) * hi ** 2

    if inequality_constraints:
        if lam is None:
            lam = np.zeros(len(inequality_constraints))
        for j, g in enumerate(inequality_constraints):
            gj = g(x)
            # Use the standard augmented Lagrangian formulation for inequalities
            val = lam[j] + rho * gj
            if val > 0:
                L_A += (val ** 2 - lam[j] ** 2) / (2 * rho)

    return L_A


def method_of_lagrange_multipliers(
    f,
    equality_constraints,
    x0,
    max_iter=100,
    tol=1e-6,
    nu_init=None,
    rho=1.0,
    verbose=False,
):
    """
    Solve equality-constrained optimization using the method of Lagrange multipliers.

    Solves:
        min f(x)
        s.t.  h_i(x) = 0,  i = 1, ..., p

    Using the augmented Lagrangian method (method of multipliers):
        1. Minimize L_A(x, nu_k) with respect to x
        2. Update nu_{k+1} = nu_k + rho * h(x)
        3. Increase rho if needed

    Parameters
    ----------
    f : callable
        Objective function f: R^n -> R.
    equality_constraints : list of callable
        Equality constraints h_i(x) = 0.
    x0 : array-like
        Initial point.
    max_iter : int
        Maximum outer iterations.
    tol : float
        Convergence tolerance on constraint violation.
    nu_init : array-like, optional
        Initial multiplier values.
    rho : float
        Penalty parameter.
    verbose : bool
        Print progress.

    Returns
    -------
    result : LagrangianResult
        Optimization result.
    """
    result = LagrangianResult()
    x = np.asarray(x0, dtype=float).copy()
    p = len(equality_constraints)

    if nu_init is not None:
        nu = np.array(nu_init, dtype=float)
    else:
        nu = np.zeros(p)

    for k in range(max_iter):
        # Minimize augmented Lagrangian w.r.t. x
        def f_aug(x_local, nu_val=nu, rho_val=rho):
            return augmented_lagrangian(
                f, equality_constraints, [], x_local,
                nu=nu_val, lam=None, rho=rho_val
            )

        from src.gradient_descent import gradient_descent

        sub_result = gradient_descent(
            f_aug, x,
            max_iter=50,
            tol=1e-8,
            step_size=0.01,
            line_search=True,
            verbose=False,
        )

        x = sub_result.x_opt

        # Compute constraint violation
        h_vals = np.array([h(x) for h in equality_constraints])
        primal_res = np.linalg.norm(h_vals)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['nu'].append(nu.copy())
        result.history['primal_residual'].append(primal_res)

        if verbose:
            print(f"Outer iter {k}: f = {f(x):.6e}, ||h(x)|| = {primal_res:.2e}, rho = {rho:.2e}")

        # Check convergence
        if primal_res < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.nu_opt = nu.copy()
            result.n_iter = k
            if verbose:
                print(f"Converged at outer iteration {k}")
            break

        # Update multipliers
        nu = nu + rho * h_vals

        # Increase penalty parameter
        if k > 0 and k % 10 == 0:
            rho *= 2

    result.x_opt = x.copy()
    result.f_opt = f(x)
    result.nu_opt = nu.copy()
    result.n_iter = k + 1

    if not result.converged:
        h_vals = np.array([h(x) for h in equality_constraints])
        result.history['primal_residual'].append(np.linalg.norm(h_vals))

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}")
        print(f"Constraint violation: {np.linalg.norm(h_vals):.2e}")
        print(f"Outer iterations: {result.n_iter}")

    return result


def admm_solver(
    f_x,
    f_z,
    A,
    b,
    x0,
    z0,
    y0=None,
    max_iter=100,
    rho=1.0,
    tol=1e-6,
    verbose=False,
):
    """
    ADMM (Alternating Direction Method of Multipliers) solver.

    Solves:
        min f_x(x) + f_z(z)
        s.t.  Ax - z = b

    ADMM alternates between minimizing with respect to x and z,
    then updating the dual variable y.

    ADMM 交替最小化 x 和 z，然后更新对偶变量 y。

    Update rules:
        x_{k+1} = argmin_x (f_x(x) + (rho/2)||Ax - z_k + y_k||^2)
        z_{k+1} = argmin_z (f_z(z) + (rho/2)||Ax_{k+1} - z + y_k||^2)
        y_{k+1} = y_k + rho*(Ax_{k+1} - z_{k+1} - b)

    Parameters
    ----------
    f_x : callable
        Objective component depending on x.
    f_z : callable
        Objective component depending on z.
    A : ndarray
        Constraint matrix.
    b : ndarray
        Constraint RHS.
    x0 : array-like
        Initial x.
    z0 : array-like
        Initial z.
    y0 : array-like, optional
        Initial dual variable y.
    max_iter : int
        Maximum iterations.
    rho : float
        ADMM penalty parameter.
    tol : float
        Convergence tolerance.
    verbose : bool
        Print progress.

    Returns
    -------
    result : LagrangianResult
        Optimization result.
    """
    result = LagrangianResult()
    x = np.asarray(x0, dtype=float).copy()
    z = np.asarray(z0, dtype=float).copy()
    m = len(b)

    if y0 is not None:
        y = np.array(y0, dtype=float)
    else:
        y = np.zeros(m)

    for k in range(max_iter):
        # X-update: minimize f_x(x) + (rho/2)||Ax - z + y||^2
        def f_aug_x(x_local, z_val=z, y_val=y, rho_val=rho):
            return f_x(x_local) + (rho_val / 2) * np.linalg.norm(
                A @ x_local - z_val + y_val
            ) ** 2

        from src.gradient_descent import gradient_descent

        x_result = gradient_descent(
            f_aug_x, x,
            max_iter=50,
            tol=1e-8,
            step_size=0.01,
            line_search=True,
            verbose=False,
        )
        x = x_result.x_opt

        # Z-update: minimize f_z(z) + (rho/2)||Ax - z + y||^2
        def f_aug_z(z_local, x_val=x, y_val=y, rho_val=rho):
            return f_z(z_local) + (rho_val / 2) * np.linalg.norm(
                A @ x_val - z_local + y_val
            ) ** 2

        z_result = gradient_descent(
            f_aug_z, z,
            max_iter=50,
            tol=1e-8,
            step_size=0.01,
            line_search=True,
            verbose=False,
        )
        z = z_result.x_opt

        # Dual update
        y = y + rho * (A @ x - z - b)

        # Compute residuals
        primal_res = np.linalg.norm(A @ x - z - b)
        dual_res = np.linalg.norm(-rho * A.T @ (A @ x - z))

        result.history['x'].append(x.copy())
        result.history['f'].append(f_x(x) + f_z(z))
        result.history['lambda'].append(lam if 'lam' in dir() else np.zeros(0))
        result.history['nu'].append(y.copy())
        result.history['primal_residual'].append(primal_res)
        result.history['dual_residual'].append(dual_res)

        if verbose:
            print(f"Iter {k:3d}: obj = {f_x(x) + f_z(z):.6e}, "
                  f"primal_res = {primal_res:.2e}, dual_res = {dual_res:.2e}")

        # Check convergence
        if primal_res < tol and dual_res < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f_x(x) + f_z(z)
            result.nu_opt = y.copy()
            result.n_iter = k
            if verbose:
                print(f"ADMM converged at iteration {k}")
            break

    result.x_opt = x.copy()
    result.f_opt = f_x(x) + f_z(z)
    result.nu_opt = y.copy()
    result.n_iter = k + 1

    if verbose:
        print(f"\nFinal: obj = {result.f_opt:.10e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result
