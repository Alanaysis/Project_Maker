"""
Tests for STL parser module.
"""

import sys
import os
import struct
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stl_parser import STLTriangle, STLModel, load_stl, parse_binary_stl


def create_test_stl_binary(filepath: str):
    """Create a simple triangular prism STL file."""
    triangles = [
        # Triangle 1
        ([1, 0, 0], [0, 1, 0], [0, 0, 1]),
        # Triangle 2
        ([1, 0, 0], [0, 0, 1], [0, 1, 0]),
    ]

    with open(filepath, 'wb') as f:
        header = b'Test STL' + b'\x00' * (80 - len(b'Test STL'))
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))

        for v0, v1, v2 in triangles:
            e1 = np.array(v1) - np.array(v0)
            e2 = np.array(v2) - np.array(v0)
            normal = np.cross(e1, e2).astype(np.float64)
            length = np.linalg.norm(normal)
            if length > 0:
                normal /= length
            f.write(struct.pack('<3f', *normal))
            f.write(struct.pack('<9f', *[float(v) for v in v0] + [float(v) for v in v1] + [float(v) for v in v2]))
            f.write(struct.pack('<H', 0))


class TestSTLTriangle:
    """Test STLTriangle class."""

    def test_triangle_creation(self):
        v0 = np.array([1.0, 0.0, 0.0])
        v1 = np.array([0.0, 1.0, 0.0])
        v2 = np.array([0.0, 0.0, 1.0])
        normal = np.array([1.0, 1.0, 1.0]) / np.sqrt(3)

        tri = STLTriangle(v0, v1, v2, normal)
        assert np.allclose(tri.vertex_a, v0)
        assert np.allclose(tri.vertex_b, v1)
        assert np.allclose(tri.vertex_c, v2)
        assert np.allclose(tri.normal, normal)

    def test_vertices_array(self):
        v0 = np.array([1.0, 0.0, 0.0])
        v1 = np.array([0.0, 1.0, 0.0])
        v2 = np.array([0.0, 0.0, 1.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        verts = tri.vertices
        assert verts.shape == (3, 3)
        assert np.allclose(verts[0], v0)
        assert np.allclose(verts[1], v1)
        assert np.allclose(verts[2], v2)

    def test_centroid(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([3.0, 0.0, 0.0])
        v2 = np.array([0.0, 3.0, 0.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        centroid = tri.centroid()
        expected = np.array([1.0, 1.0, 0.0])
        assert np.allclose(centroid, expected)

    def test_area_right_triangle(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([3.0, 0.0, 0.0])
        v2 = np.array([0.0, 4.0, 0.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        # Area = 0.5 * base * height = 0.5 * 3 * 4 = 6
        assert abs(tri.area() - 6.0) < 1e-10

    def test_bounding_box(self):
        v0 = np.array([1.0, 2.0, 3.0])
        v1 = np.array([4.0, 5.0, 6.0])
        v2 = np.array([2.0, 1.0, 7.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        min_pt, max_pt = tri.bounding_box()
        assert np.allclose(min_pt, [1.0, 1.0, 3.0])
        assert np.allclose(max_pt, [4.0, 5.0, 7.0])


class TestSTLModel:
    """Test STLModel class."""

    def test_model_creation(self):
        model = STLModel("test_model")
        assert model.name == "test_model"
        assert len(model.triangles) == 0
        assert model.bounds is None

    def test_model_bounds(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 1.0, 1.0])
        v2 = np.array([2.0, 0.0, 0.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        model = STLModel()
        model.triangles = [tri]
        bounds = model.compute_bounds()

        assert bounds is not None
        assert np.allclose(bounds[0], [0.0, 0.0, 0.0])
        assert np.allclose(bounds[1], [2.0, 1.0, 1.0])

    def test_num_vertices(self):
        model = STLModel("empty")
        assert model.num_vertices() == 0

        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        model.triangles = [tri, tri, tri]
        assert model.num_vertices() == 9

    def test_total_area(self):
        v0 = np.array([0.0, 0.0, 0.0])
        v1 = np.array([2.0, 0.0, 0.0])
        v2 = np.array([0.0, 2.0, 0.0])
        tri = STLTriangle(v0, v1, v2, np.array([0, 0, 1]))

        model = STLModel()
        model.triangles = [tri]
        assert abs(model.total_area() - 2.0) < 1e-10


class TestLoadSTL:
    """Test STL file loading."""

    def test_load_binary_stl(self, tmp_path=None):
        """Test loading a binary STL file."""
        import tempfile
        if tmp_path is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                filepath = tmp_dir + '/test.stl'
                create_test_stl_binary(filepath)
                model = load_stl(filepath)
                assert len(model.triangles) == 2
                assert model.bounds is not None
        else:
            filepath = str(tmp_path) + '/test.stl'
            create_test_stl_binary(filepath)
            model = load_stl(filepath)
            assert len(model.triangles) == 2
            assert model.bounds is not None

    def test_load_invalid_file(self, tmp_path):
        filepath = str(tmp_path / 'invalid.stl')
        with open(filepath, 'wb') as f:
            f.write(b'invalid' + b'\x00' * 75)

        # Should not crash, but may raise ValueError
        try:
            model = load_stl(filepath)
        except (ValueError, struct.error):
            pass  # Expected


def run_all_tests():
    """Run all tests and report results."""
    import tempfile

    tests = [
        ("TestSTLTriangle.test_triangle_creation", TestSTLTriangle),
        ("TestSTLTriangle.test_vertices_array", TestSTLTriangle),
        ("TestSTLTriangle.test_centroid", TestSTLTriangle),
        ("TestSTLTriangle.test_area_right_triangle", TestSTLTriangle),
        ("TestSTLTriangle.test_bounding_box", TestSTLTriangle),
        ("TestSTLModel.test_model_creation", TestSTLModel),
        ("TestSTLModel.test_model_bounds", TestSTLModel),
        ("TestSTLModel.test_num_vertices", TestSTLModel),
        ("TestSTLModel.test_total_area", TestSTLModel),
        ("TestLoadSTL.test_load_binary_stl", TestLoadSTL),
    ]

    passed = 0
    failed = 0

    for name, test_class in tests:
        test_instance = test_class()
        method_name = name.split('.')[-1]
        method = getattr(test_instance, method_name)

        try:
            if 'tmp_path' in str(method.__code__.co_varnames):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    method(tmp_dir)
            else:
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
