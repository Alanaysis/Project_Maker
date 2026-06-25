"""
贝叶斯优化库
============

一个基于高斯过程的贝叶斯优化实现。

主要组件：
- gaussian_process: 高斯过程回归
- acquisition: 采集函数（EI, UCB, PI）
- optimizer: 贝叶斯优化器
"""

__version__ = "0.1.0"
__author__ = "AI Analysis"

from .gaussian_process import GaussianProcess
from .acquisition import ExpectedImprovement, UpperConfidenceBound, ProbabilityOfImprovement
from .optimizer import BayesianOptimizer
