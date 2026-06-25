"""数独求解器 - 约束求解器应用示例"""

from __future__ import annotations
from typing import List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import CSPSolver, Variable, Domain


class SudokuSolver:
    """数独求解器。

    将数独问题建模为 CSP:
    - 变量: 81 个格子 (row, col)
    - 域: 1-9
    - 约束: 行、列、宫 AllDifferent

    Example:
        >>> puzzle = [
        ...     [5, 3, 0, 0, 7, 0, 0, 0, 0],
        ...     [6, 0, 0, 1, 9, 5, 0, 0, 0],
        ...     [0, 9, 8, 0, 0, 0, 0, 6, 0],
        ...     [8, 0, 0, 0, 6, 0, 0, 0, 3],
        ...     [4, 0, 0, 8, 0, 3, 0, 0, 1],
        ...     [7, 0, 0, 0, 2, 0, 0, 0, 6],
        ...     [0, 6, 0, 0, 0, 0, 2, 8, 0],
        ...     [0, 0, 0, 4, 1, 9, 0, 0, 5],
        ...     [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ... ]
        >>> solver = SudokuSolver(puzzle)
        >>> solution = solver.solve()
    """

    def __init__(self, puzzle: List[List[int]]) -> None:
        """初始化数独求解器。

        Args:
            puzzle: 9x9 数独盘面，0 表示待填
        """
        self.puzzle = puzzle
        self._solver = CSPSolver(use_ac3=True)
        self._variables: List[List[Variable]] = []
        self._setup()

    def _setup(self) -> None:
        """设置变量和约束。"""
        # 创建变量
        for row in range(9):
            row_vars = []
            for col in range(9):
                val = self.puzzle[row][col]
                if val == 0:
                    # 未填格子，域为 1-9
                    var = self._solver.add_variable(
                        f"r{row}c{col}", range(1, 10)
                    )
                else:
                    # 已填格子，域为单值
                    var = self._solver.add_variable(
                        f"r{row}c{col}", [val]
                    )
                row_vars.append(var)
            self._variables.append(row_vars)

        # 行约束: 每行 AllDifferent
        for row in range(9):
            self._solver.add_all_different(
                self._variables[row], f"row_{row}"
            )

        # 列约束: 每列 AllDifferent
        for col in range(9):
            col_vars = [self._variables[row][col] for row in range(9)]
            self._solver.add_all_different(col_vars, f"col_{col}")

        # 宫约束: 每个 3x3 宫 AllDifferent
        for box_row in range(3):
            for box_col in range(3):
                box_vars = []
                for r in range(3):
                    for c in range(3):
                        box_vars.append(
                            self._variables[box_row * 3 + r][box_col * 3 + c]
                        )
                self._solver.add_all_different(
                    box_vars, f"box_{box_row}_{box_col}"
                )

    def solve(self) -> Optional[List[List[int]]]:
        """求解数独。

        Returns:
            9x9 解矩阵，或 None 表示无解
        """
        result = self._solver.solve()
        if result is None:
            return None

        solution = []
        for row in range(9):
            sol_row = []
            for col in range(9):
                var_name = f"r{row}c{col}"
                sol_row.append(result[var_name])
            solution.append(sol_row)
        return solution

    @staticmethod
    def print_board(board: List[List[int]]) -> str:
        """格式化打印数独盘面。"""
        lines = []
        for i, row in enumerate(board):
            if i > 0 and i % 3 == 0:
                lines.append("------+-------+------")
            line_parts = []
            for j, val in enumerate(row):
                if j > 0 and j % 3 == 0:
                    line_parts.append("|")
                line_parts.append(str(val) if val != 0 else ".")
            lines.append(" ".join(line_parts))
        return "\n".join(lines)

    @staticmethod
    def validate(board: List[List[int]]) -> bool:
        """验证数独解是否有效。"""
        # 检查行
        for row in board:
            if len(set(row)) != 9:
                return False

        # 检查列
        for col in range(9):
            column = [board[row][col] for row in range(9)]
            if len(set(column)) != 9:
                return False

        # 检查宫
        for box_row in range(3):
            for box_col in range(3):
                box = []
                for r in range(3):
                    for c in range(3):
                        box.append(board[box_row * 3 + r][box_col * 3 + c])
                if len(set(box)) != 9:
                    return False

        return True


def main():
    """数独求解示例。"""
    # 经典数独题目
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]

    print("=== 数独求解器 ===\n")
    print("题目:")
    print(SudokuSolver.print_board(puzzle))
    print()

    solver = SudokuSolver(puzzle)
    solution = solver.solve()

    if solution:
        print("解:")
        print(SudokuSolver.print_board(solution))
        print(f"\n验证: {'通过' if SudokuSolver.validate(solution) else '失败'}")
    else:
        print("无解!")


if __name__ == "__main__":
    main()
