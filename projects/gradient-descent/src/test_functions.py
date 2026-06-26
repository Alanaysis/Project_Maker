"""
Test functions for optimization benchmarking.

Standard test functions for evaluating optimizer performance:
- Sphere: convex, unimodal
- Rosenbrock: non-convex, narrow valley
- Rastrigin: multi-modal, periodic
- Ackley: multi-modal
- Beale: multi-modal
- Himmelblau: multi-modal
"""

import numpy as np


def sphere(params):
    """Sphere function: f(x) = sum(x_i^2)

    Global minimum: f(0, 0, ...) = 0

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays. Flattened for computation.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    return np.sum(flat ** 2)


def sphere_grad(params):
    """Gradient of the Sphere function."""
    flat = np.concatenate([p.flatten() for p in params])
    grad_flat = 2 * flat
    grads = []
    offset = 0
    for p in params:
        size = p.size
        grads.append(grad_flat[offset:offset + size].reshape(p.shape))
        offset += size
    return grads


def rosenbrock(params):
    """Rosenbrock function: f(x,y) = (a-x)^2 + b*(y-x^2)^2

    Standard: a=1, b=100. Global minimum: f(1, 1) = 0.

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    a, b = 1.0, 100.0
    total = 0.0
    for i in range(0, len(flat) - 1, 2):
        total += (a - flat[i]) ** 2 + b * (flat[i + 1] - flat[i] ** 2) ** 2
    return total


def rosenbrock_grad(params):
    """Gradient of the Rosenbrock function."""
    flat = np.concatenate([p.flatten() for p in params])
    a, b = 1.0, 100.0
    grad_flat = np.zeros_like(flat)
    for i in range(0, len(flat) - 1, 2):
        dx = -2 * (a - flat[i]) - 4 * b * flat[i] * (flat[i + 1] - flat[i] ** 2)
        dy = 2 * b * (flat[i + 1] - flat[i] ** 2)
        grad_flat[i] = dx
        grad_flat[i + 1] = dy
    grads = []
    offset = 0
    for p in params:
        size = p.size
        grads.append(grad_flat[offset:offset + size].reshape(p.shape))
        offset += size
    return grads


def rastrigin(params):
    """Rastrigin function: f(x) = A*n + sum(x_i^2 - A*cos(2*pi*x_i))

    A=10. Global minimum: f(0, 0, ...) = 0.

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    A = 10.0
    n = len(flat)
    return A * n + np.sum(flat ** 2 - A * np.cos(2 * np.pi * flat))


def rastrigin_grad(params):
    """Gradient of the Rastrigin function."""
    flat = np.concatenate([p.flatten() for p in params])
    A = 10.0
    grad_flat = 2 * flat + 2 * np.pi * A * np.sin(2 * np.pi * flat)
    grads = []
    offset = 0
    for p in params:
        size = p.size
        grads.append(grad_flat[offset:offset + size].reshape(p.shape))
        offset += size
    return grads


def ackley(params):
    """Ackley function:
    f(x) = -a*exp(-b*sqrt(sum(x_i^2)/n)) - exp(sum(cos(c*x_i))/n) + a + e

    a=20, b=0.2, c=2*pi. Global minimum: f(0, 0, ...) = 0.

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    a, b, c = 20.0, 0.2, 2 * np.pi
    n = len(flat)
    term1 = -a * np.exp(-b * np.sqrt(np.sum(flat ** 2) / n))
    term2 = -np.exp(np.sum(np.cos(c * flat)) / n)
    return term1 + term2 + a + np.e


def ackley_grad(params):
    """Gradient of the Ackley function."""
    flat = np.concatenate([p.flatten() for p in params])
    a, b, c = 20.0, 0.2, 2 * np.pi
    n = len(flat)
    norm_term = np.sqrt(np.sum(flat ** 2) / n) + 1e-16
    exp_term1 = np.exp(-b * norm_term)
    exp_term2 = np.sum(np.cos(c * flat)) / n

    grad_flat = np.zeros_like(flat)
    # Gradient of term1
    grad_flat += -a * exp_term1 * (-b) * (1 / (2 * norm_term)) * (2 * flat / n)
    # Gradient of term2
    grad_flat += -(-np.sin(c * flat) * c) / n

    grads = []
    offset = 0
    for p in params:
        size = p.size
        grads.append(grad_flat[offset:offset + size].reshape(p.shape))
        offset += size
    return grads


