"""
SMO (Sequential Minimal Optimization) 算法模块
=============================================

SMO 算法由 John Platt 于 1998 年提出，用于高效求解 SVM 的对偶问题。

SVM 对偶问题:
    最大化: sum(alpha_i) - 0.5 * sum(alpha_i * alpha_j * y_i * y_j * K(x_i, x_j))
    约束:   0 <= alpha_i <= C, 对所有 i
            sum(alpha_i * y_i) = 0

SMO 算法的核心思想:
    1. 选择两个拉格朗日乘子 alpha_i 和 alpha_j
    2. 固定其他乘子，解析求解这两个乘子的最优值
    3. 重复直到收敛

选择两个乘子的原因: 由于约束 sum(alpha_i * y_i) = 0，至少需要同时更新两个乘子。
"""

import numpy as np
from typing import Callable, Tuple


class SMO:
    """
    SMO 优化算法实现

    属性:
        C: 正则化参数，控制误分类的惩罚程度
        tol: 容差，用于判断是否收敛
        max_passes: 最大无变化迭代次数，用于判断收敛
    """

    def __init__(
        self,
        C: float = 1.0,
        tol: float = 1e-3,
        max_passes: int = 10
    ):
        """
        初始化 SMO 优化器

        参数:
            C: 正则化参数 (惩罚参数)
                - C 大: 对误分类的惩罚更大，间隔更小，可能过拟合
                - C 小: 对误分类的惩罚更小，间隔更大，可能欠拟合
            tol: 容差，KKT 条件的违反程度小于此值时认为满足
            max_passes: 最大无变化迭代次数
        """
        self.C = C
        self.tol = tol
        self.max_passes = max_passes

    def optimize(
        self,
        K: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """
        使用 SMO 算法求解 SVM 对偶问题

        参数:
            K: 预计算的核矩阵，形状为 (n_samples, n_samples)
            y: 标签向量，值为 +1 或 -1，形状为 (n_samples,)

        返回:
            alpha: 拉格朗日乘子，形状为 (n_samples,)
            b: 偏置项
        """
        n_samples = K.shape[0]
        alpha = np.zeros(n_samples)
        b = 0.0
        passes = 0

        while passes < self.max_passes:
            num_changed_alphas = 0

            for i in range(n_samples):
                # 计算第 i 个样本的预测值和误差
                Ei = self._compute_error(i, K, y, alpha, b)

                # 检查是否违反 KKT 条件
                if self._violates_kkt(y[i], Ei, alpha[i]):
                    # 随机选择第二个乘子 j (j != i)
                    j = self._select_j(i, n_samples)
                    Ej = self._compute_error(j, K, y, alpha, b)

                    # 保存旧的 alpha 值
                    alpha_i_old = alpha[i]
                    alpha_j_old = alpha[j]

                    # 计算 alpha_j 的上下界
                    L, H = self._compute_bounds(y[i], y[j], alpha[i], alpha[j])

                    if L == H:
                        continue

                    # 计算 eta (二阶导数)
                    eta = K[i, i] + K[j, j] - 2 * K[i, j]

                    if eta <= 0:
                        continue

                    # 更新 alpha_j
                    alpha[j] = alpha_j_old + y[j] * (Ei - Ej) / eta

                    # 裁剪 alpha_j 到 [L, H] 范围
                    alpha[j] = np.clip(alpha[j], L, H)

                    # 检查 alpha_j 是否有显著变化
                    if abs(alpha[j] - alpha_j_old) < 1e-5:
                        continue

                    # 更新 alpha_i
                    alpha[i] = alpha_i_old + y[i] * y[j] * (alpha_j_old - alpha[j])

                    # 计算偏置项 b
                    b1 = (b - Ei
                          - y[i] * (alpha[i] - alpha_i_old) * K[i, i]
                          - y[j] * (alpha[j] - alpha_j_old) * K[i, j])

                    b2 = (b - Ej
                          - y[i] * (alpha[i] - alpha_i_old) * K[i, j]
                          - y[j] * (alpha[j] - alpha_j_old) * K[j, j])

                    if 0 < alpha[i] < self.C:
                        b = b1
                    elif 0 < alpha[j] < self.C:
                        b = b2
                    else:
                        b = (b1 + b2) / 2.0

                    num_changed_alphas += 1

            if num_changed_alphas == 0:
                passes += 1
            else:
                passes = 0

        return alpha, b

    def _compute_error(
        self,
        i: int,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        b: float
    ) -> float:
        """
        计算第 i 个样本的预测误差

        Ei = f(xi) - yi
        其中 f(xi) = sum(alpha_j * y_j * K(xi, xj)) + b
        """
        prediction = np.sum(alpha * y * K[i]) + b
        return prediction - y[i]

    def _violates_kkt(self, yi: float, Ei: float, alpha_i: float) -> bool:
        """
        检查是否违反 KKT 条件

        KKT 条件:
        - alpha_i = 0 时，yi * f(xi) >= 1
        - 0 < alpha_i < C 时，yi * f(xi) = 1
        - alpha_i = C 时，yi * f(xi) <= 1

        违反条件:
        - alpha_i < C 且 yi * Ei < -tol (应增大 alpha_i)
        - alpha_i > 0 且 yi * Ei > tol (应减小 alpha_i)
        """
        return ((alpha_i < self.C and yi * Ei < -self.tol) or
                (alpha_i > 0 and yi * Ei > self.tol))

    def _select_j(self, i: int, n_samples: int) -> int:
        """
        选择第二个乘子 j

        简单实现: 随机选择 j != i
        更优的实现会选择使 |Ei - Ej| 最大的 j
        """
        j = i
        while j == i:
            j = np.random.randint(0, n_samples)
        return j

    def _compute_bounds(
        self,
        yi: float,
        yj: float,
        alpha_i: float,
        alpha_j: float
    ) -> Tuple[float, float]:
        """
        计算 alpha_j 的上下界 L 和 H

        根据约束 0 <= alpha_i, alpha_j <= C 和 yi*alpha_i + yj*alpha_j = 常数
        """
        if yi != yj:
            L = max(0, alpha_j - alpha_i)
            H = min(self.C, self.C + alpha_j - alpha_i)
        else:
            L = max(0, alpha_i + alpha_j - self.C)
            H = min(self.C, alpha_i + alpha_j)

        return L, H
