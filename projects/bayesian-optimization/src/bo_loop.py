"""
Bayesian Optimization main loop.

Bayesian Optimization is a sequential design strategy for global optimization
of black-box functions. The key idea is to build a probabilistic surrogate
model (Gaussian Process) of the objective function and use an acquisition
function to decide where to sample next.

Algorithm overview:

    1. Initialize: Sample n_init points uniformly at random
    2. For t = 1 to n_iter:
        a. Fit GP to observed data D_t = {(x_i, y_i)}_{i=1}^{t+n_init-1}
        b. Compute acquisition function alpha(x) using GP posterior
        c. Find x_{t+1} = argmax_x alpha(x)
        d. Evaluate objective: y_{t+1} = f(x_{t+1}) + noise
        e. Update: D_{t+1} = D_t U {x_{t+1}, y_{t+1}}
    3. Return best observed point

The acquisition function balances:
- Exploitation: sample near current best (high predicted value)
- Exploration: sample where uncertainty is high (large predictive variance)

This tradeoff is controlled by hyperparameters like xi (for EI) or beta (for UCB).
"""

import numpy as np
from typing import Optional, Callable, List, Tuple, Dict
from .gaussian_process import GaussianProcess
from .acquisition import expected_improvement, upper_confidence_bound, probability_of_improvement
from .optimization import maximize_acquisition, optimize_acquisition_with_gp, latin_hypercube_sampling
from .noise_model import NoiseModel
from .kernel import RBFKernel, MaternKernel


