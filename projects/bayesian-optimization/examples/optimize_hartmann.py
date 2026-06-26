"""
Example 2: Optimize Hartmann function using Bayesian Optimization.

The Hartmann function is a standard benchmark for Bayesian Optimization.
It's a d-dimensional multimodal function with a known global minimum.

This example demonstrates:
- BO on higher-dimensional problems
- Using the Matern kernel (better for non-smooth functions)
- Comparing BO performance against the true optimum
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.benchmarks import hartmann, hartmann_bounds, hartmann_true_minimum
from src.bo_loop import BayesianOptimization


def main():
    """Run BO on the Hartmann function."""
    n_dim = 6
    bounds = hartmann_bounds(n_dim)
    f_min, x_opt = hartmann_true_minimum(n_dim)

    print("=== Hartmann Function Optimization (d=6) ===")
    print(f"True minimum: f(x*) = {f_min:.6f}")
    print(f"True minimizer: {x_opt.round(6)}")
    print()

    # Run BO with different acquisition functions
    for acq in ["ei", "ucb", "pi"]:
        print(f"\n--- Acquisition: {acq.upper()} ---")
        bo = BayesianOptimization(
            bounds=bounds,
            acquisition=acq,
            xi=0.01 if acq in ("ei", "pi") else None,
            beta=2.0 if acq == "ucb" else None,
            n_initial=10,
            n_opt_restarts=20,
            random_state=42,
        )

        result = bo.run(hartmann, n_iter=30, verbose=False)

        print(f"  BO found: f(x) = {result['best_y']:.6f}")
        print(f"  Gap from optimum: {result['best_y'] - f_min:.6f}")

    # Plot convergence for all acquisition functions
    _plot_hartmann_convergence(bounds, f_min)


def _plot_hartmann_convergence(bounds, f_min):
    """Plot convergence of different acquisition functions."""
    acqs = ["ei", "ucb", "pi"]
    colors = ["blue", "green", "red"]

    fig, ax = plt.subplots(figsize=(10, 6))

    for acq, color in zip(acqs, colors):
        bo = BayesianOptimization(
            bounds=bounds,
            acquisition=acq,
            xi=0.01 if acq in ("ei", "pi") else None,
            beta=2.0 if acq == "ucb" else None,
            n_initial=10,
            n_opt_restarts=20,
            random_state=42,
        )
        result = bo.run(hartmann, n_iter=30, verbose=False)

        ax.plot(result["best_y_history"], f"-{acq[0]}", label=f"{acq.upper()}",
                linewidth=2, alpha=0.8)

    ax.axhline(y=f_min, color="black", linestyle="--", linewidth=2,
               label=f"True minimum = {f_min:.4f}")
    ax.set_xlabel("BO Iteration", fontsize=12)
    ax.set_ylabel("Best f(x)", fontsize=12)
    ax.set_title("Hartmann Function: Acquisition Function Comparison", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("examples/output_hartmann_convergence.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: examples/output_hartmann_convergence.png")


if __name__ == "__main__":
    main()
