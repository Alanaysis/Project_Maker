"""Controller design example."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src import (
    TransferFunction,
    TimeResponse,
    FrequencyResponse,
    PerformanceMetrics,
    ControllerDesigner,
)


def main():
    print("=" * 60)
    print("Controller Design Example")
    print("=" * 60)

    # Plant: G(s) = 1 / (s(s+1)) -- integrator with lag
    plant = TransferFunction([1], [1, 1, 0])
    print(f"\nPlant: {plant}")
    print(f"Poles: {plant.poles()}")

    # --- PID Design ---
    print("\n--- PID Controller Design ---")
    designer = ControllerDesigner(plant)

    # Ziegler-Nichols step method
    pid_params = designer.pid_ziegler_nichols(method="step")
    print(f"PID Parameters (Z-N step):")
    print(f"  Kp = {pid_params.Kp:.4f}")
    print(f"  Ki = {pid_params.Ki:.4f}")
    print(f"  Kd = {pid_params.Kd:.4f}")

    # Create PID controller
    pid_tf = ControllerDesigner.pid_transfer_function(pid_params)
    print(f"PID Transfer Function: {pid_tf}")

    # Closed-loop with PID
    open_loop = pid_tf * plant
    closed_loop = open_loop.feedback()
    print(f"Closed-loop poles: {closed_loop.poles()}")

    # Analyze closed-loop performance
    cl_pm = PerformanceMetrics(closed_loop)
    cl_metrics = cl_pm.step_metrics(t_final=10)
    print(f"Closed-loop step response:")
    print(f"  Rise Time:     {cl_metrics.rise_time:.4f} s")
    print(f"  Overshoot:     {cl_metrics.overshoot_pct:.2f} %")
    print(f"  Settling Time: {cl_metrics.settling_time:.4f} s")

    # --- Lead Compensator ---
    print("\n--- Lead Compensator Design ---")
    lead = designer.design_lead(phase_boost_deg=60, omega_cross=2.0)
    print(f"Lead compensator: {lead}")

    # Closed-loop with lead
    open_loop_lead = lead * plant
    cl_lead = open_loop_lead.feedback()
    print(f"Closed-loop poles: {cl_lead.poles()}")

    cl_lead_pm = PerformanceMetrics(cl_lead)
    cl_lead_metrics = cl_lead_pm.step_metrics(t_final=10)
    print(f"Lead-compensated step response:")
    print(f"  Rise Time:     {cl_lead_metrics.rise_time:.4f} s")
    print(f"  Overshoot:     {cl_lead_metrics.overshoot_pct:.2f} %")
    print(f"  Settling Time: {cl_lead_metrics.settling_time:.4f} s")

    # --- Lag Compensator ---
    print("\n--- Lag Compensator Design ---")
    lag = designer.design_lag(low_freq_gain_boost=10, omega_cross=1.0)
    print(f"Lag compensator: {lag}")

    # --- Frequency domain comparison ---
    print("\n--- Frequency Domain Comparison ---")
    fr_plant = FrequencyResponse(plant)
    fr_lead = FrequencyResponse(open_loop_lead)

    m_plant = fr_plant.margins()
    m_lead = fr_lead.margins()
    print(f"Plant margins: GM={m_plant.gain_margin_db}, PM={m_plant.phase_margin_deg}")
    print(f"Lead-comp margins: GM={m_lead.gain_margin_db}, PM={m_lead.phase_margin_deg}")

    print("\n" + "=" * 60)
    print("Design complete.")


if __name__ == "__main__":
    main()
