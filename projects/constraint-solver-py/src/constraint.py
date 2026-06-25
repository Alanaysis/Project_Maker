"""约束模块 - 各种约束类型的实现"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple
from .variable import Variable
from .domain import Domain


class Constraint(ABC):
    """约束基类。

    Attributes:
        name: 约束名称
        variables: 受约束的变量列表
    """

    def __init__(self, name: str, variables: Sequence[Variable]) -> None:
        self.name = name
        self.variables = list(variables)

    @abstractmethod
    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """检查约束在给定赋值下是否满足。"""
        ...

    @abstractmethod
    def revise(self, xi: Variable, xj: Variable) -> bool:
        """AC-3 算法的修订操作。

        根据约束缩减 xi 的域，使得 xi 的每个值在 xj 的域中都有支持。
        返回 True 表示 xi 的域被修改。
        """
        ...

    def get_neighbors(self, var: Variable) -> List[Variable]:
        """获取与给定变量在同一约束中的其他变量。"""
        return [v for v in self.variables if v.name != var.name]

    def __repr__(self) -> str:
        var_names = [v.name for v in self.variables]
        return f"{self.__class__.__name__}({self.name!r}, vars={var_names})"


class AllDifferentConstraint(Constraint):
    """AllDifferent 约束 - 所有变量取不同值。

    Example:
        >>> x, y, z = Variable("x", Domain([1,2,3])), ...
        >>> c = AllDifferentConstraint("alldiff", [x, y, z])
    """

    def __init__(self, name: str, variables: Sequence[Variable]) -> None:
        super().__init__(name, variables)

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """检查所有已赋值变量的值是否互不相同。"""
        values = []
        for var in self.variables:
            if var.name in assignment:
                val = assignment[var.name]
                if val in values:
                    return False
                values.append(val)
        return True

    def revise(self, xi: Variable, xj: Variable) -> bool:
        """AC-3 修订: 如果 xj 域是单值集，从 xi 域中移除该值。"""
        revised = False
        if xj.domain.is_singleton():
            val = xj.domain.get_only_value()
            if xi.domain.remove(val):
                revised = True
        return revised


class LinearConstraint(Constraint):
    """线性约束 - 支持 a*x + b*y + ... op c 的形式。

    支持的操作符: ==, !=, <, <=, >, >=

    Example:
        >>> c = LinearConstraint("sum10", [x, y], lambda vals: sum(vals) == 10)
        >>> c = LinearConstraint.from_expression("lt", [x, y], "x + y < 10")
    """

    def __init__(
        self,
        name: str,
        variables: Sequence[Variable],
        predicate: Callable[[Dict[str, Any]], bool],
        coefficients: Optional[Dict[str, float]] = None,
        operator: str = "==",
        constant: float = 0.0,
    ) -> None:
        super().__init__(name, variables)
        self.predicate = predicate
        self.coefficients = coefficients or {v.name: 1.0 for v in variables}
        self.operator = operator
        self.constant = constant

    @classmethod
    def from_expression(
        cls,
        name: str,
        variables: Sequence[Variable],
        expression: str,
    ) -> LinearConstraint:
        """从表达式字符串创建线性约束。

        支持格式:
        - "a*x + b*y op c" (与常数比较)
        - "x op y" (变量之间比较)

        其中 op 是 ==, !=, <, <=, >, >=
        """
        import re

        # 解析操作符
        ops = ["<=", ">=", "!=", "==", "<", ">"]
        op_found = None
        for op in ops:
            if op in expression:
                op_found = op
                break

        if op_found is None:
            raise ValueError(f"表达式中未找到操作符: {expression}")

        left, right = expression.split(op_found, 1)
        left = left.strip()
        right = right.strip()

        # 解析左右两侧的系数
        coefficients: Dict[str, float] = {}
        constant = 0.0

        def parse_side(side: str, sign: float = 1.0) -> None:
            """解析表达式的一侧，提取变量系数和常数。"""
            terms = side.replace("-", "+-").split("+")
            for term in terms:
                term = term.strip()
                if not term:
                    continue
                # 匹配 a*x 或 x 或 a
                match = re.match(r"([+-]?\d*\.?\d*)\s*\*?\s*(\w+)", term)
                if match:
                    coeff_str, var_name = match.groups()
                    # 检查是否是变量名
                    var_names = {v.name for v in variables}
                    if var_name in var_names:
                        coeff = float(coeff_str) if coeff_str and coeff_str not in ["", "+", "-"] else (
                            -1.0 if coeff_str == "-" else 1.0
                        )
                        coefficients[var_name] = coefficients.get(var_name, 0.0) + coeff * sign
                    else:
                        # 尝试作为常数解析
                        try:
                            val = float(term)
                            nonlocal constant
                            constant += val * sign
                        except ValueError:
                            pass

        parse_side(left, 1.0)
        # 右侧移到左侧 (变号)
        parse_side(right, -1.0)
        # 常数也移到左侧
        # 现在约束形式为: sum(coeff * var) op 0
        # 但为了保持可读性，我们保留原始形式
        # 重新解析: 系数在左侧，常数在右侧
        coefficients.clear()
        constant = 0.0
        parse_side(left, 1.0)

        # 检查右侧是否是常数
        try:
            constant = float(right)
        except ValueError:
            # 右侧是变量，需要将其移到左侧
            match = re.match(r"([+-]?\d*\.?\d*)\s*\*?\s*(\w+)", right)
            if match:
                coeff_str, var_name = match.groups()
                coeff = float(coeff_str) if coeff_str and coeff_str not in ["", "+", "-"] else (
                    -1.0 if coeff_str == "-" else 1.0
                )
                coefficients[var_name] = coefficients.get(var_name, 0.0) - coeff
            constant = 0.0

        # 创建谓词
        ops_map = {
            "==": lambda a, b: abs(a - b) < 1e-9,
            "!=": lambda a, b: abs(a - b) >= 1e-9,
            "<": lambda a, b: a < b - 1e-9,
            "<=": lambda a, b: a <= b + 1e-9,
            ">": lambda a, b: a > b + 1e-9,
            ">=": lambda a, b: a >= b - 1e-9,
        }

        def predicate(assignment: Dict[str, Any]) -> bool:
            total = 0.0
            for var_name, coeff in coefficients.items():
                if var_name in assignment:
                    total += coeff * assignment[var_name]
                else:
                    return True  # 未赋值的变量跳过检查
            return ops_map[op_found](total, constant)

        return cls(name, variables, predicate, coefficients, op_found, constant)

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """检查线性约束是否满足。"""
        # 只有当所有变量都已赋值时才检查
        for var in self.variables:
            if var.name not in assignment:
                return True
        return self.predicate(assignment)

    def revise(self, xi: Variable, xj: Variable) -> bool:
        """AC-3 修订: 根据线性关系缩减 xi 的域。"""
        revised = False
        values_to_remove = []

        for val_xi in xi.domain:
            supported = False
            # 检查 xj 域中是否有支持值
            for val_xj in xj.domain:
                test_assignment = {xi.name: val_xi, xj.name: val_xj}
                # 只测试这两个变量的约束
                partial = True
                for var in self.variables:
                    if var.name not in test_assignment:
                        if var.name != xi.name and var.name != xj.name:
                            partial = False
                            break
                if partial and self._check_pair(xi.name, val_xi, xj.name, val_xj):
                    supported = True
                    break
            if not supported:
                values_to_remove.append(val_xi)

        for val in values_to_remove:
            xi.domain.remove(val)
            revised = True

        return revised

    def _check_pair(self, name1: str, val1: Any, name2: str, val2: Any) -> bool:
        """检查一对值是否满足约束。"""
        total = 0.0
        for var_name, coeff in self.coefficients.items():
            if var_name == name1:
                total += coeff * val1
            elif var_name == name2:
                total += coeff * val2
            else:
                # 其他变量未赋值，无法完整检查
                return True

        ops_map = {
            "==": lambda a, b: abs(a - b) < 1e-9,
            "!=": lambda a, b: abs(a - b) >= 1e-9,
            "<": lambda a, b: a < b - 1e-9,
            "<=": lambda a, b: a <= b + 1e-9,
            ">": lambda a, b: a > b + 1e-9,
            ">=": lambda a, b: a >= b - 1e-9,
        }
        return ops_map[self.operator](total, self.constant)


class TableConstraint(Constraint):
    """表约束 (显式约束) - 通过枚举允许的元组来定义约束。

    Example:
        >>> c = TableConstraint("table", [x, y], [(1,2), (2,3), (3,1)])
    """

    def __init__(
        self,
        name: str,
        variables: Sequence[Variable],
        tuples: Sequence[Sequence[Any]],
    ) -> None:
        super().__init__(name, variables)
        self.tuples = [tuple(t) for t in tuples]
        self._tuple_set = set(self.tuples)

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """检查赋值是否与某个允许元组一致。"""
        # 只检查已赋值的变量
        partial = []
        all_assigned = True
        for var in self.variables:
            if var.name in assignment:
                partial.append(assignment[var.name])
            else:
                all_assigned = False
                partial.append(None)

        if not all_assigned:
            # 部分赋值: 检查是否有元组与当前部分赋值兼容
            for t in self.tuples:
                compatible = True
                for i, var in enumerate(self.variables):
                    if var.name in assignment and t[i] != assignment[var.name]:
                        compatible = False
                        break
                if compatible:
                    return True
            return False

        return tuple(partial) in self._tuple_set

    def revise(self, xi: Variable, xj: Variable) -> bool:
        """AC-3 修订: 移除 xi 中没有 xj 支持的值。"""
        xi_idx = None
        xj_idx = None
        for i, var in enumerate(self.variables):
            if var.name == xi.name:
                xi_idx = i
            elif var.name == xj.name:
                xj_idx = i

        if xi_idx is None or xj_idx is None:
            return False

        revised = False
        values_to_remove = []

        for val_xi in xi.domain:
            supported = False
            for t in self.tuples:
                if t[xi_idx] == val_xi and t[xj_idx] in xj.domain:
                    supported = True
                    break
            if not supported:
                values_to_remove.append(val_xi)

        for val in values_to_remove:
            xi.domain.remove(val)
            revised = True

        return revised

    def __repr__(self) -> str:
        var_names = [v.name for v in self.variables]
        return f"TableConstraint({self.name!r}, vars={var_names}, tuples={len(self.tuples)})"
