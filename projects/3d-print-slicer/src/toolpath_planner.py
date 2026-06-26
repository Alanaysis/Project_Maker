"""
Toolpath generation module.

Toolpath planning determines the order and path that the extruder head
follows to deposit material. The standard approach is:

1. Perimeter first: Print the outer boundary (and any inner holes)
2. Infill second: Fill the interior with the chosen pattern

Key considerations:
- Minimize travel moves (non-extruding movements)
- Avoid collisions with printed geometry
- Maintain consistent extrusion rate
- Handle layer transitions smoothly
"""

import numpy as np
from typing import List, Tuple, Optional
from .infill_generator import InfillPattern, generate_infill


class ToolpathSegment:
    """Represents a single move in the toolpath."""
    __slots__ = ['start', 'end', 'is_extruding', 'move_type', 'z_height']

    def __init__(self, start: np.ndarray, end: np.ndarray,
                 is_extruding: bool = False, move_type: str = "move"):
        self.start = start
        self.end = end
        self.is_extruding = is_extruding
        self.move_type = move_type  # "extrude" or "travel"
        self.z_height = end[2]

    def length(self) -> float:
        return np.linalg.norm(self.end - self.start)

    def __repr__(self):
        return (f"Toolpath({self.move_type}: ({self.start[0]:.2f},{self.start[1]:.2f},{self.start[2]:.2f}) "
                f"-> ({self.end[0]:.2f},{self.end[1]:.2f},{self.end[2]:.2f}))")


class ToolpathPlanner:
    """
    Plans the complete toolpath for all layers.

    The planning strategy:
    1. For each layer, generate perimeter paths first
    2. Then generate infill paths
    3. Connect paths with minimal travel moves
    4. Order segments to minimize total travel distance
    """

    def __init__(self, layer_height: float = 0.2,
                 perimeter_width: float = 0.4,
                 infill_pattern: InfillPattern = InfillPattern.GRID,
                 infill_spacing: float = 4.0,
                 infill_percentage: float = 15.0,
                 top_layers: int = 3,
                 bottom_layers: int = 3):
        self.layer_height = layer_height
        self.perimeter_width = perimeter_width
        self.infill_pattern = infill_pattern
        self.infill_spacing = infill_spacing
        self.infill_percentage = infill_percentage
        self.top_layers = top_layers
        self.bottom_layers = bottom_layers
        self.toolpath: List[ToolpathSegment] = []

    def plan(self, layer_geometries, bounds: Tuple[np.ndarray, np.ndarray]
             ) -> List[ToolpathSegment]:
        """
        Generate the complete toolpath for all layers.

        Args:
            layer_geometries: List of LayerGeometry from layer_generator
            bounds: (min_corner, max_corner) of the entire model

        Returns:
            Ordered list of ToolpathSegments
        """
        self.toolpath = []
        min_pt, max_pt = bounds

        for i, geo in enumerate(layer_geometries):
            z = geo.z_height

            # Add travel move to layer start position
            if self.toolpath:
                last_end = self.toolpath[-1].end
                start_pt = np.array([min_pt[0], min_pt[1], z])
                self.toolpath.append(ToolpathSegment(last_end, start_pt, is_extruding=False, move_type="travel"))

            # Generate perimeter paths
            perimeter_segments = self._plan_perimeters(geo, z)
            self.toolpath.extend(perimeter_segments)

            # Generate infill paths
            if geo.infill_loops:
                infill_segments = self._plan_infill(geo, z, min_pt, max_pt)
                self.toolpath.extend(infill_segments)

        return self.toolpath

    def _plan_perimeters(self, geo, z: float) -> List[ToolpathSegment]:
        """Plan perimeter (outline) paths for a single layer."""
        segments = []

        for perimeter in geo.perimeter_loops:
            if len(perimeter) < 2:
                continue

            for j in range(len(perimeter) - 1):
                start = perimeter[j]
                end = perimeter[j + 1]

                # Add travel move to perimeter start
                if segments:
                    last_end = segments[-1].end
                    segments.append(ToolpathSegment(last_end, start, is_extruding=False, move_type="travel"))

                # Add extrusion segment
                segments.append(ToolpathSegment(start, end, is_extruding=True, move_type="perimeter"))

        return segments

    def _plan_infill(self, geo, z: float, min_pt: np.ndarray,
                     max_pt: np.ndarray) -> List[ToolpathSegment]:
        """Plan infill paths for a single layer."""
        segments = []

        # Generate infill pattern
        infill_lines = generate_infill(
            z_height=z,
            bounds=(min_pt, max_pt),
            pattern=self.infill_pattern,
            spacing=self.infill_spacing,
            infill_percentage=self.infill_percentage
        )

        # Connect infill lines with minimal travel
        for line in infill_lines:
            start, end = line[0], line[1]

            if segments:
                last_end = segments[-1].end
                # Choose closest end of this line
                dist_to_start = np.linalg.norm(last_end - start)
                dist_to_end = np.linalg.norm(last_end - end)

                if dist_to_start < dist_to_end:
                    segments.append(ToolpathSegment(last_end, start, is_extruding=False, move_type="travel"))
                    segments.append(ToolpathSegment(start, end, is_extruding=True, move_type="infill"))
                else:
                    segments.append(ToolpathSegment(last_end, end, is_extruding=False, move_type="travel"))
                    segments.append(ToolpathSegment(end, start, is_extruding=True, move_type="infill"))
            else:
                segments.append(ToolpathSegment(start, end, is_extruding=True, move_type="infill"))

        return segments


def optimize_travel_distance(toolpath: List[ToolpathSegment]) -> List[ToolpathSegment]:
    """
    Optimize toolpath by minimizing travel distances between segments.

    Uses a greedy nearest-neighbor approach to reorder infill segments.
    Perimeter segments are kept in order (they must form closed loops).
    """
    # Separate perimeter and infill segments
    perimeters = [s for s in toolpath if s.move_type == "perimeter"]
    infill = [s for s in toolpath if s.move_type == "infill"]

    if not infill:
        return toolpath

    # Optimize infill order
    optimized = _optimize_infill_order(infill)

    # Rebuild toolpath
    result = []
    infill_idx = 0
    for s in toolpath:
        result.append(s)
        if s.move_type == "perimeter":
            # Insert optimized infill after each perimeter
            pass

    return toolpath


def _optimize_infill_order(infill: List[ToolpathSegment]) -> List[ToolpathSegment]:
    """Reorder infill segments to minimize travel distance."""
    if len(infill) <= 1:
        return infill

    remaining = list(infill)
    optimized = []

    # Start from the first segment
    current = remaining.pop(0)
    optimized.append(current)

    while remaining:
        # Find nearest next segment start
        best_idx = 0
        best_dist = np.linalg.norm(remaining[0].start - current.end)

        for i in range(1, len(remaining)):
            dist = np.linalg.norm(remaining[i].start - current.end)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        next_seg = remaining.pop(best_idx)
        optimized.append(next_seg)
        current = next_seg

    return optimized
