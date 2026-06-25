"""
表格识别模块

提供表格检测、结构识别、单元格提取和数据输出功能。
"""

__version__ = "1.0.0"
__author__ = "Table Recognition Team"

from .detector import TableDetector
from .structure import StructureRecognizer
from .extractor import CellExtractor
from .pipeline import TableRecognitionPipeline

__all__ = [
    "TableDetector",
    "StructureRecognizer",
    "CellExtractor",
    "TableRecognitionPipeline",
]
