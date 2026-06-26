"""
网格生成模块 (Mesh Generation Module)

实现2D/3D网格划分功能，包括三角形、四边形、四面体单元。

FEM理论背景:
- 有限元法将连续体离散化为有限个单元
- 网格质量直接影响求解精度和收敛性
- 2D: 三角形(T3/T6)、四边形(Q4/Q8)单元
- 3D: 四面体(T4/T10)、六面体(H8/H20)单元
"""

import numpy as np
from typing import List, Tuple, Optional
import math


def generate_triangular_mesh(
    width: float,
    height: float,
    element_size: float,
    mesh_type: str = "uniform"
) -> Tuple[np.ndarray, List[List[int]]]:
    """
    生成2D三角形网格 (Generate 2D triangular mesh)

    将矩形区域划分为三角形单元。

    参数:
        width: 区域宽度
        height: 区域高度
        element_size: 单元特征尺寸
        mesh_type: 网格类型 ('uniform' 均匀, 'graded' 梯度)

    返回:
        nodes: 节点坐标数组 (N, 2)
        elements: 单元连接表 (M, 3)，每行是三个节点的索引

    FEM原理:
        节点是离散化的自由度位置，单元连接表定义了每个单元包含哪些节点。
        三角形单元有3个节点，每个节点2个平动自由度(ux, uy)。
    """
    nodes = []
    elements = []

    nx = max(int(width / element_size), 1)
    ny = max(int(height / element_size), 1)

    dx = width / nx
    dy = height / ny

    # 生成节点
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = i * dx
            y = j * dy
            if mesh_type == "graded" and ny > 1 and j > ny // 2:
                # 梯度网格: 下半部分节点更密集
                x = i * dx * (1 + 0.5 * (j - ny // 2) / max(ny // 2, 1))
            nodes.append([x, y])

    nodes = np.array(nodes)
    node_count = len(nodes)

    # 生成三角形单元 (每个四边形分为2个三角形)
    for j in range(ny):
        for i in range(nx):
            # 四边形节点索引
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1)
            n3 = n2 + 1

            if mesh_type == "graded" and j > ny // 2:
                # 梯度网格: 使用不同拆分方式
                elements.append([n0, n2, n1])
                elements.append([n1, n2, n3])
            else:
                # 标准对角线拆分
                elements.append([n0, n1, n2])
                elements.append([n1, n3, n2])

    return nodes, elements


def generate_quadrilateral_mesh(
    width: float,
    height: float,
    element_size: float
) -> Tuple[np.ndarray, List[List[int]]]:
    """
    生成2D四边形网格 (Generate 2D quadrilateral mesh)

    参数:
        width: 区域宽度
        height: 区域高度
        element_size: 单元特征尺寸

    返回:
        nodes: 节点坐标数组 (N, 2)
        elements: 单元连接表 (M, 4)，每行是四个节点的索引
    """
    nodes = []
    elements = []

    nx = max(int(width / element_size), 1)
    ny = max(int(height / element_size), 1)

    dx = width / nx
    dy = height / ny

    # 生成节点
    for j in range(ny + 1):
        for i in range(nx + 1):
            nodes.append([i * dx, j * dy])

    nodes = np.array(nodes)

    # 生成四边形单元
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1) + 1
            n3 = n2 + 1
            elements.append([n0, n1, n2, n3])

    return nodes, elements


