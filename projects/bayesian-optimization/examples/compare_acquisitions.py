"""
Example 3: Compare acquisition functions on multiple benchmarks.

This example runs BO with all three acquisition functions (EI, UCB, PI)
on multiple benchmark functions to compare their performance.

Key comparisons:
- Expected Improvement (EI): balances exploration and exploitation
- Upper Confidence Bound (UCB): theoretically grounded, no f_best needed
- Probability of Improvement (PI): simplest, but can be too greedy
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.benchmarks import branin, branin_bounds, hartmann, hartmann_bounds
from src.bo_loop import BayesianOptimization


def compare_acquisitions(objective, bounds, f_min, name, n_iter=25):
    """Compare all acquisition functions on a benchmark.

    Args:
        objective: Objective function
        bounds: Search bounds
        f_min: True minimum value
        name: Benchmark name for titles
        n_iter: Number of BO iterations

    Returns:
        Dictionary of results per acquisition function
    """
    results = {}

    for acq in ["ei", "ucb", "pi"]:
        bo = BayesianOptimization(
            bounds=bounds,
            acquisition=acq,
            xi=0.01 if acq in ("ei", "pi") else None,
            beta=2.0 if acq == "ucb" else None,
            n_initial=10,
            n_opt_restarts=15,
            random_state=42,
        )
        result = bo.run(objective, n_iter=n_iter, verbose=False)
        results[acq] = result

        print(f"  {acq.upper()}: final best = {result['best_y']:.6f}, "
              f"gap = {result['best_y'] - f_min:.6f}")

    return results


def main():
    """Run acquisition function comparison on Branin and Hartmann."""
    print("=== Acquisition Function Comparison ===\n")

    # Branin comparison
    print("--- Branin Function ---")
    branin_results = compare_acquisitions(branin, branin_bounds(), 0.397887, "Branin", n_iter=25)

    # Hartmann comparison
    print("\n--- Hartmann Function (d=6) ---")
    hartmann_results = compare_acquisitions(
        hartmann, hartmann_bounds(6), -3.322371, "Hartmann", n_iter=30
    )

    # Plot comparison
    _plot_comparison(branin_results, hartmann_results)


def _plot_comparison(branin_results, hartmann_results):
    """Plot comparison of acquisition functions."""
    acqs = ["ei", "ucb", "pi"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, results, name in [
        (axes[0], branin_results, "Branin"),
        (axes[1], hartmann_results, "Hartmann"),
    ]:
        for acq, color in zip(acqs, colors):
            history = results[acq]["best_y_history"]
            ax.plot(history, f"-{acq[0]}", label=acq.upper(),
                    linewidth=2, alpha=0.8)

        ax.set_title(name)
        ax.set_xlabel("BO Iteration")
        ax.set_ylabel("Best f(x)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("examples/output_acquisition_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nSaved: examples/output_acquisition_comparison.png")


if __name__ == "__main__":
    main()
