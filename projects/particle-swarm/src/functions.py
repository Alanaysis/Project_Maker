"""
经典测试函数（Benchmark Functions）

用于评估 PSO 算法性能的标准测试函数：
- Sphere: 简单单峰函数
- Rosenbrock: 窄谷函数（"香蕉函数"）
- Rastrigin: 多峰函数，大量局部最优
- Ackley: 多峰函数，大量局部最优
- Griewank: 多峰函数，相关性结构
"""

import numpy as np
from typing import Callable


def sphere(x: np.ndarray) -> float:
    """
    Sphere 函数（球面函数）

    f(x) = sum(x_i^2)
    全局最优: f(0, 0, ..., 0) = 0
    搜索范围: [-100, 100]
    特点: 单峰、凸函数，最简单的测试函数
    """
    return float(np.sum(x**2))


def rosenbrock(x: np.ndarray) -> float:
    """
    Rosenbrock 函数（香蕉函数）

    f(x) = sum(100 * (x_{i+1} - x_i^2)^2 + (1 - x_i)^2)
    全局最优: f(1, 1, ..., 1) = 0
    搜索范围: [-30, 30]
    特点: 单峰但有狭窄的全局最优谷，难以收敛
    """
    n = len(x)
    if n < 2:
        raise ValueError("Rosenbrock 函数至少需要 2 个维度")

    result = 0.0
    for i in range(n - 1):
        result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
    return float(result)


def rastrigin(x: np.ndarray) -> float:
    """
    Rastrigin 函数

    f(x) = 10n + sum(x_i^2 - 10 * cos(2 * pi * x_i))
    全局最优: f(0, 0, ..., 0) = 0
    搜索范围: [-5.12, 5.12]
    特点: 多峰，大量局部最优，但所有局部最优的值相同
    """
    n = len(x)
    return float(10 * n + np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))


def ackley(x: np.ndarray) -> float:
    """
    Ackley 函数

    f(x) = -20 * exp(-0.2 * sqrt(1/n * sum(x_i^2))) - exp(1/n * sum(cos(2*pi*x_i))) + 20 + e
    全局最优: f(0, 0, ..., 0) = 0
    搜索范围: [-32, 32]
    特点: 多峰，大量局部最优，指数函数使搜索困难
    """
    n = len(x)
    sum_sq = np.sum(x**2) / n
    sum_cos = np.sum(np.cos(2 * np.pi * x)) / n

    return float(
        -20 * np.exp(-0.2 * np.sqrt(sum_sq)) - np.exp(sum_cos) + 20 + np.e
    )


def griewank(x: np.ndarray) -> float:
    """
    Griewank 函数

    f(x) = 1 + sum(x_i^2 / 4000) - prod(cos(x_i / sqrt(i+1)))
    全局最优: f(0, 0, ..., 0) = 0
    搜索范围: [-600, 600]
    特点: 多峰，但随着维度增加，局部最优数量减少
    """
    sum_sq = np.sum(x**2) / 4000
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return float(1 + sum_sq - prod_cos)


# 测试函数注册表
BENCHMARK_FUNCTIONS: dict[str, dict] = {
    "sphere": {
        "function": sphere,
        "bounds": (-100.0, 100.0),
        "optimal": 0.0,
        "optimal_position": lambda d: np.zeros(d),
        "description": "单峰球面函数",
    },
    "rosenbrock": {
        "function": rosenbrock,
        "bounds": (-30.0, 30.0),
        "optimal": 0.0,
        "optimal_position": lambda d: np.ones(d),
        "description": "窄谷函数（香蕉函数）",
    },
    "rastrigin": {
        "function": rastrigin,
        "bounds": (-5.12, 5.12),
        "optimal": 0.0,
        "optimal_position": lambda d: np.zeros(d),
        "description": "多峰函数，大量局部最优",
    },
    "ackley": {
        "function": ackley,
        "bounds": (-32.0, 32.0),
        "optimal": 0.0,
        "optimal_position": lambda d: np.zeros(d),
        "description": "多峰函数，指数函数",
    },
    "griewank": {
        "function": griewank,
        "bounds": (-600.0, 600.0),
        "optimal": 0.0,
        "optimal_position": lambda d: np.zeros(d),
        "description": "多峰函数，乘积结构",
    },
}


def get_function(name: str) -> dict:
    """
    获取测试函数信息

    参数:
        name: 函数名称

    返回:
        包含函数、边界、最优值等信息的字典

    异常:
        KeyError: 如果函数名称不存在
    """
    if name not in BENCHMARK_FUNCTIONS:
        available = ", ".join(BENCHMARK_FUNCTIONS.keys())
        raise KeyError(f"未知函数 '{name}'，可用函数: {available}")
    return BENCHMARK_FUNCTIONS[name]
