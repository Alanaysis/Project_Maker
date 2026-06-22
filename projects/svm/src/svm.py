"""
SVM 分类器模块
=============

实现完整的 SVM 分类器，整合核函数和 SMO 优化算法。

SVM (Support Vector Machine) 的核心思想:
    找到一个超平面，使得两类数据之间的间隔 (margin) 最大化。
    这个超平面只由少数"支持向量"决定。

支持向量 (Support Vectors):
    距离决策边界最近的训练样本点。
    这些点"支撑"了决策边界的位置。
"""

import numpy as np
from typing import Callable, Optional, Literal

from .kernel import linear_kernel, rbf_kernel, polynomial_kernel, precompute_kernel_matrix
from .smo import SMO


class SVM:
    """
    SVM 分类器

    支持:
    - 线性核 (Linear Kernel)
    - RBF 核 (Radial Basis Function / 高斯核)
    - 多项式核 (Polynomial Kernel)

    使用 SMO 算法进行优化。

    属性:
        kernel_type: 核函数类型
        C: 正则化参数
        gamma: RBF 核的参数
        degree: 多项式核的阶数
        coef0: 多项式核的独立项系数
        alpha: 拉格朗日乘子 (训练后可用)
        b: 偏置项 (训练后可用)
        support_vectors: 支持向量 (训练后可用)
        support_vector_labels: 支持向量的标签 (训练后可用)
        support_vector_alphas: 支持向量对应的 alpha 值 (训练后可用)
    """

    def __init__(
        self,
        kernel: Literal["linear", "rbf", "polynomial"] = "rbf",
        C: float = 1.0,
        gamma: float = 1.0,
        degree: int = 3,
        coef0: float = 1.0,
        tol: float = 1e-3,
        max_passes: int = 10
    ):
        """
        初始化 SVM 分类器

        参数:
            kernel: 核函数类型，可选 "linear", "rbf", "polynomial"
            C: 正则化参数，控制误分类的惩罚程度
            gamma: RBF 核的宽度参数
            degree: 多项式核的阶数
            coef0: 多项式核的独立项系数
            tol: SMO 算法的容差
            max_passes: SMO 算法的最大无变化迭代次数
        """
        self.kernel_type = kernel
        self.C = C
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.tol = tol
        self.max_passes = max_passes

        # 初始化核函数
        self._kernel_func = self._create_kernel()

        # 训练后的属性
        self.alpha: Optional[np.ndarray] = None
        self.b: Optional[float] = None
        self.support_vectors: Optional[np.ndarray] = None
        self.support_vector_labels: Optional[np.ndarray] = None
        self.support_vector_alphas: Optional[np.ndarray] = None
        self._X_train: Optional[np.ndarray] = None
        self._y_train: Optional[np.ndarray] = None

    def _create_kernel(self) -> Callable[[np.ndarray, np.ndarray], float]:
        """根据 kernel_type 创建对应的核函数"""
        if self.kernel_type == "linear":
            return linear_kernel()
        elif self.kernel_type == "rbf":
            return rbf_kernel(self.gamma)
        elif self.kernel_type == "polynomial":
            return polynomial_kernel(self.degree, self.coef0)
        else:
            raise ValueError(f"不支持的核函数类型: {self.kernel_type}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SVM":
        """
        训练 SVM 分类器

        参数:
            X: 训练数据，形状为 (n_samples, n_features)
            y: 标签，值为 +1 或 -1，形状为 (n_samples,)

        返回:
            self: 训练后的 SVM 实例

        异常:
            ValueError: 如果标签不是 +1 或 -1
        """
        # 验证标签
        unique_labels = np.unique(y)
        if not np.array_equal(unique_labels, [-1, 1]):
            raise ValueError("标签必须为 +1 或 -1")

        n_samples = X.shape[0]

        # 预计算核矩阵
        K = precompute_kernel_matrix(X, self._kernel_func)

        # 使用 SMO 算法求解
        smo = SMO(C=self.C, tol=self.tol, max_passes=self.max_passes)
        self.alpha, self.b = smo.optimize(K, y)

        # 提取支持向量 (alpha > 0 的样本)
        support_mask = self.alpha > 1e-7
        self.support_vectors = X[support_mask]
        self.support_vector_labels = y[support_mask]
        self.support_vector_alphas = self.alpha[support_mask]

        # 保存训练数据 (用于预测)
        self._X_train = X
        self._y_train = y

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测新数据的类别

        参数:
            X: 待预测数据，形状为 (n_samples, n_features)

        返回:
            predictions: 预测结果，值为 +1 或 -1，形状为 (n_samples,)

        异常:
            RuntimeError: 如果模型尚未训练
        """
        if self.alpha is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        decision_values = self.decision_function(X)
        return np.sign(decision_values).astype(int)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        计算决策函数值

        f(x) = sum(alpha_i * y_i * K(xi, x)) + b

        参数:
            X: 输入数据，形状为 (n_samples, n_features)

        返回:
            decision_values: 决策函数值，形状为 (n_samples,)

        异常:
            RuntimeError: 如果模型尚未训练
        """
        if self.alpha is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        n_samples = X.shape[0]
        decision_values = np.zeros(n_samples)

        for i in range(n_samples):
            s = 0.0
            for j in range(len(self._X_train)):
                if self.alpha[j] > 1e-7:
                    s += (self.alpha[j] * self._y_train[j] *
                          self._kernel_func(self._X_train[j], X[i]))
            decision_values[i] = s + self.b

        return decision_values

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算分类准确率

        参数:
            X: 测试数据，形状为 (n_samples, n_features)
            y: 真实标签，值为 +1 或 -1，形状为 (n_samples,)

        返回:
            accuracy: 分类准确率，范围 [0, 1]
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def get_support_vectors(self) -> np.ndarray:
        """
        获取支持向量

        返回:
            support_vectors: 支持向量，形状为 (n_support_vectors, n_features)
        """
        if self.support_vectors is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")
        return self.support_vectors

    def get_n_support_vectors(self) -> int:
        """
        获取支持向量的数量

        返回:
            n_support_vectors: 支持向量的数量
        """
        if self.support_vectors is None:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")
        return len(self.support_vectors)

    def __repr__(self) -> str:
        """返回 SVM 实例的字符串表示"""
        return (f"SVM(kernel='{self.kernel_type}', C={self.C}, "
                f"gamma={self.gamma}, degree={self.degree})")
