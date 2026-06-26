"""
Tests for G-code generator and toolpath planner modules.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.toolpath_planner import ToolpathPlanner, ToolpathSegment
from src.gcode_generator import GCodeGenerator, estimate_print_time, estimate_material_usage
from src.infill_generator import InfillPattern


class TestToolpathSegment:
    """Test ToolpathSegment class."""

    def test_segment_creation(self):
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([1.0, 1.0, 0.2])
        seg = ToolpathSegment(start, end, is_extruding=True, move_type="perimeter")

        assert np.allclose(seg.start, start)
        assert np.allclose(seg.end, end)
        assert seg.is_extruding
        assert seg.move_type == "perimeter"
        assert seg.z_height == 0.2

    def test_segment_length(self):
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([3.0, 4.0, 0.0])
        seg = ToolpathSegment(start, end)
        assert abs(seg.length() - 5.0) < 1e-10


class TestGCodeGenerator:
    """Test G-code generation."""

    def test_header_generation(self):
        generator = GCodeGenerator()
        generator.layer_count = 50
        generator.extruder_temp = 200.0
        generator.bed_temp = 60.0

        gcode = generator.generate([], {'min': np.array([0, 0, 0]), 'max': np.array([10, 10, 10])})

        assert "G28" in gcode
        assert "G90" in gcode
        assert "M140" in gcode
        assert "M104" in gcode
        assert "200.0" in gcode
        assert "60.0" in gcode

    def test_footer_generation(self):
        generator = GCodeGenerator()
        generator.layer_count = 50
        generator.extruder_temp = 200.0
        generator.bed_temp = 60.0

        gcode = generator.generate([], {'min': np.array([0, 0, 0]), 'max': np.array([10, 10, 10])})

        assert "M104 S0" in gcode
        assert "M140 S0" in gcode
        assert "G28" in gcode

    def test_extrusion_move(self):
        generator = GCodeGenerator()
        generator.layer_count = 1
        generator.extruder_temp = 200.0
        generator.bed_temp = 60.0

        segments = [
            ToolpathSegment(np.array([0, 0, 0]), np.array([10, 0, 0.2]), True, "perimeter"),
        ]

        gcode = generator.generate(segments, {'min': np.array([0, 0, 0]), 'max': np.array([10, 10, 10])})

        assert "G1" in gcode
        assert "X10" in gcode
        assert "Z0.20000" in gcode

    def test_travel_move(self):
        generator = GCodeGenerator()
        generator.layer_count = 1
        generator.extruder_temp = 200.0
        generator.bed_temp = 60.0

        segments = [
            ToolpathSegment(np.array([0, 0, 0]), np.array([5, 5, 0.4]), False, "travel"),
        ]

        gcode = generator.generate(segments, {'min': np.array([0, 0, 0]), 'max': np.array([10, 10, 10])})

        assert "G0" in gcode

    def test_gcode_is_string(self):
        generator = GCodeGenerator()
        generator.layer_count = 10
        generator.extruder_temp = 200.0
        generator.bed_temp = 60.0

        gcode = generator.generate([], {'min': np.array([0, 0, 0]), 'max': np.array([10, 10, 10])})

        assert isinstance(gcode, str)
        assert len(gcode) > 0


class TestEstimateFunctions:
    """Test print time and material estimation."""

    def test_estimate_print_time(self):
        segments = [
            ToolpathSegment(np.array([0, 0, 0]), np.array([10, 0, 0.2]), True, "perimeter"),
            ToolpathSegment(np.array([10, 0, 0.2]), np.array([0, 10, 0.2]), False, "travel"),
        ]

        estimates = estimate_print_time(segments, print_speed=60.0, travel_speed=150.0)

        assert 'total_time' in estimates
        assert 'print_time' in estimates
        assert 'travel_time' in estimates
        assert estimates['print_time'] > 0
        assert estimates['travel_time'] > 0
        assert estimates['total_time'] > 0

    def test_estimate_material_usage(self):
        segments = [
            ToolpathSegment(np.array([0, 0, 0]), np.array([10, 0, 0.2]), True, "perimeter"),
        ]

        estimates = estimate_material_usage(segments, filament_diameter=1.75, nozzle_diameter=0.4)

        assert 'extrusion_length_mm' in estimates
        assert 'volume_mm3' in estimates
        assert 'mass_g' in estimates
        assert abs(float(estimates['extrusion_length_mm']) - 10.0) < 0.01
        assert float(estimates['mass_g']) > 0

    def test_empty_toolpath_estimates(self):
        time_est = estimate_print_time([])
        material_est = estimate_material_usage([])

        assert time_est['total_time'] == 0
        assert material_est['extrusion_length_mm'] == 0


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("TestToolpathSegment.test_segment_creation", TestToolpathSegment),
        ("TestToolpathSegment.test_segment_length", TestToolpathSegment),
        ("TestGCodeGenerator.test_header_generation", TestGCodeGenerator),
        ("TestGCodeGenerator.test_footer_generation", TestGCodeGenerator),
        ("TestGCodeGenerator.test_extrusion_move", TestGCodeGenerator),
        ("TestGCodeGenerator.test_travel_move", TestGCodeGenerator),
        ("TestGCodeGenerator.test_gcode_is_string", TestGCodeGenerator),
        ("TestEstimateFunctions.test_estimate_print_time", TestEstimateFunctions),
        ("TestEstimateFunctions.test_estimate_material_usage", TestEstimateFunctions),
        ("TestEstimateFunctions.test_empty_toolpath_estimates", TestEstimateFunctions),
    ]

    passed = 0
    failed = 0

    for name, test_class in tests:
        test_instance = test_class()
        method_name = name.split('.')[-1]
        method = getattr(test_instance, method_name)

        try:
            method()
            print(f"  ✓ {name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {passed+failed} total")
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
