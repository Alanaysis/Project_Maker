"""
采集函数模块
============

实现贝叶斯优化常用的采集函数：
- Expected Improvement (EI)
- Upper Confidence Bound (UCB)
- Probability of Improvement (PI)
"""

import numpy as np
from abc import ABC, abstractmethod
from scipy.stats import norm
from typing import Optional


class AcquisitionFunction(ABC):
    """采集函数基类"""

    @abstractmethod
    def __call__(self, X: np.ndarray, gp, y_best: float = None) -> np.ndarray:
        """计算采集函数值"""
        pass


class ExpectedImprovement(AcquisitionFunction):
    """
    期望改进采集函数

    EI(x) = E[max(f(x) - f_best, 0)]
           = (mu(x) - f_best) * Phi(Z) + sigma(x) * phi(Z)

    其中：
    - mu(x): 预测均值
    - sigma(x): 预测标准差
    - f_best: 当前最优值
    - Z = (mu(x) - f_best) / sigma(x)
    - Phi: 标准正态分布 CDF
    - phi: 标准正态分布 PDF

    参数：
        xi: 探索-开发权衡参数（默认 0.01）
    """

    def __init__(self, xi: float = 0.01):
        self.xi = xi

    def __call__(self, X: np.ndarray, gp, y_best: Optional[float] = None) -> np.ndarray:
        """
        计算期望改进

        参数：
            X: 候选点，形状 (n_points, n_features)
            gp: 高斯过程模型
            y_best: 当前最优值

        返回：
            ei: 期望改进值，形状 (n_points,)
        """
        X = np.atleast_2d(X)

        # 获取预测均值和标准差
        mu, sigma = gp.predict(X, return_std=True)
        sigma = sigma.reshape(-1)

        if y_best is None:
            y_best = np.max(gp.y_train)

        # 计算 Z
        with np.errstate(divide='ignore', invalid='ignore'):
            Z = (mu - y_best - self.xi) / sigma
            Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)

        # 计算 EI
        ei = (mu - y_best - self.xi) * norm.cdf(Z) + sigma * norm.pdf(Z)

        # 当 sigma 接近 0 时，EI 应该为 0
        ei[sigma < 1e-8] = 0.0

        return ei


class UpperConfidenceBound(AcquisitionFunction):
    """
    置信上界采集函数

    UCB(x) = mu(x) + kappa * sigma(x)

    参数：
        kappa: 探索参数（默认 2.0）
        是否随迭代衰减
    """

    def __init__(self, kappa: float = 2.0, decay: bool = False):
        self.kappa = kappa
        self.decay = decay
        self.iteration = 0

    def __call__(self, X: np.ndarray, gp, y_best: Optional[float] = None) -> np.ndarray:
        """
        计算置信上界

        参数：
            X: 候选点，形状 (n_points, n_features)
            gp: 高斯过程模型
            y_best: 当前最优值（UCB 不使用）

        返回：
            ucb: 置信上界值，形状 (n_points,)
        """
        X = np.atleast_2d(X)

        # 获取预测均值和标准差
        mu, sigma = gp.predict(X, return_std=True)
        sigma = sigma.reshape(-1)

        # 计算 kappa（可选衰减）
        kappa = self.kappa
        if self.decay:
            kappa = self.kappa * np.sqrt(np.log(self.iteration + 1) / (self.iteration + 1))

        # 计算 UCB
        ucb = mu + kappa * sigma

        self.iteration += 1

        return ucb


class ProbabilityOfImprovement(AcquisitionFunction):
    """
    概率改进采集函数

    PI(x) = P(f(x) > f_best + xi)
           = Phi((mu(x) - f_best - xi) / sigma(x))

    参数：
        xi: 探索参数（默认 0.01）
    """

    def __init__(self, xi: float = 0.01):
        self.xi = xi

    def __call__(self, X: np.ndarray, gp, y_best: Optional[float] = None) -> np.ndarray:
        """
        计算概率改进

        参数：
            X: 候选点，形状 (n_points, n_features)
            gp: 高斯过程模型
            y_best: 当前最优值

        返回：
            pi: 概率改进值，形状 (n_points,)
        """
        X = np.atleast_2d(X)

        # 获取预测均值和标准差
        mu, sigma = gp.predict(X, return_std=True)
        sigma = sigma.reshape(-1)

        if y_best is None:
            y_best = np.max(gp.y_train)

        # 计算 Z
        with np.errstate(divide='ignore', invalid='ignore'):
            Z = (mu - y_best - self.xi) / sigma
            Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)

        # 计算 PI
        pi = norm.cdf(Z)

        # 当 sigma 接近 0 时，PI 应该为 0
        pi[sigma < 1e-8] = 0.0

        return pi


class ThompsonSampling(AcquisitionFunction):
    """
    Thompson 采样

    从后验分布中采样函数，选择最大化采样函数的点。
    """

    def __init__(self, n_samples: int = 1):
        self.n_samples = n_samples

    def __call__(self, X: np.ndarray, gp, y_best: Optional[float] = None) -> np.ndarray:
        """
        计算 Thompson 采样值

        参数：
            X: 候选点，形状 (n_points, n_features)
            gp: 高斯过程模型
            y_best: 当前最优值（不使用）

        返回：
            ts: 采样函数值，形状 (n_points,)
        """
        X = np.atleast_2d(X)

        # 从后验分布采样
        samples = gp.sample(X, n_samples=self.n_samples)

        # 返回采样的平均值
        return np.mean(samples, axis=1)


def create_acquisition(name: str, **kwargs) -> AcquisitionFunction:
    """
    工厂函数：创建采集函数

    参数：
        name: 采集函数名称 ('ei', 'ucb', 'pi', 'ts')
        **kwargs: 采集函数参数

    返回：
        acquisition: 采集函数实例
    """
    acquisitions = {
        'ei': ExpectedImprovement,
        'ucb': UpperConfidenceBound,
        'pi': ProbabilityOfImprovement,
        'ts': ThompsonSampling
    }

    if name not in acquisitions:
        raise ValueError(f"未知的采集函数: {name}，可选: {list(acquisitions.keys())}")

    return acquisitions[name](**kwargs)
