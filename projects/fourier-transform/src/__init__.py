"""
傅里叶变换实现包

提供 DFT、FFT、频谱分析和可视化功能。
"""

from .dft import dft, idft
from .fft import fft, ifft, fft_radix2
from .spectrum import (
    magnitude_spectrum,
    power_spectrum,
    phase_spectrum,
    frequency_bins,
    find_peaks,
    spectral_centroid,
    bandwidth,
)
from .visualization import (
    plot_time_domain,
    plot_spectrum,
    plot_spectrogram,
    plot_dft_vs_fft,
)

__version__ = "1.0.0"
__all__ = [
    # DFT
    "dft",
    "idft",
    # FFT
    "fft",
    "ifft",
    "fft_radix2",
    # Spectrum analysis
    "magnitude_spectrum",
    "power_spectrum",
    "phase_spectrum",
    "frequency_bins",
    "find_peaks",
    "spectral_centroid",
    "bandwidth",
    # Visualization
    "plot_time_domain",
    "plot_spectrum",
    "plot_spectrogram",
    "plot_dft_vs_fft",
]
