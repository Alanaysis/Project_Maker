"""应用示例测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from examples.sudoku import SudokuSolver
from examples.n_queens import NQueensSolver
from examples.timetable import TimetableSolver


class TestSudokuSolver:
    """数独求解器测试。"""

    def test_solve_simple(self):
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
        solver = SudokuSolver(puzzle)
        solution = solver.solve()
        assert solution is not None
        assert SudokuSolver.validate(solution)

    def test_solve_already_complete(self):
        puzzle = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ]
        solver = SudokuSolver(puzzle)
        solution = solver.solve()
        assert solution is not None
        assert SudokuSolver.validate(solution)

    def test_print_board(self):
        puzzle = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        board_str = SudokuSolver.print_board(puzzle)
        assert "1 2 3" in board_str


class TestNQueensSolver:
    """N 皇后求解器测试。"""

    def test_solve_4_queens(self):
        solver = NQueensSolver(4)
        solution = solver.solve()
        assert solution is not None
        assert NQueensSolver.validate(solution)

    def test_solve_8_queens(self):
        solver = NQueensSolver(8)
        solution = solver.solve()
        assert solution is not None
        assert NQueensSolver.validate(solution)

    def test_all_solutions_4_queens(self):
        solver = NQueensSolver(4)
        solutions = solver.solve_all()
        assert len(solutions) == 2
        for sol in solutions:
            assert NQueensSolver.validate(sol)

    def test_all_solutions_8_queens(self):
        solver = NQueensSolver(8)
        solutions = solver.solve_all()
        assert len(solutions) == 92
        for sol in solutions:
            assert NQueensSolver.validate(sol)

    def test_print_board(self):
        solution = [2, 4, 1, 3]
        board_str = NQueensSolver.print_board(solution)
        assert "Q" in board_str
        assert "." in board_str

    def test_no_solution_2_queens(self):
        # 2 皇后无解
        solver = NQueensSolver(2)
        solution = solver.solve()
        assert solution is None

    def test_no_solution_3_queens(self):
        # 3 皇后无解
        solver = NQueensSolver(3)
        solution = solver.solve()
        assert solution is None


class TestTimetableSolver:
    """排课问题求解器测试。"""

    def test_solve_simple(self):
        courses = ["数学", "物理", "化学"]
        teachers = ["张老师", "李老师", "王老师"]
        slots = ["周一-1", "周一-2", "周二-1"]
        teacher_courses = {
            "张老师": ["数学"],
            "李老师": ["物理"],
            "王老师": ["化学"],
        }
        solver = TimetableSolver(
            courses, teachers, slots, teacher_courses
        )
        solution = solver.solve()
        assert solution is not None
        assert len(solution) == 3

    def test_teacher_conflict(self):
        courses = ["数学", "物理"]
        teachers = ["张老师"]
        slots = ["周一-1", "周一-2"]
        teacher_courses = {"张老师": ["数学", "物理"]}
        solver = TimetableSolver(
            courses, teachers, slots, teacher_courses
        )
        solution = solver.solve()
        assert solution is not None
        assert solution["数学"] != solution["物理"]

    def test_print_timetable(self):
        solution = {"数学": "周一-1", "物理": "周一-2"}
        slots = ["周一-1", "周一-2"]
        timetable_str = TimetableSolver.print_timetable(solution, slots)
        assert "数学" in timetable_str
        assert "物理" in timetable_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
