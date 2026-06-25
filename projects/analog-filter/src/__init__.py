"""模拟滤波器 (Analog Filter) - 从零实现模拟滤波器

包含低通、高通、带通、带阻滤波器，支持频率响应分析和实际应用。
"""

from .lowpass import RCLowPass, RLLowPass
from .highpass import RCHighPass, RLHighPass
from .bandpass import RLCBandPass
from .bandstop import RLCBandStop
from .frequency_response import (
    generate_log_freq,
    generate_linear_freq,
    find_cutoff_frequency,
    find_bandwidth,
    cascade_transfer_functions,
    analyze_filter,
    db_to_linear,
    linear_to_db,
)
from .visualization import (
    plot_bode,
    plot_magnitude,
    plot_phase,
    plot_step_response,
    plot_impulse_response,
    plot_comparison,
    plot_pole_zero,
)
from .applications import (
    AudioCrossover,
    NotchFilter,
    SignalConditioner,
)

__version__ = "1.0.0"

__all__ = [
    # 低通滤波器
    "RCLowPass",
    "RLLowPass",
    # 高通滤波器
    "RCHighPass",
    "RLHighPass",
    # 带通滤波器
    "RLCBandPass",
    # 带阻滤波器
    "RLCBandStop",
    # 频率响应工具
    "generate_log_freq",
    "generate_linear_freq",
    "find_cutoff_frequency",
    "find_bandwidth",
    "cascade_transfer_functions",
    "analyze_filter",
    "db_to_linear",
    "linear_to_db",
    # 可视化
    "plot_bode",
    "plot_magnitude",
    "plot_phase",
    "plot_step_response",
    "plot_impulse_response",
    "plot_comparison",
    "plot_pole_zero",
    # 实际应用
    "AudioCrossover",
    "NotchFilter",
    "SignalConditioner",
]
