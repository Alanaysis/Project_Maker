"""
去模糊化模块

将模糊输出转换为精确值

去模糊化方法:
- 重心法 (Center of Gravity, COG)
- 最大隶属度法 (Mean of Maximum, MOM)
- 面积中心法 (Center of Sums, COS)
- 加权平均法 (Weighted Average)
"""

import numpy as np
from typing import Dict, List, Tuple, Union


class Defuzzifier:
    """
    去模糊化器

    将模糊输出转换为精确值

    支持的去模糊化方法:
    - 'cog': 重心法 (Center of Gravity)
    - 'mom': 最大隶属度法 (Mean of Maximum)
    - 'cos': 面积中心法 (Center of Sums)
    - 'wa': 加权平均法 (Weighted Average)
    """

    def __init__(self, method: str = 'cog'):
        """
        初始化去模糊化器

        参数:
            method: 去模糊化方法 ('cog', 'mom', 'cos', 'wa')
        """
        self.method = method.lower()
        valid_methods = ['cog', 'mom', 'cos', 'wa']
        if self.method not in valid_methods:
            raise ValueError(f"不支持的方法: {method}. 可用方法: {valid_methods}")

    def defuzzify(self, x: np.ndarray, mf_values: np.ndarray) -> float:
        """
        去模糊化

        参数:
            x: 论域值数组
            mf_values: 隶属函数值数组

        返回:
            精确输出值
        """
        x = np.asarray(x, dtype=float)
        mf_values = np.asarray(mf_values, dtype=float)

        if len(x) != len(mf_values):
            raise ValueError("x 和 mf_values 长度必须相同")

        if self.method == 'cog':
            return self._center_of_gravity(x, mf_values)
        elif self.method == 'mom':
            return self._mean_of_maximum(x, mf_values)
        elif self.method == 'cos':
            return self._center_of_sums(x, mf_values)
        elif self.method == 'wa':
            return self._weighted_average(x, mf_values)
        else:
            raise ValueError(f"不支持的方法: {self.method}")

    def _center_of_gravity(self, x: np.ndarray, mf_values: np.ndarray) -> float:
        """
        重心法 (Center of Gravity)

        计算隶属函数曲线下的重心

        公式:
            x* = ∫(x * μ(x)) dx / ∫ μ(x) dx

        参数:
            x: 论域值数组
            mf_values: 隶属函数值数组

        返回:
            重心位置
        """
        numerator = np.sum(x * mf_values)
        denominator = np.sum(mf_values)

        if denominator == 0:
            # 如果没有激活，返回论域中心
            return np.mean(x)

        return numerator / denominator

    def _mean_of_maximum(self, x: np.ndarray, mf_values: np.ndarray) -> float:
        """
        最大隶属度法 (Mean of Maximum)

        返回最大隶属度对应值的平均值

        参数:
            x: 论域值数组
            mf_values: 隶属函数值数组

        返回:
            最大隶属度位置的平均值
        """
        max_mf = np.max(mf_values)

        if max_mf == 0:
            return np.mean(x)

        # 找到所有最大隶属度的位置
        max_indices = np.where(mf_values == max_mf)[0]

        # 返回这些位置的平均值
        return np.mean(x[max_indices])

    def _center_of_sums(self, x: np.ndarray, mf_values: np.ndarray) -> float:
        """
        面积中心法 (Center of Sums)

        基于数值积分的精确重心计算，使用梯形积分公式

        公式:
            x* = ∫(x * μ(x)) dx / ∫ μ(x) dx

        参数:
            x: 论域值数组
            mf_values: 隶属函数值数组

        返回:
            面积中心位置
        """
        # 使用梯形积分
        numerator = np.trapz(x * mf_values, x)
        denominator = np.trapz(mf_values, x)

        if denominator == 0:
            return np.mean(x)

        return numerator / denominator

    def _weighted_average(self, x: np.ndarray, mf_values: np.ndarray) -> float:
        """
        加权平均法

        使用隶属度作为权重计算加权平均值。
        与重心法的区别在于此处使用加权平均而非积分。

        公式:
            x* = Σ(xi * wi) / Σ wi
            其中 wi = μ(xi)

        参数:
            x: 论域值数组
            mf_values: 隶属函数值数组

        返回:
            加权平均值
        """
        weights = mf_values
        total_weight = np.sum(weights)

        if total_weight == 0:
            return np.mean(x)

        return np.sum(x * weights) / total_weight

    def defuzzify_multiple(self, x: np.ndarray,
                           fuzzy_outputs: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        对多个输出变量进行去模糊化

        参数:
            x: 论域值数组 (假设所有变量共享相同论域)
            fuzzy_outputs: 模糊输出字典
                格式: {变量名: 隶属函数值数组}

        返回:
            精确输出值字典
                格式: {变量名: 精确值}
        """
        results = {}

        for var_name, mf_values in fuzzy_outputs.items():
            results[var_name] = self.defuzzify(x, mf_values)

        return results

    def get_method(self) -> str:
        """
        获取当前去模糊化方法

        返回:
            方法名称
        """
        return self.method

    def set_method(self, method: str):
        """
        设置去模糊化方法

        参数:
            method: 方法名称
        """
        valid_methods = ['cog', 'mom', 'cos', 'wa']
        if method.lower() not in valid_methods:
            raise ValueError(f"不支持的方法: {method}. 可用方法: {valid_methods}")
        self.method = method.lower()

    def __repr__(self):
        return f"Defuzzifier(method='{self.method}')"
