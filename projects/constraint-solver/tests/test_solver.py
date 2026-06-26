"""Test the solver with various geometric configurations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from src.entities import Point
from src.constraints import (
    DistanceConstraint,
    AngleConstraint,
    ParallelConstraint,
    PerpendicularConstraint,
    MidpointConstraint,
    EqualRadiusConstraint,
    HorizontalConstraint,
    VerticalConstraint,
    ConstraintType,
)
from src.constraint_graph import ConstraintGraph
from src.solver import NewtonRaphsonSolver, SolverConfig


class TestSolverExamples:
    """Integration tests for solver with realistic examples."""

    def test_solve_square(self):
        """Solve a square with side length 4."""
        side = 4.0
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)
        C = Point(1.0, 1.0)
        D = Point(0.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C, D]:
            graph.add_entity(p)

        constraints = [
            HorizontalConstraint(A, B),
            DistanceConstraint(A, B, side),
            VerticalConstraint(B, C),
            DistanceConstraint(B, C, side),
            HorizontalConstraint(C, D),
            DistanceConstraint(C, D, side),
            VerticalConstraint(D, A),
            DistanceConstraint(D, A, side),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # Verify square dimensions
        assert abs(A.distance_to(B) - side) < 1e-5
        assert abs(B.distance_to(C) - side) < 1e-5
        assert abs(C.distance_to(D) - side) < 1e-5
        assert abs(D.distance_to(A) - side) < 1e-5

    def test_solve_right_angle_at_origin(self):
        """Solve two perpendicular lines meeting at origin."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)
        C = Point(0.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C]:
            graph.add_entity(p)

        constraints = [
            HorizontalConstraint(A, B),
            VerticalConstraint(A, C),
            DistanceConstraint(A, B, 3.0),
            DistanceConstraint(A, C, 4.0),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # B should be on x-axis, C on y-axis
        assert abs(B.y) < 1e-5
        assert abs(C.x) < 1e-5
        assert abs(A.distance_to(B) - 3.0) < 1e-5
        assert abs(A.distance_to(C) - 4.0) < 1e-5

    def test_solve_midpoint(self):
        """Solve a midpoint constraint."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(4.0, 4.0)
        M = Point(1.0, 1.0)  # Initial guess

        graph = ConstraintGraph()
        for p in [A, B, M]:
            graph.add_entity(p)

        constraints = [
            DistanceConstraint(A, B, 5.0),
            MidpointConstraint(M, A, B),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        # M should be at midpoint of AB
        mx = (A.x + B.x) / 2.0
        my = (A.y + B.y) / 2.0
        assert abs(M.x - mx) < 1e-5
        assert abs(M.y - my) < 1e-5

    def test_solve_angle_constraint(self):
        """Solve with an angle constraint."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)
        C = Point(1.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C]:
            graph.add_entity(p)

        angle_60 = np.pi / 3  # 60 degrees

        constraints = [
            HorizontalConstraint(A, B),
            DistanceConstraint(A, B, 3.0),
            DistanceConstraint(A, C, 3.0),
            AngleConstraint(A, B, A, C, angle_60),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        assert abs(A.distance_to(B) - 3.0) < 1e-5
        assert abs(A.distance_to(C) - 3.0) < 1e-5

    def test_solve_parallel_lines(self):
        """Solve two parallel lines of equal length."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(3.0, 0.0)
        C = Point(1.0, 1.0)
        D = Point(4.0, 1.0)

        graph = ConstraintGraph()
        for p in [A, B, C, D]:
            graph.add_entity(p)

        constraints = [
            HorizontalConstraint(A, B),
            DistanceConstraint(A, B, 3.0),
            HorizontalConstraint(C, D),
            DistanceConstraint(C, D, 3.0),
            ParallelConstraint(A, B, C, D),
            DistanceConstraint(A, C, 2.0),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)

        assert abs(A.distance_to(B) - 3.0) < 1e-5
        assert abs(C.distance_to(D) - 3.0) < 1e-5

    def test_solve_equal_radius(self):
        """Test equal radius constraint (requires Circle entities)."""
        from src.entities import Circle

        center1 = Point(0.0, 0.0, fixed=True)
        center2 = Point(3.0, 0.0)

        c1 = Circle(center1, 2.0)
        c2 = Circle(center2, 1.0)

        graph = ConstraintGraph()
        for p in [center1, center2]:
            graph.add_entity(p)

        constraints = [
            DistanceConstraint(center1, center2, 5.0),
            EqualRadiusConstraint(c1, c2),
        ]
        for c in constraints:
            graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        # Equal radius constraint doesn't affect point positions directly
        # but should not cause errors
        assert converged

    def test_solver_convergence_history(self):
        """Test that solver records convergence history."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 0.0)

        graph = ConstraintGraph()
        graph.add_entity(A)
        graph.add_entity(B)

        c = DistanceConstraint(A, B, 3.0)
        graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        assert len(history) > 0
        assert history[-1] < history[0]  # Should converge (decrease)

    def test_solver_with_bad_initial_guess(self):
        """Test solver with initial guess far from solution."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(100.0, 100.0)  # Far from target

        graph = ConstraintGraph()
        graph.add_entity(A)
        graph.add_entity(B)

        c = DistanceConstraint(A, B, 1.0)
        graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(
            verbose=False,
            step_limit=10.0,
            damping=0.8,
        ))
        solution, converged, history = solver.solve(graph)

        # Should still converge with damping
        assert converged


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_point_no_constraints(self):
        """Single fixed point with no constraints."""
        A = Point(0.0, 0.0, fixed=True)

        graph = ConstraintGraph()
        graph.add_entity(A)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert len(solution) == 0

    def test_all_fixed_points(self):
        """All points are fixed - no solving needed."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 1.0, fixed=True)

        graph = ConstraintGraph()
        graph.add_entity(A)
        graph.add_entity(B)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert len(solution) == 0

    def test_zero_length_distance(self):
        """Distance constraint with zero target distance."""
        A = Point(0.0, 0.0, fixed=True)
        B = Point(1.0, 1.0)

        graph = ConstraintGraph()
        graph.add_entity(A)
        graph.add_entity(B)

        c = DistanceConstraint(A, B, 0.0)
        graph.add_constraint(c)

        solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
        solution, converged, history = solver.solve(graph)

        assert converged
        solver.system.update_points(solution)
        assert abs(A.distance_to(B)) < 1e-5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
