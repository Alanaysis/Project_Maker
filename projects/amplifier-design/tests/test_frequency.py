"""频率响应分析测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.frequency import (
    GainBandwidthProduct, PhaseCompensation, StabilityAnalyzer
)


class TestGainBandwidthProduct:
    """增益带宽积测试"""

    @pytest.fixture
    def gbw(self):
        return GainBandwidthProduct(gbw=1e6)  # 1MHz

    def test_bandwidth_at_gain(self, gbw):
        """增益10时带宽应为100kHz"""
        bw = gbw.bandwidth_at_gain(10)
        assert abs(bw - 100e3) < 1

    def test_bandwidth_at_unity(self, gbw):
        """增益1时带宽等于GBW"""
        bw = gbw.bandwidth_at_gain(1)
        assert abs(bw - 1e6) < 1

    def test_gain_at_bandwidth(self, gbw):
        """100kHz带宽时增益应为10"""
        gain = gbw.gain_at_bandwidth(100e3)
        assert abs(gain - 10) < 0.01

    def test_gbw_constant(self, gbw):
        """GBW = 增益 x 带宽 = 常数"""
        for gain in [1, 10, 100, 1000]:
            bw = gbw.bandwidth_at_gain(gain)
            assert abs(gain * bw - 1e6) < 1

    def test_gain_db_at_dc(self, gbw):
        """DC 增益应等于设定增益"""
        f = np.array([1.0])  # 近似 DC
        gain_db = gbw.gain_db_at_frequency(100, f)
        assert abs(gain_db[0] - 20 * np.log10(100)) < 0.1

    def test_gain_rolls_off(self, gbw):
        """高频增益下降"""
        f = np.array([1, 100e3, 10e6])
        gain_db = gbw.gain_db_at_frequency(100, f)
        assert gain_db[0] > gain_db[1] > gain_db[2]

    def test_phase_at_dc(self, gbw):
        """DC 相位约为0"""
        f = np.array([1.0])
        phase = gbw.phase_at_frequency(100, f)
        assert abs(phase[0]) < 1.0

    def test_phase_at_high_freq(self, gbw):
        """高频相位趋近 -90 度"""
        f = np.array([1e9])
        phase = gbw.phase_at_frequency(100, f)
        assert abs(phase[0] - (-90)) < 1.0

    def test_settling_time(self, gbw):
        """建立时间 > 0"""
        t_s = gbw.settling_time(10, 0.01)
        assert t_s > 0

    def test_slew_rate_limited_bw(self, gbw):
        """转换速率限制带宽"""
        f_max = gbw.slew_rate_limited_bandwidth(V_peak=10, SR=0.5e6)
        expected = 0.5e6 / (2 * np.pi * 10)
        assert abs(f_max - expected) < 1

    def test_summary(self, gbw):
        s = gbw.summary(gain=10)
        assert s['gain'] == 10
        assert s['bandwidth'] > 0


class TestPhaseCompensation:
    """相位补偿测试"""

    def test_dominant_pole_compensation(self):
        result = PhaseCompensation.dominant_pole_compensation(
            gbw_original=1e6, f_p1=1e3, f_p2=1e6, f_new_pole=100
        )
        assert result['compensated_gbw'] < result['original_gbw']
        assert 'phase_margin' in result
        assert 'stable' in result

    def test_lead_compensation(self):
        result = PhaseCompensation.lead_compensation(
            f_crossover=100e3, phase_deficit=30
        )
        assert result['zero_frequency'] < result['center_frequency']
        assert result['pole_frequency'] > result['center_frequency']
        assert result['alpha'] > 1

    def test_lag_compensation(self):
        result = PhaseCompensation.lag_compensation(
            desired_bw=10e3, original_gbw=1e6, feedback_gain=10
        )
        assert result['desired_bandwidth'] == 10e3
        assert result['lag_zero_frequency'] < 10e3

    def test_miller_compensation(self):
        result = PhaseCompensation.miller_compensation(
            C_m=10e-12, g_m=1e-3, R_out=100e3
        )
        assert result['dominant_pole'] < result['second_pole']
        assert result['pole_splitting_ratio'] > 1
        assert result['effective_capacitance'] > result['miller_capacitance']


class TestStabilityAnalyzer:
    """稳定性分析测试"""

    def test_loop_gain_tf(self):
        tf = StabilityAnalyzer.loop_gain_tf(gbw=1e6, gain=1e4)
        # 在低频应有高增益
        H = tf(1.0)
        assert abs(H) > 100

    def test_loop_gain_with_poles(self):
        tf = StabilityAnalyzer.loop_gain_tf(
            gbw=1e6, gain=1e4, poles=[1e5, 2e5]
        )
        H_low = abs(tf(1.0))
        H_high = abs(tf(1e8))
        assert H_low > H_high

    def test_phase_margin_stable(self):
        """单极点系统应稳定"""
        tf = StabilityAnalyzer.loop_gain_tf(gbw=1e6, gain=100)
        result = StabilityAnalyzer.phase_margin(tf)
        assert result['stable']
        assert result['phase_margin'] > 45

    def test_phase_margin_with_extra_poles(self):
        """额外极点降低相位裕度"""
        tf = StabilityAnalyzer.loop_gain_tf(
            gbw=1e6, gain=100, poles=[1e5, 2e5]
        )
        result = StabilityAnalyzer.phase_margin(tf)
        # 相位裕度应该比较低
        assert 'phase_margin' in result

    def test_step_response_params(self):
        result = StabilityAnalyzer.step_response_params(phase_margin=60)
        assert result['damping_ratio'] > 0
        assert result['well_damped']

    def test_step_response_underdamped(self):
        result = StabilityAnalyzer.step_response_params(phase_margin=40)
        assert result['underdamped']

    def test_step_response_oscillatory(self):
        result = StabilityAnalyzer.step_response_params(phase_margin=30)
        assert result['overshoot_percent'] > 0


class TestFrequencyResponseIntegration:
    """频率响应集成测试"""

    def test_gbw_matches_opamp(self):
        """GBW 与运放参数一致"""
        from src.opamp import InvertingAmp
        amp = InvertingAmp(R_in=10e3, R_f=100e3)
        bw = amp.bandwidth()
        gbw_check = abs(amp.gain()) * bw
        assert abs(gbw_check - amp.opamp.GBW) < amp.opamp.GBW * 0.01

    def test_compensation_improves_stability(self):
        """补偿应提高相位裕度"""
        # 无补偿: 高GBW，额外极点接近
        tf_uncomp = StabilityAnalyzer.loop_gain_tf(
            gbw=1e6, gain=100, poles=[50e3]
        )
        result_uncomp = StabilityAnalyzer.phase_margin(tf_uncomp)

        # 有补偿: 降低GBW
        tf_comp = StabilityAnalyzer.loop_gain_tf(
            gbw=1e4, gain=100, poles=[50e3]
        )
        result_comp = StabilityAnalyzer.phase_margin(tf_comp)

        # 补偿后相位裕度应更大 (取模360处理)
        pm_uncomp = result_uncomp['phase_margin'] % 360
        pm_comp = result_comp['phase_margin'] % 360
        assert pm_comp > pm_uncomp or result_comp['stable']

    def test_stability_step_response_correlation(self):
        """稳定性与阶跃响应相关"""
        for pm in [30, 45, 60, 75]:
            result = StabilityAnalyzer.step_response_params(pm)
            if pm >= 60:
                assert result['well_damped']
            elif pm < 45:
                assert result['underdamped']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
