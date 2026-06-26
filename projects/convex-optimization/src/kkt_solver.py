"""
KKT Conditions Solver (KKT 条件求解器)

This module implements solvers for Karush-Kuhn-Tucker (KKT) conditions,
which are the first-order optimality conditions for constrained optimization.

KKT 条件求解器实现约束优化的最优性一阶条件求解器。

Key Concepts / 关键概念:
- For the problem:
  对于问题:
    min f(x)
    s.t.  h_i(x) = 0,  i = 1, ..., p
          g_j(x) <= 0,  j = 1, ..., q

- The KKT conditions are:
  KKT 条件:
  1. Stationarity: grad(f)(x) + sum(nu_i * grad(h_i)(x)) + sum(lam_j * grad(g_j)(x)) = 0
  2. Primal feasibility: h_i(x) = 0, g_j(x) <= 0
  3. Dual feasibility: lam_j >= 0
  4. Complementary slackness: lam_j * g_j(x) = 0

- The KKT conditions are necessary for optimality under certain regularity
  conditions (e.g., Slater's condition for convex problems).

  KKT 条件在一定的正则条件下是最优性的必要条件。

- For convex problems with Slater's condition, KKT conditions are
  necessary AND sufficient.

  对于满足 Slater 条件的凸问题，KKT 条件是必要且充分的。
"""

import numpy as np
from src.gradient_descent import numerical_gradient, gradient_descent


