"""
线性规划问题的标准表示。

支持：
- 标准形式 (max c^T x, Ax <= b, x >= 0)
- 一般形式转换为标准形式
- 松弛变量引入
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ConstraintType(Enum):
    """约束类型"""
    LE = "<="      # 小于等于
    GE = ">="      # 大于等于
    EQ = "=="      # 等于


class ObjectiveType(Enum):
    """目标类型"""
    MAX = "max"
    MIN = "min"


@dataclass
class Constraint:
    """单个约束条件"""
    coefficients: np.ndarray
    rhs: float
    constraint_type: ConstraintType

    def __post_init__(self):
        self.coefficients = np.array(self.coefficients, dtype=float)


@dataclass
class LPResult:
    """线性规划求解结果"""
    status: str           # "optimal", "infeasible", "unbounded", "multiple"
    optimal_value: Optional[float] = None
    solution: Optional[np.ndarray] = None
    dual_solution: Optional[np.ndarray] = None
    slack: Optional[np.ndarray] = None
    iterations: int = 0
    tableau_history: List[np.ndarray] = field(default_factory=list)
    message: str = ""

    def __repr__(self):
        lines = [f"LP Result: {self.status}"]
        if self.optimal_value is not None:
            lines.append(f"  Optimal Value: {self.optimal_value:.6f}")
        if self.solution is not None:
            lines.append(f"  Solution: {np.round(self.solution, 6)}")
        if self.dual_solution is not None:
            lines.append(f"  Dual Solution: {np.round(self.dual_solution, 6)}")
        if self.slack is not None:
            lines.append(f"  Slack: {np.round(self.slack, 6)}")
        lines.append(f"  Iterations: {self.iterations}")
        if self.message:
            lines.append(f"  Message: {self.message}")
        return "\n".join(lines)


class LinearProgram:
    """
    线性规划问题表示。

    支持形式：
        max/min  c^T x
        s.t.     Ax  <=/>=/==  b
                  x >= 0

    Examples
    --------
    >>> lp = LinearProgram(ObjectiveType.MAX)
    >>> lp.set_objective([3, 5])
    >>> lp.add_constraint([1, 0], 4, ConstraintType.LE)
    >>> lp.add_constraint([0, 2], 12, ConstraintType.LE)
    >>> lp.add_constraint([3, 5], 25, ConstraintType.LE)
    """

    def __init__(self, objective_type: ObjectiveType = ObjectiveType.MAX):
        self.objective_type = objective_type
        self._objective_coeffs: Optional[np.ndarray] = None
        self._constraints: List[Constraint] = []
        self._num_vars: int = 0
        self._var_names: Optional[List[str]] = None

    def set_objective(self, coefficients, names: Optional[List[str]] = None):
        """设置目标函数系数。"""
        self._objective_coeffs = np.array(coefficients, dtype=float)
        self._num_vars = len(self._objective_coeffs)
        if names is not None:
            assert len(names) == self._num_vars
            self._var_names = list(names)

    def add_constraint(self, coefficients, rhs: float, constraint_type: ConstraintType):
        """添加约束条件。"""
        coeffs = np.array(coefficients, dtype=float)
        if self._num_vars > 0:
            assert len(coeffs) == self._num_vars, \
                f"系数维度 {len(coeffs)} != 变量数 {self._num_vars}"
        self._constraints.append(Constraint(coeffs, rhs, constraint_type))

    @property
    def c(self) -> np.ndarray:
        """目标函数系数向量。"""
        return self._objective_coeffs.copy()

    @property
    def A(self) -> np.ndarray:
        """约束系数矩阵。"""
        return np.array([c.coefficients for c in self._constraints], dtype=float)

    @property
    def b(self) -> np.ndarray:
        """右端项向量。"""
        return np.array([c.rhs for c in self._constraints], dtype=float)

    @property
    def num_vars(self) -> int:
        return self._num_vars

    @property
    def num_constraints(self) -> int:
        return len(self._constraints)

    @property
    def constraints(self) -> List[Constraint]:
        return self._constraints

    def to_standard_form(self):
        """
        转换为标准形式：max c^T x, Ax <= b, x >= 0。

        处理：
        1. min -> max (取负)
        2. >= 约束 -> 乘以 -1
        3. == 约束 -> 拆分为 <= 和 >=
        4. 添加松弛变量

        Returns
        -------
        c_std : np.ndarray
            标准形式目标系数
        A_std : np.ndarray
            标准形式约束矩阵（含松弛变量）
        b_std : np.ndarray
            标准形式右端项
        num_original_vars : int
            原始变量数
        """
        c = self._objective_coeffs.copy()
        A = self.A.copy()
        b = self.b.copy()

        # 1. 如果是最小化问题，取负转为最大化
        if self.objective_type == ObjectiveType.MIN:
            c = -c

        # 2. 处理约束类型
        rows_to_add_A = []
        rows_to_add_b = []
        new_A_rows = []
        new_b_rows = []

        for i, constr in enumerate(self._constraints):
            if constr.constraint_type == ConstraintType.LE:
                new_A_rows.append(A[i])
                new_b_rows.append(b[i])
            elif constr.constraint_type == ConstraintType.GE:
                # 乘以 -1 转为 <=
                new_A_rows.append(-A[i])
                new_b_rows.append(-b[i])
            elif constr.constraint_type == ConstraintType.EQ:
                # 拆分为 <= 和 >= (即 -Ax <= -b)
                new_A_rows.append(A[i])
                new_b_rows.append(b[i])
                new_A_rows.append(-A[i])
                new_b_rows.append(-b[i])

        A_std = np.array(new_A_rows, dtype=float)
        b_std = np.array(new_b_rows, dtype=float)

        return c, A_std, b_std, self._num_vars

    def __repr__(self):
        lines = [f"Linear Program ({self.objective_type.value})"]
        obj_str = " + ".join(f"{c}*x{i}" for i, c in enumerate(self._objective_coeffs))
        lines.append(f"  Objective: {self.objective_type.value} {obj_str}")
        for constr in self._constraints:
            terms = " + ".join(f"{c}*x{i}" for i, c in enumerate(constr.coefficients))
            lines.append(f"  s.t. {terms} {constr.constraint_type.value} {constr.rhs}")
        return "\n".join(lines)
