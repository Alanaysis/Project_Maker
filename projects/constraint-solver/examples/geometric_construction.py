"""Example: Geometric construction - constructing shapes from constraints."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.entities import Point
from src.constraints import (
    DistanceConstraint,
    PerpendicularConstraint,
    ParallelConstraint,
    AngleConstraint,
    HorizontalConstraint,
    VerticalConstraint,
    MidpointConstraint,
    EqualRadiusConstraint,
)
from src.constraint_graph import ConstraintGraph
from src.solver import NewtonRaphsonSolver, SolverConfig


def construct_right_triangle():
    """Construct a right triangle with specific side lengths.

    Uses perpendicular constraint to enforce the right angle.
    """
    print("=" * 60)
    print("Geometric Construction: Right Triangle")
    print("=" * 60)

    a, b = 3.0, 4.0  # legs

    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(a, 0.0, name="B")  # B on x-axis
    C = Point(0.0, 0.0, name="C")

    graph = ConstraintGraph()
    for p in [A, B, C]:
        graph.add_entity(p)

    constraints = [
        DistanceConstraint(A, B, a),  # AB = a
        DistanceConstraint(A, C, b),  # AC = b
        PerpendicularConstraint(A, B, A, C),  # angle at A = 90 degrees
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem: {analysis['constraint_analysis']['status']}")
    print(f"  DOF: {analysis['constraint_analysis']['degrees_of_freedom']}")

    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! residual = {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! residual = {history[-1]:.2e}")

    solver.system.update_points(solution)

    print("\nVertices:")
    for p in [A, B, C]:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    hyp = B.distance_to(C)
    print(f"\nHypotenuse BC = {hyp:.4f} (expected: {np.sqrt(a**2 + b**2):.4f})")

    return [A, B, C]


def construct_parallelogram():
    """Construct a parallelogram with given side lengths and angle.

    Constraints:
    - AB = given length
    - AD = given length
    - Angle BAD = given angle
    - BC parallel to AD
    - DC parallel to AB
    """
    print("\n" + "=" * 60)
    print("Geometric Construction: Parallelogram")
    print("=" * 60)

    ab_len = 5.0
    ad_len = 3.0
    angle_deg = 60.0
    angle_rad = np.radians(angle_deg)

    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(ab_len, 0.0, name="B")
    D = Point(0.0, 0.0, name="D")
    C = Point(0.0, 0.0, name="C")

    graph = ConstraintGraph()
    for p in [A, B, C, D]:
        graph.add_entity(p)

    constraints = [
        # AB is horizontal with length ab_len
        HorizontalConstraint(A, B),
        DistanceConstraint(A, B, ab_len),

        # AD has length ad_len and angle
        DistanceConstraint(A, D, ad_len),
        AngleConstraint(A, B, A, D, angle_rad),

        # BC parallel to AD
        ParallelConstraint(B, C, A, D),

        # DC parallel to AB
        ParallelConstraint(D, C, A, B),
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem: {analysis['constraint_analysis']['status']}")
    print(f"  DOF: {analysis['constraint_analysis']['degrees_of_freedom']}")

    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! residual = {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! residual = {history[-1]:.2e}")

    solver.system.update_points(solution)

    print("\nVertices:")
    for p in [A, B, C, D]:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    # Verify properties
    print("\nVerification:")
    print(f"  AB = {A.distance_to(B):.4f} (target: {ab_len})")
    print(f"  AD = {A.distance_to(D):.4f} (target: {ad_len})")
    print(f"  BC = {B.distance_to(C):.4f} (target: {ad_len})")
    print(f"  DC = {D.distance_to(C):.4f} (target: {ab_len})")

    return [A, B, C, D]


def construct_kite():
    """Construct a kite shape (two pairs of equal adjacent sides).

    A kite has:
    - AB = AD (one pair of equal adjacent sides)
    - CB = CD (second pair of equal adjacent sides)
    - Diagonal AC is the axis of symmetry
    """
    print("\n" + "=" * 60)
    print("Geometric Construction: Kite")
    print("=" * 60)

    ab_len = 4.0
    cb_len = 3.0

    A = Point(0.0, 0.0, fixed=True, name="A")
    C = Point(6.0, 0.0, name="C")  # C on x-axis (axis of symmetry)
    B = Point(0.0, 0.0, name="B")
    D = Point(0.0, 0.0, name="D")

    graph = ConstraintGraph()
    for p in [A, B, C, D]:
        graph.add_entity(p)

    constraints = [
        # B and D are symmetric about AC (x-axis)
        DistanceConstraint(A, B, ab_len),
        DistanceConstraint(A, D, ab_len),
        DistanceConstraint(C, B, cb_len),
        DistanceConstraint(C, D, cb_len),

        # B and D symmetric about x-axis
        HorizontalConstraint(B, D),
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem: {analysis['constraint_analysis']['status']}")
    print(f"  DOF: {analysis['constraint_analysis']['degrees_of_freedom']}")

    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! residual = {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! residual = {history[-1]:.2e}")

    solver.system.update_points(solution)

    print("\nVertices:")
    for p in [A, B, C, D]:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    print("\nVerification:")
    print(f"  AB = {A.distance_to(B):.4f} (target: {ab_len})")
    print(f"  AD = {A.distance_to(D):.4f} (target: {ab_len})")
    print(f"  CB = {C.distance_to(B):.4f} (target: {cb_len})")
    print(f"  CD = {C.distance_to(D):.4f} (target: {cb_len})")

    return [A, B, C, D]


def construct_regular_hexagon():
    """Construct a regular hexagon centered at origin.

    All sides equal, all internal angles = 120 degrees.
    """
    print("\n" + "=" * 60)
    print("Geometric Construction: Regular Hexagon")
    print("=" * 60)

    side = 2.0
    angle_60 = np.pi / 3  # 60 degrees

    # Fix first two vertices to remove rigid body motion
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(side, 0.0, name="B")
    C = Point(0.0, 0.0, name="C")
    D = Point(0.0, 0.0, name="D")
    E = Point(0.0, 0.0, name="E")
    F = Point(0.0, 0.0, name="F")

    graph = ConstraintGraph()
    for p in [A, B, C, D, E, F]:
        graph.add_entity(p)

    constraints = [
        # All sides equal to 'side'
        DistanceConstraint(A, B, side),
        DistanceConstraint(B, C, side),
        DistanceConstraint(C, D, side),
        DistanceConstraint(D, E, side),
        DistanceConstraint(E, F, side),
        DistanceConstraint(F, A, side),

        # Internal angles = 120 degrees (pi - 60)
        AngleConstraint(B, A, B, C, np.pi - angle_60),
        AngleConstraint(A, B, C, D, np.pi - angle_60),
        AngleConstraint(B, C, D, E, np.pi - angle_60),
        AngleConstraint(C, D, E, F, np.pi - angle_60),
        AngleConstraint(D, E, F, A, np.pi - angle_60),
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=True))
    analysis = solver.analyze_system(graph)
    print(f"\nSystem: {analysis['constraint_analysis']['status']}")
    print(f"  DOF: {analysis['constraint_analysis']['degrees_of_freedom']}")

    solution, converged, history = solver.solve(graph)

    if converged:
        print(f"\nConverged! residual = {history[-1]:.2e}")
    else:
        print(f"\nDid not converge! residual = {history[-1]:.2e}")

    solver.system.update_points(solution)

    print("\nVertices:")
    for p in [A, B, C, D, E, F]:
        print(f"  {p.name}: ({p.x:.4f}, {p.y:.4f})")

    print("\nSide lengths (all should be ~{side}):")
    sides = [(A, B), (B, C), (C, D), (D, E), (E, F), (F, A)]
    for i, (p1, p2) in enumerate(sides):
        print(f"  Side {i+1}: {p1.distance_to(p2):.4f}")

    return [A, B, C, D, E, F]


if __name__ == '__main__':
    construct_right_triangle()
    construct_parallelogram()
    construct_kite()
    construct_regular_hexagon()
    print("\n" + "=" * 60)
    print("All geometric constructions completed!")
    print("=" * 60)
