"""
Infill pattern generation module.

Infill patterns fill the interior of each layer between perimeters.
Different patterns offer different trade-offs between strength, material usage, and print time.

Common infill patterns:
- Grid: Cross-hatch pattern, good strength in X/Y directions
- Honeycomb: Hexagonal pattern, excellent strength-to-weight ratio
- Gyroid: Spherical cubic surface, isotropic strength, smooth transitions
- Concentric: Nested perimeter copies, fast printing, weak Z-direction bonding
"""

import numpy as np
from typing import List, Tuple, Optional
from enum import Enum


class InfillPattern(Enum):
    """Supported infill patterns."""
    GRID = "grid"
    HONEYCOMB = "honeycomb"
    GYROID = "gyroid"
    CONCENTRIC = "concentric"


class InfillSegment:
    """A single line segment in an infill pattern."""
    __slots__ = ['start', 'end']

    def __init__(self, start: np.ndarray, end: np.ndarray):
        self.start = start
        self.end = end

    def length(self) -> float:
        return np.linalg.norm(self.end - self.start)


def generate_infill(z_height: float, bounds: Tuple[np.ndarray, np.ndarray],
                    pattern: InfillPattern, spacing: float,
                    infill_percentage: float = 100.0) -> List[List[np.ndarray]]:
    """
    Generate infill segments for a layer.

    Args:
        z_height: Z level of this layer
        bounds: (min_corner, max_corner) of the layer bounding box
        pattern: Infill pattern type
        spacing: Distance between adjacent infill lines (mm)
        infill_percentage: Percentage of layer to fill (0-100)

    Returns:
        List of infill line segments, each segment is [start_point, end_point]
    """
    min_pt, max_pt = bounds
    x_min, y_min = min_pt[0], min_pt[1]
    x_max, y_max = max_pt[0], max_pt[1]

    # Adjust spacing based on infill percentage
    # Higher infill % = smaller spacing
    effective_spacing = spacing * (100.0 / max(infill_percentage, 1.0))

    if pattern == InfillPattern.GRID:
        return _generate_grid(z_height, (x_min, y_min), (x_max, y_max), effective_spacing)
    elif pattern == InfillPattern.HONEYCOMB:
        return _generate_honeycomb(z_height, (x_min, y_min), (x_max, y_max), effective_spacing)
    elif pattern == InfillPattern.GYROID:
        return _generate_gyroid(z_height, (x_min, y_min), (x_max, y_max), effective_spacing)
    elif pattern == InfillPattern.CONCENTRIC:
        return _generate_concentric(z_height, (x_min, y_min), (x_max, y_max), effective_spacing)
    else:
        raise ValueError(f"Unknown infill pattern: {pattern}")


def _generate_grid(z_height: float, min_pt: Tuple[float, float],
                   max_pt: Tuple[float, float], spacing: float) -> List[List[np.ndarray]]:
    """
    Generate grid (cross-hatch) infill pattern.

    Creates two sets of parallel lines at 90 degrees to each other.
    This provides good strength in both X and Y directions.
    """
    x_min, y_min = min_pt
    x_max, y_max = max_pt
    segments = []

    # Lines parallel to X axis
    y = y_min
    while y <= y_max:
        start = np.array([x_min, y, z_height])
        end = np.array([x_max, y, z_height])
        segments.append([start, end])
        y += spacing

    # Lines parallel to Y axis (offset by half spacing to create grid)
    x = x_min + spacing / 2
    while x <= x_max:
        start = np.array([x, y_min, z_height])
        end = np.array([x, y_max, z_height])
        segments.append([start, end])
        x += spacing

    return segments


def _generate_honeycomb(z_height: float, min_pt: Tuple[float, float],
                        max_pt: Tuple[float, float], spacing: float) -> List[List[np.ndarray]]:
    """
    Generate honeycomb (hexagonal) infill pattern.

    Honeycomb is one of the most efficient infill patterns, providing:
    - Excellent strength-to-weight ratio
    - Uniform stress distribution
    - Less material than grid for same strength
    """
    x_min, y_min = min_pt
    x_max, y_max = max_pt
    segments = []

    # Hexagonal pattern parameters
    hex_width = spacing * 2 / np.sqrt(3)  # Width of hex cell
    hex_height = spacing * 2

    # Generate honeycomb cells
    col = 0
    x = x_min
    while x <= x_max + hex_width:
        row = 0
        y = y_min
        offset = (col % 2) * hex_width / 2  # Alternate row offset

        while y <= y_max + hex_height:
            cx = x + offset
            cy = y

            # Draw hexagon edges
            angles = np.array([0, 60, 120, 180, 240, 300]) * np.pi / 180
            for j in range(6):
                angle1 = angles[j]
                angle2 = angles[(j + 1) % 6]

                p1 = np.array([
                    cx + spacing * np.cos(angle1),
                    cy + spacing * np.sin(angle1),
                    z_height
                ])
                p2 = np.array([
                    cx + spacing * np.cos(angle2),
                    cy + spacing * np.sin(angle2),
                    z_height
                ])

                # Only add if within bounds
                if (min_pt[0] <= p1[0] <= max_pt[0] and
                    min_pt[1] <= p1[1] <= max_pt[1] and
                    min_pt[0] <= p2[0] <= max_pt[0] and
                    min_pt[1] <= p2[1] <= max_pt[1]):
                    segments.append([p1, p2])

            row += 1
            y += hex_height
        col += 1
        x += hex_width

    return segments


