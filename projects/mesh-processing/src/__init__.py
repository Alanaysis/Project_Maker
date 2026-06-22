"""
Mesh Processing Library
=======================

A Python library for 3D mesh processing algorithms including:
- Mesh simplification (Quadric Error Metrics)
- Mesh subdivision (Loop Subdivision)
- Mesh smoothing (Laplacian and Taubin smoothing)
"""

__version__ = "0.1.0"
__author__ = "Mesh Processing Learning Project"

from .mesh import TriangleMesh
from .simplification import MeshSimplifier
from .subdivision import MeshSubdivider
from .smoothing import MeshSmoother

__all__ = [
    "TriangleMesh",
    "MeshSimplifier",
    "MeshSubdivider",
    "MeshSmoother",
]
