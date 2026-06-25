"""Example: Audio filtering - removing noise from a signal."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.fir import fir_lowpass, fir_bandstop
from src.iir import butterworth_lowpass, chebyshev1_lowpass
from src.utils import generate_signal, add_noise, snr, plot_comparison, plot_spectrum


def main():
    fs = 1000.0
    duration = 2.0

    # Generate a clean signal: 50Hz + 120Hz components
    t, clean = generate_signal(duration, fs, [(50, 1.0), (120, 0.3)])

    # Add noise
    noisy = add_noise(clean, snr_db=15.0)

    # Apply different filters
    fir_filt = fir_lowpass(cutoff=80, num_taps=101, fs=fs)
    butter_filt = butterworth_lowpass(cutoff=80, order=6, fs=fs)
    cheby_filt = chebyshev1_lowpass(cutoff=80, order=4, ripple=1.0, fs=fs)

    fir_result = fir_filt.apply_filtfilt(noisy)
    butter_result = butter_filt.apply_filtfilt(noisy)
    cheby_result = cheby_filt.apply_filtfilt(noisy)

    # Print SNR comparison
    print("=== Audio Filtering Example ===")
    print(f"Noisy signal SNR:           {snr(clean, noisy):.2f} dB")
    print(f"FIR lowpass output SNR:     {snr(clean, fir_result):.2f} dB")
    print(f"Butterworth output SNR:     {snr(clean, butter_result):.2f} dB")
    print(f"Chebyshev I output SNR:     {snr(clean, cheby_result):.2f} dB")

    # Plot comparison
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "output"), exist_ok=True)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")

    plot_comparison(
        t,
        [clean, noisy, fir_result, butter_result, cheby_result],
        ["Clean", "Noisy", "FIR LP", "Butterworth LP", "Chebyshev I LP"],
        title="Audio Filtering Comparison",
        save_path=os.path.join(output_dir, "audio_filter.png"),
    )
    print(f"\nPlot saved to {output_dir}/audio_filter.png")


if __name__ == "__main__":
    main()