def generate_tetrahedral_mesh(
    width: float,
    height: float,
    depth: float,
    element_size: float
) -> Tuple[np.ndarray, List[List[int]]]:
    """
    生成3D四面体网格 (Generate 3D tetrahedral mesh)

    将长方体区域划分为四面体单元。

    参数:
        width: X方向尺寸
        height: Y方向尺寸
        depth: Z方向尺寸
        element_size: 单元特征尺寸

    返回:
        nodes: 节点坐标数组 (N, 3)
        elements: 单元连接表 (M, 4)，每行是四个节点的索引
    """
    nodes = []
    elements = []

    nx = max(int(width / element_size), 1)
    ny = max(int(height / element_size), 1)
    nz = max(int(depth / element_size), 1)

    dx = width / nx
    dy = height / ny
    dz = depth / nz

    # 生成节点
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                nodes.append([i * dx, j * dy, k * dz])

    nodes = np.array(nodes)
    node_count = len(nodes)

    # 将每个六面体单元分为6个四面体
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # 六面体8个节点索引 (8 corner nodes of hexahedron)
                n0 = k * (ny + 1) * (nx + 1) + j * (nx + 1) + i       # (i, j, k)
                n1 = n0 + 1                                              # (i+1, j, k)
                n2 = n0 + (nx + 1) + 1                                   # (i+1, j+1, k)
                n3 = n0 + (nx + 1)                                       # (i, j+1, k)
                n4 = n0 + (ny + 1) * (nx + 1)                            # (i, j, k+1)
                n5 = n4 + 1                                              # (i+1, j, k+1)
                n6 = n4 + (nx + 1) + 1                                   # (i+1, j+1, k+1)
                n7 = n4 + (nx + 1)                                       # (i, j+1, k+1)

                # 将六面体分为6个四面体 (split hexahedron into 6 tetrahedra)
                # Each tetrahedron needs 4 nodes
                elements.append([n0, n1, n4, n5])
                elements.append([n0, n4, n5, n7])
                elements.append([n0, n5, n7, n1])
                elements.append([n1, n5, n6, n2])
                elements.append([n1, n6, n5, n7])
                elements.append([n1, n7, n5, n2])

    return nodes, elements


def generate_triangular_mesh_circle(
    radius: float,
    element_size: float,
    center: Tuple[float, float] = (0.0, 0.0),
    mesher: str = "delaunay"
) -> Tuple[np.ndarray, List[List[int]]]:
    """
    在圆形区域内生成三角形网格 (Generate triangular mesh in circular region)

    使用Delaunay三角剖分或均匀网格方法。

    参数:
        radius: 圆半径
        element_size: 单元特征尺寸
        center: 圆心坐标
        mesher: 网格生成方法 ('delaunay' 或 'uniform')

    返回:
        nodes: 节点坐标数组 (N, 2)
        elements: 单元连接表 (M, 3)
    """
    cx, cy = center

    if mesher == "delaunay":
        # 在圆内生成随机点
        num_points = max(int(np.pi * radius**2 / (element_size**2)), 10)
        points = []
        while len(points) < num_points:
            x = cx + np.random.uniform(-radius, radius)
            y = cy + np.random.uniform(-radius, radius)
            if (x - cx)**2 + (y - cy)**2 <= radius**2:
                points.append([x, y])

        # 添加圆周上的点以确保边界精确
        num_boundary = max(int(2 * np.pi * radius / element_size), 8)
        for i in range(num_boundary):
            angle = 2 * np.pi * i / num_boundary
            points.append([cx + radius * np.cos(angle), cy + radius * np.sin(angle)])

        nodes = np.array(points)

        # 使用Delaunay三角剖分
        from scipy.spatial import Delaunay
        tri = Delaunay(nodes)
        elements = tri.simplices.tolist()

        # 过滤掉在圆外的单元
        valid_elements = []
        for elem in elements:
            in_circle = all(
                (nodes[n][0] - cx)**2 + (nodes[n][1] - cy)**2 <= radius**2 + 1e-10
                for n in elem
            )
            if in_circle:
                valid_elements.append(elem)

        return nodes, valid_elements

    else:
        # 均匀网格 + 圆内筛选
        mesh, elements = generate_triangular_mesh(
            2 * radius, 2 * radius, element_size
        )
        # 平移节点到圆心
        mesh[:, 0] += cx
        mesh[:, 1] += cy

        # 筛选圆内的节点
        mask = (mesh[:, 0] - cx)**2 + (mesh[:, 1] - cy)**2 <= radius**2
        valid_nodes = np.where(mask)[0]

        # 重新映射单元
        node_map = {old: new for new, old in enumerate(valid_nodes)}
        valid_elements = []
        for elem in elements:
            if all(n in node_map for n in elem):
                valid_elements.append([node_map[n] for n in elem])

        return mesh[valid_nodes], valid_elements


