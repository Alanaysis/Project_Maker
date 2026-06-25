"""Example: Frequency response comparison of different filter types."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.fir import fir_lowpass, fir_highpass, fir_bandpass
from src.iir import (
    butterworth_lowpass, butterworth_highpass,
    chebyshev1_lowpass, chebyshev2_lowpass,
    elliptic_lowpass,
)
from src.response import plot_response, plot_filter_comparison


def main():
    fs = 1000.0
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # --- Individual filter responses ---
    filters = {
        "FIR Lowpass (50 taps)": fir_lowpass(cutoff=100, num_taps=51, fs=fs),
        "FIR Highpass (50 taps)": fir_highpass(cutoff=200, num_taps=51, fs=fs),
        "FIR Bandpass (50 taps)": fir_bandpass(100, 300, num_taps=51, fs=fs),
        "Butterworth LP order=4": butterworth_lowpass(cutoff=100, order=4, fs=fs),
        "Butterworth HP order=4": butterworth_highpass(cutoff=200, order=4, fs=fs),
        "Chebyshev I LP order=4": chebyshev1_lowpass(cutoff=100, order=4, fs=fs),
        "Chebyshev II LP order=4": chebyshev2_lowpass(cutoff=100, order=4, fs=fs),
        "Elliptic LP order=4": elliptic_lowpass(cutoff=100, order=4, fs=fs),
    }

    for name, filt in filters.items():
        fname = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        plot_response(
            filt.b if hasattr(filt, "b") else filt.coefficients,
            filt.a if hasattr(filt, "a") else np.array([1.0]),
            fs=fs,
            title=name,
            save_path=os.path.join(output_dir, f"response_{fname}.png"),
        )
        print(f"Saved: response_{fname}.png")

    # --- Comparison: IIR lowpass filters ---
    iir_filters = [
        (butterworth_lowpass(100, 4, fs).b, butterworth_lowpass(100, 4, fs).a),
        (chebyshev1_lowpass(100, 4, 1.0, fs).b, chebyshev1_lowpass(100, 4, 1.0, fs).a),
        (chebyshev2_lowpass(100, 4, 40, fs).b, chebyshev2_lowpass(100, 4, 40, fs).a),
        (elliptic_lowpass(100, 4, 1.0, 40, fs).b, elliptic_lowpass(100, 4, 1.0, 40, fs).a),
    ]
    iir_labels = ["Butterworth", "Chebyshev I", "Chebyshev II", "Elliptic"]

    plot_filter_comparison(
        iir_filters, iir_labels, fs=fs,
        title="IIR Lowpass Filter Comparison (order=4, fc=100Hz)",
        save_path=os.path.join(output_dir, "iir_comparison.png"),
    )
    print("Saved: iir_comparison.png")

    # --- Comparison: FIR vs IIR ---
    fir_filt = fir_lowpass(cutoff=100, num_taps=51, fs=fs)
    bw_filt = butterworth_lowpass(cutoff=100, order=4, fs=fs)
    mixed_filters = [
        (fir_filt.coefficients, np.array([1.0])),
        (bw_filt.b, bw_filt.a),
    ]
    plot_filter_comparison(
        mixed_filters, ["FIR (50 taps)", "Butterworth (order 4)"], fs=fs,
        title="FIR vs IIR Lowpass Filter",
        save_path=os.path.join(output_dir, "fir_vs_iir.png"),
    )
    print("Saved: fir_vs_iir.png")

    print(f"\nAll plots saved to {output_dir}/")


if __name__ == "__main__":
    main()
