"""Unit tests for constraint solver modules."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from src.entities import Point, Line, Circle
from src.constraints import (
    DistanceConstraint,
    AngleConstraint,
    ParallelConstraint,
    PerpendicularConstraint,
    CollinearConstraint,
    ConcentricConstraint,
    TangentConstraint,
    EqualRadiusConstraint,
    MidpointConstraint,
    HorizontalConstraint,
    VerticalConstraint,
    ConstraintType,
    create_constraint,
)
from src.constraint_graph import (
    ConstraintGraph,
    ConstraintPropagationEngine,
    DependencyAnalyzer,
    OverUnderAnalyzer,
)
from src.solver import (
    NewtonRaphsonSolver,
    SolverConfig,
    ConstraintSystem,
)


class TestPoint:
    """Tests for the Point class."""

    def test_point_creation(self):
        p = Point(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0
        assert not p.fixed

    def test_point_fixed(self):
        p = Point(0.0, 0.0, fixed=True)
        assert p.fixed

    def test_point_to_array(self):
        p = Point(3.0, 4.0)
        arr = p.to_array()
        np.testing.assert_array_equal(arr, [3.0, 4.0])

    def test_point_from_array(self):
        p = Point(0.0, 0.0)
        p.from_array([5.0, 6.0])
        assert p.x == 5.0
        assert p.y == 6.0

    def test_point_distance(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        assert p1.distance_to(p2) == pytest.approx(5.0)

    def test_point_angle(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 0.0)
        assert p1.angle_to(p2) == pytest.approx(0.0)

    def test_point_equality(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0, 0.0)
        assert p1 == p1
        assert p1 != p2


class TestDistanceConstraint:
    """Tests for distance constraints."""

    def test_distance_zero(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(3.0, 4.0)
        c = DistanceConstraint(p1, p2, 5.0)
        p2.fixed_idx = 0
        vals = np.array([p2.x, p2.y])
        assert c.residual(vals) == pytest.approx(0.0)

    def test_distance_wrong(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 0.0)
        c = DistanceConstraint(p1, p2, 5.0)
        p2.fixed_idx = 0
        vals = np.array([p2.x, p2.y])
        assert c.residual(vals) == pytest.approx(-4.0)

    def test_check_satisfied(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(3.0, 4.0)
        c = DistanceConstraint(p1, p2, 5.0)
        p2.fixed_idx = 0
        vals = np.array([p2.x, p2.y])
        assert c.check_satisfied(vals)

    def test_jacobian_indices(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(3.0, 4.0)
        c = DistanceConstraint(p1, p2, 5.0)
        p2.fixed_idx = 0
        indices = c.jacobian_indices()
        assert len(indices) == 2

    def test_jacobian_indices_all_fixed(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(3.0, 4.0, fixed=True)
        c = DistanceConstraint(p1, p2, 5.0)
        indices = c.jacobian_indices()
        assert len(indices) == 0


class TestPerpendicularConstraint:
    """Tests for perpendicular constraints."""

    def test_perpendicular(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 0.0)
        p3 = Point(0.0, 0.0, fixed=True)
        p4 = Point(0.0, 1.0)
        c = PerpendicularConstraint(p1, p2, p3, p4)
        p2.fixed_idx, p4.fixed_idx = 0, 1
        vals = np.array([p2.x, p2.y, p4.x, p4.y])
        assert c.residual(vals) == pytest.approx(0.0)

    def test_not_perpendicular(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        p3 = Point(0.0, 0.0, fixed=True)
        p4 = Point(0.0, 1.0)
        c = PerpendicularConstraint(p1, p2, p3, p4)
        p2.fixed_idx, p4.fixed_idx = 0, 1
        vals = np.array([p2.x, p2.y, p4.x, p4.y])
        assert abs(c.residual(vals)) > 0.0


class TestParallelConstraint:
    """Tests for parallel constraints."""

    def test_parallel(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        p3 = Point(0.0, 0.0, fixed=True)
        p4 = Point(2.0, 2.0)
        c = ParallelConstraint(p1, p2, p3, p4)
        p2.fixed_idx = 0  # x at 0, y at 1
        p4.fixed_idx = 2  # x at 2, y at 3
        vals = np.array([1.0, 1.0, 2.0, 2.0])
        assert c.residual(vals) == pytest.approx(0.0)

    def test_not_parallel(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 0.0)
        p3 = Point(0.0, 0.0, fixed=True)
        p4 = Point(0.0, 1.0)
        c = ParallelConstraint(p1, p2, p3, p4)
        p2.fixed_idx = 0
        p4.fixed_idx = 2
        vals = np.array([1.0, 0.0, 0.0, 1.0])
        assert abs(c.residual(vals)) > 0.0


class TestCollinearConstraint:
    """Tests for collinear constraints."""

    def test_collinear(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        p3 = Point(2.0, 2.0)
        c = CollinearConstraint([p1, p2, p3])
        # fixed_idx maps to x-index in global vector
        p2.fixed_idx = 0
        p3.fixed_idx = 2
        vals = np.array([1.0, 1.0, 2.0, 2.0])
        assert c.residual(vals) == pytest.approx(0.0)

    def test_not_collinear(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 0.0)
        p3 = Point(0.0, 1.0)
        c = CollinearConstraint([p1, p2, p3])
        p2.fixed_idx = 0
        p3.fixed_idx = 2
        vals = np.array([1.0, 0.0, 0.0, 1.0])
        assert c.residual(vals) > 0.0

    def test_requires_three_points(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 1.0)
        with pytest.raises(ValueError):
            CollinearConstraint([p1, p2])


class TestMidpointConstraint:
    """Tests for midpoint constraints."""

    def test_midpoint(self):
        mid = Point(1.0, 1.0)
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(2.0, 2.0)
        c = MidpointConstraint(mid, p1, p2)
        mid.fixed_idx = 0
        p2.fixed_idx = 2
        vals = np.array([1.0, 1.0, 2.0, 2.0])
        assert c.residual(vals) == pytest.approx(0.0)

    def test_not_midpoint(self):
        mid = Point(0.5, 0.5)
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(2.0, 2.0)
        c = MidpointConstraint(mid, p1, p2)
        mid.fixed_idx, p2.fixed_idx = 0, 1
        vals = np.array([mid.x, mid.y, p2.x, p2.y])
        assert c.residual(vals) > 0.0


class TestConstraintGraph:
    """Tests for constraint graph."""

    def test_add_entity(self):
        graph = ConstraintGraph()
        p = Point(0.0, 0.0)
        graph.add_entity(p)
        assert p.id in graph.entity_nodes

    def test_add_constraint(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c)
        assert c.id in graph.constraint_nodes

    def test_remove_constraint(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c)
        graph.remove_constraint(c.id)
        assert c.id not in graph.constraint_nodes

    def test_get_entities_for_type(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c)
        dists = graph.get_entities_for_type(ConstraintType.DISTANCE)
        assert len(dists) == 1


class TestConstraintPropagation:
    """Tests for constraint propagation engine."""

    def test_propagation_fixed_points(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 5.0)
        graph.add_constraint(c)

        engine = ConstraintPropagationEngine(graph)
        propagated, remaining = engine.propagate()
        assert p1.id in engine.known_entities

    def test_reset(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        graph.add_entity(p1)
        engine = ConstraintPropagationEngine(graph)
        engine.known_entities.add(p1.id)
        engine.reset()
        assert p1.id not in engine.known_entities


class TestDependencyAnalyzer:
    """Tests for dependency analysis."""

    def test_constrained_system(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        # 2 free variables (p2.x, p2.y)
        # Need 2 constraints to fully constrain
        c1 = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c1)

        analyzer = DependencyAnalyzer(graph)
        result = analyzer.analyze()
        assert result['status'] == 'under-constrained'
        assert result['dof'] == 1  # 2 vars - 1 constraint

    def test_over_constrained(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        # 2 constraints on 2 variables -> constrained (not over)
        c1 = DistanceConstraint(p1, p2, 1.0)
        c2 = DistanceConstraint(p1, p2, 2.0)
        graph.add_constraint(c1)
        graph.add_constraint(c2)

        analyzer = DependencyAnalyzer(graph)
        result = analyzer.analyze()
        assert result['status'] == 'constrained'


class TestOverUnderAnalyzer:
    """Tests for over/under constraint detection."""

    def test_under_constrained(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)

        analyzer = OverUnderAnalyzer(graph)
        result = analyzer.check()
        assert result['status'] == 'under-constrained'
        assert result['missing_constraints'] == 2

    def test_constrained(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c1 = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c1)
        # Need 2 constraints for 2 DOF, only have 1 -> under

        analyzer = OverUnderAnalyzer(graph)
        result = analyzer.check()
        assert result['status'] == 'under-constrained'


class TestNewtonRaphsonSolver:
    """Tests for the Newton-Raphson solver."""

    def test_solve_circle(self):
        """Solve for a point at distance 5 from origin (circle intersection)."""
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 0.0)  # Initial guess

        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)

        # Add two distance constraints to fix both coordinates
        c1 = DistanceConstraint(p1, p2, 5.0)
        graph.add_constraint(c1)

        solver = NewtonRaphsonSolver(config=SolverConfig(
            max_iterations=100,
            tolerance=1e-8,
            verbose=False,
        ))
        solution, converged, history = solver.solve(graph)

        assert converged
        assert len(history) > 0
        assert history[-1] < 1e-6

    def test_solve_rectangle(self):
        """Solve a simple rectangle."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)
        C = Point(1.0, 1.0)
        D = Point(0.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C, D]:
            graph.add_entity(p)

        constraints = [
            HorizontalConstraint(A, B),
            DistanceConstraint(A, B, 5.0),
            VerticalConstraint(B, C),
            DistanceConstraint(B, C, 3.0),
            HorizontalConstraint(C, D),
            DistanceConstraint(C, D, 5.0),
            VerticalConstraint(D, A),
            DistanceConstraint(D, A, 3.0),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # Verify rectangle dimensions
        assert abs(A.distance_to(B) - 5.0) < 1e-5
        assert abs(B.distance_to(C) - 3.0) < 1e-5

    def test_solve_triangle(self):
        """Solve a triangle with given side lengths."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)
        C = Point(1.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C]:
            graph.add_entity(p)

        constraints = [
            DistanceConstraint(A, B, 3.0),
            DistanceConstraint(A, C, 4.0),
            DistanceConstraint(B, C, 5.0),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # Verify side lengths
        assert abs(A.distance_to(B) - 3.0) < 1e-5
        assert abs(A.distance_to(C) - 4.0) < 1e-5
        assert abs(B.distance_to(C) - 5.0) < 1e-5

    def test_solve_equilateral_triangle(self):
        """Solve an equilateral triangle."""
        side = 4.0
        A = Point(0.0, 0.0, fixed=True)
        B = Point(side, 0.0)
        C = Point(side / 2, 1.0)  # Initial guess for third vertex

        graph = ConstraintGraph()
        for p in [A, B, C]:
            graph.add_entity(p)

        constraints = [
            DistanceConstraint(A, B, side),
            DistanceConstraint(A, C, side),
            DistanceConstraint(B, C, side),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # All sides should be equal to 'side'
        assert abs(A.distance_to(B) - side) < 1e-5
        assert abs(A.distance_to(C) - side) < 1e-5
        assert abs(B.distance_to(C) - side) < 1e-5

    def test_solve_over_constrained(self):
        """Test handling of over-constrained system."""
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)

        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)

        # Conflicting distance constraints
        c1 = DistanceConstraint(p1, p2, 1.0)
        c2 = DistanceConstraint(p1, p2, 2.0)
        graph.add_constraint(c1)
        graph.add_constraint(c2)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        # Should still converge to least-squares solution
        assert solution is not None
        assert len(history) > 0
        assert len(history) > 1  # Multiple iterations recorded

    def test_solve_no_free_variables(self):
        """Test when all points are fixed."""
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0, fixed=True)

        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert len(solution) == 0

    def test_solve_no_free_variables(self):
        """Test when all points are fixed."""
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0, fixed=True)

        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert len(solution) == 0

    def test_analyze_system(self):
        """Test system analysis."""
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)

        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        analysis = solver.analyze_system(graph)

        assert 'constraint_analysis' in analysis
        assert 'dependency_analysis' in analysis
        assert analysis['constraint_analysis']['status'] == 'under-constrained'


class TestCreateConstraint:
    """Tests for constraint factory function."""

    def test_create_distance(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 1.0)
        c = create_constraint(ConstraintType.DISTANCE, p1, p2, 1.0)
        assert isinstance(c, DistanceConstraint)

    def test_create_perpendicular(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 0.0)
        p3 = Point(0.0, 0.0)
        p4 = Point(0.0, 1.0)
        c = create_constraint(ConstraintType.PERPENDICULAR, p1, p2, p3, p4)
        assert isinstance(c, PerpendicularConstraint)

    def test_create_horizontal(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(1.0, 0.0)
        c = create_constraint(ConstraintType.HORIZONTAL, p1, p2)
        assert isinstance(c, HorizontalConstraint)

    def test_create_vertical(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0, 1.0)
        c = create_constraint(ConstraintType.VERTICAL, p1, p2)
        assert isinstance(c, VerticalConstraint)

    def test_create_midpoint(self):
        mid = Point(1.0, 1.0)
        p1 = Point(0.0, 0.0)
        p2 = Point(2.0, 2.0)
        c = create_constraint(ConstraintType.MIDPOINT, mid, p1, p2)
        assert isinstance(c, MidpointConstraint)

    def test_create_unknown_type(self):
        with pytest.raises(ValueError):
            create_constraint(ConstraintType.SYMMETRY, None)


class TestConstraintSystem:
    """Tests for the ConstraintSystem class."""

    def test_build_system(self):
        graph = ConstraintGraph()
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(1.0, 1.0)
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 1.0)
        graph.add_constraint(c)

        system = ConstraintSystem(graph)
        system.build()

        assert system.num_variables == 2
        assert system.num_equations == 1

    def test_residual_vector(self):
        p1 = Point(0.0, 0.0, fixed=True)
        p2 = Point(3.0, 4.0)
        graph = ConstraintGraph()
        graph.add_entity(p1)
        graph.add_entity(p2)
        c = DistanceConstraint(p1, p2, 5.0)
        graph.add_constraint(c)

        system = ConstraintSystem(graph)
        system.build()

        vals = np.array([p2.x, p2.y])
        F = system.residual_vector(vals)
        assert F[0] == pytest.approx(0.0)


class TestSolverConfig:
    """Tests for solver configuration."""

    def test_default_config(self):
        config = SolverConfig()
        assert config.max_iterations == 100
        assert config.tolerance == 1e-8
        assert config.verbose is False

    def test_custom_config(self):
        config = SolverConfig(
            max_iterations=50,
            tolerance=1e-6,
            verbose=True,
        )
        assert config.max_iterations == 50
        assert config.tolerance == 1e-6
        assert config.verbose is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
