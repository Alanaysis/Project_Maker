"""
Support structure generation module.

Support structures provide temporary physical support for overhanging
geometry during printing. They are removed after printing.

Key concepts:
- Overhang angle: Below this angle, support is needed
- Support density: How dense the support material is
- Support pattern: How the support material is arranged
- Interfaces: Dense layers between support and model for easy removal
"""

import numpy as np
from typing import List, Tuple, Optional
from .mesh_slicer import Layer, SliceSegment
from .infill_generator import InfillPattern


class SupportStructure:
    """Represents a support structure for a single layer."""
    __slots__ = ['z_height', 'segments', 'is_interface', 'pattern']

    def __init__(self, z_height: float):
        self.z_height = z_height
        self.segments: List[Tuple[np.ndarray, np.ndarray]] = []
        self.is_interface = False  # Interface layer (between support and model)
        self.pattern = InfillPattern.GRID

    def __repr__(self):
        status = "interface" if self.is_interface else "support"
        return f"Support(z={self.z_height:.3f}, segments={len(self.segments)}, {status})"


class SupportGenerator:
    """
    Generates support structures for overhanging geometry.

    A support structure is needed when:
    1. A layer has geometry that doesn't connect to the layer below
    2. An overhang angle exceeds the maximum overhang angle
    3. A bridge spans too far without support

    For this learning implementation, we use a simplified approach:
    - Detect unsupported regions by comparing consecutive layers
    - Fill unsupported areas with support material
    """

    def __init__(self,
                 max_overhang_angle: float = 45.0,
                 support_density: float = 15.0,
                 support_pattern: InfillPattern = InfillPattern.GRID,
                 interface_thickness: float = 0.2,
                 z_distance_top: float = 0.2,
                 z_distance_bottom: float = 0.2):
        self.max_overhang_angle = max_overhang_angle
        self.support_density = support_density
        self.support_pattern = support_pattern
        self.interface_thickness = interface_thickness
        self.z_distance_top = z_distance_top
        self.z_distance_bottom = z_distance_bottom

    def generate(self, layers: List[Layer],
                 layer_height: float) -> List[SupportStructure]:
        """
        Generate support structures for all layers.

        Args:
            layers: Sliced layers
            layer_height: Height of each layer

        Returns:
            List of SupportStructure objects
        """
        supports = []

        # Track which areas are supported from below
        previous_bbox = None

        for i, layer in enumerate(layers):
            support = SupportStructure(layer.z_height)

            if layer.segments:
                current_bbox = self._get_bbox(layer)

                if previous_bbox is not None:
                    # Check for overhangs
                    if self._has_overhang(previous_bbox, current_bbox, layer_height):
                        # Generate support for the overhanging area
                        support.segments = self._generate_support_region(
                            current_bbox, layer.z_height
                        )
                        support.is_interface = False
                    elif self._is_adjacent_to_model(previous_bbox, current_bbox):
                        # This layer is adjacent to model material
                        # Add interface layer for easier removal
                        support.is_interface = True
                        support.segments = self._generate_support_region(
                            current_bbox, layer.z_height, dense=True
                        )

                previous_bbox = current_bbox

            supports.append(support)

        return supports

    def _get_bbox(self, layer: Layer) -> Tuple[np.ndarray, np.ndarray]:
        """Get the bounding box of a layer."""
        all_pts = []
        for seg in layer.segments:
            all_pts.extend([seg.start, seg.end])
        all_pts = np.array(all_pts)
        return (np.min(all_pts[:2], axis=0), np.max(all_pts[:2], axis=0))

    def _has_overhang(self, prev_bbox, curr_bbox, layer_height: float) -> bool:
        """Check if there's an overhang between consecutive layers."""
        if prev_bbox is None or curr_bbox is None:
            return False

        prev_min, prev_max = prev_bbox
        curr_min, curr_max = curr_bbox

        # Check if current layer extends beyond previous layer
        extends_x = (curr_max[0] > prev_max[0] + layer_height) or \
                     (curr_min[0] < prev_min[0] - layer_height)
        extends_y = (curr_max[1] > prev_max[1] + layer_height) or \
                     (curr_min[1] < prev_min[1] - layer_height)

        return extends_x or extends_y

    def _is_adjacent_to_model(self, prev_bbox, curr_bbox) -> bool:
        """Check if current layer is adjacent to model geometry."""
        if prev_bbox is None:
            return False

        prev_min, prev_max = prev_bbox
        curr_min, curr_max = curr_bbox

        # Check for overlap
        x_overlap = max(0, min(prev_max[0], curr_max[0]) - max(prev_min[0], curr_min[0]))
        y_overlap = max(0, min(prev_max[1], curr_max[1]) - max(prev_min[1], curr_min[1]))

        return x_overlap > 0 and y_overlap > 0

    def _generate_support_region(self, bbox, z_height: float,
                                  dense: bool = False) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate support segments for a bounding region."""
        min_pt, max_pt = bbox
        spacing = 3.0 if not dense else 2.0

        segments = []
        y = min_pt[1]

        while y <= max_pt[1]:
            p1 = np.array([min_pt[0], y, z_height])
            p2 = np.array([max_pt[0], y, z_height])
            segments.append((p1, p2))
            y += spacing

        return segments
