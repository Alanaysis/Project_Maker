"""
降采样模块

将高频数据降采样到较低频率，用于长时间范围查询和数据压缩。
"""

import math
from typing import List, Tuple, Dict, Optional, Any
from .aggregation import Aggregator


class Downsampler:
    """
    降采样器

    将数据点按时间间隔分组，并对每组应用聚合函数。

    支持的时间间隔:
    - 秒级: 1s, 5s, 10s, 15s, 30s
    - 分钟级: 1m, 5m, 10m, 15m, 30m
    - 小时级: 1h, 2h, 3h, 6h, 12h
    - 天级: 1d, 7d, 30d
    """

    # 时间间隔映射（秒）
    INTERVALS = {
        '1s': 1,
        '5s': 5,
        '10s': 10,
        '15s': 15,
        '30s': 30,
        '1m': 60,
        '5m': 300,
        '10m': 600,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '3h': 10800,
        '6h': 21600,
        '12h': 43200,
        '1d': 86400,
        '7d': 604800,
        '30d': 2592000,
    }

    def __init__(self, interval: str, aggregation: str = 'avg', fill: Optional[str] = None):
        """
        初始化降采样器

        Args:
            interval: 时间间隔字符串（如 '1m', '1h'）
            aggregation: 聚合函数名
            fill: 填充策略（None, 'null', '0', 'prev', 'next'）
        """
        self.interval_seconds = self._parse_interval(interval)
        self.aggregation = aggregation
        self.fill = fill
        self.agg_func = Aggregator.get(aggregation)

    @classmethod
    def _parse_interval(cls, interval: str) -> int:
        """
        解析时间间隔字符串

        Args:
            interval: 时间间隔字符串

        Returns:
            int: 秒数
        """
        if interval in cls.INTERVALS:
            return cls.INTERVALS[interval]

        # 尝试解析数字+单位格式
        if len(interval) < 2:
            raise ValueError(f"Invalid interval: {interval}")

        unit = interval[-1]
        try:
            value = int(interval[:-1])
        except ValueError:
            raise ValueError(f"Invalid interval: {interval}")

        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            raise ValueError(f"Invalid interval unit: {unit}")

    def downsample(self, points: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        执行降采样

        Args:
            points: (timestamp, value) 列表，已按时间戳排序

        Returns:
            List[Tuple[int, float]]: 降采样后的 (timestamp, value) 列表
        """
        if not points:
            return []

        # 按时间间隔分组
        buckets: Dict[int, List[float]] = {}
        for ts, value in points:
            bucket_key = (ts // self.interval_seconds) * self.interval_seconds
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(value)

        # 对每个桶应用聚合函数
        results = []
        for bucket_ts in sorted(buckets.keys()):
            values = buckets[bucket_ts]
            agg_value = self.agg_func(values)
            results.append((bucket_ts, agg_value))

        # 处理填充
        if self.fill:
            results = self._fill_gaps(results)

        return results

    def _fill_gaps(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        填充缺失的时间点

        Args:
            results: 降采样结果

        Returns:
            List[Tuple[int, float]]: 填充后的结果
        """
        if len(results) < 2:
            return results

        filled = []
        start_ts = results[0][0]
        end_ts = results[-1][0]

        # 创建结果字典
        result_dict = {ts: val for ts, val in results}

        # 遍历所有时间点
        current_ts = start_ts
        while current_ts <= end_ts:
            if current_ts in result_dict:
                filled.append((current_ts, result_dict[current_ts]))
            else:
                # 根据填充策略填充
                if self.fill == 'null':
                    filled.append((current_ts, None))
                elif self.fill == '0':
                    filled.append((current_ts, 0.0))
                elif self.fill == 'prev':
                    # 使用前一个值
                    if filled:
                        filled.append((current_ts, filled[-1][1]))
                    else:
                        filled.append((current_ts, None))
                elif self.fill == 'next':
                    # 使用下一个值
                    next_val = None
                    for ts, val in results:
                        if ts > current_ts:
                            next_val = val
                            break
                    filled.append((current_ts, next_val))

            current_ts += self.interval_seconds

        return filled

    @classmethod
    def auto_interval(cls, start: int, end: int, max_points: int = 1000) -> str:
        """
        自动选择合适的降采样间隔

        Args:
            start: 开始时间戳
            end: 结束时间戳
            max_points: 最大数据点数

        Returns:
            str: 推荐的时间间隔
        """
        duration = end - start
        interval_seconds = duration / max_points

        # 选择最接近的间隔
        best_interval = '1s'
        best_diff = float('inf')

        for name, seconds in cls.INTERVALS.items():
            diff = abs(seconds - interval_seconds)
            if diff < best_diff:
                best_diff = diff
                best_interval = name

        return best_interval


class MultiDownsampler:
    """
    多降采样器

    同时应用多个降采样配置。
    """

    def __init__(self, configs: List[Dict[str, str]]):
        """
        初始化多降采样器

        Args:
            configs: 降采样配置列表，每个配置包含 interval, aggregation, fill
        """
        self.downsamplers = []
        for config in configs:
            ds = Downsampler(
                interval=config['interval'],
                aggregation=config.get('aggregation', 'avg'),
                fill=config.get('fill')
            )
            self.downsamplers.append(ds)

    def downsample(self, points: List[Tuple[int, float]]) -> List[List[Tuple[int, float]]]:
        """
        执行多个降采样

        Args:
            points: 原始数据点

        Returns:
            List[List[Tuple[int, float]]]: 多个降采样结果
        """
        results = []
        for ds in self.downsamplers:
            results.append(ds.downsample(points))
        return results


class AdaptiveDownsampler:
    """
    自适应降采样器

    根据数据密度自动选择降采样策略。
    """

    def __init__(self, target_points: int = 1000, aggregation: str = 'avg'):
        """
        初始化自适应降采样器

        Args:
            target_points: 目标数据点数
            aggregation: 聚合函数名
        """
        self.target_points = target_points
        self.aggregation = aggregation

    def downsample(self, points: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        执行自适应降采样

        Args:
            points: 原始数据点

        Returns:
            List[Tuple[int, float]]: 降采样后的数据点
        """
        if len(points) <= self.target_points:
            return points

        # 计算时间范围
        start_ts = points[0][0]
        end_ts = points[-1][0]
        duration = end_ts - start_ts

        if duration <= 0:
            return points[:self.target_points]

        # 计算合适的间隔
        interval_seconds = duration / self.target_points

        # 选择最接近的间隔
        interval = Downsampler.auto_interval(start_ts, end_ts, self.target_points)

        # 执行降采样
        downsampler = Downsampler(interval, self.aggregation)
        return downsampler.downsample(points)
