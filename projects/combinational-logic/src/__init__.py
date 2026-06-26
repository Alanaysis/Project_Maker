"""
组合逻辑电路模拟 - 包
Combinational Logic Circuit Simulation - Package
"""

from src.gates import *
from src.adders import HalfAdder, FullAdder, RippleCarryAdder, Subtracter
from src.multiplier import DirectMultiplier, WallaceTreeMultiplier
from src.mux_demux import Multiplexer2to1, Multiplexer4to1, Multiplexer8to1
from src.mux_demux import Demultiplexer1to2, Demultiplexer1to8
from src.encoder_decoder import BinaryEncoder, BCDToBinaryEncoder
from src.encoder_decoder import BinaryDecoder, BCDDecoder, SevenSegmentDecoder
from src.comparator import Comparator1Bit, Comparator4Bit, ComparatorNBit
from src.tri_state import TriStateBuffer, BusDriver
from src.logic_synthesis import MuxLogicSynthesizer

__all__ = [
    # Gates
    "Gate", "AND", "OR", "NOT", "XOR", "NAND", "NOR", "XNOR",
    # Adders
    "HalfAdder", "FullAdder", "RippleCarryAdder", "Subtracter",
    # Multiplier
    "DirectMultiplier", "WallaceTreeMultiplier",
    # MUX/DEMUX
    "Multiplexer2to1", "Multiplexer4to1", "Multiplexer8to1",
    "Demultiplexer1to2", "Demultiplexer1to8",
    # Encoder/Decoder
    "BinaryEncoder", "BCDToBinaryEncoder",
    "BinaryDecoder", "BCDDecoder", "SevenSegmentDecoder",
    # Comparator
    "Comparator1Bit", "Comparator4Bit", "ComparatorNBit",
    # Tri-state
    "TriStateBuffer", "BusDriver",
    # Logic synthesis
    "MuxLogicSynthesizer",
]
