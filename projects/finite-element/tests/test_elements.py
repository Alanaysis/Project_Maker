"""
单元刚度矩阵测试 (Element Stiffness Matrix Tests)
"""

import unittest
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.elements import (
    plane_stress_matrix, plane_strain_matrix, hooke_3d_matrix,
    cst_stiffness_matrix, beam_stiffness_matrix, truss_stiffness_matrix,
    truss_3d_stiffness_matrix, quad_stiffness_matrix
)


class TestConstitutiveMatrix(unittest.TestCase):
    """测试弹性矩阵 (Test constitutive matrices)"""

    def test_plane_stress_matrix(self):
        """测试平面应力弹性矩阵 (Test plane stress constitutive matrix)"""
        E = 200e9
        nu = 0.3
        D = plane_stress_matrix(E, nu)

        # 检查矩阵形状 (Check matrix shape)
        self.assertEqual(D.shape, (3, 3))

        # 检查对称性 (Check symmetry)
        np.testing.assert_array_almost_equal(D, D.T)

        # 检查主对角元为正 (Check positive diagonal)
        self.assertGreater(D[0, 0], 0)
        self.assertGreater(D[1, 1], 0)
        self.assertGreater(D[2, 2], 0)

        # 检查理论值 (Check theoretical values)
        factor = E / (1 - nu**2)
        np.testing.assert_almost_equal(D[0, 0], factor)
        np.testing.assert_almost_equal(D[0, 1], factor * nu)
        np.testing.assert_almost_equal(D[2, 2], factor * (1 - nu) / 2)

    def test_plane_strain_matrix(self):
        """测试平面应变弹性矩阵 (Test plane strain constitutive matrix)"""
        E = 200e9
        nu = 0.3
        D = plane_strain_matrix(E, nu)

        self.assertEqual(D.shape, (3, 3))
        np.testing.assert_array_almost_equal(D, D.T)

        factor = E / ((1 + nu) * (1 - 2 * nu))
        np.testing.assert_almost_equal(D[0, 0], factor * (1 - nu))
        np.testing.assert_almost_equal(D[0, 1], factor * nu)

    def test_hooke_3d_matrix(self):
        """测试3D弹性矩阵 (Test 3D constitutive matrix)"""
        E = 200e9
        nu = 0.3
        D = hooke_3d_matrix(E, nu)

        self.assertEqual(D.shape, (6, 6))
        np.testing.assert_array_almost_equal(D, D.T)


