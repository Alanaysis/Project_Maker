"""
校准算法模块

提供多种校准方法用于计算量化参数：
1. MinMax: 使用激活值的最小最大值
2. Percentile: 使用百分位数
3. Entropy: 使用 KL 散度最小化
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional


class Calibrator(ABC):
    """校准器基类"""

    @abstractmethod
    def calibrate(self, activations: np.ndarray) -> Tuple[float, float]:
        """
        执行校准

        Args:
            activations: 激活值数据

        Returns:
            (min_val, max_val): 校准后的最小最大值
        """
        pass


class MinMaxCalibration(Calibrator):
    """
    MinMax 校准

    使用激活值的最小最大值作为量化范围
    - 优点：简单快速
    - 缺点：对异常值敏感
    """

    def calibrate(self, activations: np.ndarray) -> Tuple[float, float]:
        """
        MinMax 校准

        Args:
            activations: 激活值数据，可以是单个数组或数组列表

        Returns:
            (min_val, max_val)
        """
        if isinstance(activations, list):
            min_val = min(act.min() for act in activations)
            max_val = max(act.max() for act in activations)
        else:
            min_val = activations.min()
            max_val = activations.max()

        return float(min_val), float(max_val)


class PercentileCalibration(Calibrator):
    """
    百分位校准

    使用百分位数作为量化范围
    - 优点：对异常值鲁棒
    - 缺点：需要选择合适的百分位数

    Args:
        percentile: 百分位数，范围 (0, 100)
    """

    def __init__(self, percentile: float = 99.99):
        if not 0 < percentile < 100:
            raise ValueError(f"百分位数必须在 (0, 100) 之间，当前值: {percentile}")
        self.percentile = percentile

    def calibrate(self, activations: np.ndarray) -> Tuple[float, float]:
        """
        百分位校准

        Args:
            activations: 激活值数据

        Returns:
            (min_val, max_val)
        """
        if isinstance(activations, list):
            all_vals = np.concatenate([act.flatten() for act in activations])
        else:
            all_vals = activations.flatten()

        min_val = np.percentile(all_vals, 100 - self.percentile)
        max_val = np.percentile(all_vals, self.percentile)

        return float(min_val), float(max_val)


class EntropyCalibration(Calibrator):
    """
    熵校准 (KL 散度)

    寻找最优阈值，最小化原始分布和量化分布之间的 KL 散度
    - 优点：通常精度最好
    - 缺点：计算量大

    Args:
        num_bins: 直方图 bin 数量
    """

    def __init__(self, num_bins: int = 2048):
        self.num_bins = num_bins

    def calibrate(self, activations: np.ndarray) -> Tuple[float, float]:
        """
        熵校准

        使用 KL 散度最小化寻找最优阈值

        Args:
            activations: 激活值数据

        Returns:
            (min_val, max_val)
        """
        if isinstance(activations, list):
            all_vals = np.concatenate([act.flatten() for act in activations])
        else:
            all_vals = activations.flatten()

        # 计算直方图
        min_val = all_vals.min()
        max_val = all_vals.max()

        # 只考虑正值（对于 ReLU 输出）
        if min_val < 0:
            # 对于有负值的情况，使用绝对值的最大值
            abs_max = max(abs(min_val), abs(max_val))
            min_val = -abs_max
            max_val = abs_max

        # 创建直方图
        hist, bin_edges = np.histogram(all_vals, bins=self.num_bins, range=(min_val, max_val))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # 计算 KL 散度，寻找最优阈值
        best_threshold = max_val
        best_kl_div = float('inf')

        # 尝试不同的阈值
        for threshold_idx in range(self.num_bins // 2, self.num_bins):
            threshold = bin_centers[threshold_idx]

            # 计算截断分布
            clipped_hist = hist.copy()
            clipped_hist[threshold_idx:] = 0

            # 重新归一化
            if clipped_hist.sum() > 0:
                p = clipped_hist / clipped_hist.sum()
            else:
                continue

            # 量化分布
            num_quant_bins = 128  # INT8 对称量化
            quant_hist = self._quantize_distribution(hist, threshold, num_quant_bins)

            # 计算 KL 散度
            kl_div = self._kl_divergence(p, quant_hist)

            if kl_div < best_kl_div:
                best_kl_div = kl_div
                best_threshold = threshold

        return float(min_val), float(best_threshold)

    def _quantize_distribution(
        self, hist: np.ndarray, threshold: float, num_bins: int
    ) -> np.ndarray:
        """量化分布"""
        # 简化实现：将分布映射到量化 bins
        quant_hist = np.zeros(num_bins)
        bin_size = threshold / num_bins

        for i, count in enumerate(hist):
            if i * bin_size < threshold:
                bin_idx = min(int(i * bin_size / bin_size), num_bins - 1)
                quant_hist[bin_idx] += count

        # 归一化
        if quant_hist.sum() > 0:
            quant_hist = quant_hist / quant_hist.sum()

        return quant_hist

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """计算 KL 散度"""
        # 避免 log(0)
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon

        # 归一化
        p = p / p.sum()
        q = q / q.sum()

        # KL(P || Q)
        kl_div = np.sum(p * np.log(p / q))

        return float(kl_div)


class CalibratorFactory:
    """校准器工厂"""

    @staticmethod
    def create(method: str, **kwargs) -> Calibrator:
        """
        创建校准器

        Args:
            method: 校准方法名称
            **kwargs: 校准器参数

        Returns:
            Calibrator 实例
        """
        calibrators = {
            "minmax": MinMaxCalibration,
            "percentile": PercentileCalibration,
            "entropy": EntropyCalibration,
        }

        if method not in calibrators:
            raise ValueError(f"不支持的校准方法: {method}，支持: {list(calibrators.keys())}")

        return calibrators[method](**kwargs)
