"""
Triangle Mesh Data Structure

This module implements a triangle mesh data structure using numpy arrays
for efficient storage and manipulation of 3D geometry.
"""

import numpy as np
from typing import List, Tuple, Set, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class HalfEdge:
    """Half-edge data structure for mesh traversal."""
    vertex: int = -1
    next: int = -1
    twin: int = -1
    face: int = -1
    edge: int = -1


@dataclass
class Edge:
    """Edge representation."""
    halfedge: int = -1
    vertices: Tuple[int, int] = (-1, -1)


class TriangleMesh:
    """
    Triangle mesh data structure.

    Stores vertices and faces using numpy arrays for efficient computation.
    Provides adjacency information for mesh traversal and manipulation.

    Attributes:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of face vertex indices
    """

    def __init__(self, vertices: np.ndarray = None, faces: np.ndarray = None):
        """
        Initialize a triangle mesh.

        Args:
            vertices: Nx3 array of vertex positions (x, y, z)
            faces: Mx3 array of triangle face indices
        """
        if vertices is None:
            self.vertices = np.zeros((0, 3), dtype=np.float64)
        else:
            self.vertices = np.array(vertices, dtype=np.float64)

        if faces is None:
            self.faces = np.zeros((0, 3), dtype=np.int32)
        else:
            self.faces = np.array(faces, dtype=np.int32)

        # Adjacency data structures (lazy initialization)
        self._vertex_faces: Optional[Dict[int, Set[int]]] = None
        self._vertex_neighbors: Optional[Dict[int, Set[int]]] = None
        self._edge_faces: Optional[Dict[Tuple[int, int], Set[int]]] = None
        self._face_normals: Optional[np.ndarray] = None
        self._vertex_normals: Optional[np.ndarray] = None

    @property
    def num_vertices(self) -> int:
        """Number of vertices."""
        return len(self.vertices)

    @property
    def num_faces(self) -> int:
        """Number of faces."""
        return len(self.faces)

    @property
    def num_edges(self) -> int:
        """Number of edges."""
        self._build_edge_adjacency()
        return len(self._edge_faces)

    def _build_vertex_adjacency(self):
        """Build vertex adjacency information."""
        if self._vertex_faces is not None:
            return

        self._vertex_faces = {i: set() for i in range(self.num_vertices)}
        self._vertex_neighbors = {i: set() for i in range(self.num_vertices)}

        for face_idx, face in enumerate(self.faces):
            for i in range(3):
                v = face[i]
                self._vertex_faces[v].add(face_idx)
                # Add neighbors (other vertices in the same face)
                self._vertex_neighbors[v].add(face[(i + 1) % 3])
                self._vertex_neighbors[v].add(face[(i + 2) % 3])

    def _build_edge_adjacency(self):
        """Build edge adjacency information."""
        if self._edge_faces is not None:
            return

        self._edge_faces = {}

        for face_idx, face in enumerate(self.faces):
            for i in range(3):
                v0, v1 = face[i], face[(i + 1) % 3]
                edge = (min(v0, v1), max(v0, v1))
                if edge not in self._edge_faces:
                    self._edge_faces[edge] = set()
                self._edge_faces[edge].add(face_idx)

    def get_vertex_faces(self, vertex_idx: int) -> Set[int]:
        """Get indices of faces adjacent to a vertex."""
        self._build_vertex_adjacency()
        return self._vertex_faces.get(vertex_idx, set())

    def get_vertex_neighbors(self, vertex_idx: int) -> Set[int]:
        """Get indices of neighboring vertices."""
        self._build_vertex_adjacency()
        return self._vertex_neighbors.get(vertex_idx, set())

    def get_edge_faces(self, v0: int, v1: int) -> Set[int]:
        """Get indices of faces adjacent to an edge."""
        self._build_edge_adjacency()
        edge = (min(v0, v1), max(v0, v1))
        return self._edge_faces.get(edge, set())

    def compute_face_normals(self) -> np.ndarray:
        """Compute face normals for all faces."""
        if self._face_normals is not None:
            return self._face_normals

        if self.num_faces == 0:
            return np.zeros((0, 3))

        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]

        edge1 = v1 - v0
        edge2 = v2 - v0

        normals = np.cross(edge1, edge2)
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        lengths = np.maximum(lengths, 1e-10)  # Avoid division by zero

        self._face_normals = normals / lengths
        return self._face_normals

    def compute_vertex_normals(self) -> np.ndarray:
        """Compute vertex normals as average of adjacent face normals."""
        if self._vertex_normals is not None:
            return self._vertex_normals

        face_normals = self.compute_face_normals()
        self._vertex_normals = np.zeros_like(self.vertices)

        self._build_vertex_adjacency()

        for vertex_idx in range(self.num_vertices):
            adjacent_faces = self._vertex_faces[vertex_idx]
            if adjacent_faces:
                normal = np.mean(face_normals[list(adjacent_faces)], axis=0)
                length = np.linalg.norm(normal)
                if length > 1e-10:
                    normal /= length
                self._vertex_normals[vertex_idx] = normal

        return self._vertex_normals

    def compute_face_area(self, face_idx: int) -> float:
        """Compute area of a single face."""
        face = self.faces[face_idx]
        v0, v1, v2 = self.vertices[face]

        edge1 = v1 - v0
        edge2 = v2 - v0

        return 0.5 * np.linalg.norm(np.cross(edge1, edge2))

    def compute_total_area(self) -> float:
        """Compute total surface area of the mesh."""
        total = 0.0
        for i in range(self.num_faces):
            total += self.compute_face_area(i)
        return total

    def compute_edge_length(self, v0: int, v1: int) -> float:
        """Compute length of an edge."""
        return np.linalg.norm(self.vertices[v0] - self.vertices[v1])

    def invalidate_cache(self):
        """Invalidate cached adjacency and normal data."""
        self._vertex_faces = None
        self._vertex_neighbors = None
        self._edge_faces = None
        self._face_normals = None
        self._vertex_normals = None

    def add_vertex(self, position: np.ndarray) -> int:
        """
        Add a vertex to the mesh.

        Args:
            position: 3D position of the vertex

        Returns:
            Index of the new vertex
        """
        idx = self.num_vertices
        self.vertices = np.vstack([self.vertices, position.reshape(1, 3)])
        self.invalidate_cache()
        return idx

    def add_face(self, v0: int, v1: int, v2: int) -> int:
        """
        Add a triangle face to the mesh.

        Args:
            v0, v1, v2: Vertex indices

        Returns:
            Index of the new face
        """
        idx = self.num_faces
        self.faces = np.vstack([self.faces, np.array([[v0, v1, v2]], dtype=np.int32)])
        self.invalidate_cache()
        return idx

    def remove_face(self, face_idx: int):
        """Remove a face from the mesh."""
        self.faces = np.delete(self.faces, face_idx, axis=0)
        self.invalidate_cache()

    def remove_vertex(self, vertex_idx: int):
        """
        Remove a vertex and all faces containing it.

        Args:
            vertex_idx: Index of vertex to remove
        """
        # Remove faces containing this vertex
        mask = ~np.any(self.faces == vertex_idx, axis=1)
        self.faces = self.faces[mask]

        # Update face indices (shift down indices > vertex_idx)
        self.faces[self.faces > vertex_idx] -= 1

        # Remove vertex
        self.vertices = np.delete(self.vertices, vertex_idx, axis=0)
        self.invalidate_cache()

    def copy(self) -> 'TriangleMesh':
        """Create a deep copy of the mesh."""
        new_mesh = TriangleMesh(
            vertices=self.vertices.copy(),
            faces=self.faces.copy()
        )
        return new_mesh

    def validate(self) -> bool:
        """
        Validate mesh topology.

        Returns:
            True if mesh is valid
        """
        if self.num_vertices == 0 or self.num_faces == 0:
            return True

        # Check face indices are valid
        if np.any(self.faces >= self.num_vertices):
            return False
        if np.any(self.faces < 0):
            return False

        # Check for degenerate faces (duplicate vertices in face)
        for face in self.faces:
            if len(set(face)) < 3:
                return False

        return True

    @staticmethod
    def create_cube() -> 'TriangleMesh':
        """Create a unit cube mesh."""
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # Bottom
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],  # Top
        ], dtype=np.float64)

        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom
            [4, 6, 5], [4, 7, 6],  # Top
            [0, 4, 5], [0, 5, 1],  # Front
            [2, 6, 7], [2, 7, 3],  # Back
            [0, 3, 7], [0, 7, 4],  # Left
            [1, 5, 6], [1, 6, 2],  # Right
        ], dtype=np.int32)

        return TriangleMesh(vertices, faces)

    @staticmethod
    def create_icosphere(subdivisions: int = 1) -> 'TriangleMesh':
        """
        Create an icosphere mesh.

        Args:
            subdivisions: Number of subdivision iterations

        Returns:
            Icosphere mesh
        """
        # Golden ratio
        phi = (1 + np.sqrt(5)) / 2

        # Initial icosahedron vertices
        vertices = np.array([
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
        ], dtype=np.float64)

        # Normalize to unit sphere
        norms = np.linalg.norm(vertices, axis=1, keepdims=True)
        vertices /= norms

        # Initial icosahedron faces
        faces = np.array([
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
        ], dtype=np.int32)

        mesh = TriangleMesh(vertices, faces)

        # Subdivide
        from .subdivision import MeshSubdivider
        subdivider = MeshSubdivider()
        for _ in range(subdivisions):
            mesh = subdivider.loop_subdivide(mesh)

        # Project vertices back to unit sphere
        norms = np.linalg.norm(mesh.vertices, axis=1, keepdims=True)
        mesh.vertices /= norms

        return mesh

    def __repr__(self) -> str:
        return (f"TriangleMesh(vertices={self.num_vertices}, "
                f"faces={self.num_faces}, edges={self.num_edges})")
