"""
全局刚度矩阵组装模块 (Global Stiffness Matrix Assembly Module)

将单元刚度矩阵组装为全局刚度矩阵。

FEM理论背景:
- 全局刚度方程: K * U = F
  - K: 全局刚度矩阵 (n_dof x n_dof)
  - U: 节点位移向量 (n_dof x 1)
  - F: 节点力向量 (n_dof x 1)
- 组装过程: 将每个单元刚度矩阵按自由度映射累加到全局矩阵
- 边界条件处理: 约束自由度
- 求解: 线性方程组求解
"""

import numpy as np
from scipy.sparse import lil_matrix, csc_matrix
from scipy.sparse.linalg import spsolve
from typing import List, Tuple, Dict, Optional


class GlobalAssembler:
    """
    全局刚度矩阵组装器 (Global stiffness matrix assembler)

    将单元刚度矩阵组装为全局刚度矩阵，并处理边界条件。

    使用示例:
        assembler = GlobalAssembler(num_nodes, num_dofs_per_node=2)
        assembler.assemble_element(nodes, elements, element_callback)
        assembler.apply_boundary_conditions(constraints, force_vector)
        K = assembler.assemble()
        U = assembler.solve(force_vector)
    """

    def __init__(self, num_nodes: int, num_dofs_per_node: int = 2):
        """
        初始化组装器。

        参数:
            num_nodes: 节点数量
            num_dofs_per_node: 每个节点的自由度数 (2D=2, 3D=3, 梁=3)
        """
        self.num_nodes = num_nodes
        self.num_dofs_per_node = num_dofs_per_node
        self.total_dofs = num_nodes * num_dofs_per_node

        # 使用稀疏矩阵存储 (sparse matrix for efficiency)
        self.K = lil_matrix((self.total_dofs, self.total_dofs))

        # 记录已添加的单元 (track added elements)
        self.elements_added = False

    def _mark_elements_added(self):
        """标记单元已添加 (Mark elements as added)"""
        self.elements_added = True

    def assemble_element(
        self,
        node_indices: List[int],
        element_stiffness: np.ndarray
    ) -> None:
        """
        将单元刚度矩阵组装到全局刚度矩阵 (Assemble element stiffness to global)

        FEM核心步骤: 将局部单元刚度矩阵映射到全局自由度并累加。

        参数:
            node_indices: 单元节点的全局索引列表
            element_stiffness: 单元刚度矩阵 (n_dof x n_dof)
        """
        dof_per_node = self.num_dofs_per_node

        for i_local, node_i in enumerate(node_indices):
            for j_local, node_j in enumerate(node_indices):
                # 计算全局自由度索引
                i_global = dof_per_node * node_i + i_local
                j_global = dof_per_node * node_j + j_local

                # 累加到全局矩阵
                self.K[i_global, j_global] += element_stiffness[i_local, j_local]

        self._mark_elements_added()

    def apply_stress_stiffness(
        self,
        node_indices: List[int],
        element_stiffness: np.ndarray
    ) -> None:
        """
        施加应力刚化 (Apply stress stiffening)

        用于几何非线性分析，考虑应力对刚度的影响。

        参数:
            node_indices: 节点索引
            element_stiffness: 应力刚度矩阵
        """
        self.assemble_element(node_indices, element_stiffness)

    def apply_boundary_conditions(
        self,
        constraints: Dict[int, float],
        force_vector: Optional[np.ndarray] = None
    ) -> None:
        """
        应用边界条件 (Apply boundary conditions)

        使用直接法 (Direct method) 处理位移约束:
        - 对于约束自由度 i 值为 c:
          1. 将力向量修正: F_i += K_i * c
          2. 将第i行和第列置零
          3. 对角元设为1
          4. 力向量第i个分量设为约束值

        参数:
            constraints: {自由度索引: 约束值} 字典
            force_vector: 可选的力向量 (用于修正)
        """
        for dof, value in constraints.items():
            if force_vector is not None:
                # 修正力向量 (correct force vector)
                row = np.array(self.K[dof, :].toarray()).flatten()
                force_vector[dof] += np.dot(row, value * np.ones(len(row)))

            # 将约束自由度的行和列置零
            row = self.K.getrow(dof).toarray()[0]
            col = self.K.getcol(dof).toarray()[:, 0]

            # 保存对角元
            diag_val = self.K[dof, dof]

            # 置零行和列
            self.K[dof, :] = 0.0
            self.K[:, dof] = 0.0

            # 对角元设为1 (保证矩阵非奇异)
            self.K[dof, dof] = diag_val if diag_val != 0 else 1.0

    def assemble(self) -> csc_matrix:
        """
        完成组装并返回压缩稀疏列格式矩阵 (Finalize assembly and return CSC matrix)

        返回:
            K: CSC格式的全局刚度矩阵
        """
        if not self.elements_added:
            raise RuntimeError("No elements have been added. Call assemble_element() first.")

        return self.K.tocsc()

    def solve(
        self,
        force_vector: np.ndarray,
        constraints: Optional[Dict[int, float]] = None
    ) -> np.ndarray:
        """
        求解线性方程组 K*U = F (Solve linear system K*U = F)

        使用稀疏直接求解器。

        参数:
            force_vector: 节点力向量
            constraints: 可选的边界条件

        返回:
            U: 节点位移向量
        """
        K = self.assemble()

        # 创建力向量副本 (work on a copy)
        F = force_vector.copy()

        # 应用边界条件
        if constraints:
            self.apply_boundary_conditions(constraints, F)

        # 求解 K * U = F
        U = spsolve(K, F)

        return U

    def get_reaction_forces(
        self,
        force_vector: np.ndarray,
        displacement_vector: np.ndarray,
        constraints: Dict[int, float]
    ) -> np.ndarray:
        """
        计算反力 (Calculate reaction forces)

        R = K * U - F (for constrained DOFs)

        参数:
            force_vector: 原始力向量
            displacement_vector: 求得的位移向量
            constraints: 约束字典

        返回:
            reactions: 约束自由度的反力
        """
        K = self.assemble()
        reactions = np.zeros(len(constraints))

        for i, (dof, val) in enumerate(constraints.items()):
            reactions[i] = K[dof, :] @ displacement_vector - force_vector[dof]

        return reactions


