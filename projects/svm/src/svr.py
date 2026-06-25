"""
SVR 回归模块 (Support Vector Regression)
========================================

实现 epsilon-SVR (支持向量回归)，用于回归问题。

SVR 的核心思想:
    找到一个函数 f(x)，使得所有训练样本的预测误差不超过 epsilon，
    同时函数尽可能平滑。

epsilon 不敏感损失:
    L_epsilon(y, f(x)) = max(0, |y - f(x)| - epsilon)
    只有当预测误差超过 epsilon 时才计算损失。

epsilon-SVR 对偶问题:
    最小化: (1/2) * sum((alpha_i - alpha*_i)(alpha_j - alpha*_j) K(x_i, x_j))
            + epsilon * sum(alpha_i + alpha*_i)
            - sum(y_i(alpha_i - alpha*_i))
    约束:   0 <= alpha_i, alpha*_i <= C
            sum(alpha_i - alpha*_i) = 0

使用改进的 SMO 算法求解。
"""

import numpy as np
from typing import Optional, Literal

from .kernel import (
    linear_kernel,
    rbf_kernel,
    polynomial_kernel,
    sigmoid_kernel,
    precompute_kernel_matrix,
)


class SVR:
    """
    epsilon-SVR 回归器

    支持:
    - 线性核 (Linear Kernel)
    - RBF 核 (Radial Basis Function / 高斯核)
    - 多项式核 (Polynomial Kernel)
    - Sigmoid 核 (Sigmoid Kernel)

    使用改进的 SMO 算法进行优化。

    属性:
        kernel_type: 核函数类型
        C: 正则化参数
        epsilon: epsilon 不敏感损失的宽度
        gamma: RBF 核 / Sigmoid 核的参数
        degree: 多项式核的阶数
        coef0: 多项式核 / Sigmoid 核的独立项系数
        alpha: 拉格朗日乘子 (训练后可用)
        alpha_star: 拉格朗日乘子 (训练后可用)
        b: 偏置项 (训练后可用)
        support_vectors: 支持向量 (训练后可用)
    """

    def __init__(
        self,
        kernel: Literal["linear", "rbf", "polynomial", "sigmoid"] = "rbf",
        C: float = 1.0,
        epsilon: float = 0.1,
        gamma: float = 1.0,
        degree: int = 3,
        coef0: float = 1.0,
        tol: float = 1e-3,
        max_passes: int = 10,
    ):
        """
        初始化 SVR 回归器

        参数:
            kernel: 核函数类型，可选 "linear", "rbf", "polynomial", "sigmoid"
            C: 正则化参数，控制对超出 epsilon 管道的惩罚程度
            epsilon: epsilon 不敏感损失的宽度，控制回归管道的宽度
            gamma: RBF 核 / Sigmoid 核的宽度参数
            degree: 多项式核的阶数
            coef0: 多项式核 / Sigmoid 核的独立项系数
            tol: SMO 算法的容差
            max_passes: SMO 算法的最大无变化迭代次数
        """
        self.kernel_type = kernel
        self.C = C
        self.epsilon = epsilon
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.tol = tol
        self.max_passes = max_passes

        # 初始化核函数
        self._kernel_func = self._create_kernel()

        # 训练后的属性
        self.alpha: Optional[np.ndarray] = None
        self.alpha_star: Optional[np.ndarray] = None
        self.b: Optional[float] = None
        self.support_indices: Optional[np.ndarray] = None
        self._X_train: Optional[np.ndarray] = None
        self._y_train: Optional[np.ndarray] = None

    def _create_kernel(self):
        """根据 kernel_type 创建对应的核函数"""
        if self.kernel_type == "linear":
            return linear_kernel()
        elif self.kernel_type == "rbf":
            return rbf_kernel(self.gamma)
        elif self.kernel_type == "polynomial":
            return polynomial_kernel(self.degree, self.coef0)
        elif self.kernel_type == "sigmoid":
            return sigmoid_kernel(self.gamma, self.coef0)
        else:
            raise ValueError(f"不支持的核函数类型: {self.kernel_type}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SVR":
        """
        训练 SVR 回归器

        使用改进的 SMO 算法求解 epsilon-SVR 对偶问题。

        参数:
            X: 训练数据，形状为 (n_samples, n_features)
            y: 目标值，形状为 (n_samples,)

        返回:
            self: 训练后的 SVR 实例
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]

        # 预计算核矩阵
        K = precompute_kernel_matrix(X, self._kernel_func)

        # 使用 SMO 算法求解 SVR 对偶问题
        self.alpha, self.alpha_star, self.b = self._smo_svr(K, y, n_samples)

        # 提取支持向量 (alpha 或 alpha_star 显著不为零的样本)
        sv_mask = (np.abs(self.alpha) > 1e-7) | (np.abs(self.alpha_star) > 1e-7)
        self.support_indices = np.where(sv_mask)[0]

        # 保存训练数据 (用于预测)
        self._X_train = X
        self._y_train = y
        self._K_train = K

        return self

    def _smo_svr(
        self, K: np.ndarray, y: np.ndarray, n_samples: int
    ):
        """
        改进的 SMO 算法求解 epsilon-SVR 对偶问题

        epsilon-SVR 引入两组拉格朗日乘子 alpha 和 alpha_star，
        约束为 sum(alpha_i - alpha_star_i) = 0 且 0 <= alpha_i, alpha_star_i <= C。

        本实现将 (alpha, alpha_star) 视为扩展变量，每次选取一个样本 i，
        在该样本的 (alpha_i, alpha_star_i) 子空间上做解析更新。

        参数:
            K: 预计算的核矩阵
            y: 目标值向量
            n_samples: 样本数量

        返回:
            alpha: 拉格朗日乘子 alpha
            alpha_star: 拉格朗日乘子 alpha_star
            b: 偏置项
        """
        alpha = np.zeros(n_samples)
        alpha_star = np.zeros(n_samples)
        b = 0.0
        passes = 0

        while passes < self.max_passes:
            num_changed = 0

            for i in range(n_samples):
                # 计算当前预测值 f(x_i)
                fi = self._compute_prediction(i, K, y, alpha, alpha_star, b)

                # 计算误差
                Ei = fi - y[i]

                # 检查 KKT 条件是否被违反
                # 情况 1: alpha_i 可以增大
                # 条件: Ei < -epsilon 且 alpha_i < C
                #        或 Ei > epsilon 且 alpha_star_i > 0
                # 情况 2: alpha_i 可以减小
                # 条件: Ei > epsilon 且 alpha_i > 0
                #        或 Ei < -epsilon 且 alpha_star_i < C

                # 尝试更新 alpha_i
                if (Ei < -self.epsilon and alpha[i] < self.C) or (
                    Ei > self.epsilon and alpha_star[i] > 0
                ):
                    changed = self._update_alpha_pair(
                        i, K, y, alpha, alpha_star, b, is_alpha=True
                    )
                    if changed:
                        num_changed += 1
                        # 重新计算 b
                        b = self._update_bias(K, y, alpha, alpha_star, i)
                        continue

                # 尝试更新 alpha_star_i
                if (Ei > self.epsilon and alpha_star[i] < self.C) or (
                    Ei < -self.epsilon and alpha[i] > 0
                ):
                    changed = self._update_alpha_pair(
                        i, K, y, alpha, alpha_star, b, is_alpha=False
                    )
                    if changed:
                        num_changed += 1
                        b = self._update_bias(K, y, alpha, alpha_star, i)

            if num_changed == 0:
                passes += 1
            else:
                passes = 0

        return alpha, alpha_star, b

    def _compute_prediction(
        self,
        i: int,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        b: float,
    ) -> float:
        """
        计算第 i 个样本的预测值

        f(x_i) = sum_j (alpha_j - alpha_star_j) * K(x_j, x_i) + b

        参数:
            i: 样本索引
            K: 核矩阵
            y: 目标值
            alpha: 拉格朗日乘子 alpha
            alpha_star: 拉格朗日乘子 alpha_star
            b: 偏置项

        返回:
            f(x_i): 预测值
        """
        w = alpha - alpha_star
        return np.dot(w, K[i]) + b

    def _update_alpha_pair(
        self,
        i: int,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        b: float,
        is_alpha: bool,
    ) -> bool:
        """
        更新第 i 个样本的 alpha_i 或 alpha_star_i

        在 SVR 的 SMO 中，对于单个样本 i，我们同时维护 (alpha_i, alpha_star_i)。
        由于互补松弛条件，alpha_i * alpha_star_i = 0，因此每次只更新其中一个。

        本方法选择一个候选乘子，然后选取另一个样本 j 来配对更新，
        保持约束 sum(alpha - alpha_star) = 0。

        参数:
            i: 当前样本索引
            K: 核矩阵
            y: 目标值
            alpha: 拉格朗日乘子 alpha
            alpha_star: 拉格朗日乘子 alpha_star
            b: 偏置项
            is_alpha: True 表示更新 alpha_i，False 表示更新 alpha_star_i

        返回:
            是否发生了有效更新
        """
        n_samples = len(y)

        # 计算当前预测值和误差
        fi = self._compute_prediction(i, K, y, alpha, alpha_star, b)
        Ei = fi - y[i]

        # 选择第二个样本 j (启发式: 选择误差差异最大的)
        j = self._select_second(i, K, y, alpha, alpha_star, b, n_samples)
        if j < 0:
            return False

        fj = self._compute_prediction(j, K, y, alpha, alpha_star, b)
        Ej = fj - y[j]

        # 计算 eta = K[i,i] + K[j,j] - 2*K[i,j]
        eta = K[i, i] + K[j, j] - 2.0 * K[i, j]
        if eta <= 1e-12:
            return False

        if is_alpha:
            # 更新 alpha_i 和 alpha_j (配对以保持约束)
            return self._update_alphas(
                i, j, Ei, Ej, K, y, alpha, alpha_star, b, eta
            )
        else:
            # 更新 alpha_star_i 和 alpha_star_j
            return self._update_alpha_stars(
                i, j, Ei, Ej, K, y, alpha, alpha_star, b, eta
            )

    def _update_alphas(
        self,
        i: int,
        j: int,
        Ei: float,
        Ej: float,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        b: float,
        eta: float,
    ) -> bool:
        """
        更新 alpha_i 和 alpha_j

        保持约束 sum(alpha - alpha_star) = 0:
        delta_alpha_i = -delta_alpha_j

        参数:
            i, j: 样本索引
            Ei, Ej: 预测误差
            K: 核矩阵
            y: 目标值
            alpha, alpha_star: 拉格朗日乘子
            b: 偏置项
            eta: 二阶导数 K[i,i] + K[j,j] - 2*K[i,j]

        返回:
            是否发生了有效更新
        """
        alpha_i_old = alpha[i]
        alpha_j_old = alpha[j]

        # 计算未裁剪的新 alpha_j
        alpha_j_new = alpha_j_old + (Ei - Ej) / eta

        # 裁剪到 [0, C]
        alpha_j_new = np.clip(alpha_j_new, 0.0, self.C)

        # 检查是否有显著变化
        if abs(alpha_j_new - alpha_j_old) < 1e-5:
            return False

        # 更新 alpha_i 以保持约束 (delta_alpha_i = -delta_alpha_j)
        alpha_i_new = alpha_i_old - (alpha_j_new - alpha_j_old)
        alpha_i_new = np.clip(alpha_i_new, 0.0, self.C)

        # 应用更新
        alpha[i] = alpha_i_new
        alpha[j] = alpha_j_new

        return True

    def _update_alpha_stars(
        self,
        i: int,
        j: int,
        Ei: float,
        Ej: float,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        b: float,
        eta: float,
    ) -> bool:
        """
        更新 alpha_star_i 和 alpha_star_j

        保持约束 sum(alpha - alpha_star) = 0:
        delta_alpha_star_i = -delta_alpha_star_j

        参数:
            i, j: 样本索引
            Ei, Ej: 预测误差
            K: 核矩阵
            y: 目标值
            alpha, alpha_star: 拉格朗日乘子
            b: 偏置项
            eta: 二阶导数

        返回:
            是否发生了有效更新
        """
        alpha_star_i_old = alpha_star[i]
        alpha_star_j_old = alpha_star[j]

        # 计算未裁剪的新 alpha_star_j
        alpha_star_j_new = alpha_star_j_old - (Ei - Ej) / eta

        # 裁剪到 [0, C]
        alpha_star_j_new = np.clip(alpha_star_j_new, 0.0, self.C)

        # 检查是否有显著变化
        if abs(alpha_star_j_new - alpha_star_j_old) < 1e-5:
            return False

        # 更新 alpha_star_i 以保持约束
        alpha_star_i_new = alpha_star_i_old - (alpha_star_j_new - alpha_star_j_old)
        alpha_star_i_new = np.clip(alpha_star_i_new, 0.0, self.C)

        # 应用更新
        alpha_star[i] = alpha_star_i_new
        alpha_star[j] = alpha_star_j_new

        return True

    def _select_second(
        self,
        i: int,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        b: float,
        n_samples: int,
    ) -> int:
        """
        选择第二个样本 j 用于配对更新

        启发式策略: 选择使 |Ei - Ej| 最大的 j，
        因为这样的 j 能带来最大的目标函数下降。

        参数:
            i: 第一个样本索引
            K: 核矩阵
            y: 目标值
            alpha, alpha_star: 拉格朗日乘子
            b: 偏置项
            n_samples: 样本数量

        返回:
            第二个样本索引 j，如果没有合适的 j 则返回 -1
        """
        Ei = self._compute_prediction(i, K, y, alpha, alpha_star, b) - y[i]

        best_j = -1
        best_delta = -1.0

        for j in range(n_samples):
            if j == i:
                continue
            Ej = self._compute_prediction(j, K, y, alpha, alpha_star, b) - y[j]
            delta = abs(Ei - Ej)
            if delta > best_delta:
                best_delta = delta
                best_j = j

        return best_j

    def _update_bias(
        self,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
        i: int,
    ) -> float:
        """
        更新偏置项 b

        对于不在管道边界上的样本 (0 < alpha_i < C 且 alpha_star_i = 0，
        或 0 < alpha_star_i < C 且 alpha_i = 0)，可以精确计算 b。

        参数:
            K: 核矩阵
            y: 目标值
            alpha, alpha_star: 拉格朗日乘子
            i: 当前更新的样本索引

        返回:
            更新后的偏置项 b
        """
        fi = self._compute_prediction(i, K, y, alpha, alpha_star, 0.0)

        # 如果样本在管道内 (alpha 和 alpha_star 都为 0 或都为 C)
        # 则不需要精确更新 b
        if 1e-7 < alpha[i] < self.C - 1e-7 and alpha_star[i] < 1e-7:
            # alpha_i 在 (0, C) 且 alpha_star_i = 0
            # f(x_i) = y_i + epsilon (上边界)
            return y[i] + self.epsilon - fi
        elif 1e-7 < alpha_star[i] < self.C - 1e-7 and alpha[i] < 1e-7:
            # alpha_star_i 在 (0, C) 且 alpha_i = 0
            # f(x_i) = y_i - epsilon (下边界)
            return y[i] - self.epsilon - fi
        else:
            # 使用所有边界样本的平均值
            return self._average_bias(K, y, alpha, alpha_star)

    def _average_bias(
        self,
        K: np.ndarray,
        y: np.ndarray,
        alpha: np.ndarray,
        alpha_star: np.ndarray,
    ) -> float:
        """
        计算偏置项 b 的平均值

        对所有边界样本 (0 < alpha_i < C 且 alpha_star_i = 0，
        或 0 < alpha_star_i < C 且 alpha_i = 0) 计算 b 并取平均。

        参数:
            K: 核矩阵
            y: 目标值
            alpha, alpha_star: 拉格朗日乘子

        返回:
            偏置项 b 的平均值
        """
        n_samples = len(y)
        b_values = []
        w = alpha - alpha_star

        for i in range(n_samples):
            fi = np.dot(w, K[i])
            if 1e-7 < alpha[i] < self.C - 1e-7 and alpha_star[i] < 1e-7:
                b_values.append(y[i] + self.epsilon - fi)
            elif 1e-7 < alpha_star[i] < self.C - 1e-7 and alpha[i] < 1e-7:
                b_values.append(y[i] - self.epsilon - fi)

        if len(b_values) > 0:
            return np.mean(b_values)
        return 0.0

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新数据的目标值

        f(x) = sum((alpha_i - alpha_star_i) * K(x_i, x)) + b

        参数:
            X: 待预测数据，形状为 (n_samples, n_features)

        返回:
            predictions: 预测值，形状为 (n_samples,)

        异常:
            RuntimeError: 如果模型尚未训练
        """
        if self.alpha is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_test = X.shape[0]
        predictions = np.zeros(n_test)

        w = self.alpha - self.alpha_star

        for i in range(n_test):
            s = 0.0
            for j in range(len(self._X_train)):
                if abs(w[j]) > 1e-7:
                    s += w[j] * self._kernel_func(self._X_train[j], X[i])
            predictions[i] = s + self.b

        return predictions

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算 R2 决定系数 (R-squared)

        R2 = 1 - SS_res / SS_tot
        其中 SS_res = sum((y_i - f(x_i))^2), SS_tot = sum((y_i - mean(y))^2)

        参数:
            X: 测试数据，形状为 (n_samples, n_features)
            y: 真实目标值，形状为 (n_samples,)

        返回:
            r2: R2 决定系数，越接近 1 表示拟合越好
        """
        predictions = self.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            # 所有目标值相同，完美预测返回 1，否则返回 0
            return 1.0 if ss_res == 0 else 0.0

        return 1.0 - ss_res / ss_tot

    def get_support_vectors(self) -> np.ndarray:
        """
        获取支持向量

        返回:
            support_vectors: 支持向量，形状为 (n_support_vectors, n_features)

        异常:
            RuntimeError: 如果模型尚未训练
        """
        if self.support_indices is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")
        return self._X_train[self.support_indices]

    def get_n_support_vectors(self) -> int:
        """
        获取支持向量的数量

        返回:
            n_support_vectors: 支持向量的数量

        异常:
            RuntimeError: 如果模型尚未训练
        """
        if self.support_indices is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")
        return len(self.support_indices)

    def __repr__(self) -> str:
        """返回 SVR 实例的字符串表示"""
        return (
            f"SVR(kernel='{self.kernel_type}', C={self.C}, epsilon={self.epsilon}, "
            f"gamma={self.gamma}, degree={self.degree})"
        )
