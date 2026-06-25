"""
应用模块

本模块实现了数字电路的实际应用：
- SimpleCPU: 简单CPU设计
- MemoryUnit: 存储单元
"""

from .cpu import SimpleCPU
from .memory import MemoryUnit

__all__ = [
    "SimpleCPU",
    "MemoryUnit",
]
