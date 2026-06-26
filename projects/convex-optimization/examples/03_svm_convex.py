"""
Example 3: Support Vector Machine as Convex Optimization (SVM 作为凸优化)

Solves the SVM optimization problem.

SVM dual problem:
    max sum(alpha_i) - (1/2) * sum(sum(alpha_i * alpha_j * y_i * y_j * K(x_i, x_j)))
    s.t.  0 <= alpha_i <= C
          sum(alpha_i * y_i) = 0

This demonstrates how machine learning problems can be formulated
as convex optimization problems.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gradient_descent import gradient_descent
from src.convexity_checker import is_positive_semidefinite


def generate_sample_data(n_samples=50, n_features=2, seed=42):
    """Generate a simple binary classification dataset."""
    np.random.seed(seed)

    # Two clusters
    X1 = np.random.randn(n_samples // 2, n_features) + np.array([2, 0])
    X2 = np.random.randn(n_samples // 2, n_features) + np.array([-2, 0])

    X = np.vstack([X1, X2])
    y = np.hstack([np.ones(n_samples // 2), -np.ones(n_samples // 2)])

    return X, y


def linear_kernel(X, Y):
    """Compute linear kernel matrix."""
    return X @ Y.T


def rbf_kernel(X, Y, gamma=1.0):
    """Compute RBF (Gaussian) kernel matrix."""
    X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
    Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
    dist_sq = X_sq + Y_sq - 2 * X @ Y.T
    dist_sq = np.maximum(dist_sq, 0)  # Numerical stability
    return np.exp(-gamma * dist_sq)


def solve_svm_dual(X, y, C=1.0, kernel='linear', gamma=1.0):
    """
    Solve the SVM dual problem using gradient ascent.

    SVM Dual:
        max  sum(alpha_i) - (1/2) * sum(sum(alpha_i * alpha_j * y_i * y_j * K_ij))
        s.t.  0 <= alpha_i <= C
              sum(alpha_i * y_i) = 0

    We solve this by minimizing the negative of the objective.
    """
    n = len(y)

    # Compute kernel matrix
    if kernel == 'linear':
        K = linear_kernel(X, X)
    elif kernel == 'rbf':
        K = rbf_kernel(X, X, gamma)
    else:
        raise ValueError(f"Unknown kernel: {kernel}")

    # Verify K is PSD (for convexity)
    is_psd = is_positive_semidefinite(K)
    print(f"Kernel matrix is PSD: {is_psd}")

    # Kernel matrix should be PSD for convexity
    if not is_psd:
        # Add small regularization
        K += 1e-6 * np.eye(n)
        print(f"Added regularization to make K PSD")

    # Objective: minimize -L(alpha) = -(1^T*alpha - 0.5*alpha^T*Q*alpha)
    # where Q_ij = y_i * y_j * K_ij
    Q = np.outer(y, y) * K

    def f0(alpha):
        """Negative of SVM dual objective (for minimization)."""
        return -np.sum(alpha) + 0.5 * alpha @ Q @ alpha

    def grad_f0(alpha):
        """Gradient of negative dual objective."""
        return -np.ones(n) + Q @ alpha

    # Initial point (strictly feasible)
    alpha0 = np.ones(n) * 0.1

    # Projected gradient descent with box constraints [0, C]
    print(f"\nSolving SVM dual problem (C={C}, kernel={kernel})...")

    alpha = alpha0.copy()
    max_iter = 2000
    step_size = 0.001

    for i in range(max_iter):
        g = grad_f0(alpha)

        # Gradient step
        alpha_new = alpha - step_size * g

        # Project onto [0, C]
        alpha_new = np.clip(alpha_new, 0, C)

        # Project onto equality constraint: sum(alpha * y) = 0
        # Correction: subtract the mean of alpha*y, scaled by y
        violation = np.sum(alpha_new * y)
        alpha_new -= violation * y / n

        # Re-project onto [0, C]
        alpha_new = np.clip(alpha_new, 0, C)

        alpha = alpha_new

        if i % 500 == 0:
            f_val = f0(alpha)
            print(f"  Iter {i}: obj = {f_val:.6f}")

    # Find support vectors
    sv_mask = alpha > 1e-5
    n_sv = np.sum(sv_mask)
    print(f"\nNumber of support vectors: {n_sv}")

    # Compute bias term b
    sv_indices = np.where(sv_mask)[0]
    b_values = []
    for idx in sv_indices:
        if 0 < alpha[idx] < C:
            b_val = y[idx] - np.sum(alpha * y * K[idx])
            b_values.append(b_val)

    b = np.mean(b_values) if b_values else 0.0

    # Compute dual optimal value
    dual_obj = np.sum(alpha) - 0.5 * alpha @ Q @ alpha

    # Store SVM parameters
    svm_params = {
        'alpha': alpha,
        'b': b,
        'support_vectors': X[sv_mask],
        'sv_indices': np.where(sv_mask)[0],
        'n_support_vectors': n_sv,
    }

    return svm_params, dual_obj


def predict_svm(X_test, svm_params, kernel='linear', gamma=1.0):
    """Predict using the trained SVM."""
    alpha = svm_params['alpha']
    b = svm_params['b']
    sv_indices = svm_params['sv_indices']
    X_sv = svm_params['support_vectors']

    if kernel == 'linear':
        K_test = X_test @ X_sv.T
    elif kernel == 'rbf':
        K_test = rbf_kernel(X_test, X_sv, gamma)

    return np.sign(K_test @ (alpha[sv_indices] * y[:len(sv_indices)]) + b)


def main():
    print("=" * 60)
    print("Example 3: Support Vector Machine (SVM 作为凸优化)")
    print("=" * 60)

    # Generate data
    X, y = generate_sample_data(n_samples=40, n_features=2, seed=42)

    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Class distribution: {np.sum(y == 1)} positive, {np.sum(y == -1)} negative")

    # Solve with linear kernel
    print("\n--- Linear Kernel SVM ---")
    svm_linear, dual_obj_linear = solve_svm_dual(X, y, C=1.0, kernel='linear')
    print(f"Dual objective value: {dual_obj_linear:.6f}")
    print(f"Bias term: {svm_linear['b']:.4f}")

    # Solve with RBF kernel
    print("\n--- RBF Kernel SVM ---")
    svm_rbf, dual_obj_rbf = solve_svm_dual(X, y, C=1.0, kernel='rbf', gamma=1.0)
    print(f"Dual objective value: {dual_obj_rbf:.6f}")
    print(f"Bias term: {svm_rbf['b']:.4f}")

    # Verify classification
    print("\n--- Classification Verification ---")
    for kernel_name, svm_p in [('linear', svm_linear), ('rbf', svm_rbf)]:
        y_pred = predict_svm(X, svm_p, kernel=kernel_name)
        accuracy = np.mean(y_pred == y)
        print(f"  {kernel_name} kernel: accuracy = {accuracy:.4f}")

    return svm_linear, svm_rbf


if __name__ == "__main__":
    main()
