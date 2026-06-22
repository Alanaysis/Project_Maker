"""网格处理算法库

支持三角网格的简化、细分和平滑操作。
"""

__version__ = "0.1.0"

from .mesh_data import TriangleMesh, Vertex, Face
from .simplification import MeshSimplifier
from .subdivision import LoopSubdivision
from .smoothing import LaplacianSmoother

__all__ = [
    'TriangleMesh',
    'Vertex',
    'Face',
    'MeshSimplifier',
    'LoopSubdivision',
    'LaplacianSmoother'
]
