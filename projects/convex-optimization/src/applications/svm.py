"""
支持向量机 (SVM)

实现线性 SVM 和核 SVM 的求解。
"""

import numpy as np
from typing import Optional, Callable, Tuple
from dataclasses import dataclass


@dataclass
class SVMResult:
    """SVM 求解结果"""

    w: np.ndarray  # 权重向量
    b: float  # 偏置项
    support_vectors: np.ndarray  # 支持向量
    support_labels: np.ndarray  # 支持向量标签
    alphas: np.ndarray  # 拉格朗日乘子
    n_support: int  # 支持向量数量


class SVM:
    """线性 SVM

    使用 SMO (Sequential Minimal Optimization) 算法求解。

    问题：
    min 0.5 ||w||² + C Σ ξ_i
    s.t. y_i (w^T x_i + b) ≥ 1 - ξ_i
         ξ_i ≥ 0
    """

    def __init__(
        self,
        C: float = 1.0,
        tol: float = 1e-3,
        max_iter: int = 1000,
    ):
        self.C = C
        self.tol = tol
        self.max_iter = max_iter

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> SVMResult:
        """训练 SVM

        使用简化的 SMO 算法。
        """
        n_samples, n_features = X.shape

        # 初始化拉格朗日乘子
        alphas = np.zeros(n_samples)
        b = 0.0

        # SMO 主循环
        for iteration in range(self.max_iter):
            n_changed = 0

            for i in range(n_samples):
                # 计算预测值
                f_i = np.sum(alphas * y * (X @ X[i])) + b
                E_i = f_i - y[i]

                # 检查 KKT 条件
                if (y[i] * E_i < -self.tol and alphas[i] < self.C) or \
                   (y[i] * E_i > self.tol and alphas[i] > 0):

                    # 随机选择 j != i
                    j = i
                    while j == i:
                        j = np.random.randint(0, n_samples)

                    # 计算预测值
                    f_j = np.sum(alphas * y * (X @ X[j])) + b
                    E_j = f_j - y[j]

                    # 保存旧的 alpha
                    alpha_i_old = alphas[i]
                    alpha_j_old = alphas[j]

                    # 计算边界
                    if y[i] != y[j]:
                        L = max(0, alphas[j] - alphas[i])
                        H = min(self.C, self.C + alphas[j] - alphas[i])
                    else:
                        L = max(0, alphas[i] + alphas[j] - self.C)
                        H = min(self.C, alphas[i] + alphas[j])

                    if L == H:
                        continue

                    # 计算 eta
                    eta = 2 * X[i] @ X[j] - X[i] @ X[i] - X[j] @ X[j]
                    if eta >= 0:
                        continue

                    # 更新 alpha_j
                    alphas[j] = alpha_j_old - y[j] * (E_i - E_j) / eta

                    # 裁剪
                    if alphas[j] > H:
                        alphas[j] = H
                    elif alphas[j] < L:
                        alphas[j] = L

                    # 检查是否显著变化
                    if abs(alphas[j] - alpha_j_old) < 1e-5:
                        continue

                    # 更新 alpha_i
                    alphas[i] = alpha_i_old + y[i] * y[j] * (alpha_j_old - alphas[j])

                    # 更新 b
                    b1 = b - E_i - y[i] * (alphas[i] - alpha_i_old) * X[i] @ X[i] \
                         - y[j] * (alphas[j] - alpha_j_old) * X[i] @ X[j]
                    b2 = b - E_j - y[i] * (alphas[i] - alpha_i_old) * X[i] @ X[j] \
                         - y[j] * (alphas[j] - alpha_j_old) * X[j] @ X[j]

                    if 0 < alphas[i] < self.C:
                        b = b1
                    elif 0 < alphas[j] < self.C:
                        b = b2
                    else:
                        b = (b1 + b2) / 2

                    n_changed += 1

            # 检查收敛
            if n_changed == 0:
                break

        # 计算权重向量
        w = np.sum((alphas * y)[:, np.newaxis] * X, axis=0)

        # 找到支持向量
        support_mask = alphas > 1e-5
        support_vectors = X[support_mask]
        support_labels = y[support_mask]

        return SVMResult(
            w=w,
            b=b,
            support_vectors=support_vectors,
            support_labels=support_labels,
            alphas=alphas,
            n_support=np.sum(support_mask),
        )

    def predict(
        self,
        X: np.ndarray,
        result: SVMResult,
    ) -> np.ndarray:
        """预测"""
        scores = X @ result.w + result.b
        return np.sign(scores)


