"""
ADC/DAC 模块测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest

from src.adc import IdealADC, simulate_adc_chain
from src.dac import IdealDAC, simulate_dac_chain
from src.metrics import calculate_snr, calculate_thd, calculate_enob, calculate_sfdr


class TestIdealADC:
    """测试理想 ADC"""

    def test_adc_init(self):
        """ADC 初始化"""
        adc = IdealADC(num_bits=8, v_range=(-1.0, 1.0), fs=1000)

        assert adc.num_bits == 8
        assert adc.num_levels == 256
        assert adc.v_range == 2.0
        assert adc.step_size == pytest.approx(2.0 / 256)
        assert adc.fs == 1000

    def test_adc_convert(self):
        """ADC 转换"""
        adc = IdealADC(num_bits=8, v_range=(-1.0, 1.0), fs=1000)
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 1.0 * t)

        result = adc.convert(signal, 0, 1)

        assert "digital_signal" in result
        assert "digital_codes" in result
        assert "sample_times" in result
        assert "snr" in result
        assert len(result["digital_codes"]) == result["num_samples"]

    def test_adc_resolution(self):
        """ADC 分辨率"""
        adc = IdealADC(num_bits=12, v_range=(-5.0, 5.0), fs=1000)
        assert adc.get_resolution() == pytest.approx(10.0 / 4096)

    def test_adc_theoretical_snr(self):
        """ADC 理论 SNR"""
        adc = IdealADC(num_bits=16)
        assert adc.get_theoretical_snr() == pytest.approx(6.02 * 16 + 1.76)

    def test_adc_repr(self):
        """ADC 字符串表示"""
        adc = IdealADC(num_bits=8)
        repr_str = repr(adc)
        assert "IdealADC" in repr_str
        assert "bits=8" in repr_str


class TestIdealDAC:
    """测试理想 DAC"""

    def test_dac_init(self):
        """DAC 初始化"""
        dac = IdealDAC(num_bits=8, v_range=(-1.0, 1.0), fs=1000)

        assert dac.num_bits == 8
        assert dac.num_levels == 256
        assert dac.v_range == 2.0

    def test_dac_convert_zoh(self):
        """DAC ZOH 转换"""
        dac = IdealDAC(num_bits=8, v_range=(-1.0, 1.0), fs=100)
        codes = np.array([0, 64, 128, 192, 255])
        times = np.array([0.0, 0.1, 0.2, 0.3, 0.4])

        result = dac.convert(codes, times, 0, 0.5, "zoh")

        assert "analog_signal" in result
        assert "reconstruction_times" in result
        assert len(result["analog_signal"]) > 0

    def test_dac_convert_ideal(self):
        """DAC 理想重建"""
        dac = IdealDAC(num_bits=8, v_range=(-1.0, 1.0), fs=100)
        codes = np.array([0, 128, 255])
        times = np.array([0.0, 0.1, 0.2])

        result = dac.convert(codes, times, 0, 0.3, "ideal")

        assert "analog_signal" in result
        assert len(result["analog_signal"]) > 0

    def test_dac_invalid_method(self):
        """无效重建方法"""
        dac = IdealDAC(num_bits=8)
        codes = np.array([0])
        times = np.array([0.0])

        with pytest.raises(ValueError):
            dac.convert(codes, times, 0, 1.0, "invalid")

    def test_dac_resolution(self):
        """DAC 分辨率"""
        dac = IdealDAC(num_bits=12, v_range=(-5.0, 5.0))
        assert dac.get_resolution() == pytest.approx(10.0 / 4096)


class TestADCChain:
    """测试 ADC 转换链"""

    def test_simulate_adc_chain(self):
        """模拟 ADC 链"""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 1.0 * t)

        result = simulate_adc_chain(signal, signal_freq=1.0, num_bits=8, fs=1000)

        assert "digital_signal" in result
        assert "aliasing" in result
        assert "theoretical_snr" in result


class TestDACChain:
    """测试 DAC 转换链"""

    def test_simulate_dac_chain(self):
        """模拟 DAC 链"""
        codes = np.array([0, 64, 128, 192, 255])
        times = np.array([0.0, 0.1, 0.2, 0.3, 0.4])

        result = simulate_dac_chain(codes, times, num_bits=8, fs=1000)

        assert "analog_signal" in result
        assert "reconstruction_times" in result


class TestMetrics:
    """测试信号质量指标"""

    def test_calculate_snr(self):
        """SNR 计算"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        noise = np.zeros_like(signal)
        assert calculate_snr(signal, noise) == float("inf")

    def test_calculate_snr_with_noise(self):
        """有噪声的 SNR"""
        signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
        noise = np.random.randn(1000) * 0.1
        snr = calculate_snr(signal, noise)
        assert snr > 0

    def test_calculate_enob(self):
        """ENOB 计算"""
        enob = calculate_enob(62.0)
        assert enob == pytest.approx((62.0 - 1.76) / 6.02)

    def test_calculate_enob_low_sinad(self):
        """低 SINAD 的 ENOB"""
        enob = calculate_enob(1.0)
        assert enob == 0.0

    def test_calculate_thd(self):
        """THD 计算"""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t)
        result = calculate_thd(signal, fs=1000)

        assert "thd_linear" in result
        assert "thd_db" in result
        assert "fundamental_freq" in result
        assert result["fundamental_freq"] == pytest.approx(50.0, abs=1.0)

    def test_calculate_sfdr(self):
        """SFDR 计算"""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t)
        result = calculate_sfdr(signal, fs=1000)

        assert "sfdr_db" in result
        assert "fundamental_freq" in result
        assert result["fundamental_freq"] == pytest.approx(50.0, abs=1.0)
