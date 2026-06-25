"""Example: Signal denoising with various filter types."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.fir import fir_lowpass, fir_bandpass, fir_bandstop
from src.iir import butterworth_lowpass, butterworth_bandstop
from src.utils import generate_signal, add_noise, snr, plot_comparison, plot_spectrum


def main():
    fs = 2000.0
    duration = 1.0
    t = np.arange(0, duration, 1.0 / fs)

    # Signal: 50Hz fundamental + 150Hz harmonic + 500Hz interference
    clean = (np.sin(2 * np.pi * 50 * t)
             + 0.3 * np.sin(2 * np.pi * 150 * t)
             + 0.1 * np.sin(2 * np.pi * 500 * t))

    # Add broadband noise
    noisy = add_noise(clean, snr_db=10.0)

    # Strategy 1: Low-pass to keep only low frequencies
    lp_filt = fir_lowpass(cutoff=200, num_taps=101, fs=fs)
    denoised_lp = lp_filt.apply_filtfilt(noisy)

    # Strategy 2: Band-stop to remove 500Hz interference
    bs_filt = fir_bandstop(low_cutoff=450, high_cutoff=550, num_taps=101, fs=fs)
    denoised_bs = bs_filt.apply_filtfilt(noisy)

    # Strategy 3: Band-pass to keep only 50Hz + 150Hz
    bp_filt = fir_bandpass(low_cutoff=30, high_cutoff=200, num_taps=101, fs=fs)
    denoised_bp = bp_filt.apply_filtfilt(noisy)

    # Strategy 4: Butterworth low-pass
    bw_filt = butterworth_lowpass(cutoff=200, order=6, fs=fs)
    denoised_bw = bw_filt.apply_filtfilt(noisy)

    print("=== Signal Denoising Example ===")
    print(f"Noisy signal SNR:          {snr(clean, noisy):.2f} dB")
    print(f"FIR lowpass SNR:           {snr(clean, denoised_lp):.2f} dB")
    print(f"FIR bandstop SNR:          {snr(clean, denoised_bs):.2f} dB")
    print(f"FIR bandpass SNR:          {snr(clean, denoised_bp):.2f} dB")
    print(f"Butterworth lowpass SNR:   {snr(clean, denoised_bw):.2f} dB")

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    plot_comparison(
        t[:500],
        [clean[:500], noisy[:500], denoised_lp[:500], denoised_bp[:500], denoised_bw[:500]],
        ["Clean", "Noisy", "FIR LP", "FIR BP", "Butterworth LP"],
        title="Signal Denoising Strategies",
        save_path=os.path.join(output_dir, "signal_denoising.png"),
    )
    print(f"\nPlot saved to {output_dir}/signal_denoising.png")


if __name__ == "__main__":
    main()
