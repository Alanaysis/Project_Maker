"""
后处理模块测试 (Post-processing Module Tests)
"""

import unittest
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.postprocess import (
    compute_strain_cst,
    compute_stress_cst,
    von_mises_stress_2d,
    von_mises_stress_3d,
    compute_von_mises_from_stress,
    compute_strain_energy,
    compute_nodal_forces,
    average_stresses_at_nodes,
    compute_principal_stresses
)


class TestStrainComputation(unittest.TestCase):
    """测试应变计算 (Test strain computation)"""

    def test_cst_strain_constant(self):
        """测试CST常应变 (Test CST constant strain)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        # 均匀拉伸: ux = x, uy = 0 => eps_x = 1
        displacement = np.array([0, 0, 1, 0, 0.5, 0.5])

        epsilon = compute_strain_cst(nodes, displacement)

        self.assertEqual(len(epsilon), 3)
        # eps_x应该接近1 (eps_x should be close to 1)
        self.assertAlmostEqual(epsilon[0], 1.0, places=5)


class TestStressComputation(unittest.TestCase):
    """测试应力计算 (Test stress computation)"""

    def test_cst_stress_plane_stress(self):
        """测试CST平面应力 (Test CST plane stress)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        # Pure x-strain: ux=x, uy=0 => eps_x=1, eps_y=0, gamma_xy=0
        displacement = np.array([0, 0, 1, 0, 0, 0])

        stress = compute_stress_cst(nodes, displacement, 200e9, 0.3, "plane_stress")

        self.assertEqual(len(stress), 3)
        # eps_x should be close to 1, sigma_x = E/(1-nu^2) * (eps_x + nu*eps_y)
        expected_sigma_x = 200e9 / (1 - 0.3**2) * (1.0 + 0.3 * 0.0)
        self.assertAlmostEqual(stress[0], expected_sigma_x, delta=5e8)

    def test_cst_stress_plane_strain(self):
        """测试CST平面应变 (Test CST plane strain)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        displacement = np.array([0, 0, 1, 0, 0.5, 0.5])

        stress = compute_stress_cst(nodes, displacement, 200e9, 0.3, "plane_strain")

        self.assertEqual(len(stress), 3)


class TestVonMisesStress(unittest.TestCase):
    """测试Von Mises应力 (Test Von Mises stress)"""

    def test_von_mises_2d_uniaxial(self):
        """测试2D单轴拉伸Von Mises (Test 2D uniaxial Von Mises)"""
        # 单轴拉伸: sigma_x = sigma, sigma_y = 0, tau_xy = 0
        sigma_v = von_mises_stress_2d(100e6, 0, 0)
        self.assertAlmostEqual(sigma_v, 100e6, places=0)

    def test_von_mises_2d_pure_shear(self):
        """测试2D纯剪Von Mises (Test 2D pure shear Von Mises)"""
        # 纯剪: sigma_x = sigma_y = 0, tau_xy = tau
        sigma_v = von_mises_stress_2d(0, 0, 50e6)
        # sigma_v = sqrt(3 * tau^2) = tau * sqrt(3)
        expected = 50e6 * np.sqrt(3)
        self.assertAlmostEqual(sigma_v, expected, places=0)

    def test_von_mises_3d(self):
        """测试3D Von Mises (Test 3D Von Mises)"""
        # 单轴: sigma_x = 100 MPa
        sigma_v = von_mises_stress_3d(100e6, 0, 0, 0, 0, 0)
        self.assertAlmostEqual(sigma_v, 100e6, places=0)

    def test_von_mises_from_stress(self):
        """测试从应力计算Von Mises (Test Von Mises from stress vector)"""
        stress = np.array([100e6, 50e6, 30e6])
        sigma_v = compute_von_mises_from_stress(stress, dim=2)
        expected = np.sqrt(100e6**2 - 100e6*50e6 + 50e6**2 + 3*30e6**2)
        self.assertAlmostEqual(sigma_v, expected, places=0)


class TestStrainEnergy(unittest.TestCase):
    """测试应变能 (Test strain energy)"""

    def test_strain_energy_positive(self):
        """测试应变能正定性 (Test strain energy positive definiteness)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        displacement = np.array([0.01, 0.005, 0.02, 0.01, 0.015, 0.008])

        U = compute_strain_energy(nodes, displacement, 200e9, 0.3, 1.0)

        self.assertGreater(U, 0)

    def test_strain_energy_zero_displacement(self):
        """测试零位移应变能为零 (Test zero strain energy for zero displacement)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        displacement = np.zeros(6)

        U = compute_strain_energy(nodes, displacement, 200e9, 0.3, 1.0)

        self.assertAlmostEqual(U, 0, places=10)


class TestNodalForces(unittest.TestCase):
    """测试节点力 (Test nodal forces)"""

    def test_nodal_forces_consistency(self):
        """测试节点力一致性 (Test nodal force consistency)"""
        nodes = np.array([[0, 0], [1, 0], [0, 1]])
        displacement = np.array([0.001, 0.0005, 0.002, 0.001, 0.0015, 0.0008])

        f = compute_nodal_forces(nodes, displacement, 200e9, 0.3, 1.0)

        self.assertEqual(len(f), 6)
        # 节点力应该非零 (Nodal forces should be non-zero)
        self.assertGreater(np.linalg.norm(f), 0)


class TestStressAveraging(unittest.TestCase):
    """测试应力平均 (Test stress averaging)"""

    def test_stress_averaging(self):
        """测试应力平均 (Test stress averaging)"""
        nodes = np.array([[0, 0], [1, 0], [0.5, 1], [2, 0], [1, 1]])
        elements = [[0, 1, 2], [1, 3, 2], [1, 2, 4]]
        stresses = [np.array([100, 50, 30]), np.array([100, 50, 30]), np.array([100, 50, 30])]
        disps = [np.zeros(6), np.zeros(6), np.zeros(6)]

        nodal_stresses = average_stresses_at_nodes(nodes, elements, stresses, disps)

        self.assertEqual(nodal_stresses.shape, (5, 3))
        # 共享节点应该有平均应力 (Shared nodes should have averaged stress)
        self.assertGreater(nodal_stresses[2, 0], 0)


class TestPrincipalStresses(unittest.TestCase):
    """测试主应力 (Test principal stresses)"""

    def test_principal_stresses_uniaxial(self):
        """测试单轴主应力 (Test principal stresses for uniaxial)"""
        sigma_1, sigma_2, theta = compute_principal_stresses(100e6, 0, 0)

        self.assertAlmostEqual(sigma_1, 100e6, places=0)
        self.assertAlmostEqual(sigma_2, 0, places=0)

    def test_principal_stresses_shear(self):
        """测试纯剪主应力 (Test principal stresses for pure shear)"""
        sigma_1, sigma_2, theta = compute_principal_stresses(0, 0, 50e6)

        # 纯剪的主应力: sigma_1 = tau, sigma_2 = -tau
        self.assertAlmostEqual(abs(sigma_1) - 50e6, 0, places=0)
        self.assertAlmostEqual(abs(sigma_2) - 50e6, 0, places=0)


if __name__ == "__main__":
    unittest.main()
