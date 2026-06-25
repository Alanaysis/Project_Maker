"""求解器核心功能测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src import (
    Variable,
    Domain,
    CSPSolver,
    AllDifferentConstraint,
    LinearConstraint,
    TableConstraint,
    AC3,
    PathConsistency,
    BacktrackingSearch,
)


class TestVariable:
    """变量测试。"""

    def test_create_variable(self):
        var = Variable("x", Domain([1, 2, 3]))
        assert var.name == "x"
        assert var.domain.size == 3
        assert not var.is_assigned()

    def test_assign_variable(self):
        var = Variable("x", Domain([1, 2, 3]))
        var.assign(2)
        assert var.is_assigned()
        assert var.value == 2

    def test_unassign_variable(self):
        var = Variable("x", Domain([1, 2, 3]))
        var.assign(2)
        var.unassign()
        assert not var.is_assigned()
        assert var.value is None

    def test_assign_invalid_value(self):
        var = Variable("x", Domain([1, 2, 3]))
        with pytest.raises(ValueError):
            var.assign(4)

    def test_reset_variable(self):
        var = Variable("x", Domain([1, 2, 3]))
        var.domain.remove(1)
        var.assign(2)
        var.reset()
        assert not var.is_assigned()
        assert var.domain.size == 3


class TestDomain:
    """域测试。"""

    def test_create_domain(self):
        d = Domain([1, 2, 3])
        assert d.size == 3
        assert 1 in d
        assert 4 not in d

    def test_empty_domain(self):
        d = Domain()
        assert d.is_empty()
        assert d.size == 0

    def test_singleton_domain(self):
        d = Domain([5])
        assert d.is_singleton()
        assert d.get_only_value() == 5

    def test_remove_value(self):
        d = Domain([1, 2, 3])
        assert d.remove(2)
        assert d.size == 2
        assert 2 not in d

    def test_remove_nonexistent(self):
        d = Domain([1, 2, 3])
        assert not d.remove(4)
        assert d.size == 3

    def test_intersect(self):
        d1 = Domain([1, 2, 3])
        d2 = Domain([2, 3, 4])
        d3 = d1.intersect(d2)
        assert d3.size == 2
        assert 2 in d3
        assert 3 in d3

    def test_union(self):
        d1 = Domain([1, 2])
        d2 = Domain([3, 4])
        d3 = d1.union(d2)
        assert d3.size == 4

    def test_copy(self):
        d1 = Domain([1, 2, 3])
        d2 = d1.copy()
        d2.remove(1)
        assert d1.size == 3
        assert d2.size == 2


class TestAllDifferentConstraint:
    """AllDifferent 约束测试。"""

    def test_satisfied(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = AllDifferentConstraint("test", [x, y])
        assert c.is_satisfied({"x": 1, "y": 2})
        assert not c.is_satisfied({"x": 1, "y": 1})

    def test_partial_assignment(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = AllDifferentConstraint("test", [x, y])
        assert c.is_satisfied({"x": 1})  # 部分赋值总是满足

    def test_revise(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1]))
        c = AllDifferentConstraint("test", [x, y])
        revised = c.revise(x, y)
        assert revised
        assert 1 not in x.domain
        assert x.domain.size == 2


class TestLinearConstraint:
    """线性约束测试。"""

    def test_sum_constraint(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = LinearConstraint.from_expression("sum5", [x, y], "x + y == 5")
        assert c.is_satisfied({"x": 2, "y": 3})
        assert c.is_satisfied({"x": 3, "y": 2})
        assert not c.is_satisfied({"x": 1, "y": 1})

    def test_less_than(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = LinearConstraint.from_expression("lt", [x, y], "x < y")
        assert c.is_satisfied({"x": 1, "y": 2})
        assert not c.is_satisfied({"x": 2, "y": 1})
        assert not c.is_satisfied({"x": 2, "y": 2})

    def test_revise(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([3]))
        c = LinearConstraint.from_expression("sum5", [x, y], "x + y == 5")
        c.revise(x, y)
        assert x.domain.size == 1
        assert 2 in x.domain


class TestTableConstraint:
    """表约束测试。"""

    def test_satisfied(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = TableConstraint("test", [x, y], [(1, 2), (2, 3)])
        assert c.is_satisfied({"x": 1, "y": 2})
        assert not c.is_satisfied({"x": 1, "y": 3})

    def test_partial_assignment(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1, 2, 3]))
        c = TableConstraint("test", [x, y], [(1, 2), (2, 3)])
        assert c.is_satisfied({"x": 1})  # 有兼容元组
        assert not c.is_satisfied({"x": 3})  # 无兼容元组

    def test_revise(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([2, 3]))
        c = TableConstraint("test", [x, y], [(1, 2), (2, 3)])
        c.revise(x, y)
        assert x.domain.size == 2
        assert 3 not in x.domain


class TestAC3:
    """AC-3 算法测试。"""

    def test_simple_propagation(self):
        x = Variable("x", Domain([1, 2, 3]))
        y = Variable("y", Domain([1]))
        c = AllDifferentConstraint("test", [x, y])
        ac3 = AC3()
        result = ac3.propagate({"x": x, "y": y}, [c])
        assert result
        assert 1 not in x.domain
        assert x.domain.size == 2

    def test_no_solution(self):
        x = Variable("x", Domain([1]))
        y = Variable("y", Domain([1]))
        c = AllDifferentConstraint("test", [x, y])
        ac3 = AC3()
        result = ac3.propagate({"x": x, "y": y}, [c])
        assert not result  # 无解

    def test_chain_propagation(self):
        x = Variable("x", Domain([1, 2]))
        y = Variable("y", Domain([1, 2]))
        z = Variable("z", Domain([1]))
        c1 = AllDifferentConstraint("c1", [x, y])
        c2 = AllDifferentConstraint("c2", [y, z])
        ac3 = AC3()
        result = ac3.propagate(
            {"x": x, "y": y, "z": z}, [c1, c2]
        )
        assert result
        assert 1 not in y.domain  # y 不能等于 z=1
        assert 2 not in x.domain  # x 不能等于 y=2


class TestCSPSolver:
    """CSP 求解器测试。"""

    def test_simple_csp(self):
        solver = CSPSolver()
        x = solver.add_variable("x", [1, 2, 3])
        y = solver.add_variable("y", [1, 2, 3])
        solver.add_all_different([x, y])
        result = solver.solve()
        assert result is not None
        assert result["x"] != result["y"]

    def test_linear_constraint(self):
        solver = CSPSolver()
        x = solver.add_variable("x", [1, 2, 3, 4, 5])
        y = solver.add_variable("y", [1, 2, 3, 4, 5])
        solver.add_linear([x, y], "x + y == 5")
        result = solver.solve()
        assert result is not None
        assert result["x"] + result["y"] == 5

    def test_no_solution(self):
        solver = CSPSolver()
        x = solver.add_variable("x", [1])
        y = solver.add_variable("y", [1])
        solver.add_all_different([x, y])
        result = solver.solve()
        assert result is None

    def test_multiple_solutions(self):
        solver = CSPSolver()
        x = solver.add_variable("x", [1, 2])
        y = solver.add_variable("y", [1, 2])
        solver.add_all_different([x, y])
        solutions = solver.solve_all()
        assert len(solutions) == 2

    def test_three_variables(self):
        solver = CSPSolver()
        x = solver.add_variable("x", [1, 2, 3])
        y = solver.add_variable("y", [1, 2, 3])
        z = solver.add_variable("z", [1, 2, 3])
        solver.add_all_different([x, y, z])
        result = solver.solve()
        assert result is not None
        assert len(set(result.values())) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
