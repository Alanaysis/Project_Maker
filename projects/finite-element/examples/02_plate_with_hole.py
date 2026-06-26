"""
示例2: 带孔平板应力集中 (Plate with Hole Stress Concentration)

问题描述:
- 无限大平板中的小孔在远场拉伸下的应力集中
- 理论应力集中系数 Kt = 3 (无限大板)
- 有限板需要修正

理论背景 (FEM Theory):
- 应力集中: 几何不连续处应力局部增大的现象
- 应力集中系数: Kt = sigma_max / sigma_nominal
- 对于圆孔: Kt ≈ 3 (无限大板，单向拉伸)
- 有限板: Kt = 3.0 - 3.14*(d/W) + 3.667*(d/W)^2 - 1.53*(d/W)^3
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh import generate_triangular_mesh_circle, refine_mesh
from src.elements import cst_stiffness_matrix
from src.assembly import GlobalAssembler
from src.postprocess import compute_stress_cst, von_mises_stress_2d
from src.visualize import plot_mesh, plot_stress, create_visualization_dashboard


def plate_with_hole():
    """
    带孔平板应力集中分析 (Plate with hole stress concentration analysis)

    几何: 100x100mm平板，中心有20mm直径圆孔
    边界条件: 左端固定，右端施加拉伸位移
    材料: E = 200 GPa, nu = 0.3
    """
    print("=" * 60)
    print("示例2: 带孔平板应力集中")
    print("=" * 60)

    # 材料参数 (Material parameters)
    E = 200e9      # 200 GPa
    nu = 0.3       # Poisson's ratio
    thickness = 1.0  # 1 mm (thickness)

    # 几何参数 (Geometry)
    plate_size = 100.0  # mm
    hole_radius = 10.0  # mm (20mm diameter hole)

    # 使用圆形网格生成器 (Use circular mesh generator)
    element_size = 5.0
    nodes, elements = generate_triangular_mesh_circle(
        hole_radius, element_size,
        center=(0, 0),
        mesher="delaunay"
    )

    # 扩展为方形板 (Expand to square plate)
    # 只保留在板内的节点和单元
    half_width = plate_size / 2
    valid_mask = (
        (nodes[:, 0] >= -half_width) & (nodes[:, 0] <= half_width) &
        (nodes[:, 1] >= -half_width) & (nodes[:, 1] <= half_width) &
        (nodes[:, 0]**2 + nodes[:, 1]**2 >= hole_radius**2 - 1e-6)
    )

    valid_indices = np.where(valid_mask)[0]
    node_map = {old: new for new, old in enumerate(valid_indices)}
    refined_nodes = nodes[valid_indices]

    refined_elements = []
    for elem in elements:
        if all(n in node_map for n in elem):
            refined_elements.append([node_map[n] for n in elem])

    nodes = refined_nodes
    elements = refined_elements

    print(f"网格信息 (Mesh info):")
    print(f"  节点数 (Nodes): {len(nodes)}")
    print(f"  单元数 (Elements): {len(elements)}")

    # 网格可视化 (Mesh visualization)
    plot_mesh(nodes, elements, title="Plate with Hole Mesh",
              filename="examples/output/plate_hole_mesh.png", figsize=(8, 8))

    # 自由度 (DOFs)
    num_dofs = 2 * len(nodes)

    # 组装刚度矩阵 (Assemble stiffness)
    assembler = GlobalAssembler(len(nodes), num_dofs_per_node=2)

    for elem in elements:
        elem_nodes = nodes[elem]
        k_elem = cst_stiffness_matrix(elem_nodes, E, nu, thickness)
        assembler.assemble_element(elem, k_elem)

    # 边界条件 (Boundary conditions)
    constraints = {}
    tol = 1.0  # tolerance in mm

    # 左端固定 (Left end fixed)
    for i, node in enumerate(nodes):
        if abs(node[0] + half_width) < tol:
            constraints[2 * i] = 0.0
            constraints[2 * i + 1] = 0.0

    # 右端施加位移 (Apply displacement at right end)
    # 施加一个小的拉伸位移来产生应力
    applied_disp = 0.1  # mm
    for i, node in enumerate(nodes):
        if abs(node[0] - half_width) < tol:
            constraints[2 * i] = applied_disp  # ux = 0.1 mm
            # uy自由 (uy free)

    print(f"约束数量 (Number of constraints): {len(constraints)}")

    # 力向量为零 (Force vector is zero - displacement-driven)
    force_vector = np.zeros(num_dofs)

    # 求解 (Solve)
    print("\n求解中... (Solving...)")
    displacement = assembler.solve(force_vector, constraints)

    # 应力分析 (Stress analysis)
    element_stresses = []
    for elem in elements:
        elem_nodes = nodes[elem]
        dof_indices = [2*n for n in elem] + [2*n+1 for n in elem]
        elem_disp = displacement[dof_indices]
        stress = compute_stress_cst(elem_nodes, elem_disp, E, nu, "plane_stress")
        element_stresses.append(stress)

    # Von Mises应力
    von_mises = [von_mises_stress_2d(s[0], s[1], s[2]) for s in element_stresses]
    max_vm = max(von_mises)

    print(f"\nVon Mises应力最大值 (Max Von Mises stress): {max_vm/1e6:.2f} MPa")

    # 名义应力 (Nominal stress)
    # sigma_nom = E * epsilon = E * (applied_disp / plate_width)
    sigma_nom = E * (applied_disp / plate_size) / 1e6  # MPa
    Kt = max_vm / E * plate_size / applied_disp if applied_disp > 0 else 0

    # 理论Kt (理论值对于圆孔≈3)
    print(f"名义应力 (Nominal stress): {sigma_nom:.2f} MPa")
    print(f"应力集中系数 (Stress concentration factor): Kt ≈ {Kt:.2f}")
    print(f"理论值 (Theoretical): Kt ≈ 3.0 (无限大板)")

    # 可视化 (Visualization)
    print("\n生成可视化... (Generating visualizations...)")
    create_visualization_dashboard(
        nodes, elements, displacement, element_stresses,
        output_prefix="examples/output/plate_hole"
    )

    # 绘制应力云图 (Plot stress contour)
    plot_stress(nodes, elements, element_stresses, stress_type="von_mises",
                title="Von Mises Stress - Plate with Hole",
                filename="examples/output/plate_hole_stress.png",
                figsize=(10, 10))

    print("\n示例2完成! (Example 2 complete!)")
    return nodes, elements, displacement, element_stresses


if __name__ == "__main__":
    os.makedirs("examples/output", exist_ok=True)
    plate_with_hole()
