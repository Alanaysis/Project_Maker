"""网格数据结构模块

实现三角网格的核心数据结构，包括顶点、面和网格类。
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Vertex:
    """顶点类

    Attributes:
        id: 顶点唯一标识符
        position: 三维坐标 [x, y, z]
        normal: 法向量 [nx, ny, nz]
        adjacent_vertices: 相邻顶点ID集合
        adjacent_faces: 相邻面ID集合
    """
    id: int
    position: np.ndarray
    normal: np.ndarray = field(default_factory=lambda: np.zeros(3))
    adjacent_vertices: Set[int] = field(default_factory=set)
    adjacent_faces: Set[int] = field(default_factory=set)

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=np.float64)
        self.normal = np.asarray(self.normal, dtype=np.float64)


@dataclass
class Face:
    """面类（三角形）

    Attributes:
        id: 面唯一标识符
        vertices: 三个顶点ID [v0, v1, v2]
        normal: 面法向量
        adjacent_faces: 相邻面ID集合
    """
    id: int
    vertices: Tuple[int, int, int]
    normal: np.ndarray = field(default_factory=lambda: np.zeros(3))
    adjacent_faces: Set[int] = field(default_factory=set)

    def __post_init__(self):
        self.vertices = tuple(self.vertices)
        self.normal = np.asarray(self.normal, dtype=np.float64)


class TriangleMesh:
    """三角网格类

    核心网格数据结构，存储顶点、面及其拓扑关系。
    """

    def __init__(self):
        self._vertices: Dict[int, Vertex] = {}
        self._faces: Dict[int, Face] = {}
        self._next_vertex_id = 0
        self._next_face_id = 0

    @property
    def vertices(self) -> Dict[int, Vertex]:
        """获取所有顶点"""
        return self._vertices

    @property
    def faces(self) -> Dict[int, Face]:
        """获取所有面"""
        return self._faces

    @property
    def num_vertices(self) -> int:
        """顶点数量"""
        return len(self._vertices)

    @property
    def num_faces(self) -> int:
        """面数量"""
        return len(self._faces)

    @property
    def num_edges(self) -> int:
        """边数量"""
        edges = set()
        for face in self._faces.values():
            v0, v1, v2 = face.vertices
            edges.add((min(v0, v1), max(v0, v1)))
            edges.add((min(v1, v2), max(v1, v2)))
            edges.add((min(v0, v2), max(v0, v2)))
        return len(edges)

    def add_vertex(self, position: np.ndarray) -> int:
        """添加顶点

        Args:
            position: 三维坐标 [x, y, z]

        Returns:
            新顶点的ID
        """
        vertex_id = self._next_vertex_id
        self._next_vertex_id += 1
        self._vertices[vertex_id] = Vertex(id=vertex_id, position=position)
        return vertex_id

    def add_face(self, v0: int, v1: int, v2: int) -> int:
        """添加三角形面

        Args:
            v0, v1, v2: 三个顶点的ID

        Returns:
            新面的ID

        Raises:
            ValueError: 如果顶点不存在或面退化
        """
        for vid in [v0, v1, v2]:
            if vid not in self._vertices:
                raise ValueError(f"顶点 {vid} 不存在")

        if v0 == v1 or v1 == v2 or v0 == v2:
            raise ValueError("退化面：顶点不能重复")

        face_id = self._next_face_id
        self._next_face_id += 1

        face = Face(id=face_id, vertices=(v0, v1, v2))
        self._faces[face_id] = face

        # 更新拓扑关系
        for vid in [v0, v1, v2]:
            self._vertices[vid].adjacent_faces.add(face_id)

        self._vertices[v0].adjacent_vertices.update([v1, v2])
        self._vertices[v1].adjacent_vertices.update([v0, v2])
        self._vertices[v2].adjacent_vertices.update([v0, v1])

        # 更新相邻面关系
        self._update_face_adjacency(face_id)

        # 计算法向量
        self._compute_face_normal(face_id)

        return face_id

    def remove_face(self, face_id: int) -> None:
        """移除面

        Args:
            face_id: 面ID
        """
        if face_id not in self._faces:
            return

        face = self._faces[face_id]

        # 更新顶点的相邻面
        for vid in face.vertices:
            if vid in self._vertices:
                self._vertices[vid].adjacent_faces.discard(face_id)

        # 更新相邻面的相邻面关系
        for adj_face_id in face.adjacent_faces:
            if adj_face_id in self._faces:
                self._faces[adj_face_id].adjacent_faces.discard(face_id)

        del self._faces[face_id]

    def remove_vertex(self, vertex_id: int) -> None:
        """移除顶点及其相邻面

        Args:
            vertex_id: 顶点ID
        """
        if vertex_id not in self._vertices:
            return

        vertex = self._vertices[vertex_id]

        # 移除所有相邻面
        face_ids = list(vertex.adjacent_faces)
        for face_id in face_ids:
            self.remove_face(face_id)

        # 更新相邻顶点
        for adj_vid in vertex.adjacent_vertices:
            if adj_vid in self._vertices:
                self._vertices[adj_vid].adjacent_vertices.discard(vertex_id)

        del self._vertices[vertex_id]

    def get_vertex(self, vertex_id: int) -> Optional[Vertex]:
        """获取顶点"""
        return self._vertices.get(vertex_id)

    def get_face(self, face_id: int) -> Optional[Face]:
        """获取面"""
        return self._faces.get(face_id)

    def get_edge_faces(self, v0: int, v1: int) -> List[int]:
        """获取包含指定边的面

        Args:
            v0, v1: 边的两个顶点ID

        Returns:
            包含该边的面ID列表
        """
        faces_v0 = set(self._vertices[v0].adjacent_faces) if v0 in self._vertices else set()
        faces_v1 = set(self._vertices[v1].adjacent_faces) if v1 in self._vertices else set()
        common_faces = faces_v0 & faces_v1

        result = []
        for face_id in common_faces:
            face = self._faces[face_id]
            if v0 in face.vertices and v1 in face.vertices:
                result.append(face_id)
        return result

    def compute_all_normals(self) -> None:
        """计算所有面和顶点的法向量"""
        # 计算面法向量
        for face_id in self._faces:
            self._compute_face_normal(face_id)

        # 计算顶点法向量
        for vertex_id in self._vertices:
            self._compute_vertex_normal(vertex_id)

    def _compute_face_normal(self, face_id: int) -> None:
        """计算面法向量"""
        face = self._faces[face_id]
        v0 = self._vertices[face.vertices[0]].position
        v1 = self._vertices[face.vertices[1]].position
        v2 = self._vertices[face.vertices[2]].position

        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)

        if norm > 1e-10:
            face.normal = normal / norm
        else:
            face.normal = np.zeros(3)

    def _compute_vertex_normal(self, vertex_id: int) -> None:
        """计算顶点法向量（相邻面法向量的平均）"""
        vertex = self._vertices[vertex_id]
        normal = np.zeros(3)

        for face_id in vertex.adjacent_faces:
            if face_id in self._faces:
                normal += self._faces[face_id].normal

        norm = np.linalg.norm(normal)
        if norm > 1e-10:
            vertex.normal = normal / norm
        else:
            vertex.normal = np.zeros(3)

    def _update_face_adjacency(self, face_id: int) -> None:
        """更新面的相邻面关系"""
        face = self._faces[face_id]
        v0, v1, v2 = face.vertices

        # 查找共享边的面
        edges = [(v0, v1), (v1, v2), (v0, v2)]
        for edge in edges:
            adjacent_faces = self.get_edge_faces(*edge)
            for adj_face_id in adjacent_faces:
                if adj_face_id != face_id:
                    face.adjacent_faces.add(adj_face_id)
                    self._faces[adj_face_id].adjacent_faces.add(face_id)

    def clone(self) -> 'TriangleMesh':
        """深拷贝网格"""
        new_mesh = TriangleMesh()
        new_mesh._next_vertex_id = self._next_vertex_id
        new_mesh._next_face_id = self._next_face_id

        for vid, vertex in self._vertices.items():
            new_mesh._vertices[vid] = Vertex(
                id=vertex.id,
                position=vertex.position.copy(),
                normal=vertex.normal.copy(),
                adjacent_vertices=set(vertex.adjacent_vertices),
                adjacent_faces=set(vertex.adjacent_faces)
            )

        for fid, face in self._faces.items():
            new_mesh._faces[fid] = Face(
                id=face.id,
                vertices=face.vertices,
                normal=face.normal.copy(),
                adjacent_faces=set(face.adjacent_faces)
            )

        return new_mesh

    def get_face_vertices(self, face_id: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """获取面的三个顶点坐标"""
        face = self._faces[face_id]
        v0 = self._vertices[face.vertices[0]].position
        v1 = self._vertices[face.vertices[1]].position
        v2 = self._vertices[face.vertices[2]].position
        return v0, v1, v2
