"""信号采样重建 (Signal Sampling & Reconstruction) - 从零实现信号采样与重建

包含采样、量化、重建、混叠和实际应用等模块。
"""

from .sampling import (
    SamplingConfig,
    nyquist_sample,
    oversample,
    undersample,
    sample_signal,
    calculate_nyquist_rate,
)
from .quantization import (
    UniformQuantizer,
    NonUniformQuantizer,
    mu_law_quantizer,
    a_law_quantizer,
    snr_quantization,
)
from .reconstruction import (
    zero_order_hold,
    first_order_hold,
    sinc_interpolation,
    reconstruct_signal,
    compare_reconstruction,
)
from .aliasing import (
    demonstrate_aliasing,
    anti_aliasing_filter,
    compute_spectrum,
    show_aliasing_effect,
)
from .audio_sampling import (
    AudioSampler,
    resample_audio,
    demonstrate_audio_quantization,
)
from .image_sampling import (
    ImageSampler,
    downsample_image,
    upsample_image,
    demonstrate_image_aliasing,
)

__version__ = "1.0.0"

__all__ = [
    # 采样
    "SamplingConfig",
    "nyquist_sample",
    "oversample",
    "undersample",
    "sample_signal",
    "calculate_nyquist_rate",
    # 量化
    "UniformQuantizer",
    "NonUniformQuantizer",
    "mu_law_quantizer",
    "a_law_quantizer",
    "snr_quantization",
    # 重建
    "zero_order_hold",
    "first_order_hold",
    "sinc_interpolation",
    "reconstruct_signal",
    "compare_reconstruction",
    # 混叠
    "demonstrate_aliasing",
    "anti_aliasing_filter",
    "compute_spectrum",
    "show_aliasing_effect",
    # 音频采样
    "AudioSampler",
    "resample_audio",
    "demonstrate_audio_quantization",
    # 图像采样
    "ImageSampler",
    "downsample_image",
    "upsample_image",
    "demonstrate_image_aliasing",
]
