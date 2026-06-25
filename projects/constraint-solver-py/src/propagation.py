"""约束传播模块 - AC-3 和路径相容算法"""

from __future__ import annotations
from typing import Any, Dict, List, Set, Tuple
from collections import deque
from .variable import Variable
from .constraint import Constraint


class AC3:
    """弧相容算法 (AC-3)。

    通过迭代地修订弧来实现弧相容。
    如果某个变量的域变为空，则 CSP 无解。

    Time Complexity: O(e * d^3) 其中 e 是约束数, d 是最大域大小
    """

    def __init__(self) -> None:
        self._steps = 0

    @property
    def steps(self) -> int:
        """返回上次运行的步骤数。"""
        return self._steps

    def propagate(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
    ) -> bool:
        """执行 AC-3 传播。

        Args:
            variables: 变量名字典
            constraints: 约束列表

        Returns:
            True 如果传播成功 (域非空), False 如果发现无解
        """
        self._steps = 0

        # 构建邻接图: variable_name -> list of (constraint, neighbor)
        neighbors: Dict[str, List[Tuple[Constraint, Variable]]] = {
            name: [] for name in variables
        }
        for constraint in constraints:
            for var in constraint.variables:
                for neighbor in constraint.get_neighbors(var):
                    neighbors[var.name].append((constraint, neighbor))

        # 初始化队列: 所有弧 (xi, xj)
        queue: deque[Tuple[Variable, Variable, Constraint]] = deque()
        for constraint in constraints:
            for i, vi in enumerate(constraint.variables):
                for j, vj in enumerate(constraint.variables):
                    if i != j:
                        queue.append((vi, vj, constraint))

        # 迭代修订
        while queue:
            xi, xj, constraint = queue.popleft()
            self._steps += 1

            if self._revise(xi, xj, constraint):
                if xi.domain.is_empty():
                    return False  # 无解

                # 将涉及 xi 的其他弧加入队列
                for c, neighbor in neighbors[xi.name]:
                    if neighbor.name != xj.name:
                        queue.append((neighbor, xi, c))

        return True

    def _revise(
        self, xi: Variable, xj: Variable, constraint: Constraint
    ) -> bool:
        """修订弧 (xi, xj)。"""
        return constraint.revise(xi, xj)

    def propagate_with_assignment(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
        assignment: Dict[str, Any],
    ) -> bool:
        """带赋值的 AC-3 传播。

        只传播与已赋值变量相关的弧。
        """
        self._steps = 0

        queue: deque[Tuple[Variable, Variable, Constraint]] = deque()

        # 将涉及已赋值变量的弧加入队列
        for constraint in constraints:
            for var in constraint.variables:
                if var.name in assignment:
                    for neighbor in constraint.get_neighbors(var):
                        if neighbor.name not in assignment:
                            queue.append((neighbor, var, constraint))

        while queue:
            xi, xj, constraint = queue.popleft()
            self._steps += 1

            if self._revise(xi, xj, constraint):
                if xi.domain.is_empty():
                    return False

                for constraint2 in constraints:
                    if xi in constraint2.variables:
                        for neighbor in constraint2.get_neighbors(xi):
                            if neighbor.name != xj.name and neighbor.name not in assignment:
                                queue.append((neighbor, xi, constraint2))

        return True


class PathConsistency:
    """路径相容算法 (PC-2)。

    比弧相容更强的相容性，确保任意两个变量之间的值对
    都能通过第三个变量扩展为一致的三元组。

    Time Complexity: O(n^3 * d^3)
    """

    def __init__(self) -> None:
        self._steps = 0

    @property
    def steps(self) -> int:
        """返回上次运行的步骤数。"""
        return self._steps

    def propagate(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
    ) -> bool:
        """执行路径相容传播。

        Args:
            variables: 变量名字典
            constraints: 约束列表

        Returns:
            True 如果传播成功, False 如果发现无解
        """
        self._steps = 0

        var_list = list(variables.values())
        n = len(var_list)

        # 构建约束图
        constraint_map: Dict[Tuple[str, str], List[Constraint]] = {}
        for c in constraints:
            for i, vi in enumerate(c.variables):
                for j, vj in enumerate(c.variables):
                    if i != j:
                        key = (vi.name, vj.name)
                        if key not in constraint_map:
                            constraint_map[key] = []
                        constraint_map[key].append(c)

        # 初始化队列
        queue: deque[Tuple[Variable, Variable, Variable]] = deque()
        for i in range(n):
            for j in range(n):
                if i != j:
                    for k in range(n):
                        if k != i and k != j:
                            queue.append((var_list[i], var_list[j], var_list[k]))

        while queue:
            xi, xj, xk = queue.popleft()
            self._steps += 1

            if self._enforce_pc(xi, xj, xk, constraint_map):
                if xi.domain.is_empty():
                    return False

                # 重新加入受影响的三元组
                for m in range(n):
                    var_m = var_list[m]
                    if var_m.name not in (xi.name, xj.name, xk.name):
                        queue.append((var_m, xi, xj))

        return True

    def _enforce_pc(
        self,
        xi: Variable,
        xj: Variable,
        xk: Variable,
        constraint_map: Dict[Tuple[str, str], List[Constraint]],
    ) -> bool:
        """强制路径相容: 确保 R_ij 通过 xk 有支持。"""
        revised = False

        # 获取相关约束
        c_ij = constraint_map.get((xi.name, xj.name), [])
        c_ik = constraint_map.get((xi.name, xk.name), [])
        c_kj = constraint_map.get((xk.name, xj.name), [])

        if not c_ik or not c_kj:
            return False

        values_to_remove = []

        for val_i in xi.domain:
            supported = False
            for val_k in xk.domain:
                # 检查 (xi=val_i, xk=val_k) 是否满足 c_ik
                ik_ok = True
                for c in c_ik:
                    test = {xi.name: val_i, xk.name: val_k}
                    if not c.is_satisfied(test):
                        ik_ok = False
                        break

                if not ik_ok:
                    continue

                for val_j in xj.domain:
                    # 检查 (xk=val_k, xj=val_j) 是否满足 c_kj
                    kj_ok = True
                    for c in c_kj:
                        test = {xk.name: val_k, xj.name: val_j}
                        if not c.is_satisfied(test):
                            kj_ok = False
                            break

                    if not kj_ok:
                        continue

                    # 检查 (xi=val_i, xj=val_j) 是否满足 c_ij
                    ij_ok = True
                    for c in c_ij:
                        test = {xi.name: val_i, xj.name: val_j}
                        if not c.is_satisfied(test):
                            ij_ok = False
                            break

                    if ij_ok:
                        supported = True
                        break

                if supported:
                    break

            if not supported:
                values_to_remove.append(val_i)

        for val in values_to_remove:
            xi.domain.remove(val)
            revised = True

        return revised
