"""
Benchmark functions for Bayesian Optimization testing.

Standard test functions with known optima, used to evaluate BO algorithms:

1. Branin function: 2D, multimodal, cheap to evaluate
2. Hartmann function: d-dimensional, multimodal, standard for BO benchmarks
3. Booth, Rastrigin, Ackley: Additional test functions

These functions are "black boxes" - the BO algorithm has no knowledge
of their structure and must learn purely from function evaluations.
"""

import numpy as np
from typing import Tuple


def branin(x: np.ndarray) -> float:
    """Branin function (2D).

    A classic test function for optimization algorithms. It has three
    global minima at known locations, making it useful for testing
    global optimization algorithms.

    f(x) = a * (x2 - b * x1^2 + c * x1 - r)^2 + s * (1 - t) * cos(x1) + s

    Global minimum: f(x*) = 0.397887 at three points:
        (-pi, 12.275), (pi, 2.275), (9.42478, 2.475)

    Args:
        x: Input array of shape (2,)

    Returns:
        Function value
    """
    x1, x2 = x[0], x[1]

    a = 1.0
    b = 5.1 / (4.0 * np.pi ** 2)
    c = 5.0 / np.pi
    r = 6.0
    s = 10.0
    t = 1.0 / (8.0 * np.pi)

    term1 = a * (x2 - b * x1 ** 2 + c * x1 - r) ** 2
    term2 = s * (1 - t) * np.cos(x1) + s

    return float(term1 + term2)


def branin_bounds() -> np.ndarray:
    """Get bounds for the Branin function.

    Returns:
        Bounds array of shape (2, 2)
    """
    return np.array([
        [-5.0, 10.0],   # x1
        [0.0, 15.0],    # x2
    ])


def branin_true_minimum() -> Tuple[float, np.ndarray]:
    """Get the true minimum of the Branin function.

    Returns:
        Tuple of (minimum_value, optimal_points) where optimal_points
        is an array of the three global minimizers.
    """
    f_min = 0.397887
    x_opt = np.array([
        [-np.pi, 12.275],
        [np.pi, 2.275],
        [9.42478, 2.475],
    ])
    return f_min, x_opt


def hartmann(x: np.ndarray, n: int = 6) -> float:
    """Hartmann function (d-dimensional).

    A standard benchmark for Bayesian Optimization. It's a multimodal
    function with a known global minimum.

    f(x) = -sum_{i=1}^m alpha_i * sum_{j=1}^d B_{ij} * (x_j - A_{ij})^2

    where m=4 (number of terms), d=n (dimension), and alpha, A, B
    are fixed matrices.

    Global minimum for d=6: f(x*) = -3.32237 at x* = (0.20169, 0.15001,
    0.47687, 0.27533, 0.31165, 0.65730)

    Args:
        x: Input array of shape (d,)
        n: Dimensionality (default 6)

    Returns:
        Function value
    """
    # Hartmann coefficients (standard 4-term)
    alpha = np.array([1.0, 1.2, 3.0, 3.2])

    A = np.array([
        [3.0, 10.0, 30.0, 0.1, 10.0, 0.1],
        [0.1, 99.0, 99.0, 99.0, 99.0, 99.0],
        [10.0, 90.0, 90.0, 99.0, 1.0, 99.0],
        [0.1, 10.0, 99.0, 99.0, 99.0, 0.1],
    ]) / 100.0

    B = np.array([
        [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
        [0.1, 20.0, 20.0, 20.0, 20.0, 0.1],
        [1.0, 10.0, 10.0, 10.0, 10.0, 1.0],
        [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
    ])

    # Use first n dimensions of A and B
    A_n = A[:, :n]
    B_n = B[:, :n]

    # Normalize input to [0, 1]
    x_norm = np.clip(x / 100.0, 0.0, 1.0)

    # Compute sum_j B_ij * (x_j - A_ij)^2 for each term i
    diff = x_norm[np.newaxis, :] - A_n  # (4, n)
    inner = np.sum(B_n * diff ** 2, axis=1)  # (4,)

    return float(-np.sum(alpha * np.exp(-inner)))


def hartmann_bounds(n: int = 6) -> np.ndarray:
    """Get bounds for the Hartmann function.

    Args:
        n: Dimensionality

    Returns:
        Bounds array of shape (n, 2) for [0, 1]^n
    """
    return np.array([[0.0, 1.0]] * n)


def hartmann_true_minimum(n: int = 6) -> Tuple[float, np.ndarray]:
    """Get the true minimum of the Hartmann function.

    Args:
        n: Dimensionality

    Returns:
        Tuple of (minimum_value, optimal_point)
    """
    if n == 6:
        f_min = -3.322371
        x_opt = np.array([0.20169, 0.15001, 0.47687, 0.27533, 0.31165, 0.65730]) * 100.0
    elif n == 2:
        f_min = -3.8627
        x_opt = np.array([0.114614, 0.555721]) * 100.0
    elif n == 3:
        f_min = -3.8627
        x_opt = np.array([0.20169, 0.15001, 0.47687]) * 100.0
    else:
        f_min = -3.322371
        x_opt = np.array([0.20169, 0.15001, 0.47687, 0.27533, 0.31165, 0.65730]) * 100.0

    return f_min, x_opt


def booth(x: np.ndarray) -> float:
    """Booth function (2D).

    f(x) = (x1 + 2*x2 - 7)^2 + (2*x1 + x2 - 5)^2

    Global minimum: f(1, 3) = 0

    Args:
        x: Input array of shape (2,)

    Returns:
        Function value
    """
    return float((x[0] + 2 * x[1] - 7) ** 2 + (2 * x[0] + x[1] - 5) ** 2)


def booth_bounds() -> np.ndarray:
    """Get bounds for the Booth function."""
    return np.array([
        [-10.0, 10.0],
        [-10.0, 10.0],
    ])


def rastrigin(x: np.ndarray) -> float:
    """Rastrigin function (d-dimensional).

    A highly multimodal function, useful for testing global optimization.

    f(x) = 10*d + sum_{i=1}^d [x_i^2 - 10*cos(2*pi*x_i)]

    Global minimum: f(0) = 0 at origin.

    Args:
        x: Input array of shape (d,)

    Returns:
        Function value
    """
    d = len(x)
    return float(10 * d + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x)))