def assemble_global_stiffness(
    num_nodes: int,
    elements: List[List[int]],
    element_callback,
    num_dofs_per_node: int = 2
) -> Tuple[np.ndarray, int]:
    """
    便捷函数: 组装全局刚度矩阵 (Convenience function to assemble global stiffness)

    参数:
        num_nodes: 节点数
        elements: 单元连接表
        element_callback: 单元刚度计算回调函数 callback(element_nodes) -> stiffness_matrix
        num_dofs_per_node: 每节点自由度数

    返回:
        K: 全局刚度矩阵
        num_constraints: 约束数量（默认0）
    """
    assembler = GlobalAssembler(num_nodes, num_dofs_per_node)

    for elem_nodes in elements:
        k_elem = element_callback(elem_nodes)
        if k_elem is not None:
            assembler.assemble_element(elem_nodes, k_elem)

    K = assembler.assemble()
    return K, 0


def apply_displacement_bc(
    K: np.ndarray,
    F: np.ndarray,
    constraints: Dict[int, float]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    应用位移边界条件 (Apply displacement boundary conditions)

    使用"划行划列"法 (condensation method):
    - 划去约束自由度的行和列
    - 修正力向量

    参数:
        K: 全局刚度矩阵
        F: 力向量
        constraints: {自由度索引: 位移值}

    返回:
        K_reduced: 缩减后的刚度矩阵
        F_reduced: 修正后的力向量
    """
    n = K.shape[0]
    free_dofs = [i for i in range(n) if i not in constraints]
    constrained_dofs = list(constraints.keys())

    # 修正力向量
    F_new = F.copy()
    for dof in constrained_dofs:
        for i, j in enumerate(free_dofs):
            F_new[i] += K[dof, j] * constraints[dof]

    # 提取自由自由度子矩阵
    K_reduced = K[np.ix_(free_dofs, free_dofs)]
    F_reduced = F_new[free_dofs]

    return K_reduced, F_reduced


def solve_with_penalization(
    K: np.ndarray,
    F: np.ndarray,
    constraints: Dict[int, float],
    penalty_factor: float = 1e10
) -> np.ndarray:
    """
    使用罚函数法应用边界条件 (Apply BCs using penalty method)

    对于约束自由度 i 值为 c:
      K[i,i] *= penalty_factor
      F[i] += K[i,i] * c * penalty_factor

    参数:
        K: 全局刚度矩阵
        F: 力向量
        constraints: {自由度索引: 位移值}
        penalty_factor: 罚因子 (越大约束越精确，但可能病态)

    返回:
        U: 位移向量
    """
    K_modified = K.copy()
    F_modified = F.copy()

    # 将稀疏矩阵转换为稠密矩阵 (Convert sparse to dense if needed)
    if hasattr(K_modified, 'toarray'):
        K_modified = K_modified.toarray()

    for dof, value in constraints.items():
        K_modified[dof, dof] *= penalty_factor
        F_modified[dof] += K_modified[dof, dof] * value

    # 求解 (Solve)
    U = np.linalg.solve(K_modified, F_modified)

    return U


def apply_force_to_dof(
    F: np.ndarray,
    dof: int,
    force_value: float
) -> np.ndarray:
    """
    将力施加到指定自由度 (Apply force to a specific DOF)

    参数:
        F: 力向量
        dof: 自由度索引
        force_value: 力值

    返回:
        F: 更新后的力向量
    """
    F[dof] += force_value
    return F


def create_force_vector(
    num_nodes: int,
    num_dofs_per_node: int,
    forces: List[Tuple[int, float]]
) -> np.ndarray:
    """
    创建力向量 (Create force vector)

    参数:
        num_nodes: 节点数
        num_dofs_per_node: 每节点自由度数
        forces: [(自由度索引, 力值), ...] 列表

    返回:
        F: 力向量
    """
    total_dofs = num_nodes * num_dofs_per_node
    F = np.zeros(total_dofs)

    for dof_idx, force_val in forces:
        F[dof_idx] = force_val

    return F
