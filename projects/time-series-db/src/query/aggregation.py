"""
聚合函数模块

实现各种聚合函数，用于数据查询和降采样。
"""

import math
from typing import List, Optional, Callable, Dict, Any


class Aggregator:
    """
    聚合函数集合

    支持的聚合函数:
    - avg: 平均值
    - max: 最大值
    - min: 最小值
    - sum: 求和
    - count: 计数
    - first: 第一个值
    - last: 最后一个值
    - stddev: 标准差
    - median: 中位数
    - p90: 90th 百分位数
    - p95: 95th 百分位数
    - p99: 99th 百分位数
    """

    # 聚合函数注册表
    _functions: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str, func: Callable) -> None:
        """注册聚合函数"""
        cls._functions[name] = func

    @classmethod
    def get(cls, name: str) -> Callable:
        """获取聚合函数"""
        if name not in cls._functions:
            raise ValueError(f"Unknown aggregation function: {name}")
        return cls._functions[name]

    @classmethod
    def aggregate(cls, values: List[float], name: str) -> float:
        """
        执行聚合

        Args:
            values: 数值列表
            name: 聚合函数名

        Returns:
            float: 聚合结果
        """
        func = cls.get(name)
        return func(values)

    @classmethod
    def list_functions(cls) -> List[str]:
        """列出所有可用的聚合函数"""
        return list(cls._functions.keys())


# 内置聚合函数

def avg(values: List[float]) -> float:
    """计算平均值"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def max_value(values: List[float]) -> float:
    """计算最大值"""
    if not values:
        return 0.0
    return max(values)


def min_value(values: List[float]) -> float:
    """计算最小值"""
    if not values:
        return 0.0
    return min(values)


def sum_value(values: List[float]) -> float:
    """计算总和"""
    return sum(values)


def count(values: List[float]) -> float:
    """计算数量"""
    return float(len(values))


def first(values: List[float]) -> float:
    """获取第一个值"""
    if not values:
        return 0.0
    return values[0]


def last(values: List[float]) -> float:
    """获取最后一个值"""
    if not values:
        return 0.0
    return values[-1]


def stddev(values: List[float]) -> float:
    """计算标准差"""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def median(values: List[float]) -> float:
    """计算中位数"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        return sorted_values[n//2]


def percentile(values: List[float], p: float) -> float:
    """
    计算百分位数

    Args:
        values: 数值列表
        p: 百分位数 (0-100)

    Returns:
        float: 百分位数值
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return d0 + d1


def p90(values: List[float]) -> float:
    """计算 90th 百分位数"""
    return percentile(values, 90)


def p95(values: List[float]) -> float:
    """计算 95th 百分位数"""
    return percentile(values, 95)


def p99(values: List[float]) -> float:
    """计算 99th 百分位数"""
    return percentile(values, 99)


def rate(values: List[float]) -> float:
    """计算速率（每秒变化率）"""
    if len(values) < 2:
        return 0.0
    # 假设值是递增的计数器
    return (values[-1] - values[0]) / (len(values) - 1)


def increase(values: List[float]) -> float:
    """计算增量"""
    if len(values) < 2:
        return 0.0
    return values[-1] - values[0]


# 注册所有内置聚合函数
Aggregator.register('avg', avg)
Aggregator.register('max', max_value)
Aggregator.register('min', min_value)
Aggregator.register('sum', sum_value)
Aggregator.register('count', count)
Aggregator.register('first', first)
Aggregator.register('last', last)
Aggregator.register('stddev', stddev)
Aggregator.register('median', median)
Aggregator.register('p90', p90)
Aggregator.register('p95', p95)
Aggregator.register('p99', p99)
Aggregator.register('rate', rate)
Aggregator.register('increase', increase)


class MultiAggregator:
    """
    多聚合器

    同时计算多个聚合函数。
    """

    def __init__(self, aggregation_names: List[str]):
        """
        初始化多聚合器

        Args:
            aggregation_names: 聚合函数名列表
        """
        self.aggregators = {}
        for name in aggregation_names:
            self.aggregators[name] = Aggregator.get(name)

    def aggregate(self, values: List[float]) -> Dict[str, float]:
        """
        执行多个聚合

        Args:
            values: 数值列表

        Returns:
            Dict[str, float]: {聚合函数名: 结果}
        """
        results = {}
        for name, func in self.aggregators.items():
            try:
                results[name] = func(values)
            except Exception as e:
                results[name] = None
        return results


class WindowAggregator:
    """
    窗口聚合器

    在滑动窗口上执行聚合。
    """

    def __init__(self, window_size: int, aggregation: str):
        """
        初始化窗口聚合器

        Args:
            window_size: 窗口大小（数据点数量）
            aggregation: 聚合函数名
        """
        self.window_size = window_size
        self.func = Aggregator.get(aggregation)

    def aggregate(self, values: List[float]) -> List[float]:
        """
        执行窗口聚合

        Args:
            values: 数值列表

        Returns:
            List[float]: 聚合结果列表
        """
        results = []
        for i in range(len(values)):
            start = max(0, i - self.window_size + 1)
            window = values[start:i+1]
            results.append(self.func(window))
        return results