def rastrigin_bounds(n: int = 2) -> np.ndarray:
    """Get bounds for the Rastrigin function."""
    return np.array([[-5.12, 5.12]] * n)


def ackley(x: np.ndarray) -> float:
    """Ackley function (d-dimensional).

    A multimodal function with a nearly flat outer region and a deep
    central hole.

    f(x) = -20*exp(-0.2*sqrt(1/d * sum(x_i^2))) - exp(1/d * sum(cos(2*pi*x_i))) + 20 + e

    Global minimum: f(0) = 0 at origin.

    Args:
        x: Input array of shape (d,)

    Returns:
        Function value
    """
    d = len(x)
    term1 = -20 * np.exp(-0.2 * np.sqrt(np.sum(x ** 2) / d))
    term2 = -np.exp(np.sum(np.cos(2 * np.pi * x)) / d)
    return float(term1 + term2 + 20 + np.e)


def ackley_bounds(n: int = 2) -> np.ndarray:
    """Get bounds for the Ackley function."""
    return np.array([[-32.768, 32.768]] * n)


def get_benchmark(name: str, d: int = 6):
    """Get a benchmark function by name.

    Args:
        name: Benchmark name ('branin', 'hartmann', 'booth', 'rastrigin', 'ackley')
        d: Dimensionality (for d-dimensional functions)

    Returns:
        Tuple of (function, bounds, true_minimum_value, true_minimum_point)

    Raises:
        ValueError: If unknown benchmark name
    """
    benchmarks = {
        "branin": (branin, branin_bounds, branin_true_minimum),
        "hartmann": (hartmann, hartmann_bounds, hartmann_true_minimum),
        "booth": (booth, booth_bounds, lambda: (0.0, np.array([1.0, 3.0]))),
        "rastrigin": (rastrigin, lambda n=2: rastrigin_bounds(n), lambda: (0.0, np.zeros(2))),
        "ackley": (ackley, lambda n=2: ackley_bounds(n), lambda: (0.0, np.zeros(2))),
    }

    if name not in benchmarks:
        raise ValueError(f"Unknown benchmark: {name}. Available: {list(benchmarks.keys())}")

    fn, bounds_fn, min_fn = benchmarks[name]

    if name in ("hartmann", "rastrigin", "ackley"):
        bounds = bounds_fn(d)
    else:
        bounds = bounds_fn()

    min_result = min_fn()
    if callable(min_result):
        min_val, min_pt = min_result()
    else:
        min_val, min_pt = min_result

    return fn, bounds, min_val, min_pt
