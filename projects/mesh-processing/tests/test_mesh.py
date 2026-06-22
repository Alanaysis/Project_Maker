"""网格处理算法测试"""

import pytest
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh_data import TriangleMesh, Vertex, Face
from src.simplification import MeshSimplifier
from src.subdivision import LoopSubdivision
from src.smoothing import LaplacianSmoother, TaubinSmoother, WeightedLaplacianSmoother


class TestTriangleMesh:
    """测试三角网格数据结构"""

    def test_create_empty_mesh(self):
        """测试创建空网格"""
        mesh = TriangleMesh()
        assert mesh.num_vertices == 0
        assert mesh.num_faces == 0
        assert mesh.num_edges == 0

    def test_add_vertex(self):
        """测试添加顶点"""
        mesh = TriangleMesh()
        vid = mesh.add_vertex(np.array([1.0, 2.0, 3.0]))

        assert mesh.num_vertices == 1
        vertex = mesh.get_vertex(vid)
        assert vertex is not None
        np.testing.assert_array_equal(vertex.position, [1.0, 2.0, 3.0])

    def test_add_face(self):
        """测试添加面"""
        mesh = TriangleMesh()
        v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
        v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
        v2 = mesh.add_vertex(np.array([0.0, 1.0, 0.0]))

        fid = mesh.add_face(v0, v1, v2)

        assert mesh.num_faces == 1
        face = mesh.get_face(fid)
        assert face is not None
        assert face.vertices == (v0, v1, v2)

    def test_topology_update(self):
        """测试拓扑关系更新"""
        mesh = TriangleMesh()
        v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
        v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
        v2 = mesh.add_vertex(np.array([0.0, 1.0, 0.0]))

        mesh.add_face(v0, v1, v2)

        # 检查顶点的相邻关系
        assert v1 in mesh.vertices[v0].adjacent_vertices
        assert v2 in mesh.vertices[v0].adjacent_vertices
        assert v0 in mesh.vertices[v1].adjacent_vertices

    def test_face_normal(self):
        """测试面法向量计算"""
        mesh = TriangleMesh()
        v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
        v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
        v2 = mesh.add_vertex(np.array([0.0, 1.0, 0.0]))

        fid = mesh.add_face(v0, v1, v2)
        face = mesh.get_face(fid)

        # 面法向量应该指向 z 轴正方向
        np.testing.assert_allclose(face.normal, [0.0, 0.0, 1.0], atol=1e-10)

    def test_remove_face(self):
        """测试移除面"""
        mesh = TriangleMesh()
        v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
        v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
        v2 = mesh.add_vertex(np.array([0.0, 1.0, 0.0]))

        fid = mesh.add_face(v0, v1, v2)
        assert mesh.num_faces == 1

        mesh.remove_face(fid)
        assert mesh.num_faces == 0

    def test_clone(self):
        """测试网格克隆"""
        mesh = TriangleMesh()
        v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
        v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
        v2 = mesh.add_vertex(np.array([0.0, 1.0, 0.0]))
        mesh.add_face(v0, v1, v2)

        cloned = mesh.clone()

        assert cloned.num_vertices == mesh.num_vertices
        assert cloned.num_faces == mesh.num_faces

        # 修改原网格不应影响克隆
        mesh.vertices[v0].position = np.array([10.0, 10.0, 10.0])
        np.testing.assert_array_equal(cloned.vertices[v0].position, [0.0, 0.0, 0.0])


def create_tetrahedron() -> TriangleMesh:
    """创建一个四面体网格用于测试"""
    mesh = TriangleMesh()

    # 四面体的四个顶点
    v0 = mesh.add_vertex(np.array([0.0, 0.0, 0.0]))
    v1 = mesh.add_vertex(np.array([1.0, 0.0, 0.0]))
    v2 = mesh.add_vertex(np.array([0.5, np.sqrt(3)/2, 0.0]))
    v3 = mesh.add_vertex(np.array([0.5, np.sqrt(3)/6, np.sqrt(6)/3]))

    # 四个面
    mesh.add_face(v0, v1, v2)
    mesh.add_face(v0, v1, v3)
    mesh.add_face(v1, v2, v3)
    mesh.add_face(v0, v2, v3)

    return mesh


def create_sphere_mesh(resolution: int = 4) -> TriangleMesh:
    """创建一个球体网格（二十面体细分）用于测试"""
    mesh = TriangleMesh()

    # 二十面体的基础顶点
    phi = (1 + np.sqrt(5)) / 2  # 黄金比例

    vertices = [
        np.array([-1, phi, 0]),
        np.array([1, phi, 0]),
        np.array([-1, -phi, 0]),
        np.array([1, -phi, 0]),
        np.array([0, -1, phi]),
        np.array([0, 1, phi]),
        np.array([0, -1, -phi]),
        np.array([0, 1, -phi]),
        np.array([phi, 0, -1]),
        np.array([phi, 0, 1]),
        np.array([-phi, 0, -1]),
        np.array([-phi, 0, 1])
    ]

    # 归一化到单位球
    vertices = [v / np.linalg.norm(v) for v in vertices]

    vertex_ids = [mesh.add_vertex(v) for v in vertices]

    # 二十面体的面
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]

    for f in faces:
        mesh.add_face(vertex_ids[f[0]], vertex_ids[f[1]], vertex_ids[f[2]])

    return mesh


