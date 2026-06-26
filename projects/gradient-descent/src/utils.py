"""
Numerical gradient computation for verification.

Useful for checking that analytical gradients are correct:
    f'(x) ~ (f(x + h) - f(x - h)) / (2h)
"""

import numpy as np


def numerical_gradient(params, loss_fn, eps=1e-5):
    """Compute numerical gradient using central differences.

    f'(x_i) = (f(x + h*e_i) - f(x - h*e_i)) / (2h)

    Parameters
    ----------
    params : list of np.ndarray
        Current parameters.
    loss_fn : callable
        Loss function f(params) -> scalar.
    eps : float
        Step size for finite differences.

    Returns
    -------
    list of np.ndarray
        Numerical gradients with same shapes as params.
    """
    grads = []

    for i, p in enumerate(params):
        grad_p = np.zeros_like(p)
        for j in range(p.size):
            # Create perturbed params: copy all params, then modify element j of param i
            params_plus = [param.copy() for param in params]
            params_minus = [param.copy() for param in params]
            params_plus[i].ravel()[j] += eps
            params_minus[i].ravel()[j] -= eps
            loss_plus = loss_fn(params_plus)
            loss_minus = loss_fn(params_minus)
            grad_p.ravel()[j] = (loss_plus - loss_minus) / (2 * eps)
        grads.append(grad_p)
    return grads


def gradient_check(params, analytical_grads, loss_fn, eps=1e-5, threshold=1e-6):
    """Check analytical gradients against numerical gradients.

    Compares using relative error:
        error = |g_num - g_ana| / (|g_num| + |g_ana| + eps)

    Parameters
    ----------
    params : list of np.ndarray
        Current parameters.
    analytical_grads : list of np.ndarray
        Analytical gradients to verify.
    loss_fn : callable
        Loss function f(params) -> scalar.
    eps : float
        Step size for numerical gradient.
    threshold : float
        Maximum acceptable relative error.

    Returns
    -------
    tuple
        (max_error, passed) where passed is True if all gradients match.
    """
    num_grads = numerical_gradient(params, loss_fn, eps)
    max_error = 0.0
    for ng, ag in zip(num_grads, analytical_grads):
        denom = np.max(np.abs(ng) + np.abs(ag)) + eps
        error = np.max(np.abs(ng - ag)) / denom
        max_error = max(max_error, error)
    return max_error, max_error < threshold


def compute_loss(params, X, y, loss_fn, reg=0.0):
    """Compute loss with optional L2 regularization.

    Parameters
    ----------
    params : list of np.ndarray
        Current parameters.
    X : np.ndarray
        Input data.
    y : np.ndarray
        Target values.
    loss_fn : callable
        Loss function f(params, X, y) -> scalar.
    reg : float
        L2 regularization coefficient.

    Returns
    -------
    float
        Loss value (with regularization if reg > 0).
    """
    loss = loss_fn(params, X, y)
    if reg > 0:
        reg_term = 0.0
        for p in params:
            reg_term += np.sum(p ** 2)
        loss += 0.5 * reg * reg_term
    return loss


def compute_loss_grad(params, X, y, loss_fn, grad_fn, reg=0.0):
    """Compute loss and gradient with optional L2 regularization.

    Parameters
    ----------
    params : list of np.ndarray
        Current parameters.
    X : np.ndarray
        Input data.
    y : np.ndarray
        Target values.
    loss_fn : callable
        Loss function.
    grad_fn : callable
        Gradient function.
    reg : float
        L2 regularization coefficient.

    Returns
    -------
    tuple
        (loss, gradients_with_reg)
    """
    loss = loss_fn(params, X, y)
    grads = grad_fn(params, X, y)
    if reg > 0:
        grads = [g + reg * p for g, p in zip(grads, params)]
    return loss, grads