class TestCSTStiffness(unittest.TestCase):
    """测试CST单元刚度矩阵 (Test CST element stiffness matrix)"""

    def test_cst_symmetry(self):
        """测试CST刚度矩阵对称性 (Test CST stiffness matrix symmetry)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        k = cst_stiffness_matrix(nodes, 200e9, 0.3, 1.0)

        np.testing.assert_array_almost_equal(k, k.T)

    def test_cst_positive_diagonal(self):
        """测试CST刚度矩阵正对角元 (Test CST stiffness matrix positive diagonal)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        k = cst_stiffness_matrix(nodes, 200e9, 0.3, 1.0)

        for i in range(6):
            self.assertGreater(k[i, i], 0)

    def test_cst_zero_rigid_body(self):
        """测试CST刚体模式 (Test CST rigid body modes)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        k = cst_stiffness_matrix(nodes, 200e9, 0.3, 1.0)

        # 刚体平移模式: k * [1,0,1,0,1,0]^T = 0 (x-translation)
        rigid_x = np.array([1, 0, 1, 0, 1, 0])
        result = k @ rigid_x
        np.testing.assert_array_almost_equal(result, np.zeros(6), decimal=5)

        # 刚体平移模式: k * [0,1,0,1,0,1]^T = 0 (y-translation)
        rigid_y = np.array([0, 1, 0, 1, 0, 1])
        result = k @ rigid_y
        np.testing.assert_array_almost_equal(result, np.zeros(6), decimal=5)

    def test_cst_degenerate_triangle(self):
        """测试CST退化三角形 (Test CST degenerate triangle)"""
        # 共线节点应该报错 (Collinear nodes should raise error)
        nodes = np.array([[0, 0], [1, 1], [2, 2]])
        with self.assertRaises(ValueError):
            cst_stiffness_matrix(nodes, 200e9, 0.3, 1.0)


class TestBeamStiffness(unittest.TestCase):
    """测试梁单元刚度矩阵 (Test beam element stiffness matrix)"""

    def test_beam_symmetry(self):
        """测试梁刚度矩阵对称性 (Test beam stiffness matrix symmetry)"""
        k = beam_stiffness_matrix(200e9, 1e-6, 1.0, 0.01)
        np.testing.assert_array_almost_equal(k, k.T)

    def test_beam_positive_diagonal(self):
        """测试梁刚度矩阵正对角元 (Test beam stiffness matrix positive diagonal)"""
        k = beam_stiffness_matrix(200e9, 1e-6, 1.0, 0.01)
        for i in range(6):
            self.assertGreater(k[i, i], 0)

    def test_beam_units(self):
        """测试梁刚度矩阵量纲 (Test beam stiffness matrix units)"""
        E = 200e9  # Pa
        I = 1e-6   # m^4
        L = 1.0    # m
        A = 0.01   # m^2

        k = beam_stiffness_matrix(E, I, L, A)

        # EA/L 应该具有力的量纲 (EA/L should have force units)
        axial_stiffness = E * A / L
        self.assertAlmostEqual(k[0, 0] / axial_stiffness, 1.0, places=5)


class TestTrussStiffness(unittest.TestCase):
    """测试桁架单元刚度矩阵 (Test truss element stiffness matrix)"""

    def test_truss_2d_symmetry(self):
        """测试2D桁架刚度矩阵对称性 (Test 2D truss stiffness symmetry)"""
        nodes = np.array([[0, 0], [1, 0]])
        k = truss_stiffness_matrix(200e9, 0.01, nodes)
        np.testing.assert_array_almost_equal(k, k.T)

    def test_truss_2d_rigid_body(self):
        """测试2D桁架刚体模式 (Test 2D truss rigid body modes)"""
        nodes = np.array([[0, 0], [1, 0]])
        k = truss_stiffness_matrix(200e9, 0.01, nodes)

        # 刚体平移应该产生零力 (Rigid body translation should produce zero force)
        rigid = np.array([1, 0, 1, 0])  # x-translation
        np.testing.assert_array_almost_equal(k @ rigid, np.zeros(4))

    def test_truss_3d_symmetry(self):
        """测试3D桁架刚度矩阵对称性 (Test 3D truss stiffness symmetry)"""
        nodes = np.array([[0, 0, 0], [1, 1, 1]])
        k = truss_3d_stiffness_matrix(200e9, 0.01, nodes)
        np.testing.assert_array_almost_equal(k, k.T)

    def test_truss_3d_rigid_body(self):
        """测试3D桁架刚体模式 (Test 3D truss rigid body modes)"""
        nodes = np.array([[0, 0, 0], [1, 0, 0]])
        k = truss_3d_stiffness_matrix(200e9, 0.01, nodes)

        rigid = np.array([1, 0, 0, 1, 0, 0])  # x-translation
        np.testing.assert_array_almost_equal(k @ rigid, np.zeros(6))


class TestQuadStiffness(unittest.TestCase):
    """测试四边形单元刚度矩阵 (Test quad element stiffness matrix)"""

    def test_quad_symmetry(self):
        """测试四边形刚度矩阵对称性 (Test quad stiffness symmetry)"""
        nodes = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        k = quad_stiffness_matrix(nodes, 200e9, 0.3, 1.0)
        np.testing.assert_array_almost_equal(k, k.T)

    def test_quad_positive_diagonal(self):
        """测试四边形刚度矩阵正对角元 (Test quad stiffness positive diagonal)"""
        nodes = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        k = quad_stiffness_matrix(nodes, 200e9, 0.3, 1.0)
        for i in range(8):
            self.assertGreater(k[i, i], 0)

    def test_quad_rigid_body(self):
        """测试四边形刚体模式 (Test quad rigid body modes)"""
        nodes = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        k = quad_stiffness_matrix(nodes, 200e9, 0.3, 1.0)

        # 刚体x平移 (x-translation)
        rigid_x = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        np.testing.assert_array_almost_equal(k @ rigid_x, np.zeros(8), decimal=5)


if __name__ == "__main__":
    unittest.main()
