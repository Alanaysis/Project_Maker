"""
电路仿真 SPICE - Circuit Simulation with SPICE

A Python-based SPICE circuit simulator implementing:
- Netlist parsing (SPICE format)
- DC analysis (Modified Nodal Analysis)
- AC analysis (frequency sweep)
- Transient analysis (time-domain simulation)
"""

from .components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource
from .netlist import NetlistParser
from .circuit import Circuit
from .dc_analysis import DCAnalysis
from .ac_analysis import ACAnalysis
from .transient_analysis import TransientAnalysis

__version__ = "1.0.0"
__all__ = [
    "Resistor", "Capacitor", "Inductor", "VoltageSource", "CurrentSource",
    "NetlistParser", "Circuit",
    "DCAnalysis", "ACAnalysis", "TransientAnalysis"
]