class BayesianOptimization:
    """Bayesian Optimization loop for black-box function optimization.

    This class implements the core BO algorithm with:
    - Gaussian Process surrogate model
    - Multiple acquisition functions (EI, UCB, PI)
    - Kernel hyperparameter optimization
    - Noise modeling
    - Tracking of optimization trajectory
    """

    def __init__(
        self,
        bounds: np.ndarray,
        acquisition: str = "ei",
        kernel: Optional[object] = None,
        noise_variance: float = 0.01,
        xi: float = 0.01,
        beta: float = 2.0,
        n_initial: int = 10,
        n_opt_restarts: int = 20,
        random_state: Optional[int] = None,
    ):
        """Initialize Bayesian Optimization.

        Args:
            bounds: Array of shape (d, 2) with (min, max) for each dimension
            acquisition: Acquisition function name ('ei', 'ucb', 'pi')
            kernel: Kernel function (default: MaternKernel with nu=2.5)
            noise_variance: Observation noise variance
            xi: Exploration parameter for EI and PI
            beta: Exploration parameter for UCB
            n_initial: Number of initial random samples
            n_opt_restarts: Number of restarts for acquisition maximization
            random_state: Random seed
        """
        self.bounds = np.asarray(bounds)
        self.d = self.bounds.shape[0]  # dimensionality
        self.acquisition = acquisition
        self.xi = xi
        self.beta = beta
        self.n_initial = n_initial
        self.n_opt_restarts = n_opt_restarts
        self.random_state = random_state

        # GP model
        self.gp = GaussianProcess(
            kernel=kernel or MaternKernel(nu=2.5),
            noise_variance=noise_variance,
        )
        self.noise_model = NoiseModel(noise_variance)

        # Tracking
        self.X_train: List[np.ndarray] = []  # all training points
        self.y_train: List[float] = []  # all training values
        self.X_candidates: Optional[np.ndarray] = None
        self.y_candidates: Optional[np.ndarray] = None
        self.history: List[Dict] = []  # per-iteration history

        # Optimization results
        self.best_x: Optional[np.ndarray] = None
        self.best_y: float = np.inf  # for minimization
        self.best_y_history: List[float] = []

        # Acquisition function values at candidates
        self.acquisition_values: Optional[np.ndarray] = None

    def _initialize(self) -> None:
        """Generate initial design points using Latin Hypercube Sampling."""
        rng = np.random.RandomState(self.random_state)
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        self.X_candidates = latin_hypercube_sampling(
            self.n_initial, self.d, lower, upper, rng
        )
        self.acquisition_values = np.zeros(self.n_initial)

    def _get_acquisition_fn(self) -> Callable:
        """Get the acquisition function based on current settings."""
        if self.acquisition.lower() == "ei":
            return expected_improvement
        elif self.acquisition.lower() == "ucb":
            return upper_confidence_bound
        elif self.acquisition.lower() == "pi":
            return probability_of_improvement
        else:
            raise ValueError(f"Unknown acquisition function: {self.acquisition}")

    def _compute_acquisition(self, X: np.ndarray) -> np.ndarray:
        """Compute acquisition function values at given points.

        Args:
            X: Points of shape (m, d)

        Returns:
            Acquisition values of shape (m,)
        """
        mu, sigma = self.gp.predict(X, return_variance=True)
        sigma = np.sqrt(np.maximum(sigma, 1e-10))

        if self.acquisition.lower() == "ei":
            return expected_improvement(X, mu, sigma, self.best_y, self.xi)
        elif self.acquisition.lower() == "ucb":
            return upper_confidence_bound(X, mu, sigma, self.beta)
        elif self.acquisition.lower() == "pi":
            return probability_of_improvement(X, mu, sigma, self.best_y, self.xi)

    def _optimize_acquisition(self) -> np.ndarray:
        """Find the point that maximizes the acquisition function.

        Uses multi-start L-BFGS-B optimization from random starting points.

        Returns:
            Optimal point of shape (d,)
        """
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]

        # Use the current candidates as starting points
        if self.X_candidates is not None:
            # Sort candidates by acquisition value
            candidate_indices = np.argsort(self.acquisition_values)[-5:]
            x_starts = self.X_candidates[candidate_indices]
        else:
            rng = np.random.RandomState(self.random_state)
            x_starts = rng.uniform(lower, upper, size=(5, self.d))

        best_x = None
        best_value = -np.inf

        for x0 in x_starts:
            bounds_i = list(zip(lower, upper))
            result = minimize_acquisition_from_start(
                x0, self.gp, self.acquisition,
                self.best_y, self.xi, self.beta, bounds_i
            )
            if result["value"] > best_value:
                best_x = result["x"]
                best_value = result["value"]

        return best_x

    def run(self, objective_fn: Callable, n_iter: int = 20, verbose: bool = True) -> Dict:
        """Run the Bayesian Optimization loop.

        Args:
            objective_fn: Black-box function to minimize. Takes (x,) -> float
            n_iter: Number of BO iterations (after initial sampling)
            verbose: Print progress

        Returns:
            Dictionary with optimization results
        """
        # Initialize
        self._initialize()

        # Initial sampling
        if verbose:
            print(f"=== Bayesian Optimization ({self.acquisition.upper()}) ===")
            print(f"Dimension: {self.d}, Initial samples: {self.n_initial}, Iterations: {n_iter}")
            print()

        print("Phase 1: Initial sampling (Latin Hypercube)")
        for i in range(self.n_initial):
            x = self.X_candidates[i]
            y = objective_fn(x)
            self.X_train.append(x.copy())
            self.y_train.append(y)

            if y < self.best_y:
                self.best_y = y
                self.best_x = x.copy()

            self.best_y_history.append(self.best_y)

            if verbose and (i + 1) % 5 == 0 or i == 0:
                print(f"  Initial sample {i+1}/{self.n_initial}: x={x.round(4)}, f(x)={y:.6f}, best={self.best_y:.6f}")

        print()
        print(f"Best after initialization: x={self.best_x.round(4)}, f(x)={self.best_y:.6f}")
        print()

        # BO iterations
        print("Phase 2: Bayesian Optimization iterations")
        for t in range(n_iter):
            # Update GP
            X_arr = np.array(self.X_train)
            y_arr = np.array(self.y_train)
            self.gp.fit(X_arr, y_arr)

            # Compute acquisition at candidates
            mu, sigma = self.gp.predict(self.X_candidates, return_variance=True)
            sigma = np.sqrt(np.maximum(sigma, 1e-10))

            self.acquisition_values = self._compute_acquisition(self.X_candidates)

            # Find next point
            next_idx = np.argmax(self.acquisition_values)
            x_next = self.X_candidates[next_idx]

            # Evaluate objective
            y_next = objective_fn(x_next)

            # Update
            self.X_train.append(x_next.copy())
            self.y_train.append(y_next)
            self.X_candidates = np.delete(self.X_candidates, next_idx, axis=0)
            self.acquisition_values = np.delete(self.acquisition_values, next_idx)

            if y_next < self.best_y:
                self.best_y = y_next
                self.best_x = x_next.copy()

            self.best_y_history.append(self.best_y)

            # Record history
            self.history.append({
                "iteration": t + 1,
                "x": x_next.copy(),
                "y": y_next,
                "best_y": self.best_y,
                "best_x": self.best_x.copy(),
                "log_ml": self.gp.get_log_marginal_likelihood(),
            })

            if verbose and (t + 1) % 5 == 0 or t == 0:
                print(f"  Iter {t+1}/{n_iter}: x={x_next.round(4)}, f(x)={y_next:.6f}, "
                      f"best={self.best_y:.6f}, log-ML={self.gp.get_log_marginal_likelihood():.2f}")

        if verbose:
            print()
            print(f"=== Optimization Complete ===")
            print(f"Best solution: x={self.best_x.round(6)}, f(x)={self.best_y:.6f}")
            print(f"Total evaluations: {len(self.X_train)}")

        return self.get_result()

    def get_result(self) -> Dict:
        """Get optimization results.

        Returns:
            Dictionary with results
        """
        return {
            "best_x": self.best_x,
            "best_y": self.best_y,
            "X_history": np.array(self.X_train),
            "y_history": np.array(self.y_train),
            "best_y_history": np.array(self.best_y_history),
            "history": self.history,
            "gp": self.gp,
        }

    def get_gp(self) -> GaussianProcess:
        """Get the current GP model."""
        return self.gp


