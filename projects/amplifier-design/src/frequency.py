"""
频率响应分析

实现放大器频率响应的关键概念：
- 增益带宽积 (Gain-Bandwidth Product)
- 相位补偿 (Phase Compensation)
- 波特图分析
- 稳定性分析
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class FrequencyPoint:
    """频率响应数据点"""
    frequency: float      # Hz
    gain_db: float        # dB
    phase_deg: float      # 度
    gain_linear: float    # 线性增益


class GainBandwidthProduct:
    """
    增益带宽积 (GBW) 分析

    增益带宽积是运放最重要的参数之一：
    GBW = |Av| × BW = 常数

    对于单极点系统：
    - 增益每增加 20dB，带宽减小 10 倍
    - 增益每减小 20dB，带宽增加 10 倍

    GBW 决定了：
    - 在给定增益下可获得的最大带宽
    - 在给定带宽下可获得的最大增益
    - 运放的高频性能
    """

    def __init__(self, gbw: float = 1e6):
        """
        Args:
            gbw: 增益带宽积, Hz (默认 1MHz)
        """
        self.gbw = gbw

    def bandwidth_at_gain(self, gain: float) -> float:
        """
        给定增益下的带宽

        BW = GBW / |Av|

        Args:
            gain: 电压增益 (线性值)

        Returns:
            float: 带宽, Hz
        """
        return self.gbw / abs(gain)

    def gain_at_bandwidth(self, bw: float) -> float:
        """
        给定带宽下可获得的最大增益

        |Av| = GBW / BW

        Args:
            bw: 带宽, Hz

        Returns:
            float: 最大增益 (线性值)
        """
        return self.gbw / bw

    def gain_db_at_frequency(self, gain_dc: float, f: np.ndarray) -> np.ndarray:
        """
        计算单极点系统的增益频率响应

        |H(f)| = |Av| / sqrt(1 + (f/f_p)^2)
        f_p = GBW / |Av|

        Args:
            gain_dc: 低频增益 (线性值)
            f: 频率数组, Hz

        Returns:
            np.ndarray: 增益 (dB)
        """
        f_p = self.gbw / abs(gain_dc)
        gain = abs(gain_dc) / np.sqrt(1 + (f / f_p) ** 2)
        return 20 * np.log10(gain + 1e-30)

    def phase_at_frequency(self, gain_dc: float, f: np.ndarray) -> np.ndarray:
        """
        计算单极点系统的相位频率响应

        phi(f) = -arctan(f/f_p)

        Args:
            gain_dc: 低频增益 (线性值)
            f: 频率数组, Hz

        Returns:
            np.ndarray: 相位 (度)
        """
        f_p = self.gbw / abs(gain_dc)
        return -np.degrees(np.arctan(f / f_p))

    def settling_time(self, gain: float, accuracy: float = 0.01) -> float:
        """
        建立时间 (到指定精度)

        t_s ≈ -ln(accuracy) / (pi * BW)

        Args:
            gain: 电压增益
            accuracy: 建立精度 (如0.01表示1%)

        Returns:
            float: 建立时间, s
        """
        bw = self.bandwidth_at_gain(gain)
        return -np.log(accuracy) / (np.pi * bw)

    def slew_rate_limited_bandwidth(self, V_peak: float, SR: float) -> float:
        """
        受转换速率限制的最大频率

        f_max = SR / (2 * pi * V_peak)

        Args:
            V_peak: 峰值输出电压, V
            SR: 转换速率, V/s

        Returns:
            float: 最大频率, Hz
        """
        return SR / (2 * np.pi * V_peak)

    def summary(self, gain: float) -> dict:
        """给定增益下的GBW摘要"""
        bw = self.bandwidth_at_gain(gain)
        return {
            'gain': gain,
            'gain_dB': 20 * np.log10(abs(gain)),
            'bandwidth': bw,
            'gain_bandwidth_product': self.gbw,
            'unity_gain_bandwidth': self.gbw,
        }


class PhaseCompensation:
    """
    相位补偿技术

    目的: 确保反馈放大器在工作频率范围内稳定

    常用补偿方法:
    1. 主极点补偿 (Dominant Pole Compensation)
    2. 超前补偿 (Lead Compensation)
    3. 滞后补偿 (Lag Compensation)
    4. 超前-滞后补偿 (Lead-Lag Compensation)
    5. 密勒补偿 (Miller Compensation)
    """

    @staticmethod
    def dominant_pole_compensation(gbw_original: float, f_p1: float,
                                    f_p2: float, f_new_pole: float) -> dict:
        """
        主极点补偿

        将开环带宽降低到安全值，确保在单位增益交点处有足够相位裕度。

        Args:
            gbw_original: 原始增益带宽积, Hz
            f_p1: 第一个极点频率, Hz
            f_p2: 第二个极点频率, Hz
            f_new_pole: 新增的主极点频率, Hz

        Returns:
            dict: 补偿后的参数
        """
        # 补偿后的开环带宽由新主极点决定
        gbw_compensated = f_new_pole * (gbw_original / f_p1)

        # 相位裕度估算
        # 在单位增益频率处，相位应大于 45 度
        f_unity = gbw_compensated
        phase_contrib_p2 = -np.degrees(np.arctan(f_unity / f_p2))
        phase_contrib_new = -np.degrees(np.arctan(f_unity / f_new_pole))
        phase_margin = 180 + phase_contrib_p2 + phase_contrib_new

        return {
            'original_gbw': gbw_original,
            'compensated_gbw': gbw_compensated,
            'new_pole': f_new_pole,
            'phase_margin': phase_margin,
            'stable': phase_margin > 45,
        }

    @staticmethod
    def lead_compensation(f_crossover: float, phase_deficit: float) -> dict:
        """
        超前补偿

        在交越频率附近添加相位超前，提高相位裕度。

        Args:
            f_crossover: 交越频率, Hz
            phase_deficit: 需要补偿的相位 (度)

        Returns:
            dict: 补偿网络参数
        """
        # 最大相位超前发生在 f_z 和 f_p 的几何平均处
        # f_center = f_crossover
        # alpha = (1 + sin(phi_max)) / (1 - sin(phi_max))
        phi_rad = np.radians(phase_deficit)
        alpha = (1 + np.sin(phi_rad)) / (1 - np.sin(phi_rad))

        f_zero = f_crossover / np.sqrt(alpha)
        f_pole = f_crossover * np.sqrt(alpha)

        return {
            'center_frequency': f_crossover,
            'phase_boost_deg': phase_deficit,
            'zero_frequency': f_zero,
            'pole_frequency': f_pole,
            'alpha': alpha,
        }

    @staticmethod
    def lag_compensation(desired_bw: float, original_gbw: float,
                          feedback_gain: float) -> dict:
        """
        滞后补偿

        降低高频增益，在保证稳定性的前提下维持低频性能。

        Args:
            desired_bw: 期望带宽, Hz
            original_gbw: 原始增益带宽积, Hz
            feedback_gain: 反馈网络增益

        Returns:
            dict: 补偿参数
        """
        # 滞后网络在 desired_bw 处开始衰减
        f_lag = desired_bw / 10  # 滞后零点

        # 新的单位增益频率
        new_ugf = original_gbw / feedback_gain

        return {
            'desired_bandwidth': desired_bw,
            'lag_zero_frequency': f_lag,
            'new_unity_gain_freq': new_ugf,
            'gain_reduction_dB': 20 * np.log10(feedback_gain),
        }

    @staticmethod
    def miller_compensation(C_m: float, g_m: float, R_out: float) -> dict:
        """
        密勒补偿

        利用密勒效应，通过小电容实现大等效电容。
        常用于多级放大器内部补偿。

        Args:
            C_m: 密勒电容, F
            g_m: 跨导, S
            R_out: 输出电阻, Ohm

        Returns:
            dict: 补偿参数
        """
        # 主极点: f_p1 = 1 / (2 * pi * R_out * C_m * A_v2)
        # 其中 A_v2 = g_m * R_out (第二级增益)
        A_v2 = g_m * R_out
        C_effective = C_m * (1 + A_v2)

        f_p1 = 1 / (2 * np.pi * R_out * C_effective)
        f_p2 = g_m / (2 * np.pi * C_m)  # 第二极点被推高

        return {
            'miller_capacitance': C_m,
            'effective_capacitance': C_effective,
            'dominant_pole': f_p1,
            'second_pole': f_p2,
            'pole_splitting_ratio': f_p2 / f_p1,
        }


class StabilityAnalyzer:
    """
    环路稳定性分析器

    分析反馈放大器的稳定性：
    - 增益裕度 (Gain Margin)
    - 相位裕度 (Phase Margin)
    - 奈奎斯特判据
    """

    @staticmethod
    def loop_gain_tf(gbw: float, gain: float,
                     poles: list = None, zeros: list = None) -> callable:
        """
        创建环路增益传递函数

        Args:
            gbw: 增益带宽积, Hz
            gain: 低频环路增益
            poles: 额外极点列表, Hz
            zeros: 额外零点列表, Hz

        Returns:
            callable: 传递函数 H(f)
        """
        poles = poles or []
        zeros = zeros or []

        def tf(f):
            s = 1j * 2 * np.pi * f
            # 主极点 (由 GBW 决定)
            f_p0 = gbw / gain
            H = gain / (1 + s / (2 * np.pi * f_p0))

            # 额外极点
            for p in poles:
                H = H / (1 + s / (2 * np.pi * p))

            # 额外零点
            for z in zeros:
                H = H * (1 + s / (2 * np.pi * z))

            return H

        return tf

    @staticmethod
    def phase_margin(tf: callable, f_range: tuple = (1, 1e8)) -> dict:
        """
        计算相位裕度

        Args:
            tf: 传递函数 callable
            f_range: 频率范围 (f_min, f_max)

        Returns:
            dict: 相位裕度和相关参数
        """
        f = np.logspace(np.log10(f_range[0]), np.log10(f_range[1]), 10000)
        H = tf(f)

        # 找到增益交越频率 (|H| = 1)
        gain_db = 20 * np.log10(np.abs(H) + 1e-30)
        phase = np.degrees(np.angle(H))

        # 在交越频率处插值相位
        idx_cross = np.argmin(np.abs(gain_db))

        if idx_cross == 0 or idx_cross == len(f) - 1:
            phase_margin_val = 180 + phase[idx_cross]
        else:
            # 线性插值精确找到交越频率
            if gain_db[idx_cross - 1] * gain_db[idx_cross + 1] < 0:
                # 跨越0dB
                f1, f2 = f[idx_cross - 1], f[idx_cross + 1]
                g1, g2 = gain_db[idx_cross - 1], gain_db[idx_cross + 1]
                f_cross = f1 + (f2 - f1) * (-g1) / (g2 - g1)
                phase_cross = np.interp(f_cross, f[idx_cross - 1:idx_cross + 2],
                                        phase[idx_cross - 1:idx_cross + 2])
                phase_margin_val = 180 + phase_cross
            else:
                phase_margin_val = 180 + phase[idx_cross]

        # 找到相位交越频率 (phase = -180)
        phase_diff = np.abs(phase + 180)
        idx_phase = np.argmin(phase_diff)
        gain_at_phase_cross = gain_db[idx_phase]

        return {
            'gain_crossover_freq': f[idx_cross],
            'phase_margin': phase_margin_val,
            'gain_margin': -gain_at_phase_cross,
            'stable': phase_margin_val > 45,
            'conditionally_stable': 30 < phase_margin_val <= 45,
            'unstable': phase_margin_val <= 30,
        }

    @staticmethod
    def step_response_params(phase_margin: float) -> dict:
        """
        从相位裕度估算阶跃响应参数

        Args:
            phase_margin: 相位裕度, 度

        Returns:
            dict: 阶跃响应参数
        """
        # 超调量估算: OS% ≈ 100 * exp(-pi * PM / sqrt(1 - (PM/180)^2))
        # 简化: OS% ≈ 100 * exp(-pi * PM / 180) for PM > 30
        pm_rad = np.radians(phase_margin)

        if phase_margin > 20:
            zeta = -np.log(phase_margin / 100) / np.sqrt(np.pi ** 2 + np.log(phase_margin / 100) ** 2)
            zeta = min(zeta, 1.0)
        else:
            zeta = 0.1

        overshoot_pct = 100 * np.exp(-np.pi * zeta / np.sqrt(1 - zeta ** 2)) if zeta < 1 else 0

        return {
            'phase_margin': phase_margin,
            'damping_ratio': zeta,
            'overshoot_percent': overshoot_pct,
            'well_damped': phase_margin >= 60,
            'underdamped': phase_margin < 60,
        }
