"""
Mesh slicing algorithm.

Slicing converts a 3D triangle mesh into a series of 2D cross-sections at
different Z heights (layers). Each layer represents the intersection of the
mesh with a horizontal plane at that Z level.

Key concept: When a triangle is intersected by a slicing plane, the result
is a line segment (or empty). All such segments at a given Z form the
layer's cross-section geometry.
"""

import numpy as np
from typing import List, Tuple, Optional
from .stl_parser import STLModel, STLTriangle


class SliceSegment:
    """A line segment representing the intersection of a triangle with a slicing plane."""
    __slots__ = ['start', 'end']

    def __init__(self, start: np.ndarray, end: np.ndarray):
        self.start = start
        self.end = end

    def length(self) -> float:
        return np.linalg.norm(self.end - self.start)

    def midpoint(self) -> np.ndarray:
        return (self.start + self.end) / 2.0

    def __repr__(self):
        return f"Segment(({self.start[0]:.3f},{self.start[1]:.3f}) -> ({self.end[0]:.3f},{self.end[1]:.3f}))"


class Layer:
    """Represents a single sliced layer at a specific Z height."""
    __slots__ = ['z_height', 'segments', 'perimeters', 'infill_regions']

    def __init__(self, z_height: float):
        self.z_height = z_height
        self.segments: List[SliceSegment] = []
        self.perimeters: List[List[np.ndarray]] = []  # Closed perimeter loops
        self.infill_regions: List[List[np.ndarray]] = []  # Regions to fill

    @property
    def total_segment_length(self) -> float:
        return sum(s.length() for s in self.segments)

    def __repr__(self):
        return f"Layer(z={self.z_height:.3f}, segments={len(self.segments)})"


def intersect_triangle_with_plane(tri: STLTriangle, z: float) -> Optional[SliceSegment]:
    """
    Find the intersection of a triangle with a horizontal plane at height z.

    For each edge of the triangle, check if it crosses the plane.
    If exactly 2 edges cross, we get a line segment.
    If 0 or 1 edge crosses, no intersection (or vertex touching).
    If all 3 vertices are on the plane, the triangle is coplanar (skip).

    Returns a SliceSegment if the triangle is intersected, None otherwise.
    """
    va, vb, vc = tri.vertex_a, tri.vertex_b, tri.vertex_c

    # Determine which vertices are above/below/on the plane
    above = []
    below = []
    on_plane = []

    if va[2] > z:
        above.append(va)
    elif va[2] < z:
        below.append(va)
    else:
        on_plane.append(va)

    if vb[2] > z:
        above.append(vb)
    elif vb[2] < z:
        below.append(vb)
    else:
        on_plane.append(vb)

    if vc[2] > z:
        above.append(vc)
    elif vc[2] < z:
        below.append(vc)
    else:
        on_plane.append(vc)

    # Need at least one vertex above and one below for a crossing
    if len(above) == 0 or len(below) == 0:
        return None

    # Find the two intersection points by linear interpolation
    intersection_points = []

    # Edge va-vb
    if (va[2] - z) * (vb[2] - z) <= 0 and va[2] != vb[2]:
        t = (z - va[2]) / (vb[2] - va[2])
        p = va + t * (vb - va)
        p[2] = z  # Snap to plane
        intersection_points.append(p)

    # Edge vb-vc
    if (vb[2] - z) * (vc[2] - z) <= 0 and vb[2] != vc[2]:
        t = (z - vb[2]) / (vc[2] - vb[2])
        p = vb + t * (vc - vb)
        p[2] = z
        intersection_points.append(p)

    # Edge vc-va
    if (vc[2] - z) * (va[2] - z) <= 0 and vc[2] != va[2]:
        t = (z - vc[2]) / (va[2] - vc[2])
        p = vc + t * (va - vc)
        p[2] = z
        intersection_points.append(p)

    if len(intersection_points) == 2:
        return SliceSegment(intersection_points[0], intersection_points[1])

    return None


def slice_mesh(model: STLModel, z_min: float, z_max: float,
               layer_height: float) -> List[Layer]:
    """
    Slice a mesh model into layers at regular Z intervals.

    For each layer:
    1. Find all triangles that intersect the slicing plane
    2. Compute intersection segments for each triangle
    3. Store segments for perimeter extraction

    Returns a list of Layer objects sorted from bottom to top.
    """
    layers = []
    z = z_min

    while z <= z_max:
        layer = Layer(z)

        for tri in model.triangles:
            segment = intersect_triangle_with_plane(tri, z)
            if segment is not None:
                layer.segments.append(segment)

        layers.append(layer)
        z += layer_height

    return layers


def extract_perimeters(layers: List[Layer]) -> List[List[List[np.ndarray]]]:
    """
    Extract closed perimeter loops from layer segments.

    Perimeters are the outer boundary of each layer. They are extracted by:
    1. Connecting segments end-to-end where they overlap
    2. Forming closed loops

    This is a simplified approach - a production slicer would use a more
    sophisticated polygon reconstruction algorithm.
    """
    all_perimeters = []

    for layer in layers:
        if not layer.segments:
            all_perimeters.append([])
            continue

        # Sort segments by their x-coordinate to help with ordering
        segments = sorted(layer.segments, key=lambda s: s.start[0])

        # Group segments that form connected chains
        perimeters = _connect_segments(segments)
        layer.perimeters = perimeters
        all_perimeters.append(perimeters)

    return all_perimeters


def _connect_segments(segments: List[SliceSegment], tol: float = 1e-6
                      ) -> List[List[np.ndarray]]:
    """Connect line segments into closed loops."""
    if not segments:
        return []

    used = [False] * len(segments)
    loops = []

    for i, seg in enumerate(segments):
        if used[i]:
            continue

        # Start a new chain from this segment
        chain = [seg.start.copy(), seg.end.copy()]
        used[i] = True

        # Try to extend the chain
        changed = True
        while changed:
            changed = False
            for j, other in enumerate(segments):
                if used[j]:
                    continue

                # Check if other connects to the end of chain
                if np.linalg.norm(other.start - chain[-1]) < tol:
                    chain.append(other.end.copy())
                    used[j] = True
                    changed = True
                elif np.linalg.norm(other.end - chain[-1]) < tol:
                    chain.append(other.start.copy())
                    used[j] = True
                    changed = True
                elif np.linalg.norm(other.start - chain[0]) < tol:
                    chain.insert(0, other.end.copy())
                    used[j] = True
                    changed = True
                elif np.linalg.norm(other.end - chain[0]) < tol:
                    chain.insert(0, other.start.copy())
                    used[j] = True
                    changed = True

        # Only close the loop if it's roughly closed
        if np.linalg.norm(chain[-1] - chain[0]) < tol:
            loops.append(chain)

    return loops
