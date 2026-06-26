"""
Binary STL file parser for 3D models.

STL (Stereolithography) is a common 3D file format that represents triangular meshes.
Binary STL has a fixed structure:
- 80-byte header
- 4-byte triangle count
- For each triangle: 12 floats (normal + 3 vertices) + 2-byte attribute byte count
"""

import struct
import numpy as np
from typing import Tuple, List, Optional


class STLTriangle:
    """Represents a single triangle in an STL mesh."""
    __slots__ = ['vertex_a', 'vertex_b', 'vertex_c', 'normal']

    def __init__(self, vertex_a: np.ndarray, vertex_b: np.ndarray,
                 vertex_c: np.ndarray, normal: np.ndarray):
        self.vertex_a = vertex_a
        self.vertex_b = vertex_b
        self.vertex_c = vertex_c
        self.normal = normal

    @property
    def vertices(self) -> np.ndarray:
        """Return all 3 vertices as a (3, 3) array."""
        return np.array([self.vertex_a, self.vertex_b, self.vertex_c])

    @property
    def edges(self) -> List[np.ndarray]:
        """Return the 3 edges of the triangle."""
        return [
            self.vertex_b - self.vertex_a,
            self.vertex_c - self.vertex_b,
            self.vertex_a - self.vertex_c,
        ]

    def centroid(self) -> np.ndarray:
        """Calculate the centroid of the triangle."""
        return (self.vertex_a + self.vertex_b + self.vertex_c) / 3.0

    def area(self) -> float:
        """Calculate the area of the triangle using cross product."""
        edge1 = self.vertex_b - self.vertex_a
        edge2 = self.vertex_c - self.vertex_a
        return np.linalg.norm(np.cross(edge1, edge2)) / 2.0

    def bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return (min_corner, max_corner) of the triangle bounding box."""
        verts = self.vertices
        return np.min(verts, axis=0), np.max(verts, axis=0)


class STLModel:
    """Represents a complete STL mesh."""
    __slots__ = ['triangles', 'name', 'bounds']

    def __init__(self, name: str = ""):
        self.triangles: List[STLTriangle] = []
        self.name = name
        self.bounds = None

    def compute_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the axis-aligned bounding box of the mesh."""
        all_verts = []
        for tri in self.triangles:
            all_verts.extend([tri.vertex_a, tri.vertex_b, tri.vertex_c])
        all_verts = np.array(all_verts)
        self.bounds = (np.min(all_verts, axis=0), np.max(all_verts, axis=0))
        return self.bounds

    def num_vertices(self) -> int:
        return len(self.triangles) * 3

    def total_area(self) -> float:
        return sum(t.area() for t in self.triangles)

    def __len__(self) -> int:
        return len(self.triangles)


def parse_binary_stl(filepath: str) -> STLModel:
    """
    Parse a binary STL file.

    Binary STL format:
    - 80 bytes: header
    - 4 bytes: uint32 triangle count
    - For each triangle (50 bytes):
        - 12 bytes: normal vector (3 x float32)
        - 36 bytes: 3 vertices (9 x float32)
        - 2 bytes: attribute byte count (uint16)
    """
    model = STLModel()

    with open(filepath, 'rb') as f:
        header = f.read(80)
        model.name = header.decode('latin-1').strip('\x00')

        # Read triangle count
        data = f.read(4)
        if len(data) < 4:
            raise ValueError("Invalid STL file: cannot read triangle count")
        num_triangles = struct.unpack('<I', data)[0]

        for _ in range(num_triangles):
            data = f.read(50)
            if len(data) < 50:
                raise ValueError(f"Invalid STL file: truncated at triangle {_}")

            # Unpack: 3 floats normal + 9 floats vertices + 1 uint16
            values = struct.unpack('<3f9fH', data)
            normal = np.array(values[:3], dtype=np.float64)
            verts = np.array(values[3:12], dtype=np.float64).reshape(3, 3)

            triangle = STLTriangle(verts[0], verts[1], verts[2], normal)
            model.triangles.append(triangle)

    model.compute_bounds()
    return model


def parse_ascii_stl(filepath: str) -> STLModel:
    """
    Parse an ASCII STL file.

    ASCII STL format:
    solid name
      facet normal nx ny nz
        outer loop
          vertex x1 y1 z1
          vertex x2 y2 z2
          vertex x3 y3 z3
        endloop
      endfacet
    endsolid name
    """
    model = STLModel()
    triangles = []

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract normals
    normals = []
    for match in __import__('re').finditer(r'facet normal\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)', content):
        normals.append(np.array([float(match.group(i)) for i in range(1, 4)], dtype=np.float64))

    # Extract vertices
    vertex_pattern = __import__('re').finditer(r'vertex\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)', content)
    all_verts = np.array([[float(m.group(i)) for i in range(1, 4)] for m in vertex_pattern], dtype=np.float64)

    # Group vertices into triangles (3 vertices each)
    num_triangles = len(all_verts) // 3
    for i in range(num_triangles):
        idx = i * 3
        v0, v1, v2 = all_verts[idx], all_verts[idx + 1], all_verts[idx + 2]
        normal = normals[i] if i < len(normals) else np.array([0.0, 0.0, 1.0])
        triangles.append(STLTriangle(v0, v1, v2, normal))

    model.triangles = triangles
    model.compute_bounds()
    return model


def load_stl(filepath: str) -> STLModel:
    """Load an STL file, auto-detecting binary vs ASCII format."""
    with open(filepath, 'rb') as f:
        header = f.read(80)

    # Check if binary: read triangle count after header
    with open(filepath, 'rb') as f:
        f.seek(80)
        data = f.read(4)
        if len(data) >= 4:
            tri_count = struct.unpack('<I', data)[0]
            if tri_count > 0 and tri_count < 100_000_000:
                return parse_binary_stl(filepath)

    # Fallback to ASCII parsing
    return parse_ascii_stl(filepath)