def beale(params):
    """Beale function:
    f(x,y) = (1.5-x+xy)^2 + (2.25-x+xy^2)^2 + (2.625-x+xy^3)^2

    Global minimum: f(3, 0.5) = 0.

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    x, y = flat[0], flat[1] if len(flat) > 1 else 0.0
    return ((1.5 - x + x * y) ** 2 +
            (2.25 - x + x * y ** 2) ** 2 +
            (2.625 - x + x * y ** 3) ** 2)


def beale_grad(params):
    """Gradient of the Beale function."""
    flat = np.concatenate([p.flatten() for p in params])
    x, y = flat[0], flat[1] if len(flat) > 1 else 0.0
    dx = 2 * (1.5 - x + x * y) * (-1 + y) + \
         2 * (2.25 - x + x * y ** 2) * (-1 + y ** 2) + \
         2 * (2.625 - x + x * y ** 3) * (-1 + y ** 3)
    dy = 2 * (1.5 - x + x * y) * x + \
         2 * (2.25 - x + x * y ** 2) * (2 * x * y) + \
         2 * (2.625 - x + x * y ** 3) * (3 * x * y ** 2)
    grads = [np.array([[dx]]), np.array([[dy]])]
    return grads


def himmelblau(params):
    """Himmelblau function:
    f(x,y) = (x^2+y-11)^2 + (x+y^2-7)^2

    Global minima at (3,2), (2.81,-3.13), (-2.81,3.13), (-3.58,-1.84).

    Parameters
    ----------
    params : list of np.ndarray
        Parameter arrays.

    Returns
    -------
    float
        Function value.
    """
    flat = np.concatenate([p.flatten() for p in params])
    x, y = flat[0], flat[1] if len(flat) > 1 else 0.0
    return ((x ** 2 + y - 11) ** 2 + (x + y ** 2 - 7) ** 2)


def himmelblau_grad(params):
    """Gradient of the Himmelblau function."""
    flat = np.concatenate([p.flatten() for p in params])
    x, y = flat[0], flat[1] if len(flat) > 1 else 0.0
    dx = 2 * (x ** 2 + y - 11) * 2 * x + 2 * (x + y ** 2 - 7)
    dy = 2 * (x ** 2 + y - 11) + 2 * (x + y ** 2 - 7) * 2 * y
    grads = [np.array([[dx]]), np.array([[dy]])]
    return grads


def get_test_function(name: str):
    """Get a test function and its gradient by name.

    Parameters
    ----------
    name : str
        Function name: 'sphere', 'rosenbrock', 'rastrigin', 'ackley',
        'beale', 'himmelblau'.

    Returns
    -------
    tuple
        (function, gradient_function)
    """
    functions = {
        'sphere': (sphere, sphere_grad),
        'rosenbrock': (rosenbrock, rosenbrock_grad),
        'rastrigin': (rastrigin, rastrigin_grad),
        'ackley': (ackley, ackley_grad),
        'beale': (beale, beale_grad),
        'himmelblau': (himmelblau, himmelblau_grad),
    }
    if name not in functions:
        raise ValueError(f"Unknown test function: {name}. Available: {list(functions.keys())}")
    return functions[name]


# Synthetic dataset generation utilities
def make_linear_data(n_samples=500, n_features=10, noise=0.1, seed=42):
    """Generate synthetic linear regression data.

    y = X @ w_true + noise

    Parameters
    ----------
    n_samples : int
        Number of samples.
    n_features : int
        Number of features.
    noise : float
        Noise level (standard deviation).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    tuple
        (X, y, w_true)
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features)
    w_true = rng.randn(n_features)
    y = X @ w_true + noise * rng.randn(n_samples)
    return X, y, w_true


def make_moon_data(n_samples=300, noise=0.1, seed=42):
    """Generate synthetic two-moons classification data.

    Parameters
    ----------
    n_samples : int
        Total samples (split evenly between two moons).
    noise : float
        Noise level.
    seed : int
        Random seed.

    Returns
    -------
    tuple
        (X, y)
    """
    rng = np.random.RandomState(seed)
    n_per_class = n_samples // 2

    # Upper moon
    theta1 = np.linspace(0, np.pi, n_per_class)
    X1 = np.column_stack([np.cos(theta1), np.sin(theta1)])
    y1 = np.ones(n_per_class)

    # Lower moon
    theta2 = np.linspace(0, np.pi, n_per_class)
    X2 = np.column_stack([1 - np.cos(theta2), -1 + np.sin(theta2)])
    y2 = np.zeros(n_per_class)

    X = np.vstack([X1, X2]) + noise * rng.randn(n_samples, 2)
    y = np.concatenate([y1, y2])

    return X, y


def make_spiral_data(n_samples=300, noise=0.1, seed=42):
    """Generate synthetic spiral classification data.

    Parameters
    ----------
    n_samples : int
        Total samples (split evenly between two spirals).
    noise : float
        Noise level.
    seed : int
        Random seed.

    Returns
    -------
    tuple
        (X, y)
    """
    rng = np.random.RandomState(seed)
    n_per_class = n_samples // 2

    X = np.zeros((n_samples, 2))
    y = np.zeros(n_samples, dtype=int)

    for i in range(n_per_class):
        r = i / n_per_class
        t = 1.75 * i / n_per_class * 2 * np.pi + np.pi / 2
        X[i] = [r * np.sin(t), r * np.cos(t)]
        y[i] = 0

        t2 = 1.75 * i / n_per_class * 2 * np.pi + np.pi / 2
        X[i + n_per_class] = [r * np.sin(t2) + 0.5, r * np.cos(t2) + 0.5]
        y[i + n_per_class] = 1

    X += noise * rng.randn(n_samples, 2)
    return X, y
