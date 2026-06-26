"""Example: Simple 2D sketch solver for rectangles and triangles."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.entities import Point
from src.constraints import (
    DistanceConstraint,
    PerpendicularConstraint,
    HorizontalConstraint,
    VerticalConstraint,
)
from src.constraint_graph import ConstraintGraph
from src.solver import NewtonRaphsonSolver, SolverConfig


def solve_rectangle():
    """Solve a rectangle given one corner and two dimensions.

    Rectangle ABCD:
        A(0, 0)  - fixed anchor
        B(w, 0)  - constrained by horizontal and distance from A
        C(w, h)  - constrained by vertical from B and distance from B
        D(0, h)  - constrained by vertical from A and distance from D to C
    """
    print("=" * 60)
    print("Example 1: Rectangle Solver")
    print("=" * 60)

    # Create points
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(0.0, 0.0, name="B")
    C = Point(0.0, 0.0, name="C")
    D = Point(0.0, 0.0, name="D")

    points = [A, B, C, D]
    width = 5.0
    height = 3.0

    # Build constraint graph
    graph = ConstraintGraph()
    for p in points:
        graph.add_entity(p)

    # Add constraints
    constraints = [
        # AB is horizontal with length = width
        HorizontalConstraint(A, B),
        DistanceConstraint(A, B, width),

        # BC is vertical with length = height
        VerticalConstraint(B, C),
        DistanceConstraint(B, C, height),

        # CD is horizontal with length = width
        HorizontalConstraint(C, D),
        DistanceConstraint(C, D, width),

        # DA is vertical with length = height
        VerticalConstraint(D, A),
        DistanceConstraint(D, A, height),
    ]

    for c in constraints:
        graph.add_constraint(c)

    # Analyze system
    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem analysis:")
    print(f"  Status: {analysis['constraint_analysis']['status']}")
    print(f"  Degrees of freedom: {analysis['constraint_analysis']['degrees_of_freedom']}")
    print(f"  Variables: {analysis['constraint_analysis']['num_variables']}")
    print(f"  Constraints: {analysis['constraint_analysis']['num_constraints']}")

    # Solve
    print("\nSolving...")
    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! Final residual: {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! Final residual: {history[-1]:.2e}")

    # Update points
    solver.system.update_points(solution)

    # Print results
    print("\nResults:")
    for p in points:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    # Verify constraints
    print("\nConstraint verification:")
    for c in constraints:
        vals = np.array([
            A.x, A.y, B.x, B.y, C.x, C.y, D.x, D.y
        ])
        satisfied = c.check_satisfied(vals)
        print(f"  {c.constraint_type.name}: {'OK' if satisfied else 'FAIL'} "
              f"(residual={c.residual(vals):.2e})")

    return points


def solve_triangle():
    """Solve a triangle given three side lengths (SSS construction).

    Triangle ABC:
        A(0, 0)  - fixed anchor
        B(c, 0)  - constrained by horizontal and distance from A
        C        - constrained by distances from A and B
    """
    print("\n" + "=" * 60)
    print("Example 2: Triangle Solver (SSS)")
    print("=" * 60)

    # Create points
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(0.0, 0.0, name="B")
    C = Point(0.0, 0.0, name="C")

    points = [A, B, C]
    side_a = 4.0  # BC
    side_b = 5.0  # AC
    side_c = 3.0  # AB

    # Build constraint graph
    graph = ConstraintGraph()
    for p in points:
        graph.add_entity(p)

    # Add constraints
    constraints = [
        DistanceConstraint(A, B, side_c),  # AB = 3
        DistanceConstraint(B, C, side_a),  # BC = 4
        DistanceConstraint(A, C, side_b),  # AC = 5
    ]

    for c in constraints:
        graph.add_constraint(c)

    # Analyze
    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem analysis:")
    print(f"  Status: {analysis['constraint_analysis']['status']}")
    print(f"  Degrees of freedom: {analysis['constraint_analysis']['degrees_of_freedom']}")

    # Solve
    print("\nSolving...")
    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! Final residual: {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! Final residual: {history[-1]:.2e}")

    # Update points
    solver.system.update_points(solution)

    # Print results
    print("\nResults:")
    for p in points:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    # Verify
    print("\nSide lengths:")
    print(f"  AB = {A.distance_to(B):.4f} (target: {side_c})")
    print(f"  BC = {B.distance_to(C):.4f} (target: {side_a})")
    print(f"  AC = {A.distance_to(C):.4f} (target: {side_b})")

    # Calculate angle using law of cosines
    cos_C = (side_a**2 + side_b**2 - side_c**2) / (2 * side_a * side_b)
    angle_C = np.arccos(np.clip(cos_C, -1, 1))
    print(f"\nAngle C (by law of cosines): {np.degrees(angle_C):.2f} degrees")

    return points


def solve_equilateral_triangle():
    """Solve an equilateral triangle with base on x-axis."""
    print("\n" + "=" * 60)
    print("Example 3: Equilateral Triangle")
    print("=" * 60)

    side = 4.0
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(side, 0.0, name="B")
    C = Point(0.0, 0.0, name="C")

    # B is fixed by distance from A + horizontal
    # C needs two distance constraints
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

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem analysis:")
    print(f"  Status: {analysis['constraint_analysis']['status']}")
    print(f"  Degrees of freedom: {analysis['constraint_analysis']['degrees_of_freedom']}")

    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! Final residual: {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! Final residual: {history[-1]:.2e}")

    solver.system.update_points(solution)

    print("\nResults:")
    for p in [A, B, C]:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    print("\nSide lengths:")
    print(f"  AB = {A.distance_to(B):.4f}")
    print(f"  BC = {B.distance_to(C):.4f}")
    print(f"  AC = {A.distance_to(C):.4f}")

    return [A, B, C]


if __name__ == '__main__':
    solve_rectangle()
    solve_triangle()
    solve_equilateral_triangle()
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
