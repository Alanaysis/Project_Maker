"""网格简化算法模块

实现基于二次误差度量(Quadric Error Metrics, QEM)的网格简化算法。
通过边折叠操作逐步减少网格面数，同时保持网格的整体形状。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import heapq

from .mesh_data import TriangleMesh, Vertex, Face


@dataclass
class EdgeCollapseInfo:
    """边折叠信息"""
    v0: int  # 保留的顶点
    v1: int  # 被移除的顶点
    cost: float  # 折叠代价
    optimal_position: np.ndarray  # 最优位置


class QuadricMatrix:
    """二次误差矩阵

    用于计算边折叠的代价，基于 Garland & Heckbert 1997 的 QEM 算法。
    """

    def __init__(self):
        # 4x4 对称矩阵，存储为上三角部分
        self.matrix = np.zeros((4, 4))

    @classmethod
    def from_vertex(cls, vertex: np.ndarray, normal: np.ndarray) -> 'QuadricMatrix':
        """从顶点和平面创建二次矩阵

        Args:
            vertex: 顶点坐标
            normal: 平面法向量

        Returns:
            二次矩阵
        """
        q = cls()
        # 平面方程: n · (p - v) = 0
        # 即: n.x * x + n.y * y + n.z * z - n · v = 0
        d = -np.dot(normal, vertex)
        v = np.array([normal[0], normal[1], normal[2], d])
        q.matrix = np.outer(v, v)
        return q

    @classmethod
    def from_face(cls, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> 'QuadricMatrix':
        """从三角形面创建二次矩阵

        Args:
            v0, v1, v2: 三角形的三个顶点

        Returns:
            二次矩阵
        """
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)

        if norm < 1e-10:
            return cls()

        normal = normal / norm
        return cls.from_vertex(v0, normal)

    def __add__(self, other: 'QuadricMatrix') -> 'QuadricMatrix':
        """矩阵加法"""
        result = QuadricMatrix()
        result.matrix = self.matrix + other.matrix
        return result

    def __iadd__(self, other: 'QuadricMatrix') -> 'QuadricMatrix':
        """就地矩阵加法"""
        self.matrix += other.matrix
        return self

    def compute_error(self, position: np.ndarray) -> float:
        """计算顶点位置的二次误差

        Args:
            position: 顶点坐标 [x, y, z]

        Returns:
            误差值
        """
        v = np.array([position[0], position[1], position[2], 1.0])
        return float(v @ self.matrix @ v)

    def compute_optimal_position(self) -> Optional[np.ndarray]:
        """计算最优顶点位置

        Returns:
            最优位置，如果矩阵奇异则返回 None
        """
        # 尝试求解线性系统
        m = self.matrix[:3, :3]
        b = -self.matrix[:3, 3]

        try:
            position = np.linalg.solve(m, b)
            return position
        except np.linalg.LinAlgError:
            return None


class MeshSimplifier:
    """网格简化器

    使用二次误差度量(QEM)进行网格简化。
    """

    def __init__(self):
        self._quadrics: Dict[int, QuadricMatrix] = {}

    def simplify(self, mesh: TriangleMesh, target_faces: int) -> TriangleMesh:
        """简化网格

        Args:
            mesh: 输入网格
            target_faces: 目标面数

        Returns:
            简化后的网格
        """
        if target_faces >= mesh.num_faces:
            return mesh.clone()

        # 初始化二次矩阵
        self._initialize_quadrics(mesh)

        # 复制网格用于操作
        result = mesh.clone()

        # 迭代简化
        while result.num_faces > target_faces:
            # 找到最优边折叠
            collapse_info = self._find_best_collapse(result)

            if collapse_info is None:
                break

            # 执行边折叠
            self._perform_collapse(result, collapse_info)

        return result

    def _initialize_quadrics(self, mesh: TriangleMesh) -> None:
        """初始化所有顶点的二次矩阵"""
        self._quadrics.clear()

        # 为每个顶点初始化零矩阵
        for vid in mesh.vertices:
            self._quadrics[vid] = QuadricMatrix()

        # 为每个面累加二次矩阵
        for face in mesh.faces.values():
            v0, v1, v2 = face.vertices
            pos0 = mesh.vertices[v0].position
            pos1 = mesh.vertices[v1].position
            pos2 = mesh.vertices[v2].position

            face_quadric = QuadricMatrix.from_face(pos0, pos1, pos2)

            self._quadrics[v0] += face_quadric
            self._quadrics[v1] += face_quadric
            self._quadrics[v2] += face_quadric

    def _find_best_collapse(self, mesh: TriangleMesh) -> Optional[EdgeCollapseInfo]:
        """找到最优的边折叠操作

        Args:
            mesh: 当前网格

        Returns:
            最优边折叠信息，如果没有可折叠的边则返回 None
        """
        best_cost = float('inf')
        best_collapse = None

        # 遍历所有边
        checked_edges: Set[Tuple[int, int]] = set()

        for face in mesh.faces.values():
            v0, v1, v2 = face.vertices
            edges = [(v0, v1), (v1, v2), (v0, v2)]

            for edge in edges:
                edge_key = (min(edge), max(edge))
                if edge_key in checked_edges:
                    continue
                checked_edges.add(edge_key)

                # 计算折叠代价
                collapse = self._compute_collapse_cost(mesh, edge[0], edge[1])

                if collapse is not None and collapse.cost < best_cost:
                    best_cost = collapse.cost
                    best_collapse = collapse

        return best_collapse

    def _compute_collapse_cost(
        self, mesh: TriangleMesh, v0: int, v1: int
    ) -> Optional[EdgeCollapseInfo]:
        """计算边折叠的代价

        Args:
            mesh: 网格
            v0, v1: 边的两个顶点

        Returns:
            边折叠信息
        """
        if v0 not in self._quadrics or v1 not in self._quadrics:
            return None

        q0 = self._quadrics[v0]
        q1 = self._quadrics[v1]
        q_sum = q0 + q1

        # 尝试计算最优位置
        optimal_pos = q_sum.compute_optimal_position()

        if optimal_pos is not None:
            # 使用最优位置计算代价
            cost = q_sum.compute_error(optimal_pos)
        else:
            # 回退策略：选择代价最小的端点或中点
            pos0 = mesh.vertices[v0].position
            pos1 = mesh.vertices[v1].position
            mid = (pos0 + pos1) / 2.0

            cost0 = q_sum.compute_error(pos0)
            cost1 = q_sum.compute_error(pos1)
            cost_mid = q_sum.compute_error(mid)

            costs = [cost0, cost1, cost_mid]
            positions = [pos0, pos1, mid]
            min_idx = np.argmin(costs)
            cost = costs[min_idx]
            optimal_pos = positions[min_idx]

        return EdgeCollapseInfo(
            v0=v0,
            v1=v1,
            cost=cost,
            optimal_position=optimal_pos
        )

    def _perform_collapse(self, mesh: TriangleMesh, collapse: EdgeCollapseInfo) -> None:
        """执行边折叠操作

        Args:
            mesh: 网格
            collapse: 边折叠信息
        """
        v0 = collapse.v0
        v1 = collapse.v1

        # 获取 v1 的相邻面（不包含 v0 的面需要更新）
        faces_to_remove = []
        faces_to_update = []

        for face_id in mesh.vertices[v1].adjacent_faces:
            face = mesh.faces[face_id]
            if v0 in face.vertices:
                faces_to_remove.append(face_id)
            else:
                faces_to_update.append(face_id)

        # 移除退化面
        for face_id in faces_to_remove:
            mesh.remove_face(face_id)

        # 更新 v0 的位置
        mesh.vertices[v0].position = collapse.optimal_position

        # 更新 v1 相邻面的顶点引用
        for face_id in faces_to_update:
            face = mesh.faces[face_id]
            new_vertices = list(face.vertices)
            for i, vid in enumerate(new_vertices):
                if vid == v1:
                    new_vertices[i] = v0

            # 移除旧面
            mesh.remove_face(face_id)

            # 检查是否形成退化面
            if len(set(new_vertices)) == 3:
                try:
                    # 创建新面
                    mesh.add_face(*new_vertices)
                except ValueError:
                    pass  # 忽略无效面

        # 移除 v1
        if v1 in mesh.vertices:
            # 清理 v1 的相邻关系
            for adj_vid in mesh.vertices[v1].adjacent_vertices:
                if adj_vid in mesh.vertices:
                    mesh.vertices[adj_vid].adjacent_vertices.discard(v1)

            del mesh.vertices[v1]

        # 更新二次矩阵
        if v0 in self._quadrics and v1 in self._quadrics:
            self._quadrics[v0] = self._quadrics[v0] + self._quadrics[v1]
            del self._quadrics[v1]

        # 重新计算法向量
        mesh.compute_all_normals()
