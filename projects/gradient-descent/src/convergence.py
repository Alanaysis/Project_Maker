"""
Convergence monitoring and early stopping.

Tracks training metrics and detects when the optimizer has
converged or stopped making meaningful progress.
"""

import numpy as np


class ConvergenceMonitor:
    """Monitor training convergence and trigger early stopping.

    Tracks loss history, gradient norms, and parameter changes
    to detect convergence.

    Parameters
    ----------
    patience : int
        Number of epochs to wait before stopping after best loss.
    min_delta : float
        Minimum change in loss to count as improvement.
    gradient_threshold : float
        Stop if gradient norm falls below this value.
    min_gradient_change : float
        Stop if relative gradient change falls below this.
    """

    def __init__(self, patience: int = 50, min_delta: float = 1e-6,
                 gradient_threshold: float = 1e-8, min_gradient_change: float = 1e-5):
        self.patience = patience
        self.min_delta = min_delta
        self.gradient_threshold = gradient_threshold
        self.min_gradient_change = min_gradient_change

        self.loss_history = []
        self.gradient_norm_history = []
        self.best_loss = float('inf')
        self.patience_counter = 0
        self.converged = False
        self.stopped_epoch = None
        self.best_params = None

    def update(self, loss, grad_norm, params=None):
        """Update monitor with new training metrics.

        Parameters
        ----------
        loss : float
            Current loss value.
        grad_norm : float
            Current gradient norm.
        params : list of np.ndarray, optional
            Current parameters (saved when loss improves).

        Returns
        -------
        bool
            True if training should stop.
        """
        self.loss_history.append(loss)
        self.gradient_norm_history.append(grad_norm)

        # Check gradient-based convergence
        if grad_norm < self.gradient_threshold:
            self.converged = True
            self.stopped_epoch = len(self.loss_history)
            return True

        # Check loss improvement
        if loss < self.best_loss - self.min_delta:
            self.best_loss = loss
            self.patience_counter = 0
            if params is not None:
                self.best_params = [p.copy() for p in params]
        else:
            self.patience_counter += 1

        # Check patience
        if self.patience_counter >= self.patience:
            self.converged = True
            self.stopped_epoch = len(self.loss_history)
            return True

        return False

    def get_convergence_info(self):
        """Return diagnostic information.

        Returns
        -------
        dict
            Convergence diagnostics.
        """
        return {
            "converged": self.converged,
            "stopped_epoch": self.stopped_epoch,
            "best_loss": self.best_loss,
            "best_params": self.best_params,
            "final_loss": self.loss_history[-1] if self.loss_history else None,
            "loss_improvement": self.best_loss - (self.loss_history[-1] if self.loss_history else 0),
            "final_gradient_norm": self.gradient_norm_history[-1] if self.gradient_norm_history else None,
            "total_epochs": len(self.loss_history),
        }

    def reset(self):
        """Reset monitor state."""
        self.loss_history.clear()
        self.gradient_norm_history.clear()
        self.best_loss = float('inf')
        self.patience_counter = 0
        self.converged = False
        self.stopped_epoch = None
        self.best_params = None


class ConvergenceDetector:
    """Statistical convergence detection.

    Uses multiple criteria to detect convergence:
    - Gradient norm below threshold
    - Relative loss change below threshold
    - Parameter change below threshold
    - Loss variance over window is small
    """

    def __init__(self, gradient_threshold=1e-6, loss_rel_change=1e-6,
                 param_rel_change=1e-6, window_size=10):
        self.gradient_threshold = gradient_threshold
        self.loss_rel_change = loss_rel_change
        self.param_rel_change = param_rel_change
        self.window_size = window_size

    def check(self, loss, grad_norm, params, old_params=None):
        """Check if training has converged.

        Parameters
        ----------
        loss : float
            Current loss.
        grad_norm : float
            Current gradient norm.
        params : list of np.ndarray
            Current parameters.
        old_params : list of np.ndarray, optional
            Previous parameters for comparison.

        Returns
        -------
        bool
            True if converged.
        dict
            Diagnostic info.
        """
        reasons = []

        # Check gradient norm
        if grad_norm < self.gradient_threshold:
            reasons.append(f"gradient_norm={grad_norm:.2e} < {self.gradient_threshold}")

        # Check relative loss change
        if len(self.__dict__ if hasattr(self, '_losses') else []) > 0:
            pass  # handled in track_loss

        # Check parameter change
        if old_params is not None:
            max_param_change = 0.0
            for p, old_p in zip(params, old_params):
                denom = np.max(np.abs(old_p)) + 1e-8
                rel_change = np.max(np.abs(p - old_p)) / denom
                max_param_change = max(max_param_change, rel_change)
            if max_param_change < self.param_rel_change:
                reasons.append(f"param_rel_change={max_param_change:.2e}")

        converged = len(reasons) >= 1
        return converged, {"reasons": reasons, "grad_norm": grad_norm}

    def track_loss(self, loss):
        """Track loss history for variance-based detection."""
        if not hasattr(self, '_losses'):
            self._losses = []
        self._losses.append(loss)

        if len(self._losses) > self.window_size * 2:
            self._losses = self._losses[-self.window_size * 2:]

        if len(self._losses) >= self.window_size:
            recent = self._losses[-self.window_size:]
            variance = np.var(recent)
            mean = np.mean(recent)
            if mean > 0 and variance / (mean ** 2) < self.loss_rel_change:
                return True
        return False