class KKTResult:
    """
    Container for KKT solver results.
    KKT 求解器结果的容器。
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
            'stationarity': [],
            'primal_res': [],
            'dual_res': [],
            'complementarity': [],
        }


def check_kkt_conditions(
    f,
    grad_f,
    equality_constraints,
    inequality_constraints,
    x,
    nu,
    lam,
):
    """
    Check if KKT conditions are satisfied at a point.
    检查 KKT 条件在一点是否满足。

    Parameters
    ----------
    f : callable
        Objective function.
    grad_f : callable
        Gradient of objective.
    equality_constraints : list of callable
        Equality constraints h_i(x) = 0.
    inequality_constraints : list of callable
        Inequality constraints g_j(x) <= 0.
    x : ndarray
        Point to check.
    nu : array-like
        Equality multipliers.
    lam : array-like
        Inequality multipliers.

    Returns
    -------
    satisfied : bool
        True if all KKT conditions are satisfied within tolerance.
    details : dict
        Dictionary with KKT condition values.
    """
    details = {}

    # 1. Stationarity
    stationarity = grad_f(x).copy()
    for i, h in enumerate(equality_constraints):
        stationarity += nu[i] * numerical_gradient(h, x)
    for j, g in enumerate(inequality_constraints):
        stationarity += lam[j] * numerical_gradient(g, x)
    details['stationarity'] = np.linalg.norm(stationarity)

    # 2. Primal feasibility
    h_vals = np.array([h(x) for h in equality_constraints])
    g_vals = np.array([g(x) for g in inequality_constraints])
    details['primal_eq'] = np.linalg.norm(h_vals)
    details['primal_ineq'] = np.max(g_vals) if len(g_vals) > 0 else 0.0

    # 3. Dual feasibility
    details['dual_feasible'] = np.all(lam >= -1e-8)

    # 4. Complementary slackness
    comp = np.array([lam[j] * g_vals[j] for j in range(len(g_vals))])
    details['complementarity'] = np.max(np.abs(comp)) if len(comp) > 0 else 0.0

    tol = 1e-6
    satisfied = (
        details['stationarity'] < tol and
        details['primal_eq'] < tol and
        details['primal_ineq'] <= tol and
        details['dual_feasible'] and
        details['complementarity'] < tol
    )

    return satisfied, details


def solve_kkt_system(
    f,
    grad_f,
    hess_f,
    equality_constraints,
    inequality_constraints,
    x0,
    nu0=None,
    lam0=None,
    max_iter=100,
    tol=1e-8,
    verbose=False,
):
    """
    Solve KKT conditions using a primal-dual Newton method.

    This solves the KKT system directly by applying Newton's method to:
        grad_x L(x, lam, nu) = 0
        h_i(x) = 0
        lam_j * g_j(x) = mu (complementarity with barrier parameter)

    Parameters
    ----------
    f : callable
        Objective function.
    grad_f : callable
        Gradient of objective.
    hess_f : callable
        Hessian of objective.
    equality_constraints : list of callable
        Equality constraints h_i(x) = 0.
    inequality_constraints : list of callable
        Inequality constraints g_j(x) <= 0.
    x0 : array-like
        Initial point.
    nu0 : array-like, optional
        Initial equality multipliers.
    lam0 : array-like, optional
        Initial inequality multipliers.
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    verbose : bool
        Print progress.

    Returns
    -------
    result : KKTResult
        KKT solver result.
    """
    result = KKTResult()
    x = np.asarray(x0, dtype=float).copy()
    p = len(equality_constraints)
    q = len(inequality_constraints)

    if nu0 is not None:
        nu = np.array(nu0, dtype=float)
    else:
        nu = np.zeros(p)

    if lam0 is not None:
        lam = np.maximum(np.array(lam0, dtype=float), 1e-8)
    else:
        lam = np.ones(q) * 1e-6

    mu = 1e-4  # Barrier parameter for complementarity

    for k in range(max_iter):
        # Evaluate constraints and gradients
        h_vals = np.array([h(x) for h in equality_constraints]) if p > 0 else np.array([])
        g_vals = np.array([g(x) for g in inequality_constraints]) if q > 0 else np.array([])

        # Stationarity residual: grad_x L = 0
        stationarity = grad_f(x).copy()
        for i, h in enumerate(equality_constraints):
            stationarity += nu[i] * numerical_gradient(h, x)
        for j, g in enumerate(inequality_constraints):
            stationarity += lam[j] * numerical_gradient(g, x)

        # Primal feasibility residual
        primal_res = np.concatenate([h_vals, np.maximum(g_vals, 0)]) if len(h_vals) > 0 or len(g_vals) > 0 else np.array([])

        # Complementarity residual: lam_j * g_j(x) = mu
        comp_res = lam * g_vals - mu if q > 0 else np.array([])

        # Dual feasibility residual (lam >= 0)
        dual_res = np.maximum(-lam, 0) if q > 0 else np.array([])

        total_res = np.linalg.norm(stationarity) + np.linalg.norm(primal_res) + np.linalg.norm(comp_res)

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))
        result.history['stationarity'].append(np.linalg.norm(stationarity))
        result.history['primal_res'].append(np.linalg.norm(primal_res))
        result.history['dual_res'].append(np.linalg.norm(dual_res))
        result.history['complementarity'].append(np.max(np.abs(comp_res)) if len(comp_res) > 0 else 0.0)

        if verbose:
            print(f"KKT iter {k}: total_res = {total_res:.2e}, f = {f(x):.6e}, "
                  f"mu = {mu:.2e}")

        # Check convergence
        if total_res < tol:
            result.converged = True
            result.x_opt = x.copy()
            result.f_opt = f(x)
            result.nu_opt = nu.copy()
            result.lambda_opt = lam.copy()
            result.n_iter = k
            if verbose:
                print(f"KKT conditions satisfied at iteration {k}")
            break

        # Newton step to solve KKT system
        # Build KKT system Jacobian
        n = len(x)

        # Hessian of Lagrangian
        H_L = hess_f(x).copy()
        for j, g in enumerate(inequality_constraints):
            # Numerical Hessian of constraint
            h_step = 1e-5
            fi = g(x)
            for a in range(n):
                for b in range(a, n):
                    x_ab = x.copy()
                    x_ab[a] += h_step
                    x_ab[b] += h_step
                    f_ab = g(x_ab)
                    x_a = x.copy()
                    x_a[a] += h_step
                    f_a = g(x_a)
                    x_b = x.copy()
                    x_b[b] += h_step
                    f_b = g(x_b)
                    hess_g = (f_ab - f_a - f_b + fi) / (h_step ** 2)
                    H_L[a, b] += lam[j] * hess_g
                    H_L[b, a] = H_L[a, b]

        # Jacobian of constraints
        J = np.zeros((p + q, n))
        for i, h in enumerate(equality_constraints):
            J[i] = numerical_gradient(h, x)
        for j, g in enumerate(inequality_constraints):
            J[p + j] = numerical_gradient(g, x)

        # Solve KKT system
        # [H_L  J^T] [dx]   [-stationarity]
        # [J    D   ] [dnu] = [-primal_res]
        # where D = diag(lam / g) for complementarity

        try:
            if q > 0:
                D = np.diag(lam / (g_vals + 1e-12))
                A_kkt = np.block([
                    [H_L, J.T],
                    [J, np.zeros((p + q, p + q))]
                ])
                b_kkt = np.concatenate([-stationarity, -primal_res])
            else:
                A_kkt = np.block([
                    [H_L, J.T],
                    [J, np.zeros((p, p))]
                ])
                b_kkt = np.concatenate([-stationarity, -h_vals])

            step = np.linalg.solve(A_kkt, b_kkt)
        except np.linalg.LinAlgError:
            step = -stationarity
            if p + q > 0:
                step = np.concatenate([step, -primal_res]) if len(primal_res) > 0 else step

        dx = step[:n]
        dnu = step[n:n+p] if p > 0 else np.array([])
        dlam = step[n+p:] if q > 0 else np.array([])

        # Line search
        alpha = 1.0
        for _ in range(50):
            x_new = x + alpha * dx
            g_new = np.array([g(x_new) for g in inequality_constraints]) if q > 0 else np.array([])
            if np.all(g_new < 0.1) or q == 0:
                break
            alpha *= 0.5

        x = x + alpha * dx

        # Update multipliers
        nu = nu + dnu if p > 0 else nu
        if q > 0:
            lam = lam + alpha * dlam
            lam = np.maximum(lam, 1e-12)

        # Reduce barrier parameter
        mu *= 0.3

    result.x_opt = x.copy()
    result.f_opt = f(x)
    result.nu_opt = nu.copy()
    result.lambda_opt = lam.copy()
    result.n_iter = k + 1

    stationarity = grad_f(x).copy()
    for i, h in enumerate(equality_constraints):
        stationarity += nu[i] * numerical_gradient(h, x)
    for j, g in enumerate(inequality_constraints):
        stationality += lam[j] * numerical_gradient(g, x)

    if np.linalg.norm(stationarity) < tol:
        result.converged = True

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}")
        print(f"KKT iterations: {result.n_iter}, Converged: {result.converged}")

    return result


def active_set_method(
    f,
    grad_f,
    hess_f,
    equality_constraints,
    inequality_constraints,
    x0,
    max_iter=100,
    tol=1e-8,
    verbose=False,
):
    """
    Active set method for solving KKT conditions.

    The active set method identifies which inequality constraints are active
    (binding) at the solution and solves the equality-constrained subproblem.

    活跃集方法识别在解处活跃的（起作用的）不等式约束，
    并求解等式约束子问题。

    Algorithm:
        1. Identify active set of constraints
        2. Solve equality-constrained subproblem with active constraints
        3. Check KKT conditions
        4. Update active set
        5. Repeat until convergence

    Parameters
    ----------
    f : callable
        Objective function.
    grad_f : callable
        Gradient of objective.
    hess_f : callable
        Hessian of objective.
    equality_constraints : list of callable
        Equality constraints.
    inequality_constraints : list of callable
        Inequality constraints.
    x0 : array-like
        Initial point.
    max_iter : int
        Maximum iterations.
    tol : float
        Convergence tolerance.
    verbose : bool
        Print progress.

    Returns
    -------
    result : KKTResult
        KKT solver result.
    """
    result = KKTResult()
    x = np.asarray(x0, dtype=float).copy()
    q = len(inequality_constraints)

    # Initialize active set (indices of active inequality constraints)
    active_set = set()
    for j, g in enumerate(inequality_constraints):
        if g(x) > -1e-6:
            active_set.add(j)

    for k in range(max_iter):
        g_vals = np.array([g(x) for g in inequality_constraints])

        # Solve equality-constrained subproblem with active constraints
        active_constraints = [inequality_constraints[j] for j in active_set]

        from src.lagrangian import method_of_lagrange_multipliers

        sub_result = method_of_lagrange_multipliers(
            f,
            equality_constraints + active_constraints,
            x,
            max_iter=50,
            tol=tol,
            verbose=False,
        )
        x_new = sub_result.x_opt

        # Check if new point satisfies all constraints
        all_g = np.array([g(x_new) for g in inequality_constraints])

        if np.all(all_g <= 1e-6):
            # Feasible: check KKT conditions
            stationarity = grad_f(x_new).copy()
            nu_active = sub_result.nu_opt[len(equality_constraints):] if sub_result.nu_opt is not None else np.array([])

            # Map multipliers back to original constraints
            lam = np.zeros(q)
            for idx, j in enumerate(active_set):
                lam[j] = nu_active[idx] if idx < len(nu_active) else 0

            # Check dual feasibility (lam >= 0 for active constraints)
            if np.all(lam[active_set] >= -tol):
                result.converged = True
                result.x_opt = x_new.copy()
                result.f_opt = f(x_new)
                result.lambda_opt = lam
                result.nu_opt = sub_result.nu_opt if sub_result.nu_opt is not None else np.zeros(len(equality_constraints))
                result.n_iter = k
                if verbose:
                    print(f"Active set method converged at iteration {k}")
                break

        # Update active set
        active_set = set()
        for j, g in enumerate(inequality_constraints):
            if g(x_new) > -1e-6:
                active_set.add(j)

        x = x_new

        result.history['x'].append(x.copy())
        result.history['f'].append(f(x))

        if verbose:
            print(f"Active iter {k}: f = {f(x):.6e}, active = {active_set}")

    if not result.converged:
        result.x_opt = x.copy()
        result.f_opt = f(x)
        result.n_iter = k + 1

    if verbose:
        print(f"\nFinal: f(x*) = {result.f_opt:.10e}")
        print(f"Iterations: {result.n_iter}, Converged: {result.converged}")

    return result
