"""
Hyperparameter optimization for acquisition function maximization.

In Bayesian Optimization, after computing the GP posterior, we need to
find the point x that maximizes the acquisition function:

    x_{next} = argmax_x alpha(x)

This is a non-convex optimization problem that typically requires
local optimization methods. We use a multi-start L-BFGS-B approach:

1. Generate multiple random starting points
2. Run local optimization from each starting point
3. Return the best result

This helps avoid poor local optima in the acquisition function.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Tuple, Callable, Optional


def maximize_acquisition(
    acquisition_fn: Callable,
    bounds: np.ndarray,
    gp: Optional = None,
    X_train: Optional[np.ndarray] = None,
    y_train: Optional[np.ndarray] = None,
    n_restarts: int = 20,
    method: str = "L-BFGS-B",
    acquisition_params: Optional[dict] = None,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, float]:
    """Maximize an acquisition function using multi-start optimization.

    This function finds the point that maximizes the acquisition function
    by trying multiple random starting points and running local optimization
    from each.

    The multi-start strategy is crucial because acquisition functions are
    typically non-convex and have multiple local optima.

    Args:
        acquisition_fn: Function to maximize. Takes (x,) and returns scalar.
            x should be 1D array, returns scalar.
        bounds: Array of shape (d, 2) with (min, max) for each dimension.
        gp: Gaussian Process object (optional, used for prediction).
        X_train: Training inputs (optional, for GP prediction).
        y_train: Training outputs (optional, for GP prediction).
        n_restarts: Number of random starting points.
        method: Optimization method (default: 'L-BFGS-B' for bounded).
        acquisition_params: Extra parameters for acquisition function.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (best_x, best_value) where best_x is shape (d,) and
        best_value is the maximum acquisition value.
    """
    rng = np.random.RandomState(random_state)
    d = bounds.shape[0]

    # Transform bounds for optimization
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    best_x = None
    best_value = -np.inf

    # Compute acquisition at random starting points for warm start
    starts = rng.uniform(lower, upper, size=(n_restarts, d))

    for i, x0 in enumerate(starts):
        # Bounds for this restart
        bounds_i = list(zip(lower, upper))

        result = minimize(
            lambda x: -acquisition_fn(x, gp, X_train, y_train, **(acquisition_params or {})),
            x0,
            method=method,
            bounds=bounds_i,
            options={"maxiter": 200, "ftol": 1e-9},
        )

        if result.fun < -best_value:
            best_x = result.x
            best_value = -result.fun

    return best_x, best_value


def optimize_acquisition_with_gp(
    X_train: np.ndarray,
    y_train: np.ndarray,
    gp,
    acquisition_fn: Callable,
    bounds: np.ndarray,
    n_restarts: int = 20,
    n_candidates: int = 50,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, float]:
    """Optimize acquisition function using GP predictions.

    Combines GP prediction with acquisition optimization:
    1. Sample candidate points via Latin Hypercube Sampling
    2. Evaluate acquisition at candidates
    3. Refine top candidates with local optimization

    This two-phase approach is more efficient than pure multi-start
    optimization because it first narrows the search to promising regions.

    Args:
        X_train: Training inputs of shape (n, d)
        y_train: Training outputs of shape (n,)
        gp: Fitted Gaussian Process
        acquisition_fn: Acquisition function (x, mu, sigma, **params) -> value
        bounds: Array of shape (d, 2) with (min, max) for each dimension
        n_restarts: Number of local optimization restarts
        n_candidates: Number of candidate points to evaluate
        random_state: Random seed

    Returns:
        Tuple of (best_x, best_value)
    """
    rng = np.random.RandomState(random_state)
    d = bounds.shape[0]
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    # Phase 1: Generate candidates via Latin Hypercube Sampling
    candidates = latin_hypercube_sampling(n_candidates, d, lower, upper, rng)

    # Evaluate acquisition at all candidates
    mu, sigma = gp.predict(candidates, return_variance=True)
    sigma = np.sqrt(sigma)

    acquisition_values = np.array([
        acquisition_fn(candidates[i], mu[i], sigma[i])
        for i in range(n_candidates)
    ])

    # Find top candidates for local refinement
    n_top = min(n_restarts, n_candidates)
    top_indices = np.argsort(acquisition_values)[-n_top:]
    top_candidates = candidates[top_indices]

    # Phase 2: Local optimization from top candidates
    best_x = None
    best_value = -np.inf

    for x0 in top_candidates:
        bounds_i = list(zip(lower, upper))
        result = minimize(
            lambda x: -acquisition_fn(x, *gp.predict(x.reshape(1, -1))),
            x0,
            method="L-BFGS-B",
            bounds=bounds_i,
            options={"maxiter": 200, "ftol": 1e-9},
        )

        if result.fun < -best_value:
            # Recompute acquisition value with full GP prediction
            x_opt = result.x
            mu_opt, sigma_opt = gp.predict(x_opt.reshape(1, -1))
            value = acquisition_fn(x_opt, mu_opt[0], np.sqrt(sigma_opt[0]))

            best_x = x_opt
            best_value = value

    return best_x, best_value


def latin_hypercube_sampling(
    n_samples: int,
    n_dims: int,
    lower: np.ndarray,
    upper: np.ndarray,
    rng: Optional[np.random.RandomState] = None,
) -> np.ndarray:
    """Generate Latin Hypercube Sample points.

    LHS ensures that each dimension is uniformly sampled while maintaining
    space-filling properties. This is superior to pure random sampling for
    initializing optimization.

    For each dimension:
    1. Divide [0, 1] into n_samples equal intervals
    2. Place one point uniformly within each interval
    3. Randomly permute across dimensions

    Args:
        n_samples: Number of samples
        n_dims: Number of dimensions
        lower: Lower bounds of shape (n_dims,)
        upper: Upper bounds of shape (n_dims,)
        rng: Random state

    Returns:
        LHS points of shape (n_samples, n_dims)
    """
    if rng is None:
        rng = np.random.RandomState()

    # Generate base LHS in [0, 1]
    points = np.zeros((n_samples, n_dims))
    for j in range(n_dims):
        # Divide unit interval into n_samples bins
        bins = np.arange(n_samples)
        # Random offset within each bin
        offsets = rng.uniform(0, 1, size=n_samples)
        # One point per bin
        points[:, j] = (bins + offsets) / n_samples

    # Random permutation for each dimension
    for j in range(n_dims):
        rng.shuffle(points[:, j])

    # Scale to bounds
    points = lower + (upper - lower) * points

    return points


def optimize_kernel_hyperparameters(
    gp: "GaussianProcess",
    X: np.ndarray,
    y: np.ndarray,
    bounds: np.ndarray,
    n_restarts: int = 10,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, float]:
    """Optimize GP kernel hyperparameters by maximizing log marginal likelihood.

    The kernel hyperparameters (length_scale, signal_variance, etc.) control
    the GP's prior assumptions. We optimize them by maximizing:

        log p(y | X, theta) = -0.5 * y^T K^{-1} y - 0.5 * log|K| - n/2 log(2pi)

    This is the marginal likelihood (evidence), which provides a natural
    Occam's razor: it rewards good fit but penalizes unnecessary complexity.

    Args:
        gp: Gaussian Process object
        X: Training inputs of shape (n, d)
        y: Training outputs of shape (n,)
        bounds: Array of shape (n_params, 2) with hyperparameter bounds
        n_restarts: Number of random restarts
        random_state: Random seed

    Returns:
        Tuple of (best_hyperparams, best_log_ml)
    """
    rng = np.random.RandomState(random_state)
    lower = bounds[:, 0]
    upper = bounds[:, 1]
    d = bounds.shape[0]

    best_theta = None
    best_log_ml = -np.inf

    for _ in range(n_restarts):
        # Random starting point in log-space for positivity
        theta = rng.uniform(lower, upper)

        bounds_i = list(zip(lower, upper))
        result = minimize(
            lambda theta: -_log_marginal_likelihood(theta, gp.kernel, X, y),
            theta,
            method="L-BFGS-B",
            bounds=bounds_i,
            options={"maxiter": 100, "ftol": 1e-8},
        )

        if result.fun < -best_log_ml:
            best_theta = result.x
            best_log_ml = -result.fun

    return best_theta, best_log_ml


def _log_marginal_likelihood(theta: np.ndarray, kernel: "Kernel", X: np.ndarray, y: np.ndarray) -> float:
    """Compute negative log marginal likelihood for a given kernel parameterization.

    Args:
        theta: Kernel hyperparameters (length_scale, signal_variance, ...)
        kernel: Kernel object to update
        X: Training inputs
        y: Training outputs

    Returns:
        Negative log marginal likelihood
    """
    # Save original values
    orig_ls = kernel.length_scale
    orig_sv = kernel.signal_variance

    # Update kernel parameters
    kernel.length_scale = theta[0]
    kernel.signal_variance = theta[1]

    # Compute log marginal likelihood
    n = X.shape[0]
    K = kernel(X, X)
    K += 1e-6 * np.eye(n)  # noise

    try:
        L = np.linalg.cholesky(K)
        alpha = np.linalg.solve(K, y)
        log_ml = -0.5 * y @ alpha - 0.5 * np.sum(np.log(np.diag(L))) - 0.5 * n * np.log(2 * np.pi)
    except np.linalg.LinAlgError:
        log_ml = -np.inf

    # Restore original values
    kernel.length_scale = orig_ls
    kernel.signal_variance = orig_sv

    return -log_ml  # Return negative for minimization
