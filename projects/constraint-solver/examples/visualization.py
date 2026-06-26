"""Visualization tools for constraint solver output."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from typing import List, Optional
from src.entities import Point
from src.constraints import Constraint
from src.constraint_graph import ConstraintGraph


def create_text_visualization(
    points: List[Point],
    constraints: Optional[List[Constraint]] = None,
    title: str = "Constraint Solver Output",
    width: int = 60,
    height: int = 30,
) -> str:
    """Create a text-based ASCII visualization of the constraint system.

    Args:
        points: List of points to visualize
        constraints: Optional list of constraints to show
        title: Title for the visualization
        width: Width of the ASCII canvas
        height: Height of the ASCII canvas

    Returns:
        ASCII art string representation
    """
    if not points:
        return f"{title}\n(No points to display)"

    # Find bounding box
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Add padding
    pad_x = (max_x - min_x) * 0.1 + 1
    pad_y = (max_y - min_y) * 0.1 + 1
    min_x -= pad_x
    max_x += pad_x
    min_y -= pad_y
    max_y += pad_y

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    def to_grid(x: float, y: float) -> tuple:
        """Convert world coordinates to grid coordinates."""
        gx = int((x - min_x) / (max_x - min_x) * (width - 1))
        gy = height - 1 - int((y - min_y) / (max_y - min_y) * (height - 1))
        gx = max(0, min(width - 1, gx))
        gy = max(0, min(height - 1, gy))
        return gx, gy

    # Draw axes
    origin_x, origin_y = to_grid(0, 0)
    for i in range(width):
        if origin_y >= 0 and origin_y < height:
            grid[origin_y][i] = '-'
    for i in range(height):
        if origin_x >= 0 and origin_x < width:
            grid[i][origin_x] = '|'

    # Draw points
    for p in points:
        gx, gy = to_grid(p.x, p.y)
        grid[gy][gx] = 'O'

    # Draw constraints as lines
    if constraints:
        for c in constraints:
            if len(c.entities) >= 2:
                p1, p2 = c.entities[0], c.entities[1]
                gx1, gy1 = to_grid(p1.x, p1.y)
                gx2, gy2 = to_grid(p2.x, p2.y)
                # Bresenham-like line drawing
                dx = abs(gx2 - gx1)
                dy = abs(gy2 - gy1)
                sx = 1 if gx1 < gx2 else -1
                sy = 1 if gy1 < gy2 else -1
                err = dx - dy
                while True:
                    if 0 <= gy1 < height and 0 <= gx1 < width:
                        if grid[gy1][gx1] == ' ':
                            grid[gy1][gx1] = '.'
                    if gx1 == gx2 and gy1 == gy2:
                        break
                    e2 = 2 * err
                    if e2 > -dy:
                        err -= dy
                        gx1 += sx
                    if e2 < dx:
                        err += dx
                        gy1 += sy

    # Build string
    lines = [title]
    lines.append("=" * width)
    for row in grid:
        lines.append(''.join(row))
    lines.append("")

    # Legend
    lines.append("Legend:")
    lines.append("  O = Point")
    lines.append("  . = Constraint edge")
    lines.append("  - = X-axis")
    lines.append("  | = Y-axis")
    lines.append("")

    # Point coordinates
    lines.append("Point coordinates:")
    for p in points:
        fixed_str = " [fixed]" if p.fixed else ""
        lines.append(f"  {p.name}: ({p.x:.3f}, {p.y:.3f}){fixed_str}")

    if constraints:
        lines.append(f"\nConstraints ({len(constraints)}):")
        for c in constraints:
            entities = [e.name for e in c.entities[:3]]
            lines.append(f"  {c.constraint_type.name}({', '.join(entities)})"
                         f" = {c.value if c.value != 0 else ''}")

    return '\n'.join(lines)


def print_constraint_summary(graph: ConstraintGraph) -> str:
    """Print a summary of the constraint graph.

    Args:
        graph: Constraint graph to summarize

    Returns:
        Summary string
    """
    lines = []
    lines.append("Constraint Graph Summary")
    lines.append("=" * 40)
    lines.append(f"  Entities: {len(graph.entity_nodes)}")
    lines.append(f"  Constraints: {len(graph.constraint_nodes)}")

    fixed = sum(1 for p in graph.entity_nodes.values() if p.fixed)
    free = len(graph.entity_nodes) - fixed
    lines.append(f"  Fixed points: {fixed}")
    lines.append(f"  Free points: {free}")
    lines.append(f"  Degrees of freedom: {free * 2 - len(graph.constraint_nodes)}")

    # Constraint type breakdown
    type_counts = {}
    for c in graph.constraint_nodes.values():
        name = c.constraint_type.name
        type_counts[name] = type_counts.get(name, 0) + 1

    if type_counts:
        lines.append(f"\n  Constraint types:")
        for name, count in sorted(type_counts.items()):
            lines.append(f"    {name}: {count}")

    return '\n'.join(lines)


def print_iteration_history(history: list, title: str = "Solver History") -> str:
    """Format solver iteration history as a readable string.

    Args:
        history: List of residual norms per iteration
        title: Title for the output

    Returns:
        Formatted history string
    """
    lines = [title, "=" * 50]
    for i, residual in enumerate(history):
        bar_len = int(min(residual / max(history[0], 1e-16) * 40, 40))
        bar = '#' * bar_len + '.' * (40 - bar_len)
        lines.append(f"  Iter {i + 1:3d}: {residual:12.6e}  [{bar}]")
    lines.append("")
    return '\n'.join(lines)


if __name__ == '__main__':
    # Demo
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(3.0, 0.0, name="B")
    C = Point(3.0, 4.0, name="C")
    D = Point(0.0, 4.0, name="D")

    from src.constraints import DistanceConstraint
    from src.constraint_graph import ConstraintGraph

    graph = ConstraintGraph()
    for p in [A, B, C, D]:
        graph.add_entity(p)

    for c in [
        DistanceConstraint(A, B, 3.0),
        DistanceConstraint(B, C, 4.0),
        DistanceConstraint(C, D, 3.0),
        DistanceConstraint(D, A, 4.0),
    ]:
        graph.add_constraint(c)

    print(create_text_visualization([A, B, C, D], graph.constraint_nodes.values()))
    print(print_constraint_summary(graph))
