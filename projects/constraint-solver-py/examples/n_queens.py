"""N 皇后问题求解器 - 约束求解器应用示例"""

from __future__ import annotations
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import CSPSolver, Variable, Domain, AllDifferentConstraint, LinearConstraint


class NQueensSolver:
    """N 皇后问题求解器。

    将 N 皇后问题建模为 CSP:
    - 变量: Q_i 表示第 i 行皇后所在的列
    - 域: 1 到 N
    - 约束: AllDifferent + 对角线约束

    Example:
        >>> solver = NQueensSolver(8)
        >>> solution = solver.solve()
    """

    def __init__(self, n: int) -> None:
        """初始化 N 皇后求解器。

        Args:
            n: 棋盘大小 (N x N)
        """
        self.n = n
        self._solver = CSPSolver(use_ac3=True)
        self._variables: List[Variable] = []
        self._setup()

    def _setup(self) -> None:
        """设置变量和约束。"""
        # 创建变量: Q_i 表示第 i 行皇后所在的列
        for i in range(self.n):
            var = self._solver.add_variable(f"Q_{i}", range(1, self.n + 1))
            self._variables.append(var)

        # AllDifferent 约束: 所有皇后在不同列
        self._solver.add_all_different(self._variables, "different_columns")

        # 对角线约束: 任意两个皇后不在同一对角线
        for i in range(self.n):
            for j in range(i + 1, self.n):
                # |Q_i - Q_j| != |i - j|
                self._add_diagonal_constraint(i, j)

    def _add_diagonal_constraint(self, i: int, j: int) -> None:
        """添加对角线约束: |Q_i - Q_j| != |i - j|。"""
        diff = abs(i - j)
        qi = self._variables[i]
        qj = self._variables[j]

        # 使用表约束: 枚举所有满足 |qi - qj| != diff 的对
        valid_tuples = []
        for ci in range(1, self.n + 1):
            for cj in range(1, self.n + 1):
                if abs(ci - cj) != diff:
                    valid_tuples.append((ci, cj))

        self._solver.add_table(
            [qi, qj],
            valid_tuples,
            f"diag_{i}_{j}",
        )

    def solve(self) -> Optional[List[int]]:
        """求解 N 皇后问题。

        Returns:
            列位置列表 (索引 i 对应第 i 行的皇后列位置)，或 None 表示无解
        """
        result = self._solver.solve()
        if result is None:
            return None
        return [result[f"Q_{i}"] for i in range(self.n)]

    def solve_all(self, max_solutions: int = 0) -> List[List[int]]:
        """求解所有解。

        Args:
            max_solutions: 最大解数 (0 表示无限制)

        Returns:
            所有解的列表
        """
        results = self._solver.solve_all(max_solutions)
        return [
            [result[f"Q_{i}"] for i in range(self.n)]
            for result in results
        ]

    @staticmethod
    def print_board(solution: List[int]) -> str:
        """格式化打印棋盘。"""
        n = len(solution)
        lines = []
        for i in range(n):
            row = []
            for j in range(1, n + 1):
                if solution[i] == j:
                    row.append("Q")
                else:
                    row.append(".")
            lines.append(" ".join(row))
        return "\n".join(lines)

    @staticmethod
    def validate(solution: List[int]) -> bool:
        """验证 N 皇后解是否有效。"""
        n = len(solution)

        # 检查列唯一性
        if len(set(solution)) != n:
            return False

        # 检查值范围
        for val in solution:
            if val < 1 or val > n:
                return False

        # 检查对角线
        for i in range(n):
            for j in range(i + 1, n):
                if abs(solution[i] - solution[j]) == abs(i - j):
                    return False

        return True


def main():
    """N 皇后求解示例。"""
    print("=== N 皇后问题求解器 ===\n")

    # 求解 8 皇后问题
    n = 8
    print(f"求解 {n} 皇后问题:\n")

    solver = NQueensSolver(n)

    # 求解第一个解
    solution = solver.solve()
    if solution:
        print("第一个解:")
        print(NQueensSolver.print_board(solution))
        print(f"\n列位置: {solution}")
        print(f"验证: {'通过' if NQueensSolver.validate(solution) else '失败'}")

    # 求解所有解
    print(f"\n求解所有解...")
    all_solutions = solver.solve_all()
    print(f"共找到 {len(all_solutions)} 个解")

    # 打印前 3 个解
    for i, sol in enumerate(all_solutions[:3]):
        print(f"\n解 {i + 1}:")
        print(NQueensSolver.print_board(sol))


if __name__ == "__main__":
    main()