class TestMeshSimplification:
    """测试网格简化算法"""

    def test_simplification_reduces_faces(self):
        """测试简化减少面数"""
        mesh = create_sphere_mesh()
        original_faces = mesh.num_faces

        simplifier = MeshSimplifier()
        simplified = simplifier.simplify(mesh, target_faces=10)

        assert simplified.num_faces <= original_faces
        assert simplified.num_faces <= 10 + 5  # 允许一些误差

    def test_simplification_preserves_topology(self):
        """测试简化保持拓扑有效性"""
        mesh = create_sphere_mesh()

        simplifier = MeshSimplifier()
        simplified = simplifier.simplify(mesh, target_faces=10)

        # 检查所有面仍然是三角形
        for face in simplified.faces.values():
            assert len(face.vertices) == 3
            # 顶点应该都存在
            for vid in face.vertices:
                assert vid in simplified.vertices

    def test_simplification_no_change_if_target_met(self):
        """测试如果已达到目标面数则不改变"""
        mesh = create_tetrahedron()

        simplifier = MeshSimplifier()
        simplified = simplifier.simplify(mesh, target_faces=100)

        assert simplified.num_faces == mesh.num_faces


class TestLoopSubdivision:
    """测试 Loop 细分算法"""

    def test_subdivision_increases_faces(self):
        """测试细分增加面数"""
        mesh = create_tetrahedron()
        original_faces = mesh.num_faces

        subdivider = LoopSubdivision()
        subdivided = subdivider.subdivide(mesh)

        # 每个三角形应该变成4个
        assert subdivided.num_faces == original_faces * 4

    def test_subdivision_increases_vertices(self):
        """测试细分增加顶点数"""
        mesh = create_tetrahedron()
        original_vertices = mesh.num_vertices

        subdivider = LoopSubdivision()
        subdivided = subdivider.subdivide(mesh)

        # 顶点数应该增加
        assert subdivided.num_vertices > original_vertices

    def test_multiple_subdivisions(self):
        """测试多次细分"""
        mesh = create_tetrahedron()

        subdivider = LoopSubdivision()
        result = subdivider.subdivide_multiple(mesh, iterations=2)

        # 两次细分后面数应该是原来的16倍
        assert result.num_faces == mesh.num_faces * 16

    def test_subdivision_maintains_valid_mesh(self):
        """测试细分保持网格有效性"""
        mesh = create_sphere_mesh()

        subdivider = LoopSubdivision()
        subdivided = subdivider.subdivide(mesh)

        # 检查所有面都是有效的三角形
        for face in subdivided.faces.values():
            assert len(face.vertices) == 3
            for vid in face.vertices:
                assert vid in subdivided.vertices


class TestLaplacianSmoothing:
    """测试拉普拉斯平滑算法"""

    def test_smoothing_maintains_vertices(self):
        """测试平滑保持顶点数不变"""
        mesh = create_sphere_mesh()
        original_vertices = mesh.num_vertices

        smoother = LaplacianSmoother(lambda_factor=0.5)
        smoothed = smoother.smooth(mesh, iterations=5)

        assert smoothed.num_vertices == original_vertices

    def test_smoothing_maintains_faces(self):
        """测试平滑保持面数不变"""
        mesh = create_sphere_mesh()
        original_faces = mesh.num_faces

        smoother = LaplacianSmoother(lambda_factor=0.5)
        smoothed = smoother.smooth(mesh, iterations=5)

        assert smoothed.num_faces == original_faces

    def test_smoothing_changes_positions(self):
        """测试平滑改变顶点位置"""
        mesh = create_sphere_mesh()

        # 保存原始位置
        original_positions = {
            vid: v.position.copy()
            for vid, v in mesh.vertices.items()
        }

        smoother = LaplacianSmoother(lambda_factor=0.5)
        smoothed = smoother.smooth(mesh, iterations=1)

        # 至少有一些顶点位置应该改变
        changed = False
        for vid, vertex in smoothed.vertices.items():
            if not np.allclose(vertex.position, original_positions[vid]):
                changed = True
                break

        assert changed

    def test_smoothing_reduces_noise(self):
        """测试平滑减少局部变化（噪声）"""
        mesh = create_sphere_mesh()

        # 添加噪声
        noisy_mesh = mesh.clone()
        np.random.seed(42)
        for vid, vertex in noisy_mesh.vertices.items():
            noise = np.random.normal(0, 0.05, 3)
            vertex.position += noise

        def compute_local_variation(m):
            """计算局部变化：每个顶点与其相邻顶点平均位置的距离"""
            total = 0.0
            count = 0
            for vid, vertex in m.vertices.items():
                if len(vertex.adjacent_vertices) == 0:
                    continue
                avg = np.zeros(3)
                for adj_vid in vertex.adjacent_vertices:
                    avg += m.vertices[adj_vid].position
                avg /= len(vertex.adjacent_vertices)
                total += np.linalg.norm(vertex.position - avg)
                count += 1
            return total / max(count, 1)

        # 平滑前的局部变化
        variation_before = compute_local_variation(noisy_mesh)

        # 使用小 lambda 和少量迭代平滑
        smoother = LaplacianSmoother(lambda_factor=0.3)
        smoothed = smoother.smooth(noisy_mesh, iterations=3)

        # 平滑后的局部变化应该更小
        variation_after = compute_local_variation(smoothed)
        assert variation_after < variation_before