def minimize_acquisition_from_start(
    x0: np.ndarray,
    gp: GaussianProcess,
    acquisition: str,
    best_y: float,
    xi: float,
    beta: float,
    bounds: list,
) -> Dict:
    """Minimize negative acquisition from a single starting point.

    Args:
        x0: Starting point
        gp: Fitted Gaussian Process
        acquisition: Acquisition function name
        best_y: Current best value (for minimization)
        xi: EI/PI exploration parameter
        beta: UCB exploration parameter
        bounds: Optimization bounds

    Returns:
        Dictionary with 'x' (optimal point) and 'value' (max acquisition)
    """
    from scipy.optimize import minimize

    def neg_acquisition(x):
        x = np.atleast_1d(x)
        mu, sigma = gp.predict(x.reshape(1, -1), return_variance=True)
        sigma = np.sqrt(np.maximum(sigma, 1e-10))

        if acquisition.lower() == "ei":
            return -expected_improvement(x.reshape(1, -1), mu, sigma, best_y, xi)[0]
        elif acquisition.lower() == "ucb":
            return -upper_confidence_bound(x.reshape(1, -1), mu, sigma, beta)[0]
        elif acquisition.lower() == "pi":
            return -probability_of_improvement(x.reshape(1, -1), mu, sigma, best_y, xi)[0]

    result = minimize(neg_acquisition, x0, method="L-BFGS-B", bounds=bounds)

    # Recompute acquisition at optimum
    mu, sigma = gp.predict(result.x.reshape(1, -1), return_variance=True)
    sigma = np.sqrt(np.maximum(sigma, 1e-10))
    if acquisition.lower() == "ei":
        value = expected_improvement(result.x.reshape(1, -1), mu, sigma, best_y, xi)[0]
    elif acquisition.lower() == "ucb":
        value = upper_confidence_bound(result.x.reshape(1, -1), mu, sigma, beta)[0]
    elif acquisition.lower() == "pi":
        value = probability_of_improvement(result.x.reshape(1, -1), mu, sigma, best_y, xi)[0]

    return {"x": result.x, "value": value}
