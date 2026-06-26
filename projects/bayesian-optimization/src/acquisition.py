"""
Acquisition functions for Bayesian Optimization.

An acquisition function alpha(x) quantifies the utility of evaluating
the objective function at point x. It balances:

- Exploration: sampling where uncertainty is high (uncertainty > 0)
- Exploitation: sampling where predicted value is good (mu(x) is good)

Common acquisition functions:

1. Expected Improvement (EI): Expected amount by which f(x) improves
   over the current best. Integrates over the GP posterior.

2. Upper Confidence Bound (UCB): mu(x) + beta * sigma(x). Simple
   and theoretically grounded with regret bounds.

3. Probability of Improvement (PI): P(f(x) > f_best). Most basic
   acquisition, but doesn't account for magnitude of improvement.

The acquisition function is optimized at each BO iteration to select
the next evaluation point, making BO a "smart" optimizer that focuses
on promising regions.
"""

import numpy as np
from scipy.stats import norm
from typing import Tuple


def expected_improvement(
    X: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    f_best: float,
    xi: float = 0.0,
) -> np.ndarray:
    """Expected Improvement acquisition function.

    EI(x) = E[max(0, f(x) - f_best)]
          = (mu(x) - f_best + xi) * Phi(Z) + sigma(x) * phi(Z)

    where Z = (mu(x) - f_best + xi) / sigma(x),
          Phi = standard normal CDF, phi = standard normal PDF

    EI naturally balances exploration and exploitation:
    - When sigma is large (high uncertainty), the phi(Z) term dominates
      encouraging exploration
    - When mu is much larger than f_best, the Phi(Z) term dominates
      encouraging exploitation

    For sigma -> 0, EI -> max(0, mu - f_best) (greedy exploitation)

    Args:
        X: Points to evaluate of shape (m, d)
        mu: Predictive mean at X of shape (m,)
        sigma: Predictive std dev at X of shape (m,)
        f_best: Current best observed value (for minimization, the minimum)
        xi: Exploration parameter (xi > 0 encourages exploration)

    Returns:
        EI values of shape (m,)
    """
    # For minimization, improvement = f_best - f(x)
    # We want to maximize the expected improvement over f_best
    # EI = E[max(0, f_best - f(x))]
    # For GP posterior f(x) ~ N(mu, sigma^2):
    # EI = (f_best - mu + xi) * Phi(z) + sigma * phi(z)
    # where z = (f_best - mu + xi) / sigma

    # Handle case where sigma is very small (already observed point)
    mask = sigma > 1e-10
    ei = np.zeros_like(mu)

    if np.any(mask):
        sigma_masked = sigma[mask]
        mu_masked = mu[mask]

        z = (f_best - mu_masked + xi) / sigma_masked

        Phi_z = norm.cdf(z)
        phi_z = norm.pdf(z)

        ei[mask] = (f_best - mu_masked + xi) * Phi_z + sigma_masked * phi_z

    return ei


def upper_confidence_bound(
    X: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    beta: float = 2.0,
) -> np.ndarray:
    """Upper Confidence Bound acquisition function.

    UCB(x) = mu(x) + beta * sigma(x)

    The parameter beta controls the exploration-exploitation tradeoff:
    - Large beta: more exploration (prioritize uncertain regions)
    - Small beta: more exploitation (prioritize high-mean regions)

    Theoretical justification: beta = 2 * log(n) gives sublinear regret
    bounds for GP-UCB.

    UCB is simpler than EI and doesn't require knowing f_best,
    making it useful for maximization problems.

    Args:
        X: Points to evaluate of shape (m, d)
        mu: Predictive mean at X of shape (m,)
        sigma: Predictive std dev at X of shape (m,)
        beta: Exploration parameter (beta > 0)

    Returns:
        UCB values of shape (m,)
    """
    return mu + beta * sigma


def probability_of_improvement(
    X: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    f_best: float,
    xi: float = 0.0,
) -> np.ndarray:
    """Probability of Improvement acquisition function.

    PI(x) = P(f(x) > f_best)
          = Phi((mu(x) - f_best) / sigma(x))

    PI is the simplest acquisition function but has a key limitation:
    it only considers the probability of improvement, not the magnitude.
    This leads to PI concentrating around the current best point
    (where sigma is small but mu is close to f_best).

    The xi parameter adds exploration by requiring a minimum improvement.

    Args:
        X: Points to evaluate of shape (m, d)
        mu: Predictive mean at X of shape (m,)
        sigma: Predictive std dev at X of shape (m,)
        f_best: Current best observed value
        xi: Minimum improvement threshold

    Returns:
        PI values of shape (m,)
    """
    mask = sigma > 1e-10
    pi = np.zeros_like(mu)

    if np.any(mask):
        sigma_masked = sigma[mask]
        mu_masked = mu[mask]

        z = (mu_masked - f_best + xi) / sigma_masked
        pi[mask] = norm.cdf(z)

    return pi


def acquisition_function(
    X: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    name: str = "ei",
    **kwargs,
) -> np.ndarray:
    """Dispatch to the appropriate acquisition function.

    Args:
        X: Points to evaluate of shape (m, d)
        mu: Predictive mean at X of shape (m,)
        sigma: Predictive std dev at X of shape (m,)
        name: Acquisition function name ('ei', 'ucb', 'pi')
        **kwargs: Additional parameters for each acquisition function

    Returns:
        Acquisition values of shape (m,)

    Raises:
        ValueError: If unknown acquisition function name
    """
    if name.lower() == "ei":
        return expected_improvement(X, mu, sigma, kwargs.get("f_best", 0.0), kwargs.get("xi", 0.0))
    elif name.lower() == "ucb":
        return upper_confidence_bound(X, mu, sigma, kwargs.get("beta", 2.0))
    elif name.lower() == "pi":
        return probability_of_improvement(X, mu, sigma, kwargs.get("f_best", 0.0), kwargs.get("xi", 0.0))
    else:
        raise ValueError(f"Unknown acquisition function: {name}. Use 'ei', 'ucb', or 'pi'.")
