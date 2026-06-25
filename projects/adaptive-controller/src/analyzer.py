"""
性能分析器

提供自适应控制系统的性能评估工具。

评估指标：
- 跟踪误差 (MSE, RMSE, 最大误差)
- 稳态误差
- 上升时间
- 调节时间
- 超调量
- 控制能量
- 参数收敛性
"""

import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class TransientMetrics:
    """瞬态性能指标"""
    rise_time: float  # 上升时间 (10%-90%)
    settling_time: float  # 调节时间 (进入±2%范围)
    overshoot: float  # 超调量 (%)
    peak_time: float  # 峰值时间
    peak_value: float  # 峰值


@dataclass
class SteadyStateMetrics:
    """稳态性能指标"""
    steady_state_error: float  # 稳态误差
    steady_state_value: float  # 稳态值
    settling_band: float  # 稳态波动范围


@dataclass
class ControlMetrics:
    """控制性能指标"""
    control_energy: float  # 控制能量 (∫u²dt)
    max_control: float  # 最大控制量
    control_variance: float  # 控制量方差


@dataclass
class TrackingMetrics:
    """跟踪性能指标"""
    mse: float  # 均方误差
    rmse: float  # 均方根误差
    mae: float  # 平均绝对误差
    max_error: float  # 最大绝对误差
    integral_abs_error: float  # 绝对误差积分 (IAE)
    integral_squared_error: float  # 平方误差积分 (ISE)
    integral_time_abs_error: float  # 时间加权绝对误差积分 (ITAE)


