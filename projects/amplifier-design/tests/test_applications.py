"""实际应用测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.applications import SignalConditioner, SensorAmplifier, AudioAmplifier


class TestSignalConditioner:
    """信号调理器测试"""

    @pytest.fixture
    def conditioner(self):
        return SignalConditioner(gain=10.0, offset=0.0, v_ref=0.0)

    def test_basic_amplification(self, conditioner):
        signal = np.array([0.1, 0.2, 0.3])
        output = conditioner.process(signal)
        np.testing.assert_allclose(output, [1.0, 2.0, 3.0])

    def test_with_offset(self):
        sc = SignalConditioner(gain=1.0, offset=2.5, v_ref=0.0)
        signal = np.array([0.0, 1.0, -1.0])
        output = sc.process(signal)
        np.testing.assert_allclose(output, [2.5, 3.5, 1.5])

    def test_with_reference(self):
        sc = SignalConditioner(gain=10.0, offset=0.0, v_ref=2.5)
        signal = np.array([2.5, 2.6, 2.7])
        output = sc.process(signal)
        np.testing.assert_allclose(output, [0.0, 1.0, 2.0])

    def test_saturation(self, conditioner):
        signal = np.array([0.0, 2.0, -2.0])
        output = conditioner.process(signal)
        assert all(abs(v) <= 15.0 for v in output)

    def test_level_shift(self, conditioner):
        signal = np.array([0.0, 1.0, 2.0])
        shifted = conditioner.level_shift(signal, 5.0)
        np.testing.assert_allclose(shifted, [5.0, 6.0, 7.0])

    def test_ac_coupled_amplify(self, conditioner):
        """AC耦合应去除直流分量"""
        t = np.linspace(0, 1, 10000)
        signal = 2.0 + 0.1 * np.sin(2 * np.pi * 100 * t)
        output = conditioner.ac_coupled_amplify(signal, f_cutoff=10.0, fs=10000)

        # 输出直流应接近0
        assert abs(np.mean(output[-1000:])) < 0.5

    def test_differential_to_single(self, conditioner):
        v_pos = np.array([1.0, 2.0, 3.0])
        v_neg = np.array([0.5, 1.0, 1.5])
        output = conditioner.differential_to_single(v_pos, v_neg)
        np.testing.assert_allclose(output, [5.0, 10.0, 15.0])


class TestSensorAmplifier:
    """传感器放大器测试"""

    @pytest.fixture
    def sensor_amp(self):
        return SensorAmplifier()

    def test_thermocouple_amp(self, sensor_amp):
        result = sensor_amp.thermocouple_amp(R_g=100, R1=49.4e3)
        assert result['gain'] > 1
        assert result['sensitivity'] > 0
        assert '热电偶' in result['type']

    def test_thermocouple_gain_calculation(self, sensor_amp):
        result = sensor_amp.thermocouple_amp(R_g=100, R1=49.4e3)
        expected_gain = 1 + 2 * 49.4e3 / 100
        assert abs(result['gain'] - expected_gain) < 0.1

    def test_strain_gauge_amp(self, sensor_amp):
        result = sensor_amp.strain_gauge_amp(
            R_gauge=350, R_g=1000, V_excitation=5.0, gauge_factor=2.0
        )
        assert result['gain'] > 1
        assert result['bridge_output'] > 0
        assert result['amplified_output'] > result['bridge_output']

    def test_strain_gauge_sensitivity(self, sensor_amp):
        result = sensor_amp.strain_gauge_amp(
            R_gauge=350, R_g=1000, V_excitation=5.0, gauge_factor=2.0
        )
        # sensitivity = V_exc * GF * gain / 4
        expected = 5.0 * 2.0 * result['gain'] / 4
        assert abs(result['sensitivity'] - expected) < 0.1

    def test_photodiode_amp(self, sensor_amp):
        result = sensor_amp.photodiode_amp(R_f=1e6, C_f=1e-12)
        assert result['transimpedance'] == 1e6
        assert result['sensitivity'] > 0
        assert result['bandwidth'] > 0

    def test_photodiode_bandwidth(self, sensor_amp):
        result = sensor_amp.photodiode_amp(R_f=1e6, C_f=1e-12)
        # BW = 1/(2*pi*Rf*Cf)
        expected_bw = 1 / (2 * np.pi * 1e6 * 1e-12)
        assert abs(result['bandwidth'] - expected_bw) / expected_bw < 0.1

    def test_piezo_amp(self, sensor_amp):
        result = sensor_amp.piezo_amp(R_f=10e6, C_in=1e-9)
        assert result['gain'] > 1
        assert result['input_impedance'] > 1e10
        assert result['low_cutoff'] > 0


class TestAudioAmplifier:
    """音频放大器测试"""

    @pytest.fixture
    def audio_amp(self):
        return AudioAmplifier(v_supply=15.0)

    def test_preamp(self, audio_amp):
        result = audio_amp.preamp(R_in=10e3, R_f=100e3)
        assert result['gain'] == 11.0
        assert result['gain_dB'] > 0
        assert result['bandwidth'] > 0

    def test_preamp_gain_dB(self, audio_amp):
        result = audio_amp.preamp(R_in=10e3, R_f=100e3)
        expected_dB = 20 * np.log10(11)
        assert abs(result['gain_dB'] - expected_dB) < 0.1

    def test_tone_control(self, audio_amp):
        result = audio_amp.tone_control(bass_gain=2.0, treble_gain=0.5)
        assert result['bass_gain_dB'] > 0
        assert result['treble_gain_dB'] < 0

    def test_baxandall_response_flat(self, audio_amp):
        """平坦响应 (增益均为1)"""
        f = np.array([20, 1000, 20000])
        response = audio_amp.baxandall_response(f, bass_gain=1.0, treble_gain=1.0)
        # 应该接近 0dB
        assert all(abs(r) < 1.0 for r in response)

    def test_baxandall_response_bass_boost(self, audio_amp):
        """低音增强"""
        # 在低音转折频率附近检查增益
        f = np.array([100, 300, 1000, 3000, 20000])
        response_flat = audio_amp.baxandall_response(f, bass_gain=1.0, treble_gain=1.0)
        response_boost = audio_amp.baxandall_response(f, bass_gain=2.0, treble_gain=1.0)
        # 低音增强模式在 f_bass 附近应有更高增益
        assert max(response_boost) > max(response_flat)

    def test_baxandall_response_treble_cut(self, audio_amp):
        """高音衰减"""
        f = np.array([20, 1000, 20000])
        response = audio_amp.baxandall_response(f, bass_gain=1.0, treble_gain=0.5)
        # 高频应该低于低频
        assert response[2] < response[0] + 1

    def test_power_amp_driver(self, audio_amp):
        result = audio_amp.power_amp_driver(gain=10)
        assert result['gain'] == 10
        assert result['low_cutoff'] == 20
        assert result['high_cutoff'] == 20000
        assert result['bandwidth'] == 19980

    def test_power_amp_max_output(self, audio_amp):
        result = audio_amp.power_amp_driver()
        assert result['max_output_voltage'] > 0
        assert result['max_output_power_8ohm'] > 0

    def test_crossover_network(self, audio_amp):
        result = audio_amp.crossover_network(f_crossover=3000, order=2)
        assert result['crossover_frequency'] == 3000
        assert '12 dB' in result['slope']

    def test_crossover_4th_order(self, audio_amp):
        result = audio_amp.crossover_network(f_crossover=3000, order=4)
        assert '24 dB' in result['slope']


class TestApplicationsIntegration:
    """应用集成测试"""

    def test_sensor_to_conditioner_pipeline(self):
        """传感器 -> 信号调理 流水线"""
        # 模拟热电偶信号 (约 1mV)
        t = np.linspace(0, 1, 1000)
        thermocouple_signal = 1e-3 * np.sin(2 * np.pi * t) + 25e-3  # 25mV 约 625°C

        # 仪表放大器放大
        sensor_amp = SensorAmplifier()
        tc_result = sensor_amp.thermocouple_amp(R_g=100, R1=49.4e3)
        amplified = tc_result['gain'] * thermocouple_signal

        # 信号调理: 缩放到 0~3.3V 范围
        v_max = max(abs(amplified))
        conditioner = SignalConditioner(gain=1.65 / v_max, offset=1.65)
        conditioned = conditioner.process(amplified)

        # 输出应在 0-3.3V 范围
        assert all(0 <= v <= 3.3 + 0.01 for v in conditioned)

    def test_audio_preamp_to_driver(self):
        """音频前置放大 -> 驱动级"""
        audio = AudioAmplifier(v_supply=15.0)

        preamp = audio.preamp(R_in=1e3, R_f=100e3)
        driver = audio.power_amp_driver(gain=10)

        total_gain = preamp['gain'] * driver['gain']
        assert total_gain > 100

    def test_sensor_types_coverage(self):
        """覆盖所有传感器类型"""
        sa = SensorAmplifier()

        tc = sa.thermocouple_amp(R_g=100)
        sg = sa.strain_gauge_amp(R_gauge=350, R_g=1000)
        pd = sa.photodiode_amp(R_f=1e6)
        pz = sa.piezo_amp(R_f=10e6)

        # 热电偶和应变片有 gain
        assert tc['gain'] > 1
        assert sg['gain'] > 1
        # 光电二极管有 transimpedance
        assert pd['transimpedance'] > 0
        # 压电有 gain
        assert pz['gain'] > 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
