"""
ADC/DAC 模拟 - 模数/数模转换学习项目
========================================

核心模块:
- sampling: 采样过程 (理想采样、孔径误差)
- quantization: 量化 (均匀量化、非均匀量化)
- adc: 理想 ADC (模数转换器)
- dac: 理想 DAC (数模转换器)
- reconstruction: 重建滤波器
- metrics: 信号质量指标 (SNR, THD, ENOB)
"""

__version__ = "1.0.0"
__all__ = [
    "sampling",
    "quantization",
    "adc",
    "dac",
    "reconstruction",
    "metrics",
]
