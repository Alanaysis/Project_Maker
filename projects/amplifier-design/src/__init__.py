"""
放大器设计 (Amplifier Design)

模拟放大器的Python实现，包括：
- BJT基本放大器（共射、共集、共基）
- 运算放大器电路（反相、同相、差分、仪表）
- 频率响应分析
- 实际应用（信号调理、传感器放大、音频放大）
"""

__version__ = "0.1.0"

from .bjt import CommonEmitter, CommonCollector, CommonBase
from .opamp import InvertingAmp, NonInvertingAmp, DifferentialAmp, InstrumentationAmp
from .frequency import GainBandwidthProduct, PhaseCompensation
from .applications import SignalConditioner, SensorAmplifier, AudioAmplifier
