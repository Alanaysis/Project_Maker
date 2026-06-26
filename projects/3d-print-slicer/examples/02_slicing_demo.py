"""
Example: Slicing demo with layer visualization.

Demonstrates slicing a 3D model into layers and visualizing the cross-sections.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stl_parser import load_stl
from src.mesh_slicer import slice_mesh, Layer
from src.layer_generator import generate_layer_geometries


def create_test_cylinder(filepath: str, radius: float = 10.0, height: float = 20.0,
                         segments: int = 32):
    """Create a cylinder STL file for testing."""
    import struct

    triangles = []

    # Side triangles
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments

        x1 = radius * np.cos(angle1)
        y1 = radius * np.sin(angle1)
        x2 = radius * np.cos(angle2)
        y2 = radius * np.sin(angle2)

        # Bottom to top triangles
        v0 = np.array([x1, y1, 0])
        v1 = np.array([x2, y2, 0])
        v2 = np.array([x2, y2, height])
        v3 = np.array([x1, y1, height])

        triangles.append((v0, v1, v2))
        triangles.append((v0, v2, v3))

    # Top cap triangles
    center_top = np.array([0, 0, height])
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments

        p1 = np.array([radius * np.cos(angle1), radius * np.sin(angle1), height])
        p2 = np.array([radius * np.cos(angle2), radius * np.sin(angle2), height])

        triangles.append((center_top, p1, p2))

    # Bottom cap triangles
    center_bottom = np.array([0, 0, 0])
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments

        p1 = np.array([radius * np.cos(angle1), radius * np.sin(angle1), 0])
        p2 = np.array([radius * np.cos(angle2), radius * np.sin(angle2), 0])

        triangles.append((center_bottom, p2, p1))  # Reversed for correct winding

    with open(filepath, 'wb') as f:
        header = b'Binary STL cylinder' + b'\x00' * (80 - len(b'Binary STL cylinder'))
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))

        for v0, v1, v2 in triangles:
            e1 = v1 - v0
            e2 = v2 - v0
            normal = np.cross(e1, e2)
            length = np.linalg.norm(normal)
            if length > 0:
                normal /= length
            f.write(struct.pack('<3f', *normal))
            f.write(struct.pack('<9f', *v0[0], *v0[1], *v0[2],
                                *v1[0], *v1[1], *v1[2],
                                *v2[0], *v2[1], *v2[2]))
            f.write(struct.pack('<H', 0))


def visualize_layer_ascii(layer: Layer, width: int = 60, height: int = 30):
    """
    Visualize a layer's segments as ASCII art.

    This creates a top-down view (X-Y plane) of the layer's cross-section.
    """
    if not layer.segments:
        print("  [empty layer]")
        return

    # Collect all points
    all_pts = []
    for seg in layer.segments:
        all_pts.extend([seg.start[:2], seg.end[:2]])

    all_pts = np.array(all_pts)
    x_min, y_min = np.min(all_pts, axis=0)
    x_max, y_max = np.max(all_pts, axis=0)

    x_range = max(x_max - x_min, 0.001)
    y_range = max(y_max - y_min, 0.001)

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Draw segments on grid
    for seg in layer.segments:
        sx = int((seg.start[0] - x_min) / x_range * (width - 1))
        sy = int((1 - (seg.start[1] - y_min) / y_range) * (height - 1))
        ex = int((seg.end[0] - x_min) / x_range * (width - 1))
        ey = int((1 - (seg.end[1] - y_min) / y_range) * (height - 1))

        # Bresenham-like line drawing
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

    # Print grid (reversed rows for top-down view)
    print(f"  Layer Z={layer.z_height:.2f} ({len(layer.segments)} segments)")
    print("  " + "-" * width)
    for row in grid:
        print("  |" + "".join(row) + "|")
    print("  " + "-" * width)


def visualize_layers(layers: list, sample_count: int = 10):
    """Visualize a selection of layers."""
    # Select layers to visualize
    if len(layers) <= sample_count:
        selected = layers
    else:
        step = len(layers) // sample_count
        selected = [layers[i] for i in range(0, len(layers), step)]

    for layer in selected:
        visualize_layer_ascii(layer)
        print()


def print_layer_statistics(layers: list):
    """Print statistics about the sliced layers."""
    if not layers:
        print("  No layers to analyze")
        return

    print("\n" + "=" * 60)
    print("  Layer Statistics")
    print("=" * 60)
    print(f"  Total layers: {len(layers)}")
    print(f"  Z range: {layers[0].z_height:.2f} - {layers[-1].z_height:.2f}")
    print(f"  Layer height: {layers[1].z_height - layers[0].z_height:.3f}")

    # Find max and average segment counts
    max_segments = max(len(l.segments) for l in layers)
    avg_segments = np.mean([len(l.segments) for l in layers])
    max_length = max(l.total_segment_length for l in layers)
    avg_length = np.mean([l.total_segment_length for l in layers])

    print(f"  Max segments in layer: {max_segments}")
    print(f"  Avg segments per layer: {avg_segments:.1f}")
    print(f"  Max perimeter length: {max_length:.2f}")
    print(f"  Avg perimeter length: {avg_length:.2f}")
    print("=" * 60)


def main():
    """Demonstrate mesh slicing."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(project_root, 'tests', 'test_files')
    os.makedirs(test_dir, exist_ok=True)

    cylinder_path = os.path.join(test_dir, 'test_cylinder.stl')
    create_test_cylinder(cylinder_path, radius=10.0, height=20.0, segments=32)

    # Load the model
    print("Loading cylinder model...")
    model = load_stl(cylinder_path)
    print(f"  Loaded {len(model)} triangles")

    if model.bounds:
        min_pt, max_pt = model.bounds
        print(f"  Bounds: Z={min_pt[2]:.1f} to {max_pt[2]:.1f}")

    # Slice the model
    z_min = model.bounds[0][2] if model.bounds else 0.0
    z_max = model.bounds[1][2] if model.bounds else 20.0
    layer_height = 1.0

    print(f"\nSlicing model (layer height: {layer_height:.1f} mm)...")
    layers = slice_mesh(model, z_min, z_max, layer_height)
    print(f"  Generated {len(layers)} layers")

    # Print statistics
    print_layer_statistics(layers)

    # Visualize selected layers
    print("\n--- Layer Cross-Section Visualization ---")
    print("(Top-down view: X-Y plane)")
    print()
    visualize_layers(layers, sample_count=8)

    # Generate layer geometries
    print("\n--- Layer Geometries ---")
    geometries = generate_layer_geometries(layers, layer_height)
    for geo in geometries[::3]:  # Show every 3rd layer
        print(f"  {geo}")

    print("\n✓ Slicing demo complete!")


if __name__ == '__main__':
    main()
