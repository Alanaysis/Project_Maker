"""
Learning rate schedulers.

Schedulers dynamically adjust the learning rate during training:
- Step: reduce lr by factor every N epochs
- Cosine: cosine annealing from initial to minimum lr
- Exponential: lr *= gamma each step
- Warmup: linearly increase lr from 0 to target over warmup_steps
"""

import numpy as np


class StepLR:
    """Step learning rate scheduler.

    Reduces the learning rate by a factor (gamma) every step_size epochs.

    lr = initial_lr * gamma ** (epoch // step_size)

    Parameters
    ----------
    initial_lr : float
        Starting learning rate.
    step_size : int
        Number of epochs between reductions.
    gamma : float
        Multiplicative factor for each reduction. Default 0.1.
    """

    def __init__(self, initial_lr: float, step_size: int, gamma: float = 0.1):
        self.initial_lr = initial_lr
        self.step_size = step_size
        self.gamma = gamma
        self.current_lr = initial_lr
        self.epoch = 0

    def step(self):
        """Update learning rate for the next epoch.

        Returns
        -------
        float
            New learning rate.
        """
        self.epoch += 1
        self.current_lr = self.initial_lr * (self.gamma ** (self.epoch // self.step_size))
        return self.current_lr

    def get_lr(self):
        return self.current_lr


class CosineLRScheduler:
    """Cosine annealing learning rate scheduler.

    lr = min_lr + 0.5 * (initial_lr - min_lr) * (1 + cos(pi * epoch / T))

    Parameters
    ----------
    initial_lr : float
        Starting learning rate.
    T_max : int
        Maximum number of epochs (full cosine cycle).
    eta_min : float
        Minimum learning rate. Default 0.
    """

    def __init__(self, initial_lr: float, T_max: int, eta_min: float = 0.0):
        self.initial_lr = initial_lr
        self.T_max = T_max
        self.eta_min = eta_min
        self.current_lr = initial_lr
        self.epoch = 0

    def step(self):
        """Update learning rate for the next epoch.

        Returns
        -------
        float
            New learning rate.
        """
        self.epoch += 1
        self.current_lr = self.eta_min + 0.5 * (self.initial_lr - self.eta_min) * (
            1 + np.cos(np.pi * self.epoch / self.T_max)
        )
        return self.current_lr

    def get_lr(self):
        return self.current_lr


class ExponentialLR:
    """Exponential learning rate scheduler.

    lr = initial_lr * gamma^epoch

    Parameters
    ----------
    initial_lr : float
        Starting learning rate.
    gamma : float
        Multiplicative decay factor per epoch. Default 0.95.
    """

    def __init__(self, initial_lr: float, gamma: float = 0.95):
        self.initial_lr = initial_lr
        self.gamma = gamma
        self.current_lr = initial_lr
        self.epoch = 0

    def step(self):
        """Update learning rate for the next epoch.

        Returns
        -------
        float
            New learning rate.
        """
        self.epoch += 1
        self.current_lr = self.initial_lr * (self.gamma ** self.epoch)
        return self.current_lr

    def get_lr(self):
        return self.current_lr


class WarmupLR:
    """Linear warmup learning rate scheduler.

    Linearly increases the learning rate from 0 to initial_lr
    over warmup_steps, then keeps it constant.

    lr = initial_lr * min(epoch / warmup_steps, 1)

    Parameters
    ----------
    initial_lr : float
        Target (maximum) learning rate.
    warmup_steps : int
        Number of warmup steps.
    """

    def __init__(self, initial_lr: float, warmup_steps: int):
        self.initial_lr = initial_lr
        self.warmup_steps = warmup_steps
        self.current_lr = 0.0
        self.step_count = 0

    def step(self):
        """Update learning rate for the next step.

        Returns
        -------
        float
            New learning rate.
        """
        self.step_count += 1
        if self.step_count <= self.warmup_steps:
            self.current_lr = self.initial_lr * (self.step_count / self.warmup_steps)
        else:
            self.current_lr = self.initial_lr
        return self.current_lr

    def get_lr(self):
        return self.current_lr


class CompositeScheduler:
    """Composite scheduler that chains multiple schedulers.

    Example: warmup for 100 steps, then cosine annealing for 900 steps.
    """

    def __init__(self, warmup_scheduler, main_scheduler):
        self.warmup = warmup_scheduler
        self.main = main_scheduler
        self.current_lr = 0.0

    def step(self):
        """Step through the warmup or main scheduler as appropriate.

        Returns
        -------
        float
            New learning rate.
        """
        if self.warmup.step_count < self.warmup.warmup_steps:
            self.current_lr = self.warmup.step()
        else:
            self.current_lr = self.main.step()
        return self.current_lr

    def get_lr(self):
        return self.current_lr
