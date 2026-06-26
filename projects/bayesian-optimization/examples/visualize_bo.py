"""
Example 5: Visualization of the Bayesian Optimization process.

This example demonstrates the BO process step by step on a 1D function,
showing how the GP model and acquisition function evolve over iterations.

Key visualizations:
- GP posterior (mean and uncertainty) at each iteration
- Acquisition function evolution
- How BO focuses on promising regions over time
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.gaussian_process import GaussianProcess
from src.kernel import MaternKernel
from src.acquisition import expected_improvement, upper_confidence_bound
from src.bo_loop import BayesianOptimization


def goldstein_price(x: np.ndarray) -> float:
    """1D slice of the Goldstein-Price function.

    A classic test function with multiple local minima.
    """
    x = x[0]
    return (1 + (x + 1)**2 * (1 - 2*x + x**2)) * \
           (30 + (2*x - 1)**2 * (3 - 4*x + x**2))


def plot_bo_process(objective, bounds, n_iter=8):
    """Visualize the BO process on a 1D function."""
    n_points = 500
    x_grid = np.linspace(bounds[0, 0], bounds[0, 1], n_points).reshape(-1, 1)
    y_grid = np.array([objective(x) for x in x_grid])

    # Run BO but collect intermediate states
    bo = BayesianOptimization(
        bounds=bounds,
        acquisition="ei",
        xi=0.01,
        n_initial=5,
        n_opt_restarts=10,
        random_state=42,
    )

    # Initial sampling
    rng = np.random.RandomState(42)
    lower, upper = bounds[0, 0], bounds[0, 1]
    init_points = rng.uniform(lower, upper, size=5)
    init_points.sort()

    X_all = init_points.copy().reshape(-1, 1)
    y_all = np.array([objective(x.reshape(1, -1)) for x in init_points])

    # Collect states for visualization
    states = []

    # Initial state
    gp = GaussianProcess(kernel=MaternKernel(nu=2.5))
    gp.fit(X_all, y_all)
    mu, var = gp.predict(x_grid, return_variance=True)
    sigma = np.sqrt(np.maximum(var, 1e-10))
    ei = expected_improvement(x_grid, mu, sigma, np.min(y_all), 0.01)

    states.append({
        "X_train": X_all.copy(),
        "y_train": y_all.copy(),
        "mu": mu.copy(),
        "sigma": sigma.copy(),
        "ei": ei.copy(),
        "best_y": float(np.min(y_all)),
        "n_eval": len(X_all),
    })

    # BO iterations
    for t in range(n_iter):
        # Find next point (EI max)
        next_idx = np.argmax(ei)
        x_next = x_grid[next_idx].copy()
        y_next = objective(x_next.reshape(1, -1))

        X_all = np.vstack([X_all, x_next.reshape(1, -1)])
        y_all = np.concatenate([y_all, [y_next]])

        # Update GP
        gp = GaussianProcess(kernel=MaternKernel(nu=2.5))
        gp.fit(X_all, y_all)
        mu, var = gp.predict(x_grid, return_variance=True)
        sigma = np.sqrt(np.maximum(var, 1e-10))
        ei = expected_improvement(x_grid, mu, sigma, float(np.min(y_all)), 0.01)

        states.append({
            "X_train": X_all.copy(),
            "y_train": y_all.copy(),
            "mu": mu.copy(),
            "sigma": sigma.copy(),
            "ei": ei.copy(),
            "best_y": float(np.min(y_all)),
            "n_eval": len(X_all),
        })

    # Plot
    _visualize_bo_states(states, x_grid, y_grid, objective)


def _visualize_bo_states(states, x_grid, y_grid, objective):
    """Create visualization of BO process evolution."""
    n_states = len(states)

    # Create figure with subplots
    fig, axes = plt.subplots(n_states, 3, figsize=(15, 4 * n_states))
    if n_states == 1:
        axes = axes.reshape(1, -1)

    for i, state in enumerate(states):
        x = x_grid.flatten()

        # Panel 1: Function + GP posterior
        ax = axes[i, 0]
        ax.plot(x, y_grid, "k-", linewidth=1.5, label="True function")
        ax.fill_between(x, state["mu"] - 2 * state["sigma"],
                        state["mu"] + 2 * state["sigma"],
                        alpha=0.3, color="blue", label="GP ±2σ")
        ax.plot(x, state["mu"], "b--", linewidth=1.5, label="GP mean")
        ax.scatter(state["X_train"][:, 0], state["y_train"],
                   c="red", s=80, marker="x", zorder=5, label="Observations")
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        ax.set_title(f"GP Model (n={state['n_eval']})")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Panel 2: GP uncertainty
        ax = axes[i, 1]
        ax.fill_between(x, 0, state["sigma"], alpha=0.5, color="orange")
        ax.set_xlabel("x")
        ax.set_ylabel("σ(x)")
        ax.set_title("Predictive Uncertainty")
        ax.grid(True, alpha=0.3)

        # Panel 3: Acquisition function
        ax = axes[i, 2]
        ax.plot(x, state["ei"], "g-", linewidth=1.5, label="EI(x)")
        # Mark selected point
        if i > 0:
            ax.axvline(x=state["X_train"][-1, 0], color="red",
                       linestyle="--", alpha=0.5, label=f"Next: {state['X_train'][-1, 0]:.3f}")
        ax.set_xlabel("x")
        ax.set_ylabel("EI(x)")
        ax.set_title("Expected Improvement")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("examples/output_bo_process.png", dpi=150, bbox_inches="tight",
                bbox_extra_artists=plt.gcf().get_tightbbox_list() if hasattr(plt.gcf(), 'get_tightbbox_list') else [])
    plt.close()
    print("Saved: examples/output_bo_process.png")

    # Convergence plot
    fig, ax = plt.subplots(figsize=(10, 5))
    best_y_history = [s["best_y"] for s in states]
    ax.plot(range(1, len(best_y_history) + 1), best_y_history, "b-o",
            linewidth=2, markersize=8)
    ax.set_xlabel("BO Iteration")
    ax.set_ylabel("Best f(x)")
    ax.set_title("BO Convergence on 1D Function")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("examples/output_bo_convergence_1d.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: examples/output_bo_convergence_1d.png")


def main():
    """Run 1D BO visualization."""
    bounds = np.array([[-3.0, 3.0]])

    print("=== 1D BO Process Visualization ===")
    print("Showing how GP and acquisition function evolve...")
    print()

    plot_bo_process(goldstein_price, bounds, n_iter=6)


if __name__ == "__main__":
    main()
