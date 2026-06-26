"""
线性规划问题建模模块 (LP Problem Formulation)

提供线性规划问题的数据结构定义和建模接口。

线性规划 (Linear Programming, LP) 是数学优化的一个重要分支，
研究在满足一组线性约束条件下，优化线性目标函数的问题。

标准形式:
    minimize    c^T * x
    subject to  A * x <= b
                x >= 0

其中:
    - x: n 维决策变量向量
    - c: n 维目标函数系数向量
    - A: m x n 约束矩阵
    - b: m 维约束右侧向量
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class LPProblem:
    """
    线性规划问题的数据容器。

    属性:
        c: 目标函数系数向量 (minimize c^T * x)
        A: 约束矩阵 (A * x <= b)
        b: 约束右侧向量
        variable_names: 变量名称列表 (可选)
        constraint_names: 约束名称列表 (可选)
        problem_type: 优化方向 ('min' 或 'max')
    """
    c: np.ndarray
    A: np.ndarray
    b: np.ndarray
    variable_names: Optional[List[str]] = None
    constraint_names: Optional[List[str]] = None
    problem_type: str = "min"

    def __post_init__(self):
        """验证问题的维度一致性."""
        self.c = np.asarray(self.c, dtype=float)
        self.A = np.asarray(self.A, dtype=float)
        self.b = np.asarray(self.b, dtype=float)

        # 确保 c 和 b 是一维数组
        if self.c.ndim > 1:
            self.c = self.c.ravel()
        if self.b.ndim > 1:
            self.b = self.b.ravel()

        n_vars = len(self.c)
        n_constraints, m_vars = self.A.shape

        if n_vars != m_vars:
            raise ValueError(
                f"目标函数系数维度 ({n_vars}) 与约束矩阵列数 ({m_vars}) 不匹配"
            )

    @property
    def n_vars(self) -> int:
        """返回决策变量数量."""
        return len(self.c)

    @property
    def n_constraints(self) -> int:
        """返回约束数量."""
        return len(self.b)

    def __repr__(self):
        return (
            f"LPProblem(n_vars={self.n_vars}, n_constraints={self.n_constraints}, "
            f"type={self.problem_type})"
        )


def create_problem(
    c: List[float],
    A: List[List[float]],
    b: List[float],
    variable_names: Optional[List[str]] = None,
    constraint_names: Optional[List[str]] = None,
    problem_type: str = "min",
) -> LPProblem:
    """
    创建线性规划问题的便捷函数。

    Args:
        c: 目标函数系数
        A: 约束矩阵
        b: 约束右侧
        variable_names: 变量名称
        constraint_names: 约束名称
        problem_type: 'min' 或 'max'

    Returns:
        LPProblem: 构建好的线性规划问题

    Example:
        >>> # minimize 3x1 + 2x2
        >>> # subject to x1 + x2 <= 4
        >>> #            x1 >= 0, x2 >= 0
        >>> c = [3, 2]
        >>> A = [[1, 1]]
        >>> b = [4]
        >>> prob = create_problem(c, A, b)
    """
    return LPProblem(
        c=np.array(c),
        A=np.array(A),
        b=np.array(b),
        variable_names=variable_names,
        constraint_names=constraint_names,
        problem_type=problem_type,
    )


def maximize(c: List[float], A: List[List[float]], b: List[float], **kwargs) -> LPProblem:
    """
    创建最大化问题的便捷函数。

    注意: 最大化 c^T * x 等价于最小化 -c^T * x。
    求解器内部会自动处理转换。
    """
    kwargs["problem_type"] = "max"
    return create_problem(c, A, b, **kwargs)


def minimize(c: List[float], A: List[List[float]], b: List[float], **kwargs) -> LPProblem:
    """
    创建最小化问题的便捷函数。
    """
    kwargs["problem_type"] = "min"
    return create_problem(c, A, b, **kwargs)


def format_problem_text(prob: LPProblem) -> str:
    """
    将 LP 问题格式化为可读的文本描述。

    用于教学和展示目的，将数学形式转换为自然语言描述。
    """
    lines = []
    obj_type = "最大化" if prob.problem_type == "max" else "最小化"

    # 目标函数
    obj_terms = []
    for i, coeff in enumerate(prob.c):
        var_name = prob.variable_names[i] if prob.variable_names else f"x{i+1}"
        if coeff >= 0:
            obj_terms.append(f"{coeff:.4g}*{var_name}")
        else:
            obj_terms.append(f"{coeff:.4g}*{var_name}")
    obj_str = " + ".join(obj_terms)
    lines.append(f"目标函数 ({obj_type}):")
    lines.append(f"  z = {obj_str}")
    lines.append("")

    # 约束条件
    lines.append("约束条件:")
    for i, (row, val) in enumerate(zip(prob.A, prob.b)):
        cons_name = prob.constraint_names[i] if prob.constraint_names else f"约束 {i+1}"
        terms = []
        for j, coeff in enumerate(row):
            var_name = prob.variable_names[j] if prob.variable_names else f"x{j+1}"
            if coeff != 0:
                if coeff == 1:
                    terms.append(var_name)
                elif coeff == -1:
                    terms.append(f"-{var_name}")
                else:
                    terms.append(f"{coeff:.4g}*{var_name}")
        lhs = " + ".join(terms) if terms else "0"
        lines.append(f"  {lhs} <= {val:.4g}  ({cons_name})")

    # 非负约束
    var_names = prob.variable_names or [f"x{i+1}" for i in range(prob.n_vars)]
    lines.append(f"  非负约束: {', '.join(f'{v} >= 0' for v in var_names)}")

    return "\n".join(lines)
