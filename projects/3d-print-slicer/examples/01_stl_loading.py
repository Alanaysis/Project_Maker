"""
Example: STL file loading and visualization.

Demonstrates loading STL files (binary and ASCII) and displaying
basic mesh information.
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stl_parser import STLModel, STLTriangle, load_stl, parse_binary_stl, parse_ascii_stl


def create_test_cube(filepath: str, side_length: float = 10.0):
    """
    Create a simple cube STL file for testing.

    A cube has 6 faces, each with 2 triangles = 12 triangles total.
    """
    s = side_length / 2.0

    # Define the 12 triangles (6 faces x 2 triangles)
    triangles_data = [
        # Front face (z = +s)
        ([s, -s, s], [-s, -s, s], [-s, s, s]),   # Triangle 1
        ([s, -s, s], [-s, s, s], [s, s, s]),      # Triangle 2
        # Back face (z = -s)
        ([-s, -s, -s], [s, -s, -s], [s, s, -s]),  # Triangle 3
        ([-s, -s, -s], [s, s, -s], [-s, s, -s]),  # Triangle 4
        # Left face (x = -s)
        ([-s, s, s], [-s, -s, s], [-s, -s, -s]),  # Triangle 5
        ([-s, s, s], [-s, -s, -s], [-s, s, -s]),  # Triangle 6
        # Right face (x = +s)
        ([s, -s, s], [s, s, s], [s, s, -s]),      # Triangle 7
        ([s, -s, s], [s, s, -s], [s, -s, -s]),    # Triangle 8
        # Top face (y = +s)
        ([-s, s, s], [s, s, s], [s, s, -s]),      # Triangle 9
        ([-s, s, s], [s, s, -s], [-s, s, -s]),    # Triangle 10
        # Bottom face (y = -s)
        ([-s, -s, -s], [-s, -s, s], [s, -s, s]),  # Triangle 11
        ([-s, -s, -s], [s, -s, s], [s, -s, -s]),  # Triangle 12
    ]

    # Calculate normals for each triangle
    normals = []
    for v0, v1, v2 in triangles_data:
        e1 = np.array(v1) - np.array(v0)
        e2 = np.array(v2) - np.array(v0)
        normal = np.cross(e1, e2)
        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length
        normals.append(normal)

    # Write binary STL
    with open(filepath, 'wb') as f:
        # Header (80 bytes)
        header = b'Binary STL created by 3d-print-slicer' + b'\x00' * (
            80 - len(b'Binary STL created by 3d-print-slicer'))
        f.write(header)

        # Triangle count
        f.write(struct.pack('<I', len(triangles_data)))

        # Write each triangle
        for (v0, v1, v2), normal in zip(triangles_data, normals):
            f.write(struct.pack('<3f', *normal))
            f.write(struct.pack('<9f', *v0[0], *v0[1], *v0[2],
                                *v1[0], *v1[1], *v1[2],
                                *v2[0], *v2[1], *v2[2]))
            f.write(struct.pack('<H', 0))  # Attribute byte count


def create_test_torus(filepath: str, major_radius: float = 8.0,
                      minor_radius: float = 3.0,
                      num_major: int = 24, num_minor: int = 16):
    """Create a torus (donut) STL file for testing."""
    import struct

    triangles = []

    for i in range(num_major):
        for j in range(num_minor):
            u = 2 * np.pi * i / num_major
            v = 2 * np.pi * j / num_minor

            # Helper function to compute torus surface point
            def torus_point(u, v):
                x = (major_radius + minor_radius * np.cos(v)) * np.cos(u)
                y = (major_radius + minor_radius * np.cos(v)) * np.sin(u)
                z = minor_radius * np.sin(v)
                return np.array([x, y, z])

            p00 = torus_point(u, v)
            p10 = torus_point(u + 2*np.pi/num_major, v)
            p01 = torus_point(u, v + 2*np.pi/num_minor)
            p11 = torus_point(u + 2*np.pi/num_major, v + 2*np.pi/num_minor)

            triangles.append((p00, p10, p01))
            triangles.append((p10, p11, p01))

    with open(filepath, 'wb') as f:
        header = b'ASCII STL created by 3d-print-slicer' + b'\x00' * (
            80 - len(b'ASCII STL created by 3d-print-slicer'))
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


def print_mesh_info(model: STLModel):
    """Print detailed information about a loaded mesh."""
    print("=" * 60)
    print(f"  Model: {model.name}")
    print("=" * 60)
    print(f"  Triangles: {len(model)}")
    print(f"  Vertices:  {model.num_vertices()}")
    print(f"  Total Area: {model.total_area():.2f} mm²")

    if model.bounds:
        min_pt, max_pt = model.bounds
        print(f"\n  Bounding Box:")
        print(f"    Min: ({min_pt[0]:.2f}, {min_pt[1]:.2f}, {min_pt[2]:.2f})")
        print(f"    Max: ({max_pt[0]:.2f}, {max_pt[1]:.2f}, {max_pt[2]:.2f})")
        print(f"    Size: ({max_pt[0]-min_pt[0]:.2f}, "
              f"{max_pt[1]-min_pt[1]:.2f}, {max_pt[2]-min_pt[2]:.2f})")
        print(f"    Center: ({(min_pt[0]+max_pt[0])/2:.2f}, "
              f"{(min_pt[1]+max_pt[1])/2:.2f}, {(min_pt[2]+max_pt[2])/2:.2f})")
    print("=" * 60)


def main():
    """Demonstrate STL file loading."""
    import struct

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(project_root, 'tests', 'test_files')
    os.makedirs(test_dir, exist_ok=True)

    # Create test STL files
    cube_path = os.path.join(test_dir, 'test_cube.stl')
    torus_path = os.path.join(test_dir, 'test_torus.stl')

    print("Creating test STL files...")
    create_test_cube(cube_path, side_length=10.0)
    create_test_torus(torus_path, major_radius=8.0, minor_radius=3.0)

    # Load and display info
    print("\n--- Loading binary STL (cube) ---")
    cube_model = load_stl(cube_path)
    print_mesh_info(cube_model)

    print("\n--- Loading binary STL (torus) ---")
    torus_model = load_stl(torus_path)
    print_mesh_info(torus_model)

    # Show sample triangle data
    print("\n--- Sample triangle data (first triangle) ---")
    if cube_model.triangles:
        tri = cube_model.triangles[0]
        print(f"  Normal: ({tri.normal[0]:.4f}, {tri.normal[1]:.4f}, {tri.normal[2]:.4f})")
        print(f"  Vertex A: ({tri.vertex_a[0]:.4f}, {tri.vertex_a[1]:.4f}, {tri.vertex_a[2]:.4f})")
        print(f"  Vertex B: ({tri.vertex_b[0]:.4f}, {tri.vertex_b[1]:.4f}, {tri.vertex_b[2]:.4f})")
        print(f"  Vertex C: ({tri.vertex_c[0]:.4f}, {tri.vertex_c[1]:.4f}, {tri.vertex_c[2]:.4f})")
        print(f"  Area: {tri.area():.4f}")
        print(f"  Centroid: ({tri.centroid()[0]:.4f}, {tri.centroid()[1]:.4f}, {tri.centroid()[2]:.4f})")

    print("\n✓ STL loading demo complete!")


if __name__ == '__main__':
    main()
