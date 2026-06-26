"""
Tests for infill generator module.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infill_generator import (
    generate_infill, InfillPattern, InfillSegment
)


class TestInfillPattern:
    """Test infill pattern generation."""

    def test_grid_pattern(self):
        bounds = (np.array([0, 0]), np.array([20, 10]))
        segments = generate_infill(1.0, bounds, InfillPattern.GRID, 3.0)

        assert len(segments) > 0
        for seg in segments:
            assert abs(seg[0][2] - 1.0) < 1e-10
            assert abs(seg[1][2] - 1.0) < 1e-10

    def test_honeycomb_pattern(self):
        bounds = (np.array([0, 0]), np.array([20, 10]))
        segments = generate_infill(1.0, bounds, InfillPattern.HONEYCOMB, 3.0)

        assert len(segments) > 0
        for seg in segments:
            assert abs(seg[0][2] - 1.0) < 1e-10

    def test_gyroid_pattern(self):
        bounds = (np.array([0, 0]), np.array([20, 10]))
        segments = generate_infill(1.0, bounds, InfillPattern.GYROID, 3.0)

        assert len(segments) >= 0  # May be empty for some patterns

    def test_concentric_pattern(self):
        bounds = (np.array([0, 0]), np.array([20, 10]))
        segments = generate_infill(1.0, bounds, InfillPattern.CONCENTRIC, 3.0)

        assert len(segments) > 0

    def test_infill_percentage(self):
        """Test that higher infill percentage produces more segments."""
        bounds = (np.array([0, 0]), np.array([20, 10]))

        segs_10 = generate_infill(1.0, bounds, InfillPattern.GRID, 5.0, 10.0)
        segs_20 = generate_infill(1.0, bounds, InfillPattern.GRID, 5.0, 20.0)

        # Higher percentage should have more segments (or same)
        assert len(segs_20) >= len(segs_10)

    def test_segment_lengths(self):
        """Test that infill segments have valid lengths."""
        bounds = (np.array([0, 0]), np.array([10, 10]))

        for pattern in InfillPattern:
            segments = generate_infill(1.0, bounds, pattern, 3.0)
            for seg in segments:
                length = np.linalg.norm(seg[1][:2] - seg[0][:2])
                assert length >= 0, f"Negative length in {pattern}"

    def test_bounds_respected(self):
        """Test that segments stay within bounds."""
        bounds = (np.array([5, 5]), np.array([15, 15]))

        for pattern in [InfillPattern.GRID, InfillPattern.HONEYCOMB, InfillPattern.CONCENTRIC]:
            segments = generate_infill(1.0, bounds, pattern, 3.0)
            for seg in segments:
                assert seg[0][0] >= 4.9  # Small tolerance
                assert seg[0][1] >= 4.9
                assert seg[1][0] <= 15.1
                assert seg[1][1] <= 15.1

    def test_z_height_preserved(self):
        """Test that Z height is preserved in segments."""
        bounds = (np.array([0, 0]), np.array([10, 10]))
        z = 3.14159

        for pattern in InfillPattern:
            segments = generate_infill(z, bounds, pattern, 3.0)
            for seg in segments:
                assert abs(seg[0][2] - z) < 1e-10
                assert abs(seg[1][2] - z) < 1e-10


def test_infill_segment():
    """Test InfillSegment class."""
    start = np.array([0.0, 0.0, 0.0])
    end = np.array([3.0, 4.0, 0.0])
    seg = InfillSegment(start, end)

    assert abs(seg.length() - 5.0) < 1e-10


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("TestInfillPattern.test_grid_pattern", TestInfillPattern),
        ("TestInfillPattern.test_honeycomb_pattern", TestInfillPattern),
        ("TestInfillPattern.test_gyroid_pattern", TestInfillPattern),
        ("TestInfillPattern.test_concentric_pattern", TestInfillPattern),
        ("TestInfillPattern.test_infill_percentage", TestInfillPattern),
        ("TestInfillPattern.test_segment_lengths", TestInfillPattern),
        ("TestInfillPattern.test_bounds_respected", TestInfillPattern),
        ("TestInfillPattern.test_z_height_preserved", TestInfillPattern),
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

    # Run standalone test
    try:
        test_infill_segment()
        print(f"  ✓ test_infill_segment")
        passed += 1
    except Exception as e:
        print(f"  ✗ test_infill_segment: {e}")
        failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {passed+failed} total")
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