class TestTaubinSmoothing:
    """测试 Taubin 平滑算法"""

    def test_taubin_preserves_volume(self):
        """测试 Taubin 平滑更好地保持体积"""
        mesh = create_sphere_mesh()

        # 添加噪声
        noisy_mesh = mesh.clone()
        for vid, vertex in noisy_mesh.vertices.items():
            noise = np.random.normal(0, 0.05, 3)
            vertex.position += noise

        # 拉普拉斯平滑
        laplacian = LaplacianSmoother(lambda_factor=0.5)
        laplacian_smoothed = laplacian.smooth(noisy_mesh, iterations=10)

        # Taubin 平滑
        taubin = TaubinSmoother(lambda_factor=0.5, mu_factor=-0.53)
        taubin_smoothed = taubin.smooth(noisy_mesh, iterations=10)

        # 计算质心到原点的平均距离
        def avg_distance_to_origin(m):
            total = sum(
                np.linalg.norm(v.position)
                for v in m.vertices.values()
            )
            return total / m.num_vertices

        original_dist = avg_distance_to_origin(mesh)
        laplacian_dist = avg_distance_to_origin(laplacian_smoothed)
        taubin_dist = avg_distance_to_origin(taubin_smoothed)

        # Taubin 平滑应该更好地保持原始距离
        assert abs(taubin_dist - original_dist) < abs(laplacian_dist - original_dist)


class TestWeightedSmoothing:
    """测试加权平滑算法"""

    def test_uniform_weight(self):
        """测试均匀加权平滑"""
        mesh = create_sphere_mesh()

        smoother = WeightedLaplacianSmoother(lambda_factor=0.5, weight_type='uniform')
        smoothed = smoother.smooth(mesh, iterations=1)

        assert smoothed.num_vertices == mesh.num_vertices
        assert smoothed.num_faces == mesh.num_faces

    def test_area_weight(self):
        """测试面积加权平滑"""
        mesh = create_sphere_mesh()

        smoother = WeightedLaplacianSmoother(lambda_factor=0.5, weight_type='area')
        smoothed = smoother.smooth(mesh, iterations=1)

        assert smoothed.num_vertices == mesh.num_vertices

    def test_cotangent_weight(self):
        """测试余切加权平滑"""
        mesh = create_sphere_mesh()

        smoother = WeightedLaplacianSmoother(lambda_factor=0.5, weight_type='cotangent')
        smoothed = smoother.smooth(mesh, iterations=1)

        assert smoothed.num_vertices == mesh.num_vertices


class TestIntegration:
    """集成测试"""

    def test_simplify_then_subdivide(self):
        """测试先简化再细分"""
        mesh = create_sphere_mesh()
        original_faces = mesh.num_faces

        # 简化
        simplifier = MeshSimplifier()
        simplified = simplifier.simplify(mesh, target_faces=20)

        # 细分
        subdivider = LoopSubdivision()
        subdivided = subdivider.subdivide(simplified)

        # 细分后面数应该增加
        assert subdivided.num_faces > simplified.num_faces

    def test_subdivide_then_smooth(self):
        """测试先细分再平滑"""
        mesh = create_tetrahedron()

        # 细分
        subdivider = LoopSubdivision()
        subdivided = subdivider.subdivide(mesh)

        # 平滑
        smoother = LaplacianSmoother(lambda_factor=0.3)
        smoothed = smoother.smooth(subdivided, iterations=3)

        assert smoothed.num_vertices == subdivided.num_vertices
        assert smoothed.num_faces == subdivided.num_faces

    def test_full_pipeline(self):
        """测试完整处理流程"""
        mesh = create_sphere_mesh()

        # 1. 添加噪声
        for vid, vertex in mesh.vertices.items():
            noise = np.random.normal(0, 0.03, 3)
            vertex.position += noise

        # 2. 平滑去噪
        smoother = LaplacianSmoother(lambda_factor=0.3)
        smoothed = smoother.smooth(mesh, iterations=3)

        # 3. 简化
        simplifier = MeshSimplifier()
        simplified = simplifier.simplify(smoothed, target_faces=20)

        # 4. 细分恢复细节
        subdivider = LoopSubdivision()
        refined = subdivider.subdivide(simplified)

        # 验证结果
        assert refined.num_faces > simplified.num_faces
        assert refined.num_vertices > simplified.num_vertices


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
