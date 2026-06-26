"""
标准形转换模块 (Standard Form Conversion)

将任意线性规划问题转换为单纯形法所需的标准形。

单纯形法要求的问题形式 (标准形):
    目标函数: 最小化 (或最大化)
    约束:      A * x = b
    变量:      x >= 0
    右侧:      b >= 0

转换规则:
    1. 不等式约束 -> 等式约束: 添加松弛变量 (slack variables)
    2. 最大化 -> 最小化: 取负号
    3. 自由变量 (无符号限制): 分解为两个非负变量之差
    4. b < 0 的约束: 两边同乘 -1
"""

import numpy as np
from typing import Tuple, List, Dict, Optional

from .problem import LPProblem, create_problem


class StandardFormConverter:
    """
    将线性规划问题转换为单纯形法标准形。

    学习要点:
        - 松弛变量 (Slack Variables): 将 <= 约束变为等式
        - 剩余变量 (Surplus Variables): 将 >= 约束变为等式
        - 自由变量处理: x = x+ - x-
    """

    def __init__(self, problem: LPProblem):
        """
        初始化转换器。

        Args:
            problem: 原始 LP 问题
        """
        self.original_problem = problem
        self.slack_vars_added = 0  # 记录的松弛变量数量
        self.surplus_vars_added = 0  # 记录的剩余变量数量
        self.artificial_vars_added = 0  # 记录的 artificical 变量数量
        self.var_mapping: List[str] = []  # 变量名映射

    def convert_to_standard_form(self) -> LPProblem:
        """
        将问题转换为标准形 (等式约束 + 非负变量 + b >= 0)。

        Returns:
            LPProblem: 标准形问题
        """
        prob = self.original_problem

        # 处理最大化问题: max(c^T x) = min(-c^T x)
        if prob.problem_type == "max":
            c = -prob.c
        else:
            c = prob.c.copy()

        # 处理 b < 0 的约束
        A = prob.A.copy()
        b = prob.b.copy()
        for i in range(len(b)):
            if b[i] < 0:
                A[i] *= -1
                b[i] *= -1

        # 对于 A*x <= b 形式的约束，全部添加松弛变量
        # 因为 s_i >= 0, A*x + s = b => A*x <= b
        n_vars = len(c)
        n_constraints = len(b)

        # 构建松弛变量列: 每列有 n_constraints 行
        slack_columns = []
        slack_values = []
        for i in range(n_constraints):
            slack_col = np.zeros(n_constraints)
            slack_col[i] = 1.0
            slack_columns.append(slack_col)
            slack_values.append(0.0)
            self.slack_vars_added += 1

        slack_matrix = np.column_stack(slack_columns)
        new_A = np.hstack([A, slack_matrix])
        new_b = b.copy()

        # 构建目标函数系数
        slack_c = np.array(slack_values)
        new_c = np.concatenate([c, slack_c])

        # 构建变量名
        orig_names = prob.variable_names or [f"x{i+1}" for i in range(prob.n_vars)]
        slack_names = [f"s{i+1}" for i in range(len(slack_columns))]
        new_names = orig_names + slack_names

        return create_problem(
            c=new_c.tolist(),
            A=new_A.tolist(),
            b=new_b.tolist(),
            variable_names=new_names,
            constraint_names=prob.constraint_names,
            problem_type=prob.problem_type,
        )

    def get_augmented_matrix(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        获取增广矩阵形式 (用于单纯形表)。

        对于 <= 约束，添加松弛变量后:
            A*x + I*s = b
            x >= 0, s >= 0

        Returns:
            (A_eq, b, c): 等式约束矩阵、右侧向量、目标系数
        """
        std_form = self.convert_to_standard_form()
        return std_form.A, std_form.b, std_form.c

    def get_summary(self) -> Dict:
        """获取转换过程的摘要信息."""
        return {
            "original_vars": self.original_problem.n_vars,
            "original_constraints": self.original_problem.n_constraints,
            "slack_vars_added": self.slack_vars_added,
            "surplus_vars_added": self.surplus_vars_added,
            "total_vars": self.original_problem.n_vars + self.slack_vars_added + self.surplus_vars_added,
            "total_constraints": self.original_problem.n_constraints,
        }