def refine_mesh(
    nodes: np.ndarray,
    elements: List[List[int]],
    refinement_level: int = 1
) -> Tuple[np.ndarray, List[List[int]]]:
    """
    网格细化 (Mesh refinement)

    通过分割每个单元进行h-型网格细化。

    参数:
        nodes: 节点坐标数组
        elements: 单元连接表
        refinement_level: 细化次数

    返回:
        refined_nodes: 细化后的节点数组
        refined_elements: 细化后的单元连接表
    """
    current_nodes = nodes.copy()
    current_elements = [list(e) for e in elements]

    for _ in range(refinement_level):
        new_nodes = []
        new_elements = []

        # 收集边中点
        edge_midpoints = {}

        for elem in current_elements:
            # 获取单元的三条边
            edges = [(elem[0], elem[1]), (elem[1], elem[2]), (elem[2], elem[0])]
            mid_indices = []

            for edge in edges:
                edge_key = tuple(sorted(edge))
                if edge_key not in edge_midpoints:
                    # 新边中点
                    mid_idx = len(current_nodes) + len(new_nodes)
                    mid = (current_nodes[edge[0]] + current_nodes[edge[1]]) / 2.0
                    edge_midpoints[edge_key] = mid_idx
                    new_nodes.append(mid)
                else:
                    mid_idx = edge_midpoints[edge_key]
                mid_indices.append(mid_idx)

            # 将原单元分为4个子单元
            n0, n1, n2 = elem
            m0, m1, m2 = mid_indices
            new_elements.extend([
                [n0, m0, m2],
                [m0, n1, m1],
                [m2, m1, n2],
                [m0, m1, m2],
            ])

        current_nodes = np.vstack([current_nodes, np.array(new_nodes)]) if new_nodes else current_nodes
        current_elements = new_elements

    return current_nodes, current_elements


def compute_mesh_quality(nodes: np.ndarray, elements: List[List[int]]) -> dict:
    """
    计算网格质量指标 (Compute mesh quality metrics)

    评估网格的雅可比比、纵横比等质量指标。

    参数:
        nodes: 节点坐标数组
        elements: 单元连接表

    返回:
        质量指标字典
    """
    aspect_ratios = []
    jacobians = []

    for elem in elements:
        n0, n1, n2 = nodes[elem[0]], nodes[elem[1]], nodes[elem[2]]

        # 计算边长
        e1 = n1 - n0
        e2 = n2 - n0
        e3 = n2 - n1

        lengths = [np.linalg.norm(e1), np.linalg.norm(e2), np.linalg.norm(e3)]

        # 计算面积 (2D)
        area = 0.5 * abs(e1[0] * e2[1] - e1[1] * e2[0])

        if area > 1e-10 and max(lengths) > 1e-10:
            # 纵横比 (等边三角形为1)
            ar = max(lengths) / (2 * np.sqrt(3) * area / max(lengths))
            aspect_ratios.append(ar)

            # 雅可比比 (接近1表示质量好)
            jacobian = 4 * np.sqrt(3) * area / max(l**2 for l in lengths)
            jacobians.append(jacobian)

    return {
        "min_aspect_ratio": min(aspect_ratios) if aspect_ratios else float("inf"),
        "max_aspect_ratio": max(aspect_ratios) if aspect_ratios else float("inf"),
        "mean_aspect_ratio": np.mean(aspect_ratios) if aspect_ratios else float("inf"),
        "min_jacobian": min(jacobians) if jacobians else 0.0,
        "mean_jacobian": np.mean(jacobians) if jacobians else 0.0,
        "num_elements": len(elements),
        "num_nodes": len(nodes),
    }
