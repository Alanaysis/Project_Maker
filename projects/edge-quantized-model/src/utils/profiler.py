"""
性能分析模块

提供性能分析和计时功能
"""

import time
import numpy as np
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """性能分析结果"""
    name: str
    total_time: float = 0.0
    call_count: int = 0
    min_time: float = float('inf')
    max_time: float = 0.0
    times: List[float] = field(default_factory=list)

    @property
    def mean_time(self) -> float:
        """平均时间"""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0

    @property
    def std_time(self) -> float:
        """时间标准差"""
        if len(self.times) < 2:
            return 0.0
        return float(np.std(self.times))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "total_time_ms": self.total_time * 1000,
            "call_count": self.call_count,
            "mean_time_ms": self.mean_time * 1000,
            "std_time_ms": self.std_time * 1000,
            "min_time_ms": self.min_time * 1000,
            "max_time_ms": self.max_time * 1000,
        }


class Profiler:
    """
    性能分析器

    用于收集和分析性能数据

    使用示例:
        profiler = Profiler()

        with profiler.profile("conv2d"):
            # 执行卷积
            pass

        profiler.print_stats()
    """

    def __init__(self):
        """初始化性能分析器"""
        self.results: Dict[str, ProfileResult] = {}
        self._stack: List[str] = []

    @contextmanager
    def profile(self, name: str):
        """
        性能分析上下文管理器

        Args:
            name: 分析名称
        """
        start_time = time.time()
        self._stack.append(name)

        try:
            yield
        finally:
            end_time = time.time()
            elapsed = end_time - start_time
            self._stack.pop()

            # 记录结果
            if name not in self.results:
                self.results[name] = ProfileResult(name=name)

            result = self.results[name]
            result.total_time += elapsed
            result.call_count += 1
            result.min_time = min(result.min_time, elapsed)
            result.max_time = max(result.max_time, elapsed)
            result.times.append(elapsed)

    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取统计信息

        Args:
            name: 分析名称

        Returns:
            统计信息字典
        """
        if name in self.results:
            return self.results[name].to_dict()
        return None

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有统计信息

        Returns:
            所有统计信息字典
        """
        return {name: result.to_dict() for name, result in self.results.items()}

    def print_stats(self):
        """打印统计信息"""
        if not self.results:
            logger.info("没有性能数据")
            return

        logger.info("\n" + "=" * 60)
        logger.info("性能分析报告")
        logger.info("=" * 60)

        # 按总时间排序
        sorted_results = sorted(
            self.results.values(),
            key=lambda x: x.total_time,
            reverse=True,
        )

        for result in sorted_results:
            logger.info(f"\n{result.name}:")
            logger.info(f"  调用次数: {result.call_count}")
            logger.info(f"  总时间: {result.total_time * 1000:.2f} ms")
            logger.info(f"  平均时间: {result.mean_time * 1000:.2f} ms")
            logger.info(f"  标准差: {result.std_time * 1000:.2f} ms")
            logger.info(f"  最小时间: {result.min_time * 1000:.2f} ms")
            logger.info(f"  最大时间: {result.max_time * 1000:.2f} ms")

        logger.info("\n" + "=" * 60)

    def reset(self):
        """重置性能分析器"""
        self.results.clear()


class Timer:
    """
    计时器

    用于简单的计时操作

    使用示例:
        timer = Timer()
        timer.start()

        # 执行操作

        elapsed = timer.stop()
        print(f"耗时: {elapsed * 1000:.2f} ms")
    """

    def __init__(self):
        """初始化计时器"""
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def start(self):
        """开始计时"""
        self._start_time = time.time()
        self._end_time = None

    def stop(self) -> float:
        """
        停止计时

        Returns:
            耗时（秒）
        """
        if self._start_time is None:
            raise RuntimeError("计时器未启动")

        self._end_time = time.time()
        return self._end_time - self._start_time

    @property
    def elapsed(self) -> float:
        """
        获取已用时间

        Returns:
            已用时间（秒）
        """
        if self._start_time is None:
            return 0.0

        if self._end_time is not None:
            return self._end_time - self._start_time

        return time.time() - self._start_time

    @contextmanager
    def time(self):
        """
        计时上下文管理器

        Yields:
            None
        """
        self.start()
        try:
            yield
        finally:
            self.stop()


def benchmark(
    func,
    args: tuple = (),
    kwargs: dict = None,
    num_iterations: int = 100,
    warmup_iterations: int = 10,
    name: str = "benchmark",
) -> Dict[str, float]:
    """
    基准测试

    Args:
        func: 要测试的函数
        args: 位置参数
        kwargs: 关键字参数
        num_iterations: 迭代次数
        warmup_iterations: 预热次数
        name: 测试名称

    Returns:
        性能统计
    """
    if kwargs is None:
        kwargs = {}

    # 预热
    for _ in range(warmup_iterations):
        func(*args, **kwargs)

    # 测试
    times = []
    for _ in range(num_iterations):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        times.append(end_time - start_time)

    times = np.array(times)

    return {
        "name": name,
        "mean_ms": float(np.mean(times) * 1000),
        "std_ms": float(np.std(times) * 1000),
        "min_ms": float(np.min(times) * 1000),
        "max_ms": float(np.max(times) * 1000),
        "median_ms": float(np.median(times) * 1000),
        "p95_ms": float(np.percentile(times, 95) * 1000),
        "p99_ms": float(np.percentile(times, 99) * 1000),
        "fps": float(1.0 / np.mean(times)),
        "iterations": num_iterations,
    }
