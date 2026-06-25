"""
External Sort - 外部排序库

适用于大规模数据排序，无法全部装入内存的场景。
包含初始归并段生成、多路归并、置换选择排序等核心算法。
"""

from .min_heap import MinHeap
from .io_buffer import IOBuffer, BufferedWriter, BufferedReader
from .run_generator import RunGenerator, ReplacementSelection
from .kway_merger import KWayMerger
from .external_sort import ExternalSorter

__version__ = "1.0.0"
__all__ = [
    "MinHeap",
    "IOBuffer",
    "BufferedWriter",
    "BufferedReader",
    "RunGenerator",
    "ReplacementSelection",
    "KWayMerger",
    "ExternalSorter",
]
