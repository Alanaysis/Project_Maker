"""网格细分算法模块

实现 Loop 细分曲面算法，通过在每个三角形中插入新顶点并调整
现有顶点位置来增加网格的细节和平滑度。
"""

import numpy as np
from typing import Dict, Set, Tuple, List, Optional

from .mesh_data import TriangleMesh, Vertex, Face


class LoopSubdivision:
    """Loop 细分算法

    Loop 细分是一种逼近细分曲面方法，适用于三角网格。
    每次细分将每个三角形分为四个子三角形。
    """

    # Loop 细分的 beta 权重
    # beta = (1/n) * (5/8 - (3/8 + 1/4 * cos(2*pi/n))^2)
    # 对于 n=6（规则顶点），beta ≈ 1/16
    BETA_CACHE: Dict[int, float] = {}

    @classmethod
    def _compute_beta(cls, n: int) -> float:
        """计算 n 度顶点的 beta 权重

        Args:
            n: 顶点的度（相邻顶点数）

        Returns:
            beta 权重值
        """
        if n in cls.BETA_CACHE:
            return cls.BETA_CACHE[n]

        if n == 3:
            beta = 3.0 / 16.0
        else:
            # 通用公式
            alpha = (3.0 / 8.0 + 1.0 / 4.0 * np.cos(2.0 * np.pi / n))
            beta = (1.0 / n) * (5.0 / 8.0 - alpha ** 2)

        cls.BETA_CACHE[n] = beta
        return beta

    def subdivide(self, mesh: TriangleMesh) -> TriangleMesh:
        """执行一次 Loop 细分

        Args:
            mesh: 输入网格

        Returns:
            细分后的网格
        """
        new_mesh = TriangleMesh()

        # 为每个新顶点计算位置
        edge_vertices: Dict[Tuple[int, int], int] = {}  # 边 -> 新顶点ID
        vertex_map: Dict[int, int] = {}  # 旧顶点ID -> 新顶点ID

        # 第一步：计算旧顶点的新位置
        old_positions: Dict[int, np.ndarray] = {}
        for vid, vertex in mesh.vertices.items():
            new_pos = self._compute_new_vertex_position(mesh, vid)
            old_positions[vid] = new_pos

            # 添加到新网格
            new_vid = new_mesh.add_vertex(new_pos)
            vertex_map[vid] = new_vid

        # 第二步：为每条边创建新顶点
        for face in mesh.faces.values():
            v0, v1, v2 = face.vertices
            edges = [
                (min(v0, v1), max(v0, v1)),
                (min(v1, v2), max(v1, v2)),
                (min(v0, v2), max(v0, v2))
            ]

            for edge in edges:
                if edge not in edge_vertices:
                    # 计算边上的新顶点位置
                    new_pos = self._compute_edge_vertex_position(mesh, edge)
                    new_vid = new_mesh.add_vertex(new_pos)
                    edge_vertices[edge] = new_vid

        # 第三步：创建新的三角形面
        for face in mesh.faces.values():
            v0, v1, v2 = face.vertices

            # 获取边上的新顶点
            e01 = edge_vertices[(min(v0, v1), max(v0, v1))]
            e12 = edge_vertices[(min(v1, v2), max(v1, v2))]
            e02 = edge_vertices[(min(v0, v2), max(v0, v2))]

            # 获取旧顶点的新ID
            new_v0 = vertex_map[v0]
            new_v1 = vertex_map[v1]
            new_v2 = vertex_map[v2]

            # 创建四个新三角形
            try:
                new_mesh.add_face(new_v0, e01, e02)
                new_mesh.add_face(new_v1, e12, e01)
                new_mesh.add_face(new_v2, e02, e12)
                new_mesh.add_face(e01, e12, e02)
            except ValueError:
                pass  # 忽略退化面

        # 计算法向量
        new_mesh.compute_all_normals()

        return new_mesh

    def subdivide_multiple(self, mesh: TriangleMesh, iterations: int) -> TriangleMesh:
        """执行多次 Loop 细分

        Args:
            mesh: 输入网格
            iterations: 细分次数

        Returns:
            细分后的网格
        """
        result = mesh.clone()
        for _ in range(iterations):
            result = self.subdivide(result)
        return result

    def _compute_new_vertex_position(
        self, mesh: TriangleMesh, vertex_id: int
    ) -> np.ndarray:
        """计算旧顶点的新位置

        使用 Loop 的权重公式：
        new_pos = (1 - n*beta) * old_pos + beta * sum(neighbors)

        Args:
            mesh: 网格
            vertex_id: 顶点ID

        Returns:
            新位置
        """
        vertex = mesh.vertices[vertex_id]
        n = len(vertex.adjacent_vertices)

        if n == 0:
            return vertex.position.copy()

        beta = self._compute_beta(n)

        # 计算相邻顶点的平均位置
        neighbor_sum = np.zeros(3)
        for adj_vid in vertex.adjacent_vertices:
            neighbor_sum += mesh.vertices[adj_vid].position

        # Loop 权重公式
        new_pos = (1.0 - n * beta) * vertex.position + beta * neighbor_sum

        return new_pos

    def _compute_edge_vertex_position(
        self, mesh: TriangleMesh, edge: Tuple[int, int]
    ) -> np.ndarray:
        """计算边上新顶点的位置

        对于内部边：
        new_pos = 3/8 * (v0 + v1) + 1/8 * (opposite0 + opposite1)

        对于边界边：
        new_pos = 1/2 * (v0 + v1)

        Args:
            mesh: 网格
            edge: 边 (v0, v1)

        Returns:
            新位置
        """
        v0, v1 = edge
        pos0 = mesh.vertices[v0].position
        pos1 = mesh.vertices[v1].position

        # 获取包含这条边的面
        edge_faces = mesh.get_edge_faces(v0, v1)

        if len(edge_faces) == 2:
            # 内部边：找到两个相对的顶点
            opposite_vertices = []
            for face_id in edge_faces:
                face = mesh.faces[face_id]
                for vid in face.vertices:
                    if vid != v0 and vid != v1:
                        opposite_vertices.append(mesh.vertices[vid].position)
                        break

            if len(opposite_vertices) == 2:
                # Loop 内部边权重
                new_pos = (3.0 / 8.0) * (pos0 + pos1) + \
                          (1.0 / 8.0) * (opposite_vertices[0] + opposite_vertices[1])
            else:
                # 回退到中点
                new_pos = (pos0 + pos1) / 2.0
        else:
            # 边界边：使用中点
            new_pos = (pos0 + pos1) / 2.0

        return new_pos
