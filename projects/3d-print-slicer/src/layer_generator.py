"""
Layer generation module.

After slicing, we have raw intersection segments. This module processes them
into usable layer representations with perimeters and infill regions.

Key concepts:
- Perimeter (outline): The outer boundary of each layer
- Infill: The internal pattern that fills the perimeter
- Solid top/bottom: Dense layers at the top and bottom surfaces
"""

import numpy as np
from typing import List, Tuple, Dict
from .mesh_slicer import Layer, SliceSegment, extract_perimeters


class LayerGeometry:
    """Processed geometry for a single layer."""
    __slots__ = ['z_height', 'perimeter_loops', 'infill_loops', 'segment_length', 'area_estimate']

    def __init__(self, z_height: float):
        self.z_height = z_height
        self.perimeter_loops: List[List[np.ndarray]] = []  # Closed perimeter loops
        self.infill_loops: List[List[np.ndarray]] = []     # Infill path segments
        self.segment_length: float = 0.0
        self.area_estimate: float = 0.0

    def __repr__(self):
        return (f"LayerGeometry(z={self.z_height:.3f}, "
                f"perimeters={len(self.perimeter_loops)}, "
                f"infill={len(self.infill_loops)}, "
                f"length={self.segment_length:.1f})")


def generate_layer_geometries(layers: List[Layer], layer_height: float,
                              perimeter_width: float = 0.4,
                              top_layers: int = 3,
                              bottom_layers: int = 3) -> List[LayerGeometry]:
    """
    Generate processed layer geometries from raw sliced layers.

    Args:
        layers: Raw sliced layers from mesh_slicer
        layer_height: Height of each layer
        perimeter_width: Width of perimeter extrusion (mm)
        top_layers: Number of solid top layers
        bottom_layers: Number of solid bottom layers
    """
    geometries = []

    # Get layer bounds for top/bottom detection
    layer_bounds = []
    for layer in layers:
        if layer.segments:
            all_pts = []
            for seg in layer.segments:
                all_pts.extend([seg.start, seg.end])
            all_pts = np.array(all_pts)
            layer_bounds.append((np.min(all_pts, axis=0), np.max(all_pts, axis=0)))
        else:
            layer_bounds.append(None)

    # Extract perimeters for all layers
    all_perimeters = extract_perimeters(layers)

    for i, layer in enumerate(layers):
        geo = LayerGeometry(layer.z_height)

        if layer.segments:
            geo.segment_length = layer.total_segment_length

            # Extract perimeter loops
            geo.perimeter_loops = all_perimeters[i]

            # Estimate area from segment lengths and layer height
            geo.area_estimate = _estimate_layer_area(layer, layer_height)

            # Generate infill for non-solid layers
            is_top = i >= len(layers) - top_layers
            is_bottom = i < bottom_layers

            if not is_top and not is_bottom:
                geo.infill_loops = _generate_infill_regions(layer, layer_bounds[i])

        geometries.append(geo)

    return geometries


def _estimate_layer_area(layer: Layer, layer_height: float) -> float:
    """Estimate the cross-sectional area of a layer from its segments."""
    # Approximate area as total segment length * layer height
    # This is a rough estimate; a production slicer would compute polygon area
    return layer.total_segment_length * layer_height


def _generate_infill_regions(layer: Layer, bounds: Tuple[np.ndarray, np.ndarray]
                             ) -> List[List[np.ndarray]]:
    """
    Generate infill regions for a layer.

    For a learning implementation, we create simple horizontal lines
    spanning the layer's bounding box. A production slicer would use
    more sophisticated fill patterns based on the actual perimeter shape.
    """
    if not bounds or not layer.segments:
        return []

    min_pt, max_pt = bounds
    x_start, y_start = min_pt[0], min_pt[1]
    x_end, y_end = max_pt[0], max_pt[1]

    # Create horizontal infill lines spaced by layer_height
    infill_lines = []
    z = y_start
    step = 2.0  # Spacing between infill lines (mm)

    while z <= y_end:
        if x_end > x_start:
            line = [np.array([x_start, z, layer.z_height]),
                    np.array([x_end, z, layer.z_height])]
            infill_lines.append(line)
        z += step

    return infill_lines
