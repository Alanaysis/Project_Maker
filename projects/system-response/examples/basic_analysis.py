"""Basic system response analysis example."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src import (
    TransferFunction,
    TimeResponse,
    FrequencyResponse,
    PerformanceMetrics,
    StabilityAnalyzer,
)


def main():
    print("=" * 60)
    print("System Response Analysis - Basic Example")
    print("=" * 60)

    # Define a second-order system: G(s) = 4 / (s^2 + 2s + 4)
    # omega_n = 2, zeta = 0.5
    tf = TransferFunction.second_order(gain=1, omega_n=2, zeta=0.5)
    print(f"\nTransfer Function: {tf}")
    print(f"Order: {tf.order}")
    print(f"DC Gain: {tf.dc_gain:.4f}")
    print(f"Poles: {tf.poles()}")
    print(f"Zeros: {tf.zeros()}")

    # --- Time Domain ---
    print("\n--- Time Domain Response ---")
    tr = TimeResponse(tf)

    step_data = tr.step(t_final=5)
    print(f"Step response: {len(step_data.t)} points, "
          f"final value = {step_data.y[-1]:.4f}")

    impulse_data = tr.impulse(t_final=5)
    print(f"Impulse response: peak = {np.max(impulse_data.y):.4f}")

    ramp_data = tr.ramp(t_final=5)
    print(f"Ramp response: final value = {ramp_data.y[-1]:.4f}")

    # --- Performance Metrics ---
    print("\n--- Performance Metrics ---")
    pm = PerformanceMetrics(tf)
    metrics = pm.step_metrics(t_final=10)
    print(f"Rise Time:       {metrics.rise_time:.4f} s")
    print(f"Overshoot:       {metrics.overshoot_pct:.2f} %")
    print(f"Settling Time:   {metrics.settling_time:.4f} s")
    print(f"Steady-State Error: {metrics.steady_state_error:.6f}")
    print(f"Peak Value:      {metrics.peak_value:.4f}")
    print(f"Peak Time:       {metrics.peak_time:.4f} s")

    # Analytical comparison
    print("\nAnalytical (second-order):")
    analytical = PerformanceMetrics.second_order_metrics(omega_n=2, zeta=0.5)
    print(f"  Rise Time:     {analytical.rise_time:.4f} s")
    print(f"  Overshoot:     {analytical.overshoot_pct:.2f} %")
    print(f"  Settling Time: {analytical.settling_time:.4f} s")

    # --- Frequency Domain ---
    print("\n--- Frequency Response ---")
    fr = FrequencyResponse(tf)

    bode = fr.bode()
    print(f"Bode data: {len(bode.omega)} frequency points")
    print(f"  DC magnitude: {bode.magnitude_db[0]:.2f} dB")
    print(f"  HF magnitude: {bode.magnitude_db[-1]:.2f} dB")

    peak = fr.resonance_peak()
    print(f"Resonance peak: {peak['peak_db']:.2f} dB at {peak['peak_freq']:.2f} rad/s")

    bw = fr.bandwidth()
    print(f"Bandwidth (-3dB): {bw:.2f} rad/s")

    margins = fr.margins()
    print(f"Gain Margin: {margins.gain_margin_db}")
    print(f"Phase Margin: {margins.phase_margin_deg}")

    # --- Stability ---
    print("\n--- Stability Analysis ---")
    sa = StabilityAnalyzer(tf)
    routh = sa.routh()
    print(f"Routh stable: {routh.is_stable}")
    print(f"Sign changes: {routh.sign_changes}")

    info = sa.stability_margins_robust()
    print(f"Open-loop stable: {info['open_loop_stable']}")
    print(f"Closed-loop stable: {info['closed_loop_stable']}")

    print("\n" + "=" * 60)
    print("Analysis complete.")


if __name__ == "__main__":
    main()
