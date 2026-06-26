"""
Tests for mesh slicer module.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh_slicer import (
    intersect_triangle_with_plane, SliceSegment, Layer,
    slice_mesh, extract_perimeters
)
from src.stl_parser import STLTriangle


def create_test_triangles():
    """Create test triangles for slicing."""
    # Triangle that spans across Z=0 plane
    v0 = np.array([0.0, 0.0, -1.0])
    v1 = np.array([1.0, 0.0, 1.0])
    v2 = np.array([0.0, 1.0, 0.5])
    normal = np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
    tri1 = STLTriangle(v0, v1, v2, normal)

    # Triangle entirely above Z=0
    v3 = np.array([2.0, 0.0, 1.0])
    v4 = np.array([3.0, 0.0, 2.0])
    v5 = np.array([2.5, 1.0, 1.5])
    tri2 = STLTriangle(v3, v4, v5, np.array([0, 0, 1]))

    # Triangle entirely below Z=0
    v6 = np.array([4.0, 0.0, -2.0])
    v7 = np.array([5.0, 0.0, -1.0])
    v8 = np.array([4.5, 1.0, -1.5])
    tri3 = STLTriangle(v6, v7, v8, np.array([0, 0, -1]))

    return [tri1, tri2, tri3]


class TestIntersectTriangleWithPlane:
    """Test triangle-plane intersection."""

    def test_intersects_above(self):
        v0 = np.array([0.0, 0.0, -1.0])
        v1 = np.array([1.0, 0.0, 1.0])
        v2 = np.array([0.0, 1.0, 0.5])
        tri = STLTriangle(v0, v1, v2, np.array([1, 1, 1]))

        segment = intersect_triangle_with_plane(tri, 0.0)
        assert segment is not None

    def test_intersects_at(self):
        """Test intersection at Z=0.5."""
        v0 = np.array([0.0, 0.0, -1.0])
        v1 = np.array([1.0, 0.0, 1.0])
        v2 = np.array([0.0, 1.0, 0.6])
        tri = STLTriangle(v0, v1, v2, np.array([1, 1, 1]))

        segment = intersect_triangle_with_plane(tri, 0.5)
        assert segment is not None

    def test_no_intersection_above(self):
        v0 = np.array([0.0, 0.0, 1.0])
        v1 = np.array([1.0, 0.0, 2.0])
        v2 = np.array([0.0, 1.0, 1.5])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        segment = intersect_triangle_with_plane(tri, 0.0)
        assert segment is None

    def test_no_intersection_below(self):
        v0 = np.array([0.0, 0.0, -2.0])
        v1 = np.array([1.0, 0.0, -1.0])
        v2 = np.array([0.0, 1.0, -1.5])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, -1]))

        segment = intersect_triangle_with_plane(tri, 0.0)
        assert segment is None

    def test_intersection_point(self):
        """Test that intersection point is on the plane."""
        v0 = np.array([0.0, 0.0, -1.0])
        v1 = np.array([2.0, 0.0, 1.0])
        v2 = np.array([0.0, 2.0, 1.0])
        tri = STLTriangle(v0, v1, v2, np.array([1, -1, -1]))

        segment = intersect_triangle_with_plane(tri, 0.0)
        assert segment is not None
        assert abs(segment.start[2]) < 1e-10
        assert abs(segment.end[2]) < 1e-10


class TestSliceMesh:
    """Test mesh slicing."""

    def test_slice_basic(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 1.0])
        v2 = np.array([0.0, 1.0, 0.5])
        tri = STLTriangle(v0, v1, v2, np.array([1, 1, 1]))

        from src.stl_parser import STLModel
        model = STLModel()
        model.triangles = [tri]
        model.bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))

        layers = slice_mesh(model, 0.0, 1.0, 0.5)
        assert len(layers) > 0

    def test_slice_no_geometry(self):
        from src.stl_parser import STLModel
        model = STLModel()
        model.triangles = []
        model.bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))

        layers = slice_mesh(model, 0.0, 1.0, 0.5)
        assert len(layers) == 3  # 0, 0.5, 1.0

    def test_slice_layer_height(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 1.0])
        v2 = np.array([0.0, 1.0, 0.5])
        tri = STLTriangle(v0, v1, v2, np.array([1, 1, 1]))

        from src.stl_parser import STLModel
        model = STLModel()
        model.triangles = [tri]
        model.bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))

        layers = slice_mesh(model, 0.0, 1.0, 0.25)
        assert len(layers) == 5  # 0, 0.25, 0.5, 0.75, 1.0


class TestSliceSegment:
    """Test SliceSegment class."""

    def test_segment_length(self):
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([3.0, 4.0, 0.0])
        seg = SliceSegment(start, end)
        assert abs(seg.length() - 5.0) < 1e-10

    def test_segment_midpoint(self):
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([2.0, 4.0, 0.0])
        seg = SliceSegment(start, end)
        expected = np.array([1.0, 2.0, 0.0])
        assert np.allclose(seg.midpoint(), expected)

    def test_segment_repr(self):
        start = np.array([1.0, 2.0, 0.0])
        end = np.array([3.0, 4.0, 0.0])
        seg = SliceSegment(start, end)
        repr_str = repr(seg)
        assert "Segment" in repr_str


class TestLayer:
    """Test Layer class."""

    def test_layer_creation(self):
        layer = Layer(1.5)
        assert layer.z_height == 1.5
        assert len(layer.segments) == 0
        assert layer.total_segment_length == 0

    def test_layer_with_segments(self):
        s1 = SliceSegment(np.array([0, 0, 1]), np.array([1, 0, 1]))
        s2 = SliceSegment(np.array([0, 0, 1]), np.array([0, 1, 1]))

        layer = Layer(1.0)
        layer.segments = [s1, s2]
        assert layer.total_segment_length == 2.0


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("TestIntersectTriangleWithPlane.test_intersects_above", TestIntersectTriangleWithPlane),
        ("TestIntersectTriangleWithPlane.test_intersects_at", TestIntersectTriangleWithPlane),
        ("TestIntersectTriangleWithPlane.test_no_intersection_above", TestIntersectTriangleWithPlane),
        ("TestIntersectTriangleWithPlane.test_no_intersection_below", TestIntersectTriangleWithPlane),
        ("TestIntersectTriangleWithPlane.test_intersection_point", TestIntersectTriangleWithPlane),
        ("TestSliceMesh.test_slice_basic", TestSliceMesh),
        ("TestSliceMesh.test_slice_no_geometry", TestSliceMesh),
        ("TestSliceMesh.test_slice_layer_height", TestSliceMesh),
        ("TestSliceSegment.test_segment_length", TestSliceSegment),
        ("TestSliceSegment.test_segment_midpoint", TestSliceSegment),
        ("TestSliceSegment.test_segment_repr", TestSliceSegment),
        ("TestLayer.test_layer_creation", TestLayer),
        ("TestLayer.test_layer_with_segments", TestLayer),
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
