"""
网格模块测试 (Mesh Module Tests)
"""

import unittest
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh import (
    generate_triangular_mesh,
    generate_quadrilateral_mesh,
    generate_tetrahedral_mesh,
    generate_triangular_mesh_circle,
    refine_mesh,
    compute_mesh_quality
)


class TestTriangularMesh(unittest.TestCase):
    """测试三角形网格生成 (Test triangular mesh generation)"""

    def test_uniform_mesh_generation(self):
        """测试均匀网格生成 (Test uniform mesh generation)"""
        nodes, elements = generate_triangular_mesh(4.0, 1.0, 1.0)

        # 检查节点数 (Check number of nodes)
        # 4x1网格: (4+1)*(1+1) = 10 nodes
        self.assertEqual(len(nodes), 10)

        # 检查单元数 (Check number of elements)
        # 4x1四边形分为8个三角形
        self.assertEqual(len(elements), 8)

        # 检查节点坐标范围 (Check node coordinate ranges)
        self.assertAlmostEqual(nodes[:, 0].max(), 4.0, places=5)
        self.assertAlmostEqual(nodes[:, 0].min(), 0.0, places=5)
        self.assertAlmostEqual(nodes[:, 1].max(), 1.0, places=5)
        self.assertAlmostEqual(nodes[:, 1].min(), 0.0, places=5)

    def test_mesh_connectivity(self):
        """测试网格连通性 (Test mesh connectivity)"""
        nodes, elements = generate_triangular_mesh(2.0, 2.0, 1.0)

        # 每个单元应该有3个节点 (Each element should have 3 nodes)
        for elem in elements:
            self.assertEqual(len(elem), 3)

        # 所有节点索引应该在有效范围内 (All node indices should be in range)
        for elem in elements:
            for node_idx in elem:
                self.assertGreaterEqual(node_idx, 0)
                self.assertLess(node_idx, len(nodes))

    def test_graded_mesh(self):
        """测试梯度网格 (Test graded mesh)"""
        nodes, elements = generate_triangular_mesh(4.0, 1.0, 1.0, "graded")

        # 梯度网格节点数与均匀网格相同（仅分布不同）
        self.assertEqual(len(nodes), 10)
        self.assertEqual(len(elements), 8)


class TestQuadrilateralMesh(unittest.TestCase):
    """测试四边形网格生成 (Test quadrilateral mesh generation)"""

    def test_quad_mesh_generation(self):
        """测试四边形网格生成 (Test quadrilateral mesh generation)"""
        nodes, elements = generate_quadrilateral_mesh(4.0, 2.0, 1.0)

        # 4x2网格: (4+1)*(2+1) = 15 nodes
        self.assertEqual(len(nodes), 15)
        # 4x2 = 8 quadrilateral elements
        self.assertEqual(len(elements), 8)

        # 每个单元应该有4个节点 (Each element should have 4 nodes)
        for elem in elements:
            self.assertEqual(len(elem), 4)


class TestTetrahedralMesh(unittest.TestCase):
    """测试四面体网格生成 (Test tetrahedral mesh generation)"""

    def test_tet_mesh_generation(self):
        """测试四面体网格生成 (Test tetrahedral mesh generation)"""
        nodes, elements = generate_tetrahedral_mesh(2.0, 2.0, 2.0, 1.0)

        # 2x2x2网格: 3*3*3 = 27 nodes
        self.assertEqual(len(nodes), 27)

        # 2x2x2 = 8六面体，每个分为6个四面体 = 48个四面体
        self.assertEqual(len(elements), 48)

        # 每个单元应该有4个节点 (Each element should have 4 nodes)
        for elem in elements:
            self.assertEqual(len(elem), 4)


class TestCircleMesh(unittest.TestCase):
    """测试圆形区域网格 (Test circular region mesh)"""

    def test_circle_mesh_delaunay(self):
        """测试Delaunay圆形网格 (Test Delaunay circular mesh)"""
        radius = 1.0
        nodes, elements = generate_triangular_mesh_circle(radius, 0.3, mesher="delaunay")

        self.assertGreater(len(nodes), 0)
        self.assertGreater(len(elements), 0)

        # 所有节点应该在圆内 (All nodes should be inside the circle)
        for node in nodes:
            dist = np.sqrt(node[0]**2 + node[1]**2)
            self.assertLessEqual(dist, radius + 0.01)

    def test_circle_mesh_uniform(self):
        """测试均匀圆形网格 (Test uniform circular mesh)"""
        radius = 1.0
        nodes, elements = generate_triangular_mesh_circle(radius, 0.5, mesher="uniform")

        self.assertGreater(len(nodes), 0)
        self.assertGreater(len(elements), 0)


class TestMeshRefinement(unittest.TestCase):
    """测试网格细化 (Test mesh refinement)"""

    def test_refinement_increase_nodes(self):
        """测试细化增加节点数 (Test refinement increases node count)"""
        nodes, elements = generate_triangular_mesh(2.0, 2.0, 1.0)
        refined_nodes, refined_elements = refine_mesh(nodes, elements, refinement_level=1)

        self.assertGreater(len(refined_nodes), len(nodes))
        self.assertGreater(len(refined_elements), len(elements))

    def test_refinement_preserves_geometry(self):
        """测试细化保持几何形状 (Test refinement preserves geometry)"""
        nodes, elements = generate_triangular_mesh(2.0, 2.0, 1.0)
        refined_nodes, _ = refine_mesh(nodes, elements, refinement_level=2)

        # 细化后的节点应该在原始几何范围内 (Refined nodes should be within original geometry)
        self.assertAlmostEqual(refined_nodes[:, 0].max(), 2.0, places=5)
        self.assertAlmostEqual(refined_nodes[:, 1].max(), 2.0, places=5)


class TestMeshQuality(unittest.TestCase):
    """测试网格质量 (Test mesh quality)"""

    def test_quality_metrics(self):
        """测试质量指标计算 (Test quality metrics calculation)"""
        nodes, elements = generate_triangular_mesh(2.0, 2.0, 1.0)
        quality = compute_mesh_quality(nodes, elements)

        self.assertIn("min_aspect_ratio", quality)
        self.assertIn("max_aspect_ratio", quality)
        self.assertIn("mean_aspect_ratio", quality)
        self.assertIn("min_jacobian", quality)
        self.assertIn("mean_jacobian", quality)
        self.assertIn("num_elements", quality)
        self.assertIn("num_nodes", quality)

        # 雅可比比应该为正 (Jacobian should be positive)
        self.assertGreater(quality["min_jacobian"], 0)


if __name__ == "__main__":
    unittest.main()
