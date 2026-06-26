"""
Gradient clipping utilities.

Gradient clipping prevents the exploding gradient problem by
limiting the norm of gradients before they are applied:

- Norm clipping: scale gradients so their L2 norm <= max_norm
- Value clipping: clip each gradient element to [-clip_value, clip_value]
"""

import numpy as np


def clip_by_norm(grads, max_norm: float = 1.0):
    """Clip gradients by their global L2 norm.

    If the total norm exceeds max_norm, scale all gradients down
    so that the total norm equals max_norm.

    Parameters
    ----------
    grads : list of np.ndarray
        Gradients to clip.
    max_norm : float
        Maximum allowed L2 norm.

    Returns
    -------
    list of np.ndarray
        Clipped gradients.
    float
        Original gradient norm (before clipping).
    """
    # Compute total L2 norm across all gradients
    total_norm = 0.0
    for g in grads:
        total_norm += np.sum(g ** 2)
    total_norm = np.sqrt(total_norm)

    if total_norm > max_norm:
        scale = max_norm / (total_norm + 1e-6)
        clipped = [g * scale for g in grads]
    else:
        clipped = grads[:]

    return clipped, total_norm


def clip_by_value(grads, clip_value: float = 1.0):
    """Clip each gradient element to [-clip_value, clip_value].

    Parameters
    ----------
    grads : list of np.ndarray
        Gradients to clip.
    clip_value : float
        Maximum absolute value for any gradient element.

    Returns
    -------
    list of np.ndarray
        Clipped gradients.
    """
    clipped = [np.clip(g, -clip_value, clip_value) for g in grads]
    return clipped


def compute_gradient_norm(grads):
    """Compute the global L2 norm of gradients.

    Parameters
    ----------
    grads : list of np.ndarray
        Gradients.

    Returns
    -------
    float
        Global L2 norm.
    """
    total = 0.0
    for g in grads:
        total += np.sum(g ** 2)
    return np.sqrt(total)
