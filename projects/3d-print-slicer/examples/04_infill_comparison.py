"""
Example: Infill pattern comparison.

Demonstrates different infill patterns and their visual characteristics.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infill_generator import (
    generate_infill, InfillPattern, InfillSegment
)


def visualize_infill_pattern(segments, pattern_name, width=50, height=25):
    """Visualize infill segments as ASCII art."""
    if not segments:
        print(f"  {pattern_name}: [empty]")
        return

    # Collect all points
    all_pts = []
    for seg in segments:
        if isinstance(seg, tuple) and len(seg) == 2:
            all_pts.extend([seg[0][:2], seg[1][:2]])
        else:
            all_pts.extend([seg.start[:2], seg.end[:2]])

    all_pts = np.array(all_pts)
    x_min, y_min = np.min(all_pts, axis=0)
    x_max, y_max = np.max(all_pts, axis=0)

    x_range = max(x_max - x_min, 0.001)
    y_range = max(y_max - y_min, 0.001)

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Draw segments
    for seg in segments:
        if isinstance(seg, tuple) and len(seg) == 2:
            s, e = seg[0][:2], seg[1][:2]
        else:
            s, e = seg.start[:2], seg.end[:2]

        sx = int((s[0] - x_min) / x_range * (width - 1))
        sy = int((1 - (s[1] - y_min) / y_range) * (height - 1))
        ex = int((e[0] - x_min) / x_range * (width - 1))
        ey = int((1 - (e[1] - y_min) / y_range) * (height - 1))

        dx = abs(ex - sx)
        dy = abs(ey - sy)
        sx_, sy_ = sx, sy
        step_x = 1 if ex > sx else -1
        step_y = 1 if ey > sy else -1
        err = dx - dy

        while True:
            if 0 <= sy_ < height and 0 <= sx_ < width:
                grid[sy_][sx_] = '#'
            if sx_ == ex and sy_ == ey:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                sx_ += step_x
            if e2 < dx:
                err += dx
                sy_ += step_y

    # Print
    print(f"\n  {pattern_name}:")
    print("  " + "-" * width)
    for row in grid:
        print("  |" + "".join(row) + "|")
    print("  " + "-" * width)


def compare_patterns():
    """Compare all infill patterns."""
    bounds = (np.array([0, 0]), np.array([30, 20]))
    z = 1.0
    spacing = 3.5

    patterns = [
        (InfillPattern.GRID, "Grid (cross-hatch)"),
        (InfillPattern.HONEYCOMB, "Honeycomb (hexagonal)"),
        (InfillPattern.GYROID, "Gyroid (spherical cubic surface)"),
        (InfillPattern.CONCENTRIC, "Concentric (nested perimeters)"),
    ]

    print("=" * 60)
    print("  Infill Pattern Comparison")
    print(f"  Bounds: {bounds[0]} to {bounds[1]}")
    print(f"  Z height: {z:.2f} mm")
    print(f"  Spacing: {spacing:.2f} mm")
    print("=" * 60)

    for pattern, name in patterns:
        segments = generate_infill(z, bounds, pattern, spacing)
        total_length = sum(s.length() if hasattr(s, 'length') else
                          np.linalg.norm(s[1][:2] - s[0][:2])
                          for s in segments)
        print(f"\n  Pattern: {name}")
        print(f"  Segments: {len(segments)}")
        print(f"  Total length: {total_length:.1f} mm")
        visualize_infill_pattern(segments, name)

    print("\n" + "=" * 60)
    print("  Pattern Characteristics:")
    print("=" * 60)
    characteristics = [
        ("Grid", "Simple cross-hatch. Good X/Y strength. Easy to compute."),
        ("Honeycomb", "Hexagonal cells. Best strength-to-weight. Uniform stress."),
        ("Gyroid", "Continuous surface. Isotropic strength. Smooth paths."),
        ("Concentric", "Nested loops. Fastest print. Weakest Z-bonding."),
    ]
    for name, desc in characteristics:
        print(f"  {name:12s}: {desc}")
    print("=" * 60)


def compare_infill_percentages():
    """Compare different infill percentages for the same pattern."""
    bounds = (np.array([0, 0]), np.array([25, 15]))
    z = 1.0

    percentages = [5, 10, 15, 25, 50]
    pattern = InfillPattern.GRID

    print("\n" + "=" * 60)
    print(f"  Infill Percentage Comparison ({pattern.value.upper()})")
    print("=" * 60)

    for pct in percentages:
        segments = generate_infill(z, bounds, pattern, spacing=5.0, infill_percentage=pct)
        total_length = sum(
            np.linalg.norm(s[1][:2] - s[0][:2]) for s in segments
        )
        print(f"  {pct:3d}%: {len(segments):3d} segments, {total_length:7.1f} mm")

    print("=" * 60)


def main():
    """Run infill pattern comparison demos."""
    compare_patterns()
    compare_infill_percentages()

    print("\n✓ Infill pattern comparison complete!")


if __name__ == '__main__':
    main()
