"""
高斯过程回归模块
================

实现高斯过程回归，支持：
- 预测均值和方差
- 边际似然计算
- 超参数优化
"""

import numpy as np
from typing import Optional, Tuple
from .kernels import Kernel, RBF, WhiteNoise


class GaussianProcess:
    """
    高斯过程回归

    属性：
        kernel: 核函数
        noise_variance: 观测噪声方差
        X_train: 训练输入
        y_train: 训练输出
        K_inv: 核矩阵的逆（缓存）
    """

    def __init__(self, kernel: Optional[Kernel] = None,
                 noise_variance: float = 1e-6,
                 optimize_hyperparams: bool = False):
        """
        初始化高斯过程

        参数：
            kernel: 核函数，默认使用 RBF 核
            noise_variance: 观测噪声方差
            optimize_hyperparams: 是否优化超参数
        """
        self.kernel = kernel if kernel is not None else RBF()
        self.noise_variance = noise_variance
        self.optimize_hyperparams = optimize_hyperparams

        self.X_train = None
        self.y_train = None
        self.K_inv = None
        self.alpha = None
        self.log_marginal_likelihood = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'GaussianProcess':
        """
        拟合高斯过程

        参数：
            X: 训练输入，形状 (n_samples, n_features)
            y: 训练输出，形状 (n_samples,)

        返回：
            self
        """
        X = np.atleast_2d(X)
        y = np.asarray(y).ravel()

        if X.shape[0] != y.shape[0]:
            raise ValueError("X 和 y 的样本数必须相同")

        self.X_train = X
        self.y_train = y

        # 计算核矩阵
        K = self.kernel(X, X)

        # 添加噪声项
        K += self.noise_variance * np.eye(len(X))

        # Cholesky 分解（数值稳定）
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            # 如果 Cholesky 分解失败，添加小的对角项
            K += 1e-6 * np.eye(len(X))
            L = np.linalg.cholesky(K)

        # 计算 alpha = K^{-1} y
        self.alpha = np.linalg.solve(L.T, np.linalg.solve(L, y))

        # 缓存 L 用于预测
        self.L = L

        # 计算边际似然
        self.log_marginal_likelihood = -0.5 * y.dot(self.alpha) - \
                                        np.sum(np.log(np.diag(L))) - \
                                        0.5 * len(X) * np.log(2 * np.pi)

        return self

    def predict(self, X: np.ndarray, return_std: bool = False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        预测

        参数：
            X: 测试输入，形状 (n_test, n_features)
            return_std: 是否返回标准差

        返回：
            y_mean: 预测均值
            y_std: 预测标准差（如果 return_std=True）
        """
        if self.X_train is None:
            raise RuntimeError("请先调用 fit() 方法")

        X = np.atleast_2d(X)

        # 计算训练集和测试集之间的核矩阵
        K_star = self.kernel(self.X_train, X)

        # 预测均值
        y_mean = K_star.T @ self.alpha

        if return_std:
            # 计算预测方差
            K_star_star = self.kernel(X, X)
            v = np.linalg.solve(self.L, K_star)
            y_var = np.diag(K_star_star) - np.sum(v**2, axis=0)
            y_var = np.maximum(y_var, 0)  # 确保非负
            y_std = np.sqrt(y_var)
            return y_mean, y_std

        return y_mean, None

    def sample(self, X: np.ndarray, n_samples: int = 1) -> np.ndarray:
        """
        从后验分布采样

        参数：
            X: 采样点，形状 (n_points, n_features)
            n_samples: 采样数量

        返回：
            samples: 形状 (n_points, n_samples) 的采样结果
        """
        X = np.atleast_2d(X)
        y_mean, y_std = self.predict(X, return_std=True)

        # 计算协方差矩阵
        K = self.kernel(X, X)
        K_star = self.kernel(self.X_train, X)
        v = np.linalg.solve(self.L, K_star)
        cov = K - v.T @ v

        # 确保对称
        cov = (cov + cov.T) / 2

        # 添加小的对角项确保正定
        cov += 1e-6 * np.eye(len(X))

        # 采样
        samples = np.random.multivariate_normal(y_mean, cov, n_samples).T

        return samples

    def log_likelihood(self, X: np.ndarray, y: np.ndarray,
                       kernel_params: dict = None) -> float:
        """
        计算对数边际似然

        参数：
            X: 输入数据
            y: 输出数据
            kernel_params: 核函数参数

        返回：
            log_likelihood: 对数边际似然
        """
        if kernel_params is not None:
            self.kernel.set_params(**kernel_params)

        gp = GaussianProcess(kernel=self.kernel,
                             noise_variance=self.noise_variance)
        gp.fit(X, y)

        return gp.log_marginal_likelihood

    def optimize(self, X: np.ndarray, y: np.ndarray,
                 n_restarts: int = 5) -> 'GaussianProcess':
        """
        优化超参数

        参数：
            X: 训练输入
            y: 训练输出
            n_restarts: 随机重启次数

        返回：
            self
        """
        from scipy.optimize import minimize

        def objective(params):
            # 更新参数
            self.kernel.set_params(length_scale=np.exp(params[0]),
                                   signal_variance=np.exp(params[1]))
            self.noise_variance = np.exp(params[2])

            # 计算负对数似然
            gp = GaussianProcess(kernel=self.kernel,
                                 noise_variance=self.noise_variance)
            try:
                gp.fit(X, y)
                return -gp.log_marginal_likelihood
            except:
                return 1e10

        # 多次随机重启
        best_params = None
        best_value = np.inf

        for _ in range(n_restarts):
            # 随机初始参数
            x0 = np.array([
                np.log(self.kernel.length_scale) + np.random.randn(),
                np.log(self.kernel.signal_variance) + np.random.randn(),
                np.log(self.noise_variance) + np.random.randn()
            ])

            try:
                result = minimize(objective, x0, method='L-BFGS-B')
                if result.fun < best_value:
                    best_value = result.fun
                    best_params = result.x
            except:
                continue

        if best_params is not None:
            self.kernel.set_params(
                length_scale=np.exp(best_params[0]),
                signal_variance=np.exp(best_params[1])
            )
            self.noise_variance = np.exp(best_params[2])

        # 用最优参数重新拟合
        self.fit(X, y)

        return self
