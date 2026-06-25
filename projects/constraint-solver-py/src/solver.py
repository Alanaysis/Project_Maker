"""求解器模块 - CSP 求解器主类"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Tuple
from .variable import Variable
from .domain import Domain
from .constraint import (
    Constraint,
    AllDifferentConstraint,
    LinearConstraint,
    TableConstraint,
)
from .propagation import AC3, PathConsistency
from .search import BacktrackingSearch


class CSPSolver:
    """约束满足问题求解器。

    提供高级接口用于定义和求解 CSP。

    Example:
        >>> solver = CSPSolver()
        >>> x = solver.add_variable("x", [1, 2, 3])
        >>> y = solver.add_variable("y", [1, 2, 3])
        >>> solver.add_all_different([x, y])
        >>> result = solver.solve()
    """

    def __init__(
        self,
        use_ac3: bool = True,
        use_lcv: bool = False,
    ) -> None:
        """初始化求解器。

        Args:
            use_ac3: 是否使用 AC-3 弧相容
            use_lcv: 是否使用 LCV 值排序
        """
        self._variables: Dict[str, Variable] = {}
        self._constraints: List[Constraint] = []
        self._use_ac3 = use_ac3
        self._use_lcv = use_lcv

    @property
    def variables(self) -> Dict[str, Variable]:
        """所有变量的字典。"""
        return self._variables

    @property
    def constraints(self) -> List[Constraint]:
        """所有约束的列表。"""
        return self._constraints

    def add_variable(
        self, name: str, domain_values: Sequence[Any]
    ) -> Variable:
        """添加变量。

        Args:
            name: 变量名
            domain_values: 取值域

        Returns:
            创建的变量
        """
        if name in self._variables:
            raise ValueError(f"变量 {name} 已存在")
        var = Variable(name, Domain(domain_values))
        self._variables[name] = var
        return var

    def add_all_different(
        self, variables: Sequence[Variable], name: Optional[str] = None
    ) -> AllDifferentConstraint:
        """添加 AllDifferent 约束。

        Args:
            variables: 受约束的变量列表
            name: 约束名称 (可选)

        Returns:
            创建的约束
        """
        if name is None:
            name = f"alldiff_{'_'.join(v.name for v in variables)}"
        constraint = AllDifferentConstraint(name, variables)
        self._constraints.append(constraint)
        return constraint

    def add_linear(
        self,
        variables: Sequence[Variable],
        expression: str,
        name: Optional[str] = None,
    ) -> LinearConstraint:
        """添加线性约束。

        Args:
            variables: 受约束的变量列表
            expression: 线性表达式，如 "x + y == 10"
            name: 约束名称 (可选)

        Returns:
            创建的约束
        """
        if name is None:
            name = f"linear_{len(self._constraints)}"
        constraint = LinearConstraint.from_expression(name, variables, expression)
        self._constraints.append(constraint)
        return constraint

    def add_table(
        self,
        variables: Sequence[Variable],
        tuples: Sequence[Sequence[Any]],
        name: Optional[str] = None,
    ) -> TableConstraint:
        """添加表约束。

        Args:
            variables: 受约束的变量列表
            tuples: 允许的值元组列表
            name: 约束名称 (可选)

        Returns:
            创建的约束
        """
        if name is None:
            name = f"table_{len(self._constraints)}"
        constraint = TableConstraint(name, variables, tuples)
        self._constraints.append(constraint)
        return constraint

    def add_constraint(self, constraint: Constraint) -> None:
        """直接添加约束对象。"""
        self._constraints.append(constraint)

    def solve(
        self, initial_assignment: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """求解 CSP。

        Args:
            initial_assignment: 初始赋值 (可选)

        Returns:
            完整赋值字典，或 None 表示无解
        """
        if not self._variables:
            return {}

        search = BacktrackingSearch(
            use_ac3=self._use_ac3, use_lcv=self._use_lcv
        )
        return search.solve(self._variables, self._constraints, initial_assignment)

    def solve_all(
        self, max_solutions: int = 0
    ) -> List[Dict[str, Any]]:
        """求解 CSP 的所有解。

        Args:
            max_solutions: 最大解数 (0 表示无限制)

        Returns:
            所有解的列表
        """
        solutions = []
        self._find_all_solutions(
            {}, solutions, max_solutions, set()
        )
        return solutions

    def _find_all_solutions(
        self,
        assignment: Dict[str, Any],
        solutions: List[Dict[str, Any]],
        max_solutions: int,
        tried: set,
    ) -> None:
        """递归查找所有解。"""
        if max_solutions > 0 and len(solutions) >= max_solutions:
            return

        if len(assignment) == len(self._variables):
            solutions.append(assignment.copy())
            return

        # 选择未赋值变量
        unassigned = [
            v for v in self._variables.values() if v.name not in assignment
        ]
        if not unassigned:
            return

        # MRV
        var = min(unassigned, key=lambda v: v.domain.size)

        for value in var.domain:
            assignment[var.name] = value
            var.assign(value)

            # 检查一致性
            consistent = True
            for c in self._constraints:
                if var in c.variables:
                    if not c.is_satisfied(assignment):
                        consistent = False
                        break

            if consistent:
                # AC-3 传播
                saved_domains = {
                    name: v.domain.copy() for name, v in self._variables.items()
                }

                if self._use_ac3:
                    ac3 = AC3()
                    if ac3.propagate_with_assignment(
                        self._variables, self._constraints, assignment
                    ):
                        self._find_all_solutions(
                            assignment, solutions, max_solutions, tried
                        )
                else:
                    self._find_all_solutions(
                        assignment, solutions, max_solutions, tried
                    )

                # 恢复域
                for name, domain in saved_domains.items():
                    self._variables[name].domain = domain

            del assignment[var.name]
            var.unassign()

    def reset(self) -> None:
        """重置求解器状态。"""
        for var in self._variables.values():
            var.reset()

    def get_stats(self) -> Dict[str, Any]:
        """获取求解统计信息。"""
        return {
            "num_variables": len(self._variables),
            "num_constraints": len(self._constraints),
            "total_domain_size": sum(
                v.domain.size for v in self._variables.values()
            ),
        }

    def __repr__(self) -> str:
        return (
            f"CSPSolver(variables={len(self._variables)}, "
            f"constraints={len(self._constraints)})"
        )
