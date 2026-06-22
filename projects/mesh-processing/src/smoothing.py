"""网格平滑算法模块

实现拉普拉斯平滑和 Taubin 平滑算法，用于改善网格质量、
减少噪声和提高顶点分布的均匀性。
"""

import numpy as np
from typing import Dict, Optional

from .mesh_data import TriangleMesh


class LaplacianSmoother:
    """拉普拉斯平滑器

    通过将每个顶点向其相邻顶点的平均位置移动来实现平滑。
    新位置 = 旧位置 + lambda * (相邻顶点平均位置 - 旧位置)
    """

    def __init__(self, lambda_factor: float = 0.5):
        """初始化平滑器

        Args:
            lambda_factor: 平滑因子 (0, 1]，越大平滑效果越强
        """
        if not 0 < lambda_factor <= 1.0:
            raise ValueError("lambda_factor 必须在 (0, 1] 之间")
        self.lambda_factor = lambda_factor

    def smooth(self, mesh: TriangleMesh, iterations: int = 1) -> TriangleMesh:
        """执行拉普拉斯平滑

        Args:
            mesh: 输入网格
            iterations: 迭代次数

        Returns:
            平滑后的网格
        """
        result = mesh.clone()

        for _ in range(iterations):
            result = self._smooth_iteration(result)

        result.compute_all_normals()
        return result

    def _smooth_iteration(self, mesh: TriangleMesh) -> TriangleMesh:
        """执行一次平滑迭代

        Args:
            mesh: 输入网格

        Returns:
            平滑后的网格
        """
        new_mesh = mesh.clone()

        # 计算所有顶点的新位置
        new_positions: Dict[int, np.ndarray] = {}

        for vid, vertex in mesh.vertices.items():
            if len(vertex.adjacent_vertices) == 0:
                new_positions[vid] = vertex.position.copy()
                continue

            # 计算相邻顶点的平均位置
            neighbor_sum = np.zeros(3)
            for adj_vid in vertex.adjacent_vertices:
                neighbor_sum += mesh.vertices[adj_vid].position

            avg_position = neighbor_sum / len(vertex.adjacent_vertices)

            # 拉普拉斯平滑公式
            displacement = avg_position - vertex.position
            new_positions[vid] = vertex.position + self.lambda_factor * displacement

        # 更新顶点位置
        for vid, new_pos in new_positions.items():
            if vid in new_mesh.vertices:
                new_mesh.vertices[vid].position = new_pos

        return new_mesh


class TaubinSmoother:
    """Taubin 平滑器

    Taubin 平滑通过交替使用正向和负向拉普拉斯平滑来避免网格收缩。
    lambda > 0 进行收缩，mu < 0 进行膨胀。
    """

    def __init__(self, lambda_factor: float = 0.5, mu_factor: float = -0.53):
        """初始化 Taubin 平滑器

        Args:
            lambda_factor: 正向平滑因子 (0, 1]
            mu_factor: 负向平滑因子，通常为负值
        """
        if not 0 < lambda_factor <= 1.0:
            raise ValueError("lambda_factor 必须在 (0, 1] 之间")
        if mu_factor >= 0:
            raise ValueError("mu_factor 必须为负值")

        self.lambda_factor = lambda_factor
        self.mu_factor = mu_factor

    def smooth(self, mesh: TriangleMesh, iterations: int = 1) -> TriangleMesh:
        """执行 Taubin 平滑

        每次迭代包含两个步骤：
        1. 使用 lambda 进行收缩
        2. 使用 mu 进行膨胀

        Args:
            mesh: 输入网格
            iterations: 迭代次数（每次迭代包含两个步骤）

        Returns:
            平滑后的网格
        """
        result = mesh.clone()

        for _ in range(iterations):
            # 步骤1：收缩
            result = self._smooth_step(result, self.lambda_factor)
            # 步骤2：膨胀
            result = self._smooth_step(result, self.mu_factor)

        result.compute_all_normals()
        return result

    def _smooth_step(self, mesh: TriangleMesh, factor: float) -> TriangleMesh:
        """执行单步平滑

        Args:
            mesh: 输入网格
            factor: 平滑因子

        Returns:
            平滑后的网格
        """
        new_mesh = mesh.clone()
        new_positions: Dict[int, np.ndarray] = {}

        for vid, vertex in mesh.vertices.items():
            if len(vertex.adjacent_vertices) == 0:
                new_positions[vid] = vertex.position.copy()
                continue

            # 计算拉普拉斯向量
            neighbor_sum = np.zeros(3)
            for adj_vid in vertex.adjacent_vertices:
                neighbor_sum += mesh.vertices[adj_vid].position

            avg_position = neighbor_sum / len(vertex.adjacent_vertices)
            laplacian = avg_position - vertex.position

            # 应用平滑因子
            new_positions[vid] = vertex.position + factor * laplacian

        # 更新位置
        for vid, new_pos in new_positions.items():
            if vid in new_mesh.vertices:
                new_mesh.vertices[vid].position = new_pos

        return new_mesh


