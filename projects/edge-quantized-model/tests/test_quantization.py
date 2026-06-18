"""
量化模块测试

测试量化相关的功能
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.quantization.quant_ops import (
    symmetric_quantize,
    asymmetric_quantize,
    quantize_tensor,
    dequantize_tensor,
    compute_quantization_error,
)
from src.quantization.calibration import (
    MinMaxCalibration,
    PercentileCalibration,
    EntropyCalibration,
    CalibratorFactory,
)
from src.quantization.config import QuantConfig


class TestSymmetricQuantization:
    """对称量化测试"""

    def test_basic_symmetric_quantization(self):
        """测试基本对称量化"""
        tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        quantized, params = symmetric_quantize(tensor, num_bits=8)

        # 验证数据类型
        assert quantized.dtype == np.int8

        # 验证范围
        assert quantized.min() >= -128
        assert quantized.max() <= 127

        # 验证参数
        assert params.symmetric == True
        assert params.zero_point == 0
        assert params.scale > 0

    def test_symmetric_quantization_with_negative_values(self):
        """测试包含负值的对称量化"""
        tensor = np.array([-5.0, -2.0, 0.0, 2.0, 5.0])
        quantized, params = symmetric_quantize(tensor, num_bits=8)

        # 验证对称性
        assert params.zero_point == 0
        assert params.symmetric == True

    def test_per_channel_symmetric_quantization(self):
        """测试逐通道对称量化"""
        # 模拟卷积权重 [out_channels, in_channels, kh, kw]
        weight = np.random.randn(3, 16, 3, 3).astype(np.float32)

        quantized, params = symmetric_quantize(
            weight, num_bits=8, per_channel=True, channel_axis=0
        )

        # 验证逐通道参数
        assert params.per_channel == True
        assert len(params.scale) == 3  # 3 个输出通道

    def test_symmetric_quantization_accuracy(self):
        """测试对称量化精度"""
        tensor = np.random.randn(100, 100).astype(np.float32)
        quantized, params = symmetric_quantize(tensor, num_bits=8)

        # 反量化
        dequantized = dequantize_tensor(quantized, params)

        # 计算误差
        error = np.mean(np.abs(tensor - dequantized))

        # 验证误差在可接受范围内
        assert error < 0.1


class TestAsymmetricQuantization:
    """非对称量化测试"""

    def test_basic_asymmetric_quantization(self):
        """测试基本非对称量化"""
        tensor = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        quantized, params = asymmetric_quantize(tensor, num_bits=8)

        # 验证数据类型
        assert quantized.dtype == np.uint8

        # 验证范围
        assert quantized.min() >= 0
        assert quantized.max() <= 255

        # 验证参数
        assert params.symmetric == False
        assert params.scale > 0

    def test_asymmetric_quantization_with_negative_values(self):
        """测试包含负值的非对称量化"""
        tensor = np.array([-5.0, -2.0, 0.0, 2.0, 5.0])
        quantized, params = asymmetric_quantize(tensor, num_bits=8)

        # 验证非对称性
        assert params.symmetric == False

    def test_per_channel_asymmetric_quantization(self):
        """测试逐通道非对称量化"""
        weight = np.random.randn(3, 16, 3, 3).astype(np.float32)

        quantized, params = asymmetric_quantize(
            weight, num_bits=8, per_channel=True, channel_axis=0
        )

        # 验证逐通道参数
        assert params.per_channel == True
        assert len(params.scale) == 3
        assert len(params.zero_point) == 3


class TestCalibration:
    """校准测试"""

    def test_minmax_calibration(self):
        """测试 MinMax 校准"""
        calibrator = MinMaxCalibration()
        activations = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        min_val, max_val = calibrator.calibrate(activations)

        assert min_val == 1.0
        assert max_val == 5.0

    def test_percentile_calibration(self):
        """测试百分位校准"""
        calibrator = PercentileCalibration(percentile=99.0)
        activations = np.random.randn(1000)

        min_val, max_val = calibrator.calibrate(activations)

        # 验证百分位数
        assert min_val <= np.percentile(activations, 1.0)
        assert max_val >= np.percentile(activations, 99.0)

    def test_calibration_with_list(self):
        """测试列表输入的校准"""
        calibrator = MinMaxCalibration()
        activations = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
        ]

        min_val, max_val = calibrator.calibrate(activations)

        assert min_val == 1.0
        assert max_val == 6.0

    def test_calibrator_factory(self):
        """测试校准器工厂"""
        # 测试 MinMax
        calibrator = CalibratorFactory.create("minmax")
        assert isinstance(calibrator, MinMaxCalibration)

        # 测试 Percentile
        calibrator = CalibratorFactory.create("percentile", percentile=99.9)
        assert isinstance(calibrator, PercentileCalibration)

        # 测试 Entropy
        calibrator = CalibratorFactory.create("entropy", num_bins=1024)
        assert isinstance(calibrator, EntropyCalibration)

    def test_invalid_calibration_method(self):
        """测试无效的校准方法"""
        with pytest.raises(ValueError):
            CalibratorFactory.create("invalid_method")


class TestQuantizationError:
    """量化误差测试"""

    def test_compute_quantization_error(self):
        """测试量化误差计算"""
        original = np.random.randn(10, 10).astype(np.float32)
        quantized, params = symmetric_quantize(original, num_bits=8)

        errors = compute_quantization_error(original, quantized, params)

        # 验证误差指标
        assert "mse" in errors
        assert "mae" in errors
        assert "max_error" in errors
        assert "snr" in errors

        # 验证误差值
        assert errors["mse"] >= 0
        assert errors["mae"] >= 0
        assert errors["max_error"] >= 0

    def test_int8_vs_int4_error(self):
        """测试 INT8 和 INT4 量化误差对比"""
        original = np.random.randn(100, 100).astype(np.float32)

        # INT8 量化
        quantized_8, params_8 = symmetric_quantize(original, num_bits=8)
        errors_8 = compute_quantization_error(original, quantized_8, params_8)

        # INT4 量化
        quantized_4, params_4 = symmetric_quantize(original, num_bits=4)
        errors_4 = compute_quantization_error(original, quantized_4, params_4)

        # INT4 误差应该更大
        assert errors_4["mse"] > errors_8["mse"]


class TestQuantConfig:
    """量化配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = QuantConfig()

        assert config.quant_type == "int8"
        assert config.calibration_method == "percentile"
        assert config.per_channel == True
        assert config.symmetric == True
        assert config.num_bits == 8

    def test_int4_config(self):
        """测试 INT4 配置"""
        config = QuantConfig(quant_type="int4")

        assert config.quant_type == "int4"
        assert config.num_bits == 4

    def test_invalid_quant_type(self):
        """测试无效的量化类型"""
        with pytest.raises(ValueError):
            QuantConfig(quant_type="invalid")

    def test_quant_range(self):
        """测试量化范围"""
        # 对称量化
        config = QuantConfig(symmetric=True)
        qmin, qmax = config.quant_range
        assert qmin == -128
        assert qmax == 127

        # 非对称量化
        config = QuantConfig(symmetric=False)
        qmin, qmax = config.quant_range
        assert qmin == 0
        assert qmax == 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
