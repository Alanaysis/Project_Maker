"""
端侧极致量化模型框架

一个面向学习的量化推理框架，支持 INT8/INT4 量化，优化车载场景推理
"""

__version__ = "0.1.0"
__author__ = "Edge Quant Team"

from .quantization import Quantizer, QuantConfig
from .inference import InferenceEngine

__all__ = [
    "Quantizer",
    "QuantConfig",
    "InferenceEngine",
]
