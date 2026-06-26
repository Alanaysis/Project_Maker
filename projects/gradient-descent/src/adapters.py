"""
AdaGrad, RMSprop, Adam, and AdamW optimizers.

These are adaptive learning rate methods that adjust the learning rate
per-parameter based on historical gradient information.

AdaGrad:
    G_t = G_{t-1} + g_t^2
    theta = theta - lr / sqrt(G_t + eps) * g_t

RMSprop:
    E[g^2]_t = rho * E[g^2]_{t-1} + (1-rho) * g_t^2
    theta = theta - lr / sqrt(E[g^2]_t + eps) * g_t

Adam:
    m_t = beta1 * m_{t-1} + (1-beta1) * g_t
    v_t = beta2 * v_{t-1} + (1-beta2) * g_t^2
    m_hat = m_t / (1 - beta1^t)   # bias correction
    v_hat = v_t / (1 - beta2^t)
    theta = theta - lr * m_hat / sqrt(v_hat) + eps

AdamW:
    Same as Adam, but with decoupled weight decay:
    theta = theta - lr * weight_decay * theta - lr * m_hat / sqrt(v_hat + eps)
"""

import numpy as np


class AdaGradOptimizer:
    """AdaGrad optimizer with adaptive per-parameter learning rates.

    Accumulates the sum of squared gradients and divides the learning rate
    by the square root of this sum. This makes it well-suited for sparse
    data but causes the learning rate to decay too aggressively over time.

    Parameters
    ----------
    lr : float
        Initial learning rate.
    eps : float
        Numerical stability constant. Default 1e-8.
    """

    def __init__(self, lr: float = 0.01, eps: float = 1e-8):
        self.lr = lr
        self.eps = eps
        self.G = None  # accumulated squared gradients

    def reset(self):
        """Reset accumulated squared gradients."""
        self.G = None

    def step(self, params, grads):
        """Perform a single AdaGrad update step.

        Returns
        -------
        list of np.ndarray
            Updated parameters.
        """
        if self.G is None:
            self.G = [np.zeros_like(p) for p in params]

        new_params = []
        for p, g, G in zip(params, grads, self.G):
            G_new = G + g ** 2
            new_params.append(p - self.lr * g / (np.sqrt(G_new) + self.eps))
        self.G = [G_new for G_new in self.G]
        return new_params

    def get_state(self):
        return {"lr": self.lr, "eps": self.eps, "G": self.G}

    def set_state(self, state):
        self.lr = state["lr"]
        self.eps = state["eps"]
        self.G = state["G"]


class RMSpropOptimizer:
    """RMSprop optimizer.

    Uses an exponential moving average of squared gradients to adapt
    the learning rate per-parameter. Solves AdaGrad's aggressive
    learning rate decay.

    Parameters
    ----------
    lr : float
        Initial learning rate.
    rho : float
        Decay rate for the moving average. Default 0.9.
    eps : float
        Numerical stability constant. Default 1e-8.
    """

    def __init__(self, lr: float = 0.01, rho: float = 0.9, eps: float = 1e-8):
        self.lr = lr
        self.rho = rho
        self.eps = eps
        self.E = None  # exponential moving average of squared gradients

    def reset(self):
        """Reset moving average."""
        self.E = None

    def step(self, params, grads):
        """Perform a single RMSprop update step.

        Returns
        -------
        list of np.ndarray
            Updated parameters.
        """
        if self.E is None:
            self.E = [np.zeros_like(p) for p in params]

        new_params = []
        for p, g, E in zip(params, grads, self.E):
            E_new = self.rho * E + (1 - self.rho) * g ** 2
            new_params.append(p - self.lr * g / (np.sqrt(E_new) + self.eps))
        self.E = E_new
        return new_params

    def get_state(self):
        return {"lr": self.lr, "rho": self.rho, "eps": self.eps, "E": self.E}

    def set_state(self, state):
        self.lr = state["lr"]
        self.rho = state["rho"]
        self.eps = state["eps"]
        self.E = state["E"]


