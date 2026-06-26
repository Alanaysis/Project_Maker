"""
Convergence Detection (收敛检测)

This module provides tools for detecting and analyzing convergence
of optimization algorithms.

收敛检测模块提供检测和分析优化算法收敛性的工具。

Key Concepts / 关键概念:
- Convergence criteria:
  收敛准则:
  1. Gradient norm: ||grad(f)(x)|| < tol
  2. Step size: ||x_{k+1} - x_k|| < tol
  3. Function change: |f(x_{k+1}) - f(x_k)| < tol
  4. Newton decrement: sqrt(grad^T * H^{-1} * grad) < tol

- Convergence rates:
  收敛速率:
  - Linear: ||x_{k+1} - x*|| <= c * ||x_k - x*||, c in (0,1)
  - Superlinear: ||x_{k+1} - x*|| / ||x_k - x*|| -> 0
  - Quadratic: ||x_{k+1} - x*|| <= c * ||x_k - x*||^2

- Early stopping criteria prevent unnecessary computation.
  早停准则防止不必要的计算。
"""

import numpy as np


class ConvergenceDetector:
    """
    Detects convergence of optimization algorithms.
    检测优化算法的收敛性。
    """
    def __init__(
        self,
        tol=1e-8,
        min_iter=2,
        patience=10,
        norm_type='l2',
        relative_tol=True,
    ):
        """
        Parameters
        ----------
        tol : float
            Absolute convergence tolerance.
        min_iter : int
            Minimum iterations before checking convergence.
        patience : int
            Number of iterations to wait before declaring non-convergence
            when the improvement stalls.
        norm_type : str
            Norm type for gradient/step checking ('l1', 'l2', 'linf').
        relative_tol : bool
            If True, use relative tolerance based on initial function value.
        """
        self.tol = tol
        self.min_iter = min_iter
        self.patience = patience
        self.norm_type = norm_type
        self.relative_tol = relative_tol

        self.history = {
            'f': [],
            'grad_norm': [],
            'step_norm': [],
        }
        self.converged = False
        self.convergence_info = {}

    def _compute_norm(self, x):
        """Compute the specified norm."""
        if self.norm_type == 'l1':
            return np.linalg.norm(x, 1)
        elif self.norm_type == 'l2':
            return np.linalg.norm(x, 2)
        elif self.norm_type == 'linf':
            return np.linalg.norm(x, np.inf)
        else:
            return np.linalg.norm(x, 2)

    def add_point(self, x, f_val, grad=None, step=None):
        """
        Add a new optimization point to the history.
        添加新的优化点到历史中。

        Parameters
        ----------
        x : ndarray
            Current point.
        f_val : float
            Function value at x.
        grad : ndarray, optional
            Gradient at x.
        step : ndarray, optional
            Step taken to reach x.
        """
        self.history['f'].append(f_val)
        self.history['grad_norm'].append(
            self._compute_norm(grad) if grad is not None else None
        )
        self.history['step_norm'].append(
            self._compute_norm(step) if step is not None else None
        )

    def check_convergence(self):
        """
        Check if the optimization has converged.
        检查优化是否收敛。

        Returns
        -------
        converged : bool
            True if convergence criteria are met.
        info : dict
            Dictionary with convergence details.
        """
        info = {}
        n = len(self.history['f'])
        info['iteration'] = n

        if n < self.min_iter:
            info['reason'] = f"Need at least {self.min_iter} iterations"
            self.convergence_info = info
            return False

        # Check gradient norm
        if self.history['grad_norm'][-1] is not None:
            grad_norm = self.history['grad_norm'][-1]
            info['grad_norm'] = grad_norm
            if grad_norm < self.tol:
                info['reason'] = f"Gradient norm {grad_norm:.2e} < tol {self.tol}"
                self.convergence_info = info
                self.converged = True
                return True

        # Check step size
        if self.history['step_norm'][-1] is not None:
            step_norm = self.history['step_norm'][-1]
            info['step_norm'] = step_norm
            if step_norm < self.tol:
                info['reason'] = f"Step size {step_norm:.2e} < tol {self.tol}"
                self.convergence_info = info
                self.converged = True
                return True

        # Check function value change
        if n >= 2:
            f_change = abs(self.history['f'][-1] - self.history['f'][-2])
            info['f_change'] = f_change

            if self.relative_tol and abs(self.history['f'][0]) > 1e-10:
                rel_change = f_change / abs(self.history['f'][0])
                if rel_change < self.tol:
                    info['reason'] = f"Relative f change {rel_change:.2e} < tol {self.tol}"
                    self.convergence_info = info
                    self.converged = True
                    return True
            else:
                if f_change < self.tol:
                    info['reason'] = f"Absolute f change {f_change:.2e} < tol {self.tol}"
                    self.convergence_info = info
                    self.converged = True
                    return True

        # Check patience (stalled improvement)
        if n > self.min_iter + self.patience:
            recent = self.history['f'][-(self.patience + 1):]
            f_improvement = recent[-1] - recent[0]
            if abs(f_improvement) < self.tol * 0.1:
                info['reason'] = f"Stalled: f change {f_improvement:.2e} in last {self.patience} iters"
                self.convergence_info = info
                self.converged = False  # Stalled, not converged
                return False

        info['reason'] = "Not yet converged"
        self.convergence_info = info
        return False

    def analyze_convergence_rate(self):
        """
        Analyze the convergence rate from the history.
        从历史分析收敛速率。

        Estimates the convergence rate by fitting:
            log(|f_{k+1} - f*|) ≈ log(c) + p * log(|f_k - f*|)

        where p is the convergence order (p=1 linear, p=2 quadratic).

        Returns
        -------
        rate_info : dict
            Dictionary with convergence rate estimates.
        """
        f_history = np.array(self.history['f'])
        n = len(f_history)

        if n < 4:
            return {'rate': 'insufficient_data', 'order': None}

        # Estimate optimum as the minimum f value
        f_opt = np.min(f_history)
        errors = np.abs(f_history - f_opt)

        # Avoid log(0)
        errors = np.maximum(errors, 1e-30)

        # Compute consecutive error ratios
        log_errors = np.log(errors)
        log_ratios = np.diff(log_errors)

        if len(log_ratios) < 2:
            return {'rate': 'insufficient_data', 'order': None}

        # Estimate convergence order from consecutive ratios
        # For linear convergence: log(e_{k+1}/e_k) ≈ constant
        # For quadratic convergence: log(e_{k+1}) ≈ 2*log(e_k) + c
        if n >= 4:
            # Use last few iterations for rate estimation
            recent_errors = errors[-4:]
            if np.all(recent_errors > 0):
                ratios = recent_errors[1:] / recent_errors[:-1]
                avg_ratio = np.mean(ratios)

                if avg_ratio < 1e-3:
                    rate_type = 'superlinear'
                elif avg_ratio < 0.99:
                    rate_type = 'linear'
                else:
                    rate_type = 'slow'

                return {
                    'rate': rate_type,
                    'order': 1.0,
                    'avg_ratio': avg_ratio,
                    'final_error': errors[-1],
                }

        return {'rate': 'unknown', 'order': None}

    def get_summary(self):
        """
        Get a summary of the optimization convergence.
        获取优化收敛的摘要。

        Returns
        -------
        summary : dict
            Summary dictionary.
        """
        f_history = np.array(self.history['f'])
        summary = {
            'n_iterations': len(f_history),
            'f_initial': f_history[0] if len(f_history) > 0 else None,
            'f_final': f_history[-1] if len(f_history) > 0 else None,
            'f_improvement': float(f_history[0] - f_history[-1]) if len(f_history) > 1 else 0.0,
            'converged': self.converged,
            'convergence_info': self.convergence_info,
        }

        if len(f_history) >= 2:
            # Convergence rate
            rate_info = self.analyze_convergence_rate()
            summary['convergence_rate'] = rate_info.get('rate', 'unknown')

        if self.history['grad_norm'][-1] is not None:
            summary['final_grad_norm'] = self.history['grad_norm'][-1]

        return summary


