"""Digital Filter Library - FIR & IIR filter design and analysis."""

from .fir import FIRFilter, fir_lowpass, fir_highpass, fir_bandpass, fir_bandstop
from .iir import IIRFilter, butterworth_lowpass, butterworth_highpass, chebyshev1_lowpass, chebyshev2_lowpass, elliptic_lowpass
from .response import frequency_response, plot_response
from .utils import generate_signal, add_noise, plot_comparison

__version__ = "1.0.0"
__all__ = [
    "FIRFilter", "fir_lowpass", "fir_highpass", "fir_bandpass", "fir_bandstop",
    "IIRFilter", "butterworth_lowpass", "butterworth_highpass",
    "chebyshev1_lowpass", "chebyshev2_lowpass", "elliptic_lowpass",
    "frequency_response", "plot_response",
    "generate_signal", "add_noise", "plot_comparison",
]
