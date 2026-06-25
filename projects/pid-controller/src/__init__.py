"""
PID Controller - A from-scratch implementation of the PID control algorithm.

This package provides:
- PIDController: Core PID control algorithm with anti-windup and improved variants
- Plant models: First-order, second-order, and delay system simulation
- PIDTuner: Automatic parameter tuning (Ziegler-Nichols, Cohen-Coon, manual)
- Simulator: Run closed-loop simulations and collect data
"""

from .pid_controller import PIDController
from .plant import FirstOrderPlant, SecondOrderPlant, DelaySystem
from .tuner import PIDTuner
from .simulator import Simulator

__all__ = [
    "PIDController",
    "FirstOrderPlant",
    "SecondOrderPlant",
    "DelaySystem",
    "PIDTuner",
    "Simulator",
]
