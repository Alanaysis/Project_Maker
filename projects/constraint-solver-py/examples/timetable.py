"""排课问题求解器 - 约束求解器应用示例"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import CSPSolver, Variable, Domain


class TimetableSolver:
    """排课问题求解器。

    将排课问题建模为 CSP:
    - 变量: 每门课程的时间槽
    - 域: 可用时间槽
    - 约束: 教师冲突、教室冲突、学生冲突

    Example:
        >>> solver = TimetableSolver(
        ...     courses=["数学", "物理", "化学", "英语"],
        ...     teachers=["张老师", "李老师", "王老师", "赵老师"],
        ...     slots=["周一-1", "周一-2", "周二-1", "周二-2"],
        ... )
        >>> solution = solver.solve()
    """

    def __init__(
        self,
        courses: List[str],
        teachers: List[str],
        slots: List[str],
        teacher_courses: Optional[Dict[str, List[str]]] = None,
        student_groups: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """初始化排课求解器。

        Args:
            courses: 课程列表
            teachers: 教师列表
            slots: 时间槽列表
            teacher_courses: 教师-课程映射 (teacher -> courses)
            student_groups: 学生组-课程映射 (group -> courses)
        """
        self.courses = courses
        self.teachers = teachers
        self.slots = slots
        self.teacher_courses = teacher_courses or {}
        self.student_groups = student_groups or {}

        self._solver = CSPSolver(use_ac3=True)
        self._variables: Dict[str, Variable] = {}
        self._course_teacher: Dict[str, str] = {}
        self._setup()

    def _setup(self) -> None:
        """设置变量和约束。"""
        # 创建课程变量
        for course in self.courses:
            var = self._solver.add_variable(course, self.slots)
            self._variables[course] = var

        # 建立课程-教师映射
        for teacher, teacher_course_list in self.teacher_courses.items():
            for course in teacher_course_list:
                self._course_teacher[course] = teacher

        # 教师冲突约束: 同一教师的课程不能在同一时间
        for teacher, teacher_course_list in self.teacher_courses.items():
            if len(teacher_course_list) > 1:
                teacher_vars = [
                    self._variables[c] for c in teacher_course_list
                ]
                self._solver.add_all_different(
                    teacher_vars, f"teacher_{teacher}"
                )

        # 学生组冲突约束: 同一学生组的课程不能在同一时间
        for group, group_courses in self.student_groups.items():
            if len(group_courses) > 1:
                group_vars = [
                    self._variables[c] for c in group_courses
                ]
                self._solver.add_all_different(
                    group_vars, f"group_{group}"
                )

    def solve(self) -> Optional[Dict[str, str]]:
        """求解排课问题。

        Returns:
            课程-时间槽映射，或 None 表示无解
        """
        return self._solver.solve()

    def solve_all(self, max_solutions: int = 0) -> List[Dict[str, str]]:
        """求解所有可能的排课方案。

        Args:
            max_solutions: 最大解数

        Returns:
            所有解的列表
        """
        return self._solver.solve_all(max_solutions)

    @staticmethod
    def print_timetable(solution: Dict[str, str], slots: List[str]) -> str:
        """格式化打印课表。"""
        # 按时间槽组织课程
        slot_courses: Dict[str, List[str]] = {slot: [] for slot in slots}
        for course, slot in solution.items():
            slot_courses[slot].append(course)

        lines = ["=" * 50]
        lines.append("排课结果")
        lines.append("=" * 50)
        for slot in slots:
            courses = slot_courses[slot]
            if courses:
                lines.append(f"\n{slot}:")
                for course in courses:
                    lines.append(f"  - {course}")
            else:
                lines.append(f"\n{slot}: (空)")
        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


def main():
    """排课问题求解示例。"""
    print("=== 排课问题求解器 ===\n")

    # 定义课程、教师、时间槽
    courses = ["高等数学", "大学物理", "有机化学", "大学英语", "数据结构", "线性代数"]
    teachers = ["张教授", "李教授", "王教授", "赵教授", "刘教授", "陈教授"]
    slots = [
        "周一-上午1", "周一-上午2", "周一-下午1",
        "周二-上午1", "周二-上午2", "周二-下午1",
    ]

    # 教师-课程映射
    teacher_courses = {
        "张教授": ["高等数学", "线性代数"],
        "李教授": ["大学物理"],
        "王教授": ["有机化学"],
        "赵教授": ["大学英语"],
        "刘教授": ["数据结构"],
        "陈教授": ["高等数学", "数据结构"],
    }

    # 学生组-课程映射 (计算机专业学生)
    student_groups = {
        "计算机2024-1班": ["高等数学", "大学物理", "数据结构", "大学英语"],
        "计算机2024-2班": ["高等数学", "有机化学", "线性代数", "大学英语"],
    }

    solver = TimetableSolver(
        courses=courses,
        teachers=teachers,
        slots=slots,
        teacher_courses=teacher_courses,
        student_groups=student_groups,
    )

    print("课程:", courses)
    print("教师:", teachers)
    print("时间槽:", slots)
    print()

    solution = solver.solve()
    if solution:
        print(TimetableSolver.print_timetable(solution, slots))
    else:
        print("无法找到可行的排课方案!")

    # 求解多个方案
    print("\n求解所有可行方案...")
    all_solutions = solver.solve_all(max_solutions=5)
    print(f"共找到 {len(all_solutions)} 个可行方案")


if __name__ == "__main__":
    main()