def detect_convergence(
    f_history,
    grad_norm_history=None,
    step_norm_history=None,
    tol=1e-8,
    min_iter=2,
    relative_tol=True,
):
    """
    Static function to detect convergence from history arrays.
    从历史数组检测收敛性的静态函数。

    Parameters
    ----------
    f_history : array-like
        Sequence of function values.
    grad_norm_history : array-like, optional
        Sequence of gradient norms.
    step_norm_history : array-like, optional
        Sequence of step norms.
    tol : float
        Convergence tolerance.
    min_iter : int
        Minimum iterations before checking.
    relative_tol : bool
        Use relative tolerance.

    Returns
    -------
    converged : bool
        True if converged.
    info : dict
        Convergence details.
    """
    f_history = np.array(f_history)
    n = len(f_history)
    info = {'iteration': n}

    if n < min_iter:
        info['reason'] = f"Need at least {min_iter} iterations"
        return False, info

    if grad_norm_history is not None:
        gn = np.array(grad_norm_history)
        info['grad_norm'] = gn[-1]
        if gn[-1] < tol:
            info['reason'] = f"Gradient norm {gn[-1]:.2e} < tol"
            return True, info

    if step_norm_history is not None:
        sn = np.array(step_norm_history)
        info['step_norm'] = sn[-1]
        if sn[-1] < tol:
            info['reason'] = f"Step norm {sn[-1]:.2e} < tol"
            return True, info

    if n >= 2:
        f_change = abs(f_history[-1] - f_history[-2])
        info['f_change'] = f_change
        if relative_tol and abs(f_history[0]) > 1e-10:
            if f_change / abs(f_history[0]) < tol:
                info['reason'] = f"Relative change {f_change/abs(f_history[0]):.2e} < tol"
                return True, info
        else:
            if f_change < tol:
                info['reason'] = f"Absolute change {f_change:.2e} < tol"
                return True, info

    info['reason'] = "Not yet converged"
    return False, info