class AdamOptimizer:
    """Adam optimizer.

    Combines momentum (exponential moving average of gradients) with
    RMSprop (exponential moving average of squared gradients) and
    applies bias correction.

    Parameters
    ----------
    lr : float
        Learning rate. Default 0.001.
    beta1 : float
        Exponential decay rate for the first moment estimate. Default 0.9.
    beta2 : float
        Exponential decay rate for the second moment estimate. Default 0.999.
    eps : float
        Numerical stability constant. Default 1e-8.
    """

    def __init__(self, lr: float = 0.001, beta1: float = 0.9,
                 beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = None  # first moment
        self.v = None  # second moment
        self.t = 0     # timestep counter

    def reset(self):
        """Reset optimizer state."""
        self.m = None
        self.v = None
        self.t = 0

    def step(self, params, grads):
        """Perform a single Adam update step.

        Returns
        -------
        list of np.ndarray
            Updated parameters.
        """
        self.t += 1

        if self.m is None:
            self.m = [np.zeros_like(p) for p in params]
            self.v = [np.zeros_like(p) for p in params]

        new_params = []
        for p, g, m, v in zip(params, grads, self.m, self.v):
            m_new = self.beta1 * m + (1 - self.beta1) * g
            v_new = self.beta2 * v + (1 - self.beta2) * g ** 2

            # Bias correction
            m_hat = m_new / (1 - self.beta1 ** self.t)
            v_hat = v_new / (1 - self.beta2 ** self.t)

            new_params.append(p - self.lr * m_hat / (np.sqrt(v_hat) + self.eps))

        self.m = m_new
        self.v = v_new
        return new_params

    def get_state(self):
        return {
            "lr": self.lr, "beta1": self.beta1, "beta2": self.beta2,
            "eps": self.eps, "m": self.m, "v": self.v, "t": self.t,
        }

    def set_state(self, state):
        self.lr = state["lr"]
        self.beta1 = state["beta1"]
        self.beta2 = state["beta2"]
        self.eps = state["eps"]
        self.m = state["m"]
        self.v = state["v"]
        self.t = state["t"]


class AdamWOptimizer:
    """AdamW optimizer with decoupled weight decay.

    Unlike AdamW in some implementations, we apply weight decay
    directly to parameters rather than adding it to the gradient.
    This is the "decoupled weight decay" formulation from the
    original AdamW paper.

    Parameters
    ----------
    lr : float
        Learning rate. Default 0.001.
    weight_decay : float
        Weight decay coefficient (L2 regularization). Default 0.01.
    beta1 : float
        Exponential decay rate for the first moment. Default 0.9.
    beta2 : float
        Exponential decay rate for the second moment. Default 0.999.
    eps : float
        Numerical stability constant. Default 1e-8.
    """

    def __init__(self, lr: float = 0.001, weight_decay: float = 0.01,
                 beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.weight_decay = weight_decay
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = None
        self.v = None
        self.t = 0

    def reset(self):
        """Reset optimizer state."""
        self.m = None
        self.v = None
        self.t = 0

    def step(self, params, grads):
        """Perform a single AdamW update step.

        Returns
        -------
        list of np.ndarray
            Updated parameters.
        """
        self.t += 1

        if self.m is None:
            self.m = [np.zeros_like(p) for p in params]
            self.v = [np.zeros_like(p) for p in params]

        new_params = []
        for p, g, m, v in zip(params, grads, self.m, self.v):
            # Adam moment updates
            m_new = self.beta1 * m + (1 - self.beta1) * g
            v_new = self.beta2 * v + (1 - self.beta2) * g ** 2

            # Bias correction
            m_hat = m_new / (1 - self.beta1 ** self.t)
            v_hat = v_new / (1 - self.beta2 ** self.t)

            # Decoupled weight decay
            new_params.append(p * (1 - self.lr * self.weight_decay)
                              - self.lr * m_hat / (np.sqrt(v_hat) + self.eps))

        self.m = m_new
        self.v = v_new
        return new_params

    def get_state(self):
        return {
            "lr": self.lr, "weight_decay": self.weight_decay,
            "beta1": self.beta1, "beta2": self.beta2, "eps": self.eps,
            "m": self.m, "v": self.v, "t": self.t,
        }

    def set_state(self, state):
        self.lr = state["lr"]
        self.weight_decay = state["weight_decay"]
        self.beta1 = state["beta1"]
        self.beta2 = state["beta2"]
        self.eps = state["eps"]
        self.m = state["m"]
        self.v = state["v"]
        self.t = state["t"]