class WeightedLaplacianSmoother:
    """加权拉普拉斯平滑器

    使用面积加权或角度加权的拉普拉斯平滑，可以提供更好的平滑效果。
    """

    def __init__(self, lambda_factor: float = 0.5, weight_type: str = 'uniform'):
        """初始化加权平滑器

        Args:
            lambda_factor: 平滑因子
            weight_type: 权重类型 'uniform', 'area', 'cotangent'
        """
        if not 0 < lambda_factor <= 1.0:
            raise ValueError("lambda_factor 必须在 (0, 1] 之间")
        if weight_type not in ['uniform', 'area', 'cotangent']:
            raise ValueError("weight_type 必须是 'uniform', 'area' 或 'cotangent'")

        self.lambda_factor = lambda_factor
        self.weight_type = weight_type

    def smooth(self, mesh: TriangleMesh, iterations: int = 1) -> TriangleMesh:
        """执行加权拉普拉斯平滑

        Args:
            mesh: 输入网格
            iterations: 迭代次数

        Returns:
            平滑后的网格
        """
        result = mesh.clone()

        for _ in range(iterations):
            result = self._smooth_iteration(result)

        result.compute_all_normals()
        return result

    def _smooth_iteration(self, mesh: TriangleMesh) -> TriangleMesh:
        """执行一次平滑迭代

        Args:
            mesh: 输入网格

        Returns:
            平滑后的网格
        """
        new_mesh = mesh.clone()
        new_positions: Dict[int, np.ndarray] = {}

        for vid, vertex in mesh.vertices.items():
            if len(vertex.adjacent_vertices) == 0:
                new_positions[vid] = vertex.position.copy()
                continue

            # 根据权重类型计算加权平均位置
            if self.weight_type == 'uniform':
                weighted_pos = self._uniform_weight(mesh, vid)
            elif self.weight_type == 'area':
                weighted_pos = self._area_weight(mesh, vid)
            else:  # cotangent
                weighted_pos = self._cotangent_weight(mesh, vid)

            # 平滑公式
            displacement = weighted_pos - vertex.position
            new_positions[vid] = vertex.position + self.lambda_factor * displacement

        # 更新位置
        for vid, new_pos in new_positions.items():
            if vid in new_mesh.vertices:
                new_mesh.vertices[vid].position = new_pos

        return new_mesh

    def _uniform_weight(self, mesh: TriangleMesh, vertex_id: int) -> np.ndarray:
        """计算均匀加权的平均位置

        Args:
            mesh: 网格
            vertex_id: 顶点ID

        Returns:
            加权平均位置
        """
        vertex = mesh.vertices[vertex_id]
        neighbor_sum = np.zeros(3)

        for adj_vid in vertex.adjacent_vertices:
            neighbor_sum += mesh.vertices[adj_vid].position

        return neighbor_sum / len(vertex.adjacent_vertices)

    def _area_weight(self, mesh: TriangleMesh, vertex_id: int) -> np.ndarray:
        """计算面积加权的平均位置

        Args:
            mesh: 网格
            vertex_id: 顶点ID

        Returns:
            加权平均位置
        """
        vertex = mesh.vertices[vertex_id]
        weighted_sum = np.zeros(3)
        total_weight = 0.0

        for adj_vid in vertex.adjacent_vertices:
            # 计算共享边的面的面积之和作为权重
            weight = 0.0
            edge_faces = mesh.get_edge_faces(vertex_id, adj_vid)

            for face_id in edge_faces:
                face = mesh.faces[face_id]
                v0, v1, v2 = face.vertices
                p0 = mesh.vertices[v0].position
                p1 = mesh.vertices[v1].position
                p2 = mesh.vertices[v2].position

                # 三角形面积
                edge1 = p1 - p0
                edge2 = p2 - p0
                area = np.linalg.norm(np.cross(edge1, edge2)) / 2.0
                weight += area

            weighted_sum += weight * mesh.vertices[adj_vid].position
            total_weight += weight

        if total_weight > 1e-10:
            return weighted_sum / total_weight
        else:
            return vertex.position.copy()

    def _cotangent_weight(self, mesh: TriangleMesh, vertex_id: int) -> np.ndarray:
        """计算余切加权的平均位置

        Args:
            mesh: 网格
            vertex_id: 顶点ID

        Returns:
            加权平均位置
        """
        vertex = mesh.vertices[vertex_id]
        weighted_sum = np.zeros(3)
        total_weight = 0.0

        for adj_vid in vertex.adjacent_vertices:
            weight = self._compute_cotangent_weight(mesh, vertex_id, adj_vid)
            weighted_sum += weight * mesh.vertices[adj_vid].position
            total_weight += weight

        if total_weight > 1e-10:
            return weighted_sum / total_weight
        else:
            return vertex.position.copy()

    def _compute_cotangent_weight(
        self, mesh: TriangleMesh, v0: int, v1: int
    ) -> float:
        """计算两个顶点之间的余切权重

        余切权重 = cot(alpha) + cot(beta)
        其中 alpha 和 beta 是对边的两个角

        Args:
            mesh: 网格
            v0, v1: 两个顶点

        Returns:
            余切权重
        """
        weight = 0.0
        edge_faces = mesh.get_edge_faces(v0, v1)

        for face_id in edge_faces:
            face = mesh.faces[face_id]
            # 找到对边顶点
            opposite_vid = None
            for vid in face.vertices:
                if vid != v0 and vid != v1:
                    opposite_vid = vid
                    break

            if opposite_vid is None:
                continue

            # 计算余切值
            p0 = mesh.vertices[v0].position
            p1 = mesh.vertices[v1].position
            p_opp = mesh.vertices[opposite_vid].position

            # 计算对边顶点处的角的余切
            edge1 = p0 - p_opp
            edge2 = p1 - p_opp

            cos_angle = np.dot(edge1, edge2)
            sin_angle = np.linalg.norm(np.cross(edge1, edge2))

            if sin_angle > 1e-10:
                weight += cos_angle / sin_angle

        return weight
