"""
示例1: 2D悬臂梁弯曲模拟 (2D Cantilever Beam Bending Simulation)

问题描述:
- 悬臂梁: 左端固定，右端受集中载荷
- 使用CST三角形单元进行平面应力分析
- 对比FEM结果与弹性力学解析解

理论背景 (FEM Theory):
- Euler-Bernoulli梁理论: delta_max = P*L^3 / (3*E*I)
- 平面应力假设: sigma_z = tau_xz = tau_yz = 0
- CST单元: 常应变三角形单元，适合初步分析
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh import generate_triangular_mesh, refine_mesh
from src.elements import cst_stiffness_matrix, plane_stress_matrix
from src.assembly import GlobalAssembler, create_force_vector
from src.postprocess import compute_stress_cst, von_mises_stress_2d
from src.visualize import (
    plot_mesh, plot_displacement, plot_stress,
    create_visualization_dashboard
)


def cantilever_beam():
    """
    悬臂梁弯曲模拟 (Cantilever beam bending simulation)

    几何: 长L=4m，高H=1m的矩形梁
    边界条件: 左端完全固定 (ux=uy=0)
    载荷: 右端受向下集中力 P = 1000 N
    材料: E = 200 GPa (钢), nu = 0.3
    """
    print("=" * 60)
    print("示例1: 2D悬臂梁弯曲模拟")
    print("=" * 60)

    # 材料参数 (Material parameters)
    E = 200e9      # 杨氏模量 200 GPa (Young's modulus)
    nu = 0.3       # 泊松比 (Poisson's ratio)
    thickness = 0.1  # 厚度 0.1 m (Thickness)

    # 几何参数 (Geometry)
    L = 4.0    # 长度 (Length)
    H = 1.0    # 高度 (Height)

    # 网格参数 (Mesh)
    element_size = 0.5
    nodes, elements = generate_triangular_mesh(L, H, element_size, "uniform")
    print(f"网格信息 (Mesh info):")
    print(f"  节点数 (Nodes): {len(nodes)}")
    print(f"  单元数 (Elements): {len(elements)}")

    # 自由度
    num_dofs = 2 * len(nodes)

    # 组装全局刚度矩阵 (Assemble global stiffness matrix)
    assembler = GlobalAssembler(len(nodes), num_dofs_per_node=2)

    for elem in elements:
        elem_nodes = nodes[elem]
        k_elem = cst_stiffness_matrix(elem_nodes, E, nu, thickness)
        assembler.assemble_element(elem, k_elem)

    # 边界条件 (Boundary conditions)
    # 左端固定: x=0 处的所有节点 ux=uy=0
    constraints = {}
    tolerance = 0.01
    for i, node in enumerate(nodes):
        if abs(node[0]) < tolerance:  # 左端节点
            constraints[2 * i] = 0.0    # ux = 0
            constraints[2 * i + 1] = 0.0  # uy = 0

    print(f"\n约束数量 (Number of constraints): {len(constraints)}")

    # 载荷 (Loads)
    # 右端受向下集中力 P = 1000 N
    force_vector = np.zeros(num_dofs)
    # 在右端施加力 (apply force at right end)
    right_nodes = []
    for i, node in enumerate(nodes):
        if abs(node[0] - L) < tolerance:
            right_nodes.append(i)

    # 将力分配到右端节点 (distribute force to right-end nodes)
    P = -1000.0  # 向下的力 (Downward force)
    force_per_node = P / len(right_nodes)
    for node_idx in right_nodes:
        force_vector[2 * node_idx + 1] = force_per_node  # uy方向 (y-direction)

    print(f"施加的力 (Applied force): {P} N (downward)")

    # 求解 (Solve)
    print("\n求解中... (Solving...)")
    displacement = assembler.solve(force_vector, constraints)

    # 提取位移 (Extract displacements)
    ux = displacement[0:len(nodes):2]
    uy = displacement[1:len(nodes):2]

    # 最大位移 (Max displacement)
    max_disp = np.sqrt(np.max(ux**2) + np.max(uy**2))
    max_uy_idx = np.argmax(np.abs(uy))
    print(f"\n最大位移 (Max displacement):")
    print(f"  |u|_max = {max_disp:.6e} m")
    print(f"  最大挠度 (Max deflection): {uy[max_uy_idx]:.6e} m (at x={nodes[max_uy_idx][0]:.3f})")

    # 与解析解对比 (Compare with analytical solution)
    # delta_max = P*L^3 / (3*E*I)
    I = thickness * H**3 / 12  # 截面惯性矩 (Moment of inertia)
    analytical_deflection = abs(P) * L**3 / (3 * E * I)
    print(f"\n解析解 (Analytical solution):")
    print(f"  delta_max = P*L^3/(3*E*I) = {analytical_deflection:.6e} m")
    error = abs(uy[max_uy_idx] - analytical_deflection) / analytical_deflection * 100
    print(f"  误差 (Error): {error:.2f}%")

    # 应力分析 (Stress analysis)
    print("\n应力分析 (Stress analysis):")
    element_stresses = []
    element_disp = []
    for elem in elements:
        elem_nodes = nodes[elem]
        elem_disp_local = displacement[[2*i for i in elem] + [2*i+1 for i in elem]]
        stress = compute_stress_cst(elem_nodes, elem_disp_local, E, nu, "plane_stress")
        element_stresses.append(stress)
        element_disp.append(elem_disp_local)

    # Von Mises应力
    von_mises = [von_mises_stress_2d(s[0], s[1], s[2]) for s in element_stresses]
    max_vm = max(von_mises)
    print(f"  Von Mises应力最大值 (Max Von Mises stress): {max_vm:.2f} Pa")
    print(f"  Von Mises应力最大值 (Max Von Mises stress): {max_vm/1e6:.2f} MPa")

    # 可视化 (Visualization)
    print("\n生成可视化... (Generating visualizations...)")
    create_visualization_dashboard(
        nodes, elements, displacement, element_stresses,
        output_prefix="examples/output/cantilever_beam"
    )

    print("\n示例1完成! (Example 1 complete!)")
    return nodes, elements, displacement, element_stresses


if __name__ == "__main__":
    os.makedirs("examples/output", exist_ok=True)
    cantilever_beam()
