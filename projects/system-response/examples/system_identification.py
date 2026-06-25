"""System identification example."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy import signal
from src import (
    TransferFunction,
    TimeResponse,
    PerformanceMetrics,
    SystemIdentifier,
)


def main():
    print("=" * 60)
    print("System Identification Example")
    print("=" * 60)

    # --- Step Response Identification ---
    print("\n--- From Step Response ---")

    # True system: G(s) = 3 / (2s + 1)
    tf_true = TransferFunction([3], [2, 1])
    sys_true = signal.lti(tf_true.num, tf_true.den)

    # Generate noisy step response
    t = np.linspace(0, 15, 500)
    _, y_clean = signal.step(sys_true, T=t)
    noise = np.random.normal(0, 0.02, len(t))
    y_noisy = y_clean + noise

    # Identify first-order model
    result1 = SystemIdentifier.from_step_response(t, y_noisy, model_order=1)
    print(f"True system: {tf_true}")
    print(f"Identified (1st order): {result1.tf}")
    print(f"Residual: {result1.residual:.4f}")
    print(f"Identified gain: {result1.tf.dc_gain:.3f} (true: {tf_true.dc_gain})")

    # --- Second-order identification ---
    print("\n--- Second-Order Step Response ---")

    # True system: G(s) = 4 / (s^2 + 1.2s + 4)
    # omega_n = 2, zeta = 0.3
    tf_true2 = TransferFunction.second_order(gain=1, omega_n=2, zeta=0.3)
    sys_true2 = signal.lti(tf_true2.num, tf_true2.den)

    t2 = np.linspace(0, 15, 1000)
    _, y2 = signal.step(sys_true2, T=t2)

    result2 = SystemIdentifier.from_step_response(t2, y2, model_order=2)
    print(f"True system: {tf_true2}")
    print(f"Identified (2nd order): {result2.tf}")
    print(f"Residual: {result2.residual:.4f}")

    # Compare performance
    pm_true = PerformanceMetrics(tf_true2)
    pm_id = PerformanceMetrics(result2.tf)

    m_true = pm_true.step_metrics(t_final=15)
    m_id = pm_id.step_metrics(t_final=15)

    print(f"\nPerformance comparison:")
    print(f"  {'Metric':<20} {'True':>10} {'Identified':>12}")
    print(f"  {'Rise Time':<20} {m_true.rise_time:>10.4f} {m_id.rise_time:>12.4f}")
    print(f"  {'Overshoot %':<20} {m_true.overshoot_pct:>10.2f} {m_id.overshoot_pct:>12.2f}")
    print(f"  {'Settling Time':<20} {m_true.settling_time:>10.4f} {m_id.settling_time:>12.4f}")

    # --- Frequency Response Identification ---
    print("\n--- From Frequency Response ---")

    omega = np.logspace(-1, 1, 30)
    resp = tf_true.eval_freq(omega)
    mag_db = 20 * np.log10(np.abs(resp))
    phase_deg = np.degrees(np.angle(resp))

    result_fr = SystemIdentifier.from_frequency_response(
        omega, mag_db, phase_deg, order=1
    )
    print(f"Identified from freq response: {result_fr.tf}")
    print(f"Residual: {result_fr.residual:.4f}")

    print("\n" + "=" * 60)
    print("Identification complete.")


if __name__ == "__main__":
    main()
