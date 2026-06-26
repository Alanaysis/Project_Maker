"""
Example: G-code generation demo.

Demonstrates generating complete G-code from a sliced 3D model.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stl_parser import load_stl
from src.mesh_slicer import slice_mesh
from src.layer_generator import generate_layer_geometries
from src.infill_generator import InfillPattern
from src.toolpath_planner import ToolpathPlanner
from src.gcode_generator import GCodeGenerator, estimate_print_time, estimate_material_usage


def create_test_box(filepath: str, width: float = 20.0, height: float = 15.0,
                    depth: float = 10.0):
    """Create a box (hollow) STL file for testing."""
    import struct

    triangles = []
    w, h, d = width / 2, height / 2, depth / 2

    # Box faces with holes (hollow box)
    wall_thickness = 1.5
    iw = w - wall_thickness
    ih = h - wall_thickness
    id_ = d - wall_thickness

    # Front face outer
    triangles.append((np.array([w, -h, d]), np.array([-w, -h, d]), np.array([-w, h, d])))
    triangles.append((np.array([w, -h, d]), np.array([-w, h, d]), np.array([w, h, d])))
    # Back face outer
    triangles.append((np.array([-w, -h, -d]), np.array([w, -h, -d]), np.array([w, h, -d])))
    triangles.append((np.array([-w, -h, -d]), np.array([w, h, -d]), np.array([-w, h, -d])))
    # Left face outer
    triangles.append((np.array([-w, h, d]), np.array([-w, -h, d]), np.array([-w, -h, -d])))
    triangles.append((np.array([-w, h, d]), np.array([-w, -h, -d]), np.array([-w, h, -d])))
    # Right face outer
    triangles.append((np.array([w, -h, d]), np.array([w, h, d]), np.array([w, h, -d])))
    triangles.append((np.array([w, -h, d]), np.array([w, h, -d]), np.array([w, -h, -d])))
    # Top face outer
    triangles.append((np.array([-w, h, d]), np.array([w, h, d]), np.array([w, h, -d])))
    triangles.append((np.array([-w, h, d]), np.array([w, h, -d]), np.array([-w, h, -d])))
    # Bottom face outer
    triangles.append((np.array([-w, -h, -d]), np.array([-w, -h, d]), np.array([w, -h, d])))
    triangles.append((np.array([-w, -h, -d]), np.array([w, -h, d]), np.array([w, -h, -d])))

    with open(filepath, 'wb') as f:
        header = b'Binary STL box' + b'\x00' * (80 - len(b'Binary STL box'))
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


def main():
    """Demonstrate G-code generation."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(project_root, 'tests', 'test_files')
    os.makedirs(test_dir, exist_ok=True)

    box_path = os.path.join(test_dir, 'test_box.stl')
    create_test_box(box_path, width=30.0, height=20.0, depth=15.0)

    # Load the model
    print("Loading box model...")
    model = load_stl(box_path)
    print(f"  Triangles: {len(model)}")

    if model.bounds:
        min_pt, max_pt = model.bounds
        print(f"  Size: {max_pt[0]-min_pt[0]:.1f} x {max_pt[1]-min_pt[1]:.1f} x {max_pt[2]-min_pt[2]:.1f} mm")

    # Slice the model
    z_min = model.bounds[0][2]
    z_max = model.bounds[1][2]
    layer_height = 0.2

    print(f"\nSlicing (layer height: {layer_height:.2f} mm)...")
    layers = slice_mesh(model, z_min, z_max, layer_height)
    print(f"  Layers: {len(layers)}")

    # Generate layer geometries
    geometries = generate_layer_geometries(layers, layer_height)

    # Plan toolpath
    print("\nPlanning toolpath...")
    min_pt, max_pt = model.bounds
    planner = ToolpathPlanner(
        layer_height=layer_height,
        perimeter_width=0.4,
        infill_pattern=InfillPattern.GRID,
        infill_spacing=4.0,
        infill_percentage=15.0,
        top_layers=3,
        bottom_layers=3
    )
    toolpath = planner.plan(geometries, (min_pt, max_pt))
    print(f"  Toolpath segments: {len(toolpath)}")

    # Generate G-code
    print("\nGenerating G-code...")
    generator = GCodeGenerator(
        filament_diameter=1.75,
        nozzle_diameter=0.4,
        default_speed=60.0,
        travel_speed=150.0,
        initial_layer_speed=20.0
    )
    generator.layer_height = layer_height
    generator.layer_count = len(layers)
    generator.extruder_temp = 200.0
    generator.bed_temp = 60.0

    settings = {
        'infill_percentage': 15.0,
        'infill_pattern': 'grid',
        'perimeter_count': 2,
    }

    gcode = generator.generate(toolpath, {'min': min_pt, 'max': max_pt}, settings)

    # Save G-code
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output.gcode')
    with open(output_path, 'w') as f:
        f.write(gcode)
    print(f"  G-code saved to: {output_path}")

    # Print G-code header
    print("\n--- G-code Preview (first 30 lines) ---")
    lines = gcode.split('\n')
    for i, line in enumerate(lines[:30]):
        print(f"  {line}")
    if len(lines) > 30:
        print(f"  ... ({len(lines) - 30} more lines)")

    # Print estimates
    print("\n--- Print Estimates ---")
    time_est = estimate_print_time(toolpath)
    print(f"  Estimated print time: {time_est['total_time']/60:.1f} minutes")
    print(f"    Printing: {time_est['print_time']/60:.1f} min")
    print(f"    Travel:   {time_est['travel_time']/60:.1f} min")

    material_est = estimate_material_usage(toolpath)
    print(f"  Material usage:")
    print(f"    Extrusion length: {material_est['extrusion_length_mm']:.1f} mm")
    print(f"    Volume: {material_est['volume_mm3']:.1f} mm³")
    print(f"    Weight: {material_est['mass_g']:.2f} g")

    # Write full G-code to file
    full_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output_full.gcode')
    with open(full_output, 'w') as f:
        f.write(gcode)
    print(f"\n  Full G-code saved to: {full_output}")

    print("\n✓ G-code generation demo complete!")


if __name__ == '__main__':
    main()
