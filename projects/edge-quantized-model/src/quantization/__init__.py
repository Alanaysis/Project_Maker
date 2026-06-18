"""
量化模块

提供模型量化功能，支持 INT8/INT4 量化
"""

from .quantizer import Quantizer
from .calibration import (
    Calibrator,
    MinMaxCalibration,
    PercentileCalibration,
    EntropyCalibration,
)
from .quant_ops import (
    quantize_tensor,
    dequantize_tensor,
    symmetric_quantize,
    asymmetric_quantize,
)
from .config import QuantConfig

__all__ = [
    "Quantizer",
    "QuantConfig",
    "Calibrator",
    "MinMaxCalibration",
    "PercentileCalibration",
    "EntropyCalibration",
    "quantize_tensor",
    "dequantize_tensor",
    "symmetric_quantize",
    "asymmetric_quantize",
]
