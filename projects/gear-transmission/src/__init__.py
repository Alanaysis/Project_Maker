# Gear Transmission System - Package
# 齿轮传动系统 - 包

from .spur_gear import SpurGear
from .gear_ratio import GearRatioCalculator
from .transmission import TransmissionCalculator
from .efficiency import EfficiencyAnalyzer
from .gear_train import SimpleGearTrain, CompoundGearTrain, PlanetaryGearTrain
from .contact_ratio import ContactRatioCalculator

__all__ = [
    "SpurGear",
    "GearRatioCalculator",
    "TransmissionCalculator",
    "EfficiencyAnalyzer",
    "SimpleGearTrain",
    "CompoundGearTrain",
    "PlanetaryGearTrain",
    "ContactRatioCalculator",
]
