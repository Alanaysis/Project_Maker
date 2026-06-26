"""
组装模块测试 (Assembly Module Tests)
"""

import unittest
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.assembly import (
    GlobalAssembler,
    assemble_global_stiffness,
    apply_displacement_bc,
    solve_with_penalization,
    apply_force_to_dof,
    create_force_vector
)


class TestGlobalAssembler(unittest.TestCase):
    """测试全局组装器 (Test global assembler)"""

    def test_assembler_initialization(self):
        """测试组装器初始化 (Test assembler initialization)"""
        assembler = GlobalAssembler(5, 2)
        self.assertEqual(assembler.num_nodes, 5)
        self.assertEqual(assembler.total_dofs, 10)

    def test_assemble_element(self):
        """测试单元组装 (Test element assembly)"""
        assembler = GlobalAssembler(3, 2)

        # 一个简单的2节点单元刚度矩阵 (2-node element with 2 DOFs per node = 4x4)
        # node_indices=[0,1] maps to DOFs (0,1) and (2,3)
        # The code iterates over node_indices and uses i_local as DOF offset
        k_elem = np.array([[1, 0],
                           [0, 1]])

        assembler.assemble_element([0, 1], k_elem)
        K = assembler.assemble()

        # 检查组装结果 (Check assembly results)
        self.assertAlmostEqual(K[0, 0], 1.0)
        self.assertAlmostEqual(K[3, 3], 1.0)

    def test_boundary_conditions(self):
        """测试边界条件应用 (Test boundary condition application)"""
        assembler = GlobalAssembler(3, 2)

        k_elem = np.eye(4)
        assembler.assemble_element([0, 1], k_elem)

        constraints = {0: 0.0, 1: 0.0}
        force_vector = np.zeros(6)

        assembler.apply_boundary_conditions(constraints, force_vector)
        K = assembler.assemble()

        # 约束自由度的行和列应该被处理 (Constrained DOFs should be handled)
        self.assertGreater(K[0, 0], 0)
        self.assertAlmostEqual(K[0, 1], 0)

    def test_solve_simple_system(self):
        """测试简单系统求解 (Test simple system solving)"""
        # 使用1D弹簧系统 (Use 1D spring system)
        assembler = GlobalAssembler(3, 1)

        # Element 0-1: k = [[1,-1],[-1,1]]
        k1 = np.array([[1, -1], [-1, 1]])
        assembler.assemble_element([0, 1], k1)

        # Element 1-2: k = [[1,-1],[-1,1]]
        k2 = np.array([[1, -1], [-1, 1]])
        assembler.assemble_element([1, 2], k2)

        # Fix nodes 0 and 2 (prevents rigid body, all DOFs constrained)
        constraints = {0: 0.0, 2: 0.0}
        force_vector = np.array([0, 1, 0])

        U = assembler.solve(force_vector, constraints)

        # Node 1 displacement: two springs in series, k=0.5, F=1 => u=2
        self.assertAlmostEqual(U[1], 2.0, places=5)


class TestDisplacementBC(unittest.TestCase):
    """测试位移边界条件 (Test displacement boundary conditions)"""

    def test_condensation(self):
        """测试缩减法 (Test condensation method)"""
        K = np.array([[2, -1, 0],
                      [-1, 2, -1],
                      [0, -1, 1]])
        F = np.array([0, 0, 1])
        constraints = {0: 0.0}

        K_red, F_red = apply_displacement_bc(K, F, constraints)

        self.assertEqual(K_red.shape, (2, 2))
        self.assertEqual(F_red.shape, (2,))


class TestPenaltyMethod(unittest.TestCase):
    """测试罚函数法 (Test penalty method)"""

    def test_penalty_bc(self):
        """测试罚函数边界条件 (Test penalty BC)"""
        K = np.array([[2, -1], [-1, 1]])
        F = np.array([0, 1])
        constraints = {0: 0.5}

        U = solve_with_penalization(K, F, constraints, penalty_factor=1e10)

        # 约束自由度应该接近约束值 (Constrained DOF should be close to constraint value)
        self.assertAlmostEqual(U[0], 0.5, places=3)


class TestForceVector(unittest.TestCase):
    """测试力向量操作 (Test force vector operations)"""

    def test_create_force_vector(self):
        """测试力向量创建 (Test force vector creation)"""
        F = create_force_vector(3, 2, [(0, 100), (3, -50), (5, 200)])

        self.assertEqual(len(F), 6)
        self.assertAlmostEqual(F[0], 100)
        self.assertAlmostEqual(F[3], -50)
        self.assertAlmostEqual(F[5], 200)

    def test_apply_force_to_dof(self):
        """测试自由度施力 (Test applying force to DOF)"""
        F = np.zeros(6)
        F = apply_force_to_dof(F, 2, 50)

        self.assertAlmostEqual(F[2], 50)


if __name__ == "__main__":
    unittest.main()