class PerformanceAnalyzer:
    """
    性能分析器

    分析自适应控制系统的各项性能指标。

    参数：
        tolerance: 稳态误差容限 (默认 2%)
    """

    def __init__(self, tolerance: float = 0.02):
        self.tolerance = tolerance

    def compute_metrics(
        self,
        times: np.ndarray,
        reference: np.ndarray,
        actual: np.ndarray,
        control: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        计算所有性能指标

        参数：
            times: 时间序列
            reference: 参考输出
            actual: 实际输出
            control: 控制信号 (可选)

        返回：
            性能指标字典
        """
        # 计算跟踪误差
        error = actual - reference

        # 跟踪指标
        tracking = self._compute_tracking_metrics(times, error)

        # 瞬态指标
        transient = self._compute_transient_metrics(times, actual, reference)

        # 稳态指标
        steady_state = self._compute_steady_state_metrics(error)

        # 控制指标
        if control is not None:
            control_metrics = self._compute_control_metrics(times, control)
        else:
            control_metrics = ControlMetrics(0, 0, 0)

        # 合并所有指标
        metrics = {
            # 跟踪指标
            "mse": tracking.mse,
            "rmse": tracking.rmse,
            "mae": tracking.mae,
            "max_error": tracking.max_error,
            "iae": tracking.integral_abs_error,
            "ise": tracking.integral_squared_error,
            "itae": tracking.integral_time_abs_error,

            # 瞬态指标
            "rise_time": transient.rise_time,
            "settling_time": transient.settling_time,
            "overshoot": transient.overshoot,
            "peak_time": transient.peak_time,
            "peak_value": transient.peak_value,

            # 稳态指标
            "steady_state_error": steady_state.steady_state_error,
            "steady_state_value": steady_state.steady_state_value,
            "settling_band": steady_state.settling_band,

            # 控制指标
            "control_energy": control_metrics.control_energy,
            "max_control": control_metrics.max_control,
            "control_variance": control_metrics.control_variance,
        }

        return metrics

    def _compute_tracking_metrics(
        self,
        times: np.ndarray,
        error: np.ndarray,
    ) -> TrackingMetrics:
        """计算跟踪性能指标"""
        dt = times[1] - times[0] if len(times) > 1 else 1.0

        abs_error = np.abs(error)
        squared_error = error**2

        mse = np.mean(squared_error)
        rmse = np.sqrt(mse)
        mae = np.mean(abs_error)
        max_error = np.max(abs_error)

        # 积分指标
        iae = np.sum(abs_error) * dt
        ise = np.sum(squared_error) * dt
        itae = np.sum(times * abs_error) * dt

        return TrackingMetrics(
            mse=mse,
            rmse=rmse,
            mae=mae,
            max_error=max_error,
            integral_abs_error=iae,
            integral_squared_error=ise,
            integral_time_abs_error=itae,
        )

    def _compute_transient_metrics(
        self,
        times: np.ndarray,
        actual: np.ndarray,
        reference: np.ndarray,
    ) -> TransientMetrics:
        """
        计算瞬态性能指标

        假设阶跃响应，计算上升时间、调节时间、超调量等
        """
        # 计算稳态值 (取最后 10% 的平均值)
        n = len(actual)
        steady_state_value = np.mean(actual[int(0.9 * n):])

        # 计算参考值
        ref_value = np.mean(reference[int(0.9 * n):])

        # 归一化响应
        if abs(ref_value) > 1e-6:
            normalized = actual / ref_value
        else:
            normalized = actual

        # 上升时间 (10% 到 90%)
        rise_time = self._compute_rise_time(times, normalized)

        # 调节时间 (进入±2% 范围)
        settling_time = self._compute_settling_time(times, normalized)

        # 超调量
        overshoot = self._compute_overshoot(normalized)

        # 峰值时间和峰值
        peak_idx = np.argmax(np.abs(actual))
        peak_time = times[peak_idx]
        peak_value = actual[peak_idx]

        return TransientMetrics(
            rise_time=rise_time,
            settling_time=settling_time,
            overshoot=overshoot,
            peak_time=peak_time,
            peak_value=peak_value,
        )

    def _compute_rise_time(self, times: np.ndarray, response: np.ndarray) -> float:
        """计算上升时间 (10% 到 90%)"""
        try:
            # 找到第一次达到 10% 的时间
            idx_10 = np.where(response >= 0.1)[0][0]
            # 找到第一次达到 90% 的时间
            idx_90 = np.where(response >= 0.9)[0][0]
            return times[idx_90] - times[idx_10]
        except IndexError:
            return float('inf')

    def _compute_settling_time(self, times: np.ndarray, response: np.ndarray) -> float:
        """计算调节时间 (进入±2% 范围)"""
        tolerance = self.tolerance
        steady_value = 1.0  # 归一化后的稳态值

        # 从后往前找，找到最后一次超出容限的时间
        for i in range(len(response) - 1, -1, -1):
            if abs(response[i] - steady_value) > tolerance:
                if i < len(response) - 1:
                    return times[i + 1]
                else:
                    return times[-1]
        return times[0]

    def _compute_overshoot(self, response: np.ndarray) -> float:
        """计算超调量 (%)"""
        steady_value = 1.0  # 归一化后的稳态值
        peak_value = np.max(response)

        if steady_value > 1e-6:
            overshoot = (peak_value - steady_value) / steady_value * 100
            return max(0, overshoot)
        return 0.0

    def _compute_steady_state_metrics(self, error: np.ndarray) -> SteadyStateMetrics:
        """计算稳态性能指标"""
        # 取最后 10% 的误差
        n = len(error)
        steady_error = error[int(0.9 * n):]

        steady_state_error = np.mean(steady_error)
        steady_state_value = 1.0 - steady_state_error  # 假设参考值为 1
        settling_band = np.std(steady_error)

        return SteadyStateMetrics(
            steady_state_error=steady_state_error,
            steady_state_value=steady_state_value,
            settling_band=settling_band,
        )

    def _compute_control_metrics(
        self,
        times: np.ndarray,
        control: np.ndarray,
    ) -> ControlMetrics:
        """计算控制性能指标"""
        dt = times[1] - times[0] if len(times) > 1 else 1.0

        control_energy = np.sum(control**2) * dt
        max_control = np.max(np.abs(control))
        control_variance = np.var(control)

        return ControlMetrics(
            control_energy=control_energy,
            max_control=max_control,
            control_variance=control_variance,
        )

    def compute_parameter_convergence(
        self,
        param_history: Dict[str, np.ndarray],
        final_values: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        计算参数收敛性

        参数：
            param_history: 参数历史
            final_values: 最终值 (可选)

        返回：
            参数收敛性指标
        """
        convergence = {}

        for key, values in param_history.items():
            # 计算收敛时间 (参数变化率小于阈值)
            if len(values) > 1:
                diff = np.abs(np.diff(values))
                threshold = 0.01 * np.std(values)

                # 找到收敛点
                converged = False
                convergence_time = len(values)
                for i in range(len(diff) - 1, -1, -1):
                    if diff[i] > threshold:
                        convergence_time = i + 1
                        converged = True
                        break

                convergence[key] = {
                    "converged": converged,
                    "convergence_time": convergence_time,
                    "final_value": float(values[-1]),
                    "initial_value": float(values[0]),
                    "variation": float(np.std(values)),
                }

        return convergence

    def generate_report(
        self,
        metrics: Dict[str, float],
    ) -> str:
        """
        生成性能报告

        参数：
            metrics: 性能指标字典

        返回：
            格式化的性能报告
        """
        report = "=" * 60 + "\n"
        report += "自适应控制系统性能报告\n"
        report += "=" * 60 + "\n\n"

        report += "【跟踪性能指标】\n"
        report += f"  均方误差 (MSE):        {metrics.get('mse', 0):.6f}\n"
        report += f"  均方根误差 (RMSE):     {metrics.get('rmse', 0):.6f}\n"
        report += f"  平均绝对误差 (MAE):    {metrics.get('mae', 0):.6f}\n"
        report += f"  最大误差:              {metrics.get('max_error', 0):.6f}\n"
        report += f"  绝对误差积分 (IAE):    {metrics.get('iae', 0):.6f}\n"
        report += f"  平方误差积分 (ISE):    {metrics.get('ise', 0):.6f}\n"
        report += f"  时间加权误差 (ITAE):   {metrics.get('itae', 0):.6f}\n\n"

        report += "【瞬态性能指标】\n"
        report += f"  上升时间:              {metrics.get('rise_time', 0):.4f} s\n"
        report += f"  调节时间:              {metrics.get('settling_time', 0):.4f} s\n"
        report += f"  超调量:                {metrics.get('overshoot', 0):.2f} %\n"
        report += f"  峰值时间:              {metrics.get('peak_time', 0):.4f} s\n"
        report += f"  峰值:                  {metrics.get('peak_value', 0):.4f}\n\n"

        report += "【稳态性能指标】\n"
        report += f"  稳态误差:              {metrics.get('steady_state_error', 0):.6f}\n"
        report += f"  稳态值:                {metrics.get('steady_state_value', 0):.4f}\n"
        report += f"  稳态波动:              {metrics.get('settling_band', 0):.6f}\n\n"

        report += "【控制性能指标】\n"
        report += f"  控制能量:              {metrics.get('control_energy', 0):.4f}\n"
        report += f"  最大控制量:            {metrics.get('max_control', 0):.4f}\n"
        report += f"  控制量方差:            {metrics.get('control_variance', 0):.6f}\n"

        report += "=" * 60 + "\n"

        return report
