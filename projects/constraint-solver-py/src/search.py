"""搜索模块 - 回溯搜索 + MRV + 度启发式"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Set
from .variable import Variable
from .domain import Domain
from .constraint import Constraint
from .propagation import AC3


class BacktrackingSearch:
    """带回溯的深度优先搜索。

    集成了以下启发式:
    - MRV (最小剩余值): 优先选择域最小的变量
    - 度启发式: MRV 平局时选择约束最多的变量
    - LCV (最小约束值): 优先尝试对邻居约束最小的值

    Attributes:
        nodes_expanded: 搜索树中扩展的节点数
        backtrack_count: 回溯次数
    """

    def __init__(self, use_ac3: bool = True, use_lcv: bool = False) -> None:
        self.use_ac3 = use_ac3
        self.use_lcv = use_lcv
        self.nodes_expanded = 0
        self.backtrack_count = 0
        self._ac3 = AC3()

    def solve(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
        assignment: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """执行回溯搜索求解 CSP。

        Args:
            variables: 变量名字典
            constraints: 约束列表
            assignment: 初始赋值 (可选)

        Returns:
            完整赋值字典，或 None 表示无解
        """
        self.nodes_expanded = 0
        self.backtrack_count = 0

        if assignment is None:
            assignment = {}

        # 初始 AC-3 传播
        if self.use_ac3:
            if not self._ac3.propagate(variables, constraints):
                return None

        return self._backtrack(variables, constraints, assignment)

    def _backtrack(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
        assignment: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """递归回溯搜索。"""
        self.nodes_expanded += 1

        # 检查是否已完成
        if len(assignment) == len(variables):
            return assignment.copy()

        # 选择变量 (MRV + 度启发式)
        var = self._select_variable(variables, constraints, assignment)

        # 获取值排序 (LCV)
        values = self._order_values(var, variables, constraints, assignment)

        for value in values:
            # 检查一致性
            if self._is_consistent(var, value, assignment, constraints):
                # 赋值
                assignment[var.name] = value
                var.assign(value)

                # 保存域状态
                saved_domains = self._save_domains(variables)

                # AC-3 传播
                if self.use_ac3:
                    # 创建只包含未赋值变量的约束子集
                    if self._ac3.propagate_with_assignment(
                        variables, constraints, assignment
                    ):
                        result = self._backtrack(
                            variables, constraints, assignment
                        )
                        if result is not None:
                            return result
                    # AC-3 失败，回溯
                else:
                    result = self._backtrack(variables, constraints, assignment)
                    if result is not None:
                        return result

                # 回溯
                self.backtrack_count += 1
                del assignment[var.name]
                var.unassign()
                self._restore_domains(variables, saved_domains)

        return None

    def _select_variable(
        self,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
        assignment: Dict[str, Any],
    ) -> Variable:
        """选择下一个要赋值的变量 (MRV + 度启发式)。"""
        unassigned = [
            v for v in variables.values() if v.name not in assignment
        ]

        if not unassigned:
            raise ValueError("没有未赋值的变量")

        # MRV: 选择域最小的变量
        min_domain_size = min(v.domain.size for v in unassigned)
        candidates = [
            v for v in unassigned if v.domain.size == min_domain_size
        ]

        if len(candidates) == 1:
            return candidates[0]

        # 度启发式: 选择约束最多的变量
        return max(candidates, key=lambda v: self._degree(v, constraints))

    def _degree(self, var: Variable, constraints: List[Constraint]) -> int:
        """计算变量的度 (涉及的约束数)。"""
        count = 0
        for c in constraints:
            if var in c.variables:
                count += len(c.variables) - 1
        return count

    def _order_values(
        self,
        var: Variable,
        variables: Dict[str, Variable],
        constraints: List[Constraint],
        assignment: Dict[str, Any],
    ) -> List[Any]:
        """对变量的值进行排序 (LCV)。"""
        if not self.use_lcv:
            return list(var.domain)

        def count_conflicts(value: Any) -> int:
            conflicts = 0
            test_assignment = {**assignment, var.name: value}
            for c in constraints:
                if var in c.variables:
                    for neighbor in c.get_neighbors(var):
                        if neighbor.name not in assignment:
                            # 计算邻居域中被排除的值数
                            for nval in neighbor.domain:
                                test_assignment[neighbor.name] = nval
                                if not c.is_satisfied(test_assignment):
                                    conflicts += 1
                            del test_assignment[neighbor.name]
            return conflicts

        return sorted(var.domain, key=count_conflicts)

    def _is_consistent(
        self,
        var: Variable,
        value: Any,
        assignment: Dict[str, Any],
        constraints: List[Constraint],
    ) -> bool:
        """检查将 var 赋值为 value 是否与当前赋值一致。"""
        test_assignment = {**assignment, var.name: value}
        for c in constraints:
            if var in c.variables:
                if not c.is_satisfied(test_assignment):
                    return False
        return True

    def _save_domains(
        self, variables: Dict[str, Variable]
    ) -> Dict[str, Domain]:
        """保存所有变量的域状态。"""
        return {name: var.domain.copy() for name, var in variables.items()}

    def _restore_domains(
        self,
        variables: Dict[str, Variable],
        saved: Dict[str, Domain],
    ) -> None:
        """恢复变量的域状态。"""
        for name, domain in saved.items():
            variables[name].domain = domain
