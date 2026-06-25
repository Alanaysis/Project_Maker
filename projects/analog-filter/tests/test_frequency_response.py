"""
频率响应分析工具测试
====================

测试频率响应分析的各项功能。
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.frequency_response import (
    generate_log_freq,
    generate_linear_freq,
    find_cutoff_frequency,
    find_bandwidth,
    cascade_transfer_functions,
    analyze_filter,
    db_to_linear,
    linear_to_db,
)
from src.lowpass import RCLowPass
from src.highpass import RCHighPass
from src.bandpass import RLCBandPass


class TestFrequencyGeneration:
    """频率生成测试"""

    def test_log_freq(self):
        """测试对数频率生成"""
        f = generate_log_freq(1, 1e6, 100)
        assert len(f) == 100
        assert f[0] == pytest.approx(1.0)
        assert f[-1] == pytest.approx(1e6)

    def test_linear_freq(self):
        """测试线性频率生成"""
        f = generate_linear_freq(0, 10000, 100)
        assert len(f) == 100
        assert f[0] == pytest.approx(0.0)
        assert f[-1] == pytest.approx(10000)


class TestCutoffDetection:
    """截止频率检测测试"""

    def test_lowpass_cutoff(self):
        """测试低通截止频率检测"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = generate_log_freq(1, 1e6, 10000)
        mag_db = filt.magnitude_db(f)

        fc_detected = find_cutoff_frequency(f, mag_db)
        assert fc_detected == pytest.approx(filt.fc, rel=0.01)

    def test_highpass_cutoff(self):
        """测试高通截止频率检测"""
        filt = RCHighPass(R=1000, C=1e-6)
        f = generate_log_freq(1, 1e6, 10000)
        mag_db = filt.magnitude_db(f)

        fc_detected = find_cutoff_frequency(f, mag_db)
        assert fc_detected == pytest.approx(filt.fc, rel=0.01)


class TestBandwidthDetection:
    """带宽检测测试"""

    def test_bandpass_bandwidth(self):
        """测试带通滤波器带宽检测"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = generate_log_freq(1, 1e6, 10000)
        mag_db = filt.magnitude_db(f)

        f_low, f_high, bw = find_bandwidth(f, mag_db)

        assert f_low == pytest.approx(filt.lower_cutoff(), rel=0.05)
        assert f_high == pytest.approx(filt.upper_cutoff(), rel=0.05)
        assert bw == pytest.approx(filt.bw, rel=0.05)


class TestCascade:
    """级联测试"""

    def test_cascade_two_lowpass(self):
        """测试两个低通级联"""
        f = generate_log_freq(1, 1e6, 1000)

        filt1 = RCLowPass(R=1000, C=1e-6)  # fc = 159Hz
        filt2 = RCLowPass(R=1000, C=1e-7)  # fc = 1592Hz

        H_cascade = cascade_transfer_functions([filt1, filt2], f)
        H_separate = filt1.transfer_function(f) * filt2.transfer_function(f)

        np.testing.assert_allclose(H_cascade, H_separate, rtol=1e-10)


class TestAnalyzeFilter:
    """滤波器分析测试"""

    def test_analyze_lowpass(self):
        """测试低通滤波器分析"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = generate_log_freq(1, 1e6, 10000)

        result = analyze_filter(filt, f)

        assert 'frequency' in result
        assert 'magnitude' in result
        assert 'magnitude_db' in result
        assert 'phase_deg' in result
        assert 'cutoff_frequency' in result

        assert result['cutoff_frequency'] == pytest.approx(filt.fc, rel=0.01)


class TestUnitConversion:
    """单位转换测试"""

    def test_db_to_linear(self):
        """测试 dB 到线性转换"""
        assert db_to_linear(0) == pytest.approx(1.0)
        assert db_to_linear(20) == pytest.approx(10.0)
        assert db_to_linear(-20) == pytest.approx(0.1)
        assert db_to_linear(6) == pytest.approx(2.0, rel=0.01)

    def test_linear_to_db(self):
        """测试线性到 dB 转换"""
        assert linear_to_db(1.0) == pytest.approx(0.0, abs=1e-10)
        assert linear_to_db(10.0) == pytest.approx(20.0, abs=1e-10)
        assert linear_to_db(0.1) == pytest.approx(-20.0, abs=1e-10)
        assert linear_to_db(2.0) == pytest.approx(6.0206, abs=0.01)

    def test_conversion_roundtrip(self):
        """测试转换往返一致性"""
        values = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
        for v in values:
            db = linear_to_db(v)
            v_back = db_to_linear(db)
            assert v_back == pytest.approx(v, rel=1e-6)
