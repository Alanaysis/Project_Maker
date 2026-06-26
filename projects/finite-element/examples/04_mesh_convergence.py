"""
示例4: 网格收敛性分析 (Mesh Convergence Study)

问题描述:
- 对同一问题使用不同密度的网格进行求解
- 观察结果随网格细化收敛的行为
- 验证FEM解的收敛性

理论背景 (FEM Theory):
- 收敛性条件:
  1. 完备性 (Completeness): 单元能表示刚体位移和常应变
  2. 协调性 (Compatibility): 单元间位移连续
- 收敛速率:
  - CST单元 (线性): ||u - u_h|| ~ O(h)
  - 应变能: ||epsilon - epsilon_h|| ~ O(h^0.5)
- 通过收敛性分析确定合适的网格密度
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mesh import generate_triangular_mesh
from src.elements import cst_stiffness_matrix
from src.assembly import GlobalAssembler
from src.postprocess import compute_stress_cst, von_mises_stress_2d
from src.visualize import plot_convergence


def convergence_study():
    """
    网格收敛性分析 (Mesh convergence study)

    对悬臂梁问题使用不同网格密度求解，观察最大挠度的收敛。
    解析解: delta = P*L^3 / (3*E*I)
    """
    print("=" * 60)
    print("示例4: 网格收敛性分析")
    print("=" * 60)

    # 材料参数 (Material parameters)
    E = 200e9      # 200 GPa
    nu = 0.3       # Poisson's ratio
    thickness = 0.1  # 0.1 m

    # 几何参数 (Geometry)
    L = 4.0    # Length
    H = 1.0    # Height

    # 载荷 (Load)
    P = -1000.0  # Downward force

    # 解析解 (Analytical solution)
    I = thickness * H**3 / 12
    analytical_deflection = abs(P) * L**3 / (3 * E * I)
    print(f"解析解 (Analytical): delta_max = {analytical_deflection:.6e} m")

    # 不同网格尺寸 (Different mesh sizes)
    element_sizes = [1.0, 0.5, 0.25, 0.125, 0.0625]
    results = []
    errors = []

    for elem_size in element_sizes:
        print(f"\n--- 网格尺寸 (Element size): {elem_size} m ---")

        # 生成网格 (Generate mesh)
        nodes, elements = generate_triangular_mesh(L, H, elem_size, "uniform")
        print(f"  节点数 (Nodes): {len(nodes)}")
        print(f"  单元数 (Elements): {len(elements)}")

        # 自由度 (DOFs)
        num_dofs = 2 * len(nodes)

        # 组装 (Assemble)
        assembler = GlobalAssembler(len(nodes), num_dofs_per_node=2)

        for elem in elements:
            elem_nodes = nodes[elem]
            k_elem = cst_stiffness_matrix(elem_nodes, E, nu, thickness)
            assembler.assemble_element(elem, k_elem)

        # 边界条件 (Boundary conditions)
        constraints = {}
        tol = 0.01
        for i, node in enumerate(nodes):
            if abs(node[0]) < tol:
                constraints[2 * i] = 0.0
                constraints[2 * i + 1] = 0.0

        # 载荷 (Load)
        force_vector = np.zeros(num_dofs)
        right_nodes = [i for i, node in enumerate(nodes) if abs(node[0] - L) < tol]
        force_per_node = P / len(right_nodes)
        for node_idx in right_nodes:
            force_vector[2 * node_idx + 1] = force_per_node

        # 求解 (Solve)
        displacement = assembler.solve(force_vector, constraints)

        # 提取最大挠度 (Extract max deflection)
        uy = displacement[1:len(nodes):2]
        max_deflection = abs(np.max(uy))

        # 误差 (Error)
        error = abs(max_deflection - analytical_deflection) / analytical_deflection * 100
        results.append(max_deflection)
        errors.append(error)

        print(f"  最大挠度 (Max deflection): {max_deflection:.6e} m")
        print(f"  误差 (Error): {error:.2f}%")

    # 收敛性分析 (Convergence analysis)
    print("\n" + "=" * 60)
    print("收敛性总结 (Convergence Summary):")
    print("=" * 60)
    print(f"{'网格尺寸':>12} {'节点数':>10} {'挠度(m)':>15} {'误差(%)':>10}")
    print("-" * 50)
    for elem_size, nodes_count, deflection, error in zip(element_sizes,
                                                          [len(generate_triangular_mesh(L, H, s)[0]) for s in element_sizes],
                                                          results, errors):
        print(f"{elem_size:>12.4f} {nodes_count:>10} {deflection:>15.6e} {error:>10.2f}")

    # 绘制收敛曲线 (Plot convergence curve)
    plot_convergence(
        element_sizes, results,
        analytical=analytical_deflection,
        title="Mesh Convergence Study - Cantilever Beam Deflection",
        filename="examples/output/convergence_study.png"
    )

    print("\n收敛性分析完成! (Convergence study complete!)")
    return element_sizes, results, errors


if __name__ == "__main__":
    os.makedirs("examples/output", exist_ok=True)
    convergence_study()
