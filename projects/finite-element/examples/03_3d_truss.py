"""
示例3: 3D桁架分析 (3D Truss Analysis)

问题描述:
- 空间桁架结构分析
- 使用3D桁架单元 (每个节点3个自由度)
- 计算节点位移、杆件内力和反力

理论背景 (FEM Theory):
- 桁架单元只承受轴向力 (truss elements carry only axial force)
- 杆件内力: N = EA/L * (delta_L)
- 3D桁架刚度矩阵: 6x6 (每个节点3个自由度)
- 节点平衡: sum(F_external) + sum(F_member) = 0
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.elements import truss_3d_stiffness_matrix
from src.assembly import GlobalAssembler
from src.postprocess import von_mises_stress_3d
from src.visualize import plot_mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def space_truss():
    """
    3D空间桁架分析 (3D space truss analysis)

    结构: 四面体桁架 (Tetrahedral truss)
    - 节点: 4个顶点 (4 vertices)
    - 杆件: 6条边 (6 members)
    - 载荷: 顶部节点受垂直力 (Load at top node)
    - 支撑: 底部3个节点固定 (Supports at base nodes)
    """
    print("=" * 60)
    print("示例3: 3D桁架分析")
    print("=" * 60)

    # 材料参数 (Material parameters)
    E = 200e9      # 200 GPa
    A = 1e-4       # 截面积 100 mm^2 (Cross-sectional area)

    # 节点坐标 (Node coordinates) - 四面体 (Tetrahedron)
    # 底面: 等边三角形，顶部: 顶点
    L = 2.0  # 边长 (Edge length)
    nodes = np.array([
        [0, 0, 0],          # Node 0: 底面顶点1
        [L, 0, 0],          # Node 1: 底面顶点2
        [L/2, L*np.sqrt(3)/2, 0],  # Node 2: 底面顶点3
        [L/2, L*np.sqrt(3)/6, L*np.sqrt(2/3)],  # Node 3: 顶部
    ])

    # 单元连接 (Element connectivity) - 6条边 (6 edges of tetrahedron)
    elements = [
        [0, 1],  # 底边1 (Base edge 1)
        [1, 2],  # 底边2 (Base edge 2)
        [2, 0],  # 底边3 (Base edge 3)
        [0, 3],  # 侧边1 (Side edge 1)
        [1, 3],  # 侧边2 (Side edge 2)
        [2, 3],  # 侧边3 (Side edge 3)
    ]

    print("结构几何 (Structure geometry):")
    print(f"  节点数 (Nodes): {len(nodes)}")
    print(f"  杆件数 (Members): {len(elements)}")
    print("\n节点坐标 (Node coordinates):")
    for i, node in enumerate(nodes):
        print(f"  Node {i}: ({node[0]:.3f}, {node[1]:.3f}, {node[2]:.3f}) m")

    # 自由度 (DOFs)
    num_dofs = 3 * len(nodes)

    # 组装刚度矩阵 (Assemble stiffness)
    assembler = GlobalAssembler(len(nodes), num_dofs_per_node=3)

    member_forces = []
    for elem in elements:
        elem_nodes = nodes[elem]
        k_elem = truss_3d_stiffness_matrix(E, A, elem_nodes)
        assembler.assemble_element(elem, k_elem)

        # 计算杆件长度
        L_elem = np.linalg.norm(elem_nodes[1] - elem_nodes[0])
        member_forces.append(L_elem)

    print(f"\n杆件长度 (Member lengths):")
    for i, L_elem in enumerate(member_forces):
        print(f"  Member {i}: {L_elem:.4f} m")

    # 边界条件 (Boundary conditions)
    constraints = {}
    # 底部3个节点完全固定 (Fix bottom 3 nodes)
    for i in range(3):
        for j in range(3):
            constraints[3 * i + j] = 0.0

    # 载荷 (Loads)
    # 顶部节点受垂直向下的力 (Downward force at top node)
    force_vector = np.zeros(num_dofs)
    P = -10000.0  # 10 kN downward
    force_vector[3 * 3 + 2] = P  # Node 3, z-direction

    print(f"\n约束数量 (Number of constraints): {len(constraints)}")
    print(f"施加的力 (Applied load): {P/1000:.1f} kN at top node (downward)")

    # 求解 (Solve)
    print("\n求解中... (Solving...)")
    displacement = assembler.solve(force_vector, constraints)

    # 提取节点位移 (Extract nodal displacements)
    print("\n节点位移 (Nodal displacements):")
    for i in range(len(nodes)):
        ux = displacement[3*i]
        uy = displacement[3*i + 1]
        uz = displacement[3*i + 2]
        disp_mag = np.sqrt(ux**2 + uy**2 + uz**2)
        print(f"  Node {i}: ux={ux*1e3:.4f} mm, uy={uy*1e3:.4f} mm, uz={uz*1e3:.4f} mm (|u|={disp_mag*1e3:.4f} mm)")

    # 杆件内力 (Member forces)
    print("\n杆件内力 (Member forces):")
    max_stress = 0
    for idx, elem in enumerate(elements):
        elem_nodes = nodes[elem]
        dof_indices = [3*n + j for n in elem for j in range(3)]
        elem_disp = displacement[dof_indices]

        # 杆件轴向变形 (Axial deformation)
        L_elem = member_forces[idx]
        direction = (elem_nodes[1] - elem_nodes[0]) / L_elem

        # 轴向位移差 (Axial displacement difference)
        delta = np.dot(elem_disp[3:] - elem_disp[:3], direction)

        # 轴力 (Axial force): N = EA/L * delta
        N = E * A / L_elem * delta

        # 应力 (Stress)
        sigma = N / A

        member_type = "Tension (拉)" if N > 0 else "Compression (压)"
        print(f"  Member {elem[0]}-{elem[1]}: N={N/1000:.2f} kN ({member_type}), sigma={sigma/1e6:.2f} MPa")

        max_stress = max(max_stress, abs(sigma))

    print(f"\n最大应力 (Max stress): {max_stress/1e6:.2f} MPa")

    # 反力 (Reaction forces)
    reactions = assembler.get_reaction_forces(force_vector, displacement, constraints)
    print("\n支座反力 (Reaction forces):")
    for i, (dof, val) in enumerate(constraints.items()):
        node_idx = dof // 3
        dir_name = ['Fx', 'Fy', 'Fz'][dof % 3]
        print(f"  Node {node_idx} {dir_name}: {reactions[i]/1000:.2f} kN")

    # 可视化 (Visualization)
    print("\n生成可视化... (Generating visualization...)")
    plot_mesh(nodes, elements, title="3D Space Truss",
              filename="examples/output/space_truss_mesh.png",
              show_nodes=True, show_elements=True, figsize=(8, 8))

    # 3D可视化 (3D visualization)
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制杆件 (Draw members)
    for elem in elements:
        elem_nodes = nodes[elem]
        ax.plot3D(elem_nodes[:, 0], elem_nodes[:, 1], elem_nodes[:, 2], 'k-', linewidth=2)

    # 节点 (Nodes)
    ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], c='red', s=100, label='Nodes')

    # 变形示意 (Deformed shape)
    scale = 1000  # 放大变形 (Amplify deformation)
    deformed = nodes.copy()
    for i in range(len(nodes)):
        deformed[i] += scale * np.array([
            displacement[3*i],
            displacement[3*i + 1],
            displacement[3*i + 2]
        ])

    for elem in elements:
        elem_nodes = deformed[elem]
        ax.plot3D(elem_nodes[:, 0], elem_nodes[:, 1], elem_nodes[:, 2], 'r--', linewidth=1, alpha=0.5)

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('3D Space Truss (Red dashed: deformed)')
    ax.legend()

    plt.tight_layout()
    fig.savefig("examples/output/space_truss_3d.png", dpi=150, bbox_inches='tight')
    plt.close(fig)

    print("\n示例3完成! (Example 3 complete!)")
    return nodes, elements, displacement


if __name__ == "__main__":
    os.makedirs("examples/output", exist_ok=True)
    space_truss()