def _generate_gyroid(z_height: float, min_pt: Tuple[float, float],
                     max_pt: Tuple[float, float], spacing: float) -> List[List[np.ndarray]]:
    """
    Generate gyroid infill pattern.

    The gyroid is a triply periodic minimal surface defined by:
        sin(x) * cos(y) + sin(y) * cos(z) + sin(z) * cos(x) = 0

    For 2D slicing at constant Z, we get:
        sin(x) * cos(y) + sin(y) * cos(z_fixed) + sin(z_fixed) * cos(x) = 0

    Properties:
    - Isotropic strength (same in all directions)
    - Smooth continuous paths (no sharp turns)
    - Excellent for flexible parts
    - More material efficient than grid
    """
    x_min, y_min = min_pt
    x_max, y_max = max_pt
    segments = []

    # Sample the gyroid surface at this Z level
    resolution = max(int((x_max - x_min) / spacing), 1)
    step = (x_max - x_min) / resolution

    cos_z = np.cos(z_height)
    sin_z = np.sin(z_height)

    for i in range(resolution):
        x = x_min + i * step

        # Find y values where gyroid equation crosses zero
        for j in range(resolution):
            y = y_min + j * step

            # Evaluate gyroid function
            gyroid_val = np.sin(x) * np.cos(y) + sin_z * np.cos(x)

            # Check next point
            y_next = y + step
            gyroid_next = np.sin(x) * np.cos(y_next) + sin_z * np.cos(x)

            # If the function crosses zero, add a segment
            if gyroid_val * gyroid_next < 0:
                # Linear interpolation to find crossing point
                t = gyroid_val / (gyroid_val - gyroid_next)
                y_cross = y + t * step

                p1 = np.array([x, y_cross, z_height])
                p2 = np.array([x + step, y_cross + step * (gyroid_next / (gyroid_val - gyroid_next)), z_height])

                # Clamp to bounds
                p1[0] = max(x_min, min(x_max, p1[0]))
                p1[1] = max(y_min, min(y_max, p1[1]))
                p2[0] = max(x_min, min(x_max, p2[0]))
                p2[1] = max(y_min, min(y_max, p2[1]))

                segments.append([p1, p2])

    return segments


def _generate_concentric(z_height: float, min_pt: Tuple[float, float],
                         max_pt: Tuple[float, float], spacing: float) -> List[List[np.ndarray]]:
    """
    Generate concentric (nested perimeter) infill pattern.

    Creates multiple nested copies of the outer perimeter, shrunk inward
    by the spacing distance each iteration.

    Advantages:
    - Fastest to print (continuous paths)
    - Good surface finish on infill faces
    - Weak Z-direction bonding (layers don't interlock)

    Disadvantages:
    - Poor mechanical strength
    - Can cause warping due to internal stress
    """
    x_min, y_min = min_pt
    x_max, y_max = max_pt
    segments = []

    # Create a simple rectangular perimeter
    rect = [
        np.array([x_min, y_min, z_height]),
        np.array([x_max, y_min, z_height]),
        np.array([x_max, y_max, z_height]),
        np.array([x_min, y_max, z_height]),
        np.array([x_min, y_min, z_height]),  # Close the loop
    ]

    # Shrink the rectangle inward
    shrink = 0.0
    max_shrink = min(x_max - x_min, y_max - y_min) / 4.0

    while shrink < max_shrink:
        # Calculate shrunken rectangle
        dx = shrink / 2.0
        dy = shrink / 2.0

        p1 = np.array([x_min + dx, y_min + dy, z_height])
        p2 = np.array([x_max - dx, y_min + dy, z_height])
        p3 = np.array([x_max - dx, y_max - dy, z_height])
        p4 = np.array([x_min + dx, y_max - dy, z_height])

        # Add segments
        for start, end in [(p1, p2), (p2, p3), (p3, p4), (p4, p1)]:
            if end[0] > start[0] or end[1] > start[1]:
                segments.append([start, end])

        shrink += spacing

    return segments
