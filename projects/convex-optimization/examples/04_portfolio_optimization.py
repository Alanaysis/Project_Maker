"""
Example 4: Portfolio Optimization (投资组合优化)

Solves the Markowitz portfolio optimization problem.

Markowitz Portfolio Optimization:
    min w^T * Sigma * w   (portfolio variance)
    s.t.  sum(w_i) = 1    (budget constraint)
          w_i >= 0         (no short selling)
          w^T * mu >= r    (minimum return constraint)

This is a classic quadratic programming problem in finance.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convexity_checker import is_positive_semidefinite, quadratic_form
from src.gradient_descent import gradient_descent
from src.newton_method import newton_method


def generate_market_data(n_assets=5, seed=42):
    """Generate realistic market data for portfolio optimization."""
    np.random.seed(seed)

    # Expected returns (annualized)
    mu = np.array([0.08, 0.10, 0.12, 0.06, 0.15])[:n_assets]

    # Generate a valid covariance matrix
    A = np.random.randn(n_assets, n_assets) * 0.1
    Sigma = A @ A.T + np.eye(n_assets) * 0.01

    # Ensure PSD
    eigenvalues = np.linalg.eigvalsh(Sigma)
    if np.min(eigenvalues) < 0:
        Sigma += (-np.min(eigenvalues) + 1e-6) * np.eye(n_assets)

    return mu, Sigma


def markowitz_optimization(mu, Sigma, target_return=None, n_assets=None, risk_free_rate=0.02):
    """
    Solve the Markowitz portfolio optimization problem.

    min (1/2) * w^T * Sigma * w
    s.t.  sum(w_i) = 1
          w_i >= 0
          w^T * mu >= target_return (optional)

    Returns the efficient frontier.
    """
    if n_assets is None:
        n_assets = len(mu)

    # Generate efficient frontier by varying target return
    min_return = np.min(mu)
    max_return = np.max(mu)

    if target_return is None:
        target_return = (min_return + max_return) / 2

    returns = np.linspace(min_return, max_return, 20)
    frontier = []

    for r_target in returns:
        # Solve for each target return
        result = solve_single_portfolio(mu, Sigma, r_target, n_assets)
        frontier.append(result)

    return frontier


def solve_single_portfolio(mu, Sigma, target_return, n_assets):
    """Solve a single portfolio optimization problem."""
    # Objective: min (1/2) * w^T * Sigma * w
    def f0(w):
        return 0.5 * w @ Sigma @ w

    def grad_f0(w):
        return Sigma @ w

    def hess_f0(w):
        return Sigma

    # Constraints
    constraints = []

    # Budget constraint: sum(w) = 1 => handled as equality
    # We use augmented Lagrangian for the equality constraint

    # Return constraint: w^T * mu >= target_return => target_return - w^T * mu <= 0
    def return_constraint(w):
        return target_return - w @ mu

    constraints.append(return_constraint)

    # Non-negativity: w_i >= 0 => -w_i <= 0
    for i in range(n_assets):
        def make_nonneg(idx):
            return lambda w, _idx=idx: -w[_idx]
        constraints.append(make_nonneg(i))

    # Initial point (equal weight portfolio)
    w0 = np.ones(n_assets) / n_assets

    # Solve with barrier method
    mu_barrier = 0.1
    def f_barrier(w):
        val = f0(w)
        # Augmented Lagrangian for equality constraint
        budget_violation = np.sum(w) - 1.0
        rho = 10.0
        nu = 0.0  # Initial multiplier
        val += nu * budget_violation + (rho / 2) * budget_violation ** 2
        # Log barrier for inequality constraints
        for c_fn in constraints:
            ci = c_fn(w)
            if ci >= 0:
                val += 1e6
            else:
                val -= mu_barrier * np.log(-ci)
        return val

    def grad_barrier(w):
        val = grad_f0(w).copy()
        budget_violation = np.sum(w) - 1.0
        rho = 10.0
        nu = 0.0
        val += (nu + rho * budget_violation) * np.ones(n_assets)
        for c_fn in constraints:
            ci = c_fn(w)
            if ci < 0:
                ci_grad = np.zeros(n_assets)
                h = 1e-5
                for j in range(n_assets):
                    w_jp = w.copy()
                    w_jp[j] += h
                    w_jm = w.copy()
                    w_jm[j] -= h
                    ci_grad[j] = (c_fn(w_jp) - c_fn(w_jm)) / (2 * h)
                val -= mu_barrier * ci_grad / ci
        return val

    result = gradient_descent(
        f_barrier, w0,
        grad=grad_barrier,
        max_iter=3000,
        tol=1e-8,
        step_size=0.0001,
        line_search=True,
        verbose=False,
    )

    # Normalize weights to sum to 1
    w_opt = result.x_opt / np.sum(result.x_opt)

    portfolio_stats = {
        'target_return': target_return,
        'weights': w_opt,
        'expected_return': w_opt @ mu,
        'risk': np.sqrt(w_opt @ Sigma @ w_opt),
        'sharpe_ratio': (w_opt @ mu - risk_free_rate) / np.sqrt(w_opt @ Sigma @ w_opt) if np.sqrt(w_opt @ Sigma @ w_opt) > 0 else 0,
        'converged': result.converged,
    }

    return portfolio_stats


def efficient_frontier(mu, Sigma, n_points=30, risk_free_rate=0.02):
    """
    Compute the efficient frontier.

    The efficient frontier is the set of portfolios that offer
    the highest expected return for a given level of risk.

    有效前沿是每个风险水平下提供最高预期回报的投资组合集合。
    """
    n_assets = len(mu)
    min_return = np.min(mu) * 0.9
    max_return = np.max(mu) * 1.1

    returns = np.linspace(min_return, max_return, n_points)
    frontier = []

    for r_target in returns:
        stats = solve_single_portfolio(mu, Sigma, r_target, n_assets)
        if stats['converged']:
            frontier.append(stats)

    return frontier


def main():
    print("=" * 60)
    print("Example 4: Portfolio Optimization (投资组合优化)")
    print("=" * 60)

    # Generate market data
    n_assets = 5
    mu, Sigma = generate_market_data(n_assets, seed=42)

    asset_names = ['Stock A', 'Stock B', 'Stock C', 'Bond D', 'Stock E']

    print(f"\nExpected annual returns:")
    for i, name in enumerate(asset_names[:n_assets]):
        print(f"  {name}: {mu[i]*100:.2f}%")

    print(f"\nCovariance matrix (annualized):")
    print(Sigma)

    # Check PSD
    is_psd = is_positive_semidefinite(Sigma)
    print(f"\nCovariance matrix is PSD: {is_psd}")

    # Solve for different target returns
    print("\n--- Efficient Frontier ---")
    frontier = efficient_frontier(mu, Sigma, n_points=15)

    print(f"\n{'Target Return':>15} {'Expected Return':>18} {'Risk (σ)':>12} {'Sharpe Ratio':>14}")
    print("-" * 65)
    for stats in frontier:
        print(f"{stats['target_return']:15.4f} {stats['expected_return']:18.4f} "
              f"{stats['risk']:12.4f} {stats['sharpe_ratio']:14.4f}")

    # Find maximum Sharpe ratio portfolio
    best = max(frontier, key=lambda s: s['sharpe_ratio'])
    print(f"\n--- Maximum Sharpe Ratio Portfolio ---")
    print(f"Expected return: {best['expected_return']*100:.2f}%")
    print(f"Risk (σ): {best['risk']*100:.2f}%")
    print(f"Sharpe ratio: {best['sharpe_ratio']:.4f}")
    print(f"Weights:")
    for i, name in enumerate(asset_names[:n_assets]):
        print(f"  {name}: {best['weights'][i]*100:.2f}%")

    # Minimum variance portfolio (target return = min possible)
    print(f"\n--- Minimum Variance Portfolio ---")
    min_var = frontier[0]
    print(f"Risk (σ): {min_var['risk']*100:.2f}%")
    print(f"Weights:")
    for i, name in enumerate(asset_names[:n_assets]):
        print(f"  {name}: {min_var['weights'][i]*100:.2f}%")

    return frontier


if __name__ == "__main__":
    main()
