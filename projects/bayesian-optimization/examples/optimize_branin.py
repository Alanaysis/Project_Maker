"""
Example 1: Optimize Branin function using Bayesian Optimization.

The Branin function is a classic 2D test function with three global minima.
It's commonly used to benchmark optimization algorithms because:
- It's cheap to evaluate (good for demonstration)
- It has multiple local minima (tests global optimization)
- It has known global minima (for evaluation)

This example demonstrates:
- Setting up the BO loop
- Running optimization on a known benchmark
- Visualizing the optimization trajectory
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.benchmarks import branin, branin_bounds, branin_true_minimum
from src.bo_loop import BayesianOptimization


def main():
    """Run BO on the Branin function and visualize results."""
    # Setup
    bounds = branin_bounds()
    f_min, x_opt = branin_true_minimum()

    print("=== Branin Function Optimization ===")
    print(f"True minimum: f(x*) = {f_min:.6f}")
    print(f"True minimizers:\n{x_opt}")
    print()

    # Run Bayesian Optimization
    bo = BayesianOptimization(
        bounds=bounds,
        acquisition="ei",  # Expected Improvement
        xi=0.01,
        n_initial=10,
        n_opt_restarts=20,
        random_state=42,
    )

    result = bo.run(branin, n_iter=20, verbose=True)

    print(f"\nBO found: x={result['best_x'].round(6)}, f(x)={result['best_y']:.6f}")
    print(f"True minimum: f(x*)={f_min:.6f}")
    print(f"Gap: {result['best_y'] - f_min:.6f}")

    # Visualize
    _plot_branin(bo, f_min)


def _plot_branin(bo, f_min: float):
    """Plot the Branin function with BO trajectory."""
    bounds = branin_bounds()

    # Create grid
    x1 = np.linspace(bounds[0, 0], bounds[0, 1], 200)
    x2 = np.linspace(bounds[1, 0], bounds[1, 1], 200)
    X1, X2 = np.meshgrid(x1, x2)
    X_grid = np.column_stack([X1.ravel(), X2.ravel()])

    # Evaluate function on grid
    Y = np.array([branin(x) for x in X_grid]).reshape(X1.shape)

    # Get GP posterior
    mu, var = bo.gp.predict(X_grid, return_variance=True)
    mu = mu.reshape(X1.shape)
    var = var.reshape(X1.shape)

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Contour of function values
    ax = axes[0]
    contour = ax.contourf(X1, X2, Y, levels=50, cmap="viridis")
    ax.plot(x_opt[:, 0], x_opt[:, 1], "r*", markersize=15, label="True minima")
    if len(bo.X_train) > 0:
        X_arr = np.array(bo.X_train)
        ax.scatter(X_arr[:, 0], X_arr[:, 1], c="red", s=50, marker="x", label="BO samples")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title("Branin Function")
    ax.legend()
    plt.colorbar(contour, ax=ax)

    # Contour of GP predictive mean
    ax = axes[1]
    contour = ax.contourf(X1, X2, mu, levels=50, cmap="viridis")
    if len(bo.X_train) > 0:
        X_arr = np.array(bo.X_train)
        ax.scatter(X_arr[:, 0], X_arr[:, 1], c="red", s=50, marker="x", label="BO samples")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title("GP Predictive Mean")
    ax.legend()
    plt.colorbar(contour, ax=ax)

    # Contour of GP predictive variance
    ax = axes[2]
    contour = ax.contourf(X1, X2, np.sqrt(var), levels=50, cmap="magma")
    if len(bo.X_train) > 0:
        X_arr = np.array(bo.X_train)
        ax.scatter(X_arr[:, 0], X_arr[:, 1], c="red", s=50, marker="x", label="BO samples")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title("GP Predictive Std Dev")
    ax.legend()
    plt.colorbar(contour, ax=ax)

    plt.tight_layout()
    plt.savefig("examples/output_branin.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: examples/output_branin.png")

    # Plot convergence
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(bo.best_y_history, "b-o", linewidth=2, markersize=8)
    ax.axhline(y=f_min, color="r", linestyle="--", label=f"True minimum = {f_min:.4f}")
    ax.set_xlabel("BO Iteration")
    ax.set_ylabel("Best f(x)")
    ax.set_title("Branin Optimization Convergence")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("examples/output_branin_convergence.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: examples/output_branin_convergence.png")


if __name__ == "__main__":
    main()
