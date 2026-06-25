"""
组合电路模块

本模块实现了各种组合逻辑电路：
- Multiplexer: 多路选择器
- Demultiplexer: 解码器/多路分配器
- Decoder: 二进制解码器
- Encoder: 编码器
- HalfAdder: 半加器
- FullAdder: 全加器
- RippleCarryAdder: 纹波进位加法器
- Comparator: 比较器
- ALU: 算术逻辑单元
"""

from .multiplexer import Multiplexer, Demultiplexer
from .decoder import Decoder, Encoder
from .adder import HalfAdder, FullAdder, RippleCarryAdder
from .comparator import Comparator
from .alu import ALU

__all__ = [
    "Multiplexer",
    "Demultiplexer",
    "Decoder",
    "Encoder",
    "HalfAdder",
    "FullAdder",
    "RippleCarryAdder",
    "Comparator",
    "ALU",
]
