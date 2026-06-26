"""Interactive constraint solver with matplotlib visualization.

Run this example to see constraint solving in action with visual output.
Requires matplotlib to be installed.
"""

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
    MidpointConstraint,
)
from src.constraint_graph import ConstraintGraph
from src.solver import NewtonRaphsonSolver, SolverConfig


def visualize_rectangle():
    """Visualize rectangle constraint solving."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping visualization")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- Initial state (under-constrained) ---
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(3.0, 0.0, name="B")
    C = Point(3.0, 2.0, name="C")
    D = Point(0.0, 2.0, name="D")

    ax1.set_aspect('equal')
    ax1.set_title("Initial Positions", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='k', linewidth=0.5)
    ax1.axvline(x=0, color='k', linewidth=0.5)

    for p in [A, B, C, D]:
        ax1.plot(p.x, p.y, 'bo', markersize=8)
        ax1.text(p.x + 0.15, p.y + 0.15, p.name, fontsize=10)

    # Draw initial edges
    edges = [(A, B), (B, C), (C, D), (D, A)]
    for p1, p2 in edges:
        ax1.plot([p1.x, p2.x], [p1.y, p2.y], 'b--', alpha=0.3)

    # --- Solve for rectangle ---
    A2 = Point(0.0, 0.0, fixed=True, name="A")
    B2 = Point(1.0, 1.0, name="B")
    C2 = Point(1.0, 1.0, name="C")
    D2 = Point(1.0, 1.0, name="D")

    graph = ConstraintGraph()
    for p in [A2, B2, C2, D2]:
        graph.add_entity(p)

    constraints = [
        HorizontalConstraint(A2, B2),
        DistanceConstraint(A2, B2, 5.0),
        VerticalConstraint(B2, C2),
        DistanceConstraint(B2, C2, 3.0),
        HorizontalConstraint(C2, D2),
        DistanceConstraint(C2, D2, 5.0),
        VerticalConstraint(D2, A2),
        DistanceConstraint(D2, A2, 3.0),
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
    solution, converged, history = solver.solve(graph)
    solver.system.update_points(solution)

    ax2.set_aspect('equal')
    ax2.set_title("After Constraint Solving", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.axvline(x=0, color='k', linewidth=0.5)

    for p in [A2, B2, C2, D2]:
        ax2.plot(p.x, p.y, 'ro', markersize=10)
        ax2.text(p.x + 0.15, p.y + 0.15, p.name, fontsize=10)

    for p1, p2 in edges:
        ax2.plot([p1.x, p2.x], [p1.y, p2.y], 'r-', linewidth=2)

    # Add convergence plot
    ax3 = fig.add_subplot(1, 2, 3) if False else None

    plt.tight_layout()
    plt.savefig('/tmp/constraint_solver_rectangle.png', dpi=100, bbox_inches='tight')
    print("Visualization saved to /tmp/constraint_solver_rectangle.png")

    plt.close()


def visualize_convergence():
    """Visualize the convergence history of the solver."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available")
        return

    # Solve a triangle to get convergence data
    A = Point(0.0, 0.0, fixed=True, name="A")
    B = Point(2.0, 0.0, name="B")
    C = Point(1.0, 1.0, name="C")

    graph = ConstraintGraph()
    for p in [A, B, C]:
        graph.add_entity(p)

    constraints = [
        DistanceConstraint(A, B, 4.0),
        DistanceConstraint(A, C, 3.0),
        DistanceConstraint(B, C, 5.0),
    ]

    for c in constraints:
        graph.add_constraint(c)

    solver = NewtonRaphsonSolver(config=SolverConfig(verbose=False))
    solution, converged, history = solver.solve(graph)

    # Plot convergence
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(history, 'b-o', markersize=4)
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Residual Norm', fontsize=12)
    ax.set_title('Newton-Raphson Convergence History', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=1e-8, color='r', linestyle='--', alpha=0.5, label='Tolerance')
    ax.legend()
    plt.tight_layout()
    plt.savefig('/tmp/constraint_solver_convergence.png', dpi=100, bbox_inches='tight')
    print("Convergence plot saved to /tmp/constraint_solver_convergence.png")
    plt.close()


if __name__ == '__main__':
    print("Running constraint solver visualizations...")
    visualize_rectangle()
    visualize_convergence()
    print("Done!")