class KernelSVM:
    """核 SVM

    使用核技巧处理非线性问题。
    """

    def __init__(
        self,
        C: float = 1.0,
        kernel: str = "rbf",
        gamma: float = 1.0,
        degree: int = 3,
        tol: float = 1e-3,
        max_iter: int = 1000,
    ):
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        self.degree = degree
        self.tol = tol
        self.max_iter = max_iter

    def compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """计算核矩阵"""
        if self.kernel == "linear":
            return X1 @ X2.T
        elif self.kernel == "rbf":
            # K(x, y) = exp(-gamma ||x - y||²)
            sq_dist = np.sum(X1 ** 2, axis=1, keepdims=True) + \
                      np.sum(X2 ** 2, axis=1) - 2 * X1 @ X2.T
            return np.exp(-self.gamma * sq_dist)
        elif self.kernel == "poly":
            return (self.gamma * X1 @ X2.T + 1) ** self.degree
        else:
            raise ValueError(f"未知核函数: {self.kernel}")

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, float, np.ndarray]:
        """训练核 SVM

        返回: (alphas, b, support_vectors)
        """
        n_samples = X.shape[0]

        # 计算核矩阵
        K = self.compute_kernel(X, X)

        # 初始化
        alphas = np.zeros(n_samples)
        b = 0.0

        # 简化的 SMO
        for iteration in range(self.max_iter):
            n_changed = 0

            for i in range(n_samples):
                f_i = np.sum(alphas * y * K[i]) + b
                E_i = f_i - y[i]

                if (y[i] * E_i < -self.tol and alphas[i] < self.C) or \
                   (y[i] * E_i > self.tol and alphas[i] > 0):

                    j = i
                    while j == i:
                        j = np.random.randint(0, n_samples)

                    f_j = np.sum(alphas * y * K[j]) + b
                    E_j = f_j - y[j]

                    alpha_i_old = alphas[i]
                    alpha_j_old = alphas[j]

                    if y[i] != y[j]:
                        L = max(0, alphas[j] - alphas[i])
                        H = min(self.C, self.C + alphas[j] - alphas[i])
                    else:
                        L = max(0, alphas[i] + alphas[j] - self.C)
                        H = min(self.C, alphas[i] + alphas[j])

                    if L == H:
                        continue

                    eta = 2 * K[i, j] - K[i, i] - K[j, j]
                    if eta >= 0:
                        continue

                    alphas[j] = alpha_j_old - y[j] * (E_i - E_j) / eta

                    if alphas[j] > H:
                        alphas[j] = H
                    elif alphas[j] < L:
                        alphas[j] = L

                    if abs(alphas[j] - alpha_j_old) < 1e-5:
                        continue

                    alphas[i] = alpha_i_old + y[i] * y[j] * (alpha_j_old - alphas[j])

                    b1 = b - E_i - y[i] * (alphas[i] - alpha_i_old) * K[i, i] \
                         - y[j] * (alphas[j] - alpha_j_old) * K[i, j]
                    b2 = b - E_j - y[i] * (alphas[i] - alpha_i_old) * K[i, j] \
                         - y[j] * (alphas[j] - alpha_j_old) * K[j, j]

                    if 0 < alphas[i] < self.C:
                        b = b1
                    elif 0 < alphas[j] < self.C:
                        b = b2
                    else:
                        b = (b1 + b2) / 2

                    n_changed += 1

            if n_changed == 0:
                break

        return alphas, b, X

    def predict(
        self,
        X: np.ndarray,
        alphas: np.ndarray,
        b: float,
        support_vectors: np.ndarray,
        support_labels: np.ndarray,
    ) -> np.ndarray:
        """预测"""
        K = self.compute_kernel(X, support_vectors)
        scores = K @ (alphas * support_labels) + b
        return np.sign(scores)
