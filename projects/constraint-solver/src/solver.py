"""Numerical solver using Newton-Raphson method for geometric constraint solving.

The core idea is to solve a system of non-linear equations:
    F(x) = 0
where x is the vector of unknown variables (coordinates of free points)
and F is the vector of constraint residuals.

Newton-Raphson iteration:
    x_{k+1} = x_k - J(x_k)^{-1} * F(x_k)

For rectangular systems (more equations than variables or vice versa),
we use least-squares: min ||F(x)||^2 via Gauss-Newton.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from .entities import Point
from .constraints import Constraint
from .constraint_graph import ConstraintGraph


class SolverConfig:
    """Configuration for the numerical solver."""

    def __init__(
        self,
        max_iterations: int = 100,
        tolerance: float = 1e-8,
        step_limit: float = 10.0,
        damping: float = 0.8,
        verbose: bool = False,
    ):
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.step_limit = step_limit
        self.damping = damping
        self.verbose = verbose


class ConstraintSystem:
    """Manages mapping between free variables, constraints, and the system."""

    def __init__(self, graph: ConstraintGraph):
        self.graph = graph
        self.point_to_vars: Dict[int, List[int]] = {}  # point_id -> [x_idx, y_idx]
        self.free_points: List[int] = []
        self.active_constraints: List[Constraint] = []
        self.num_variables = 0
        self.num_equations = 0
        # Per-constraint: maps local entity index to global variable index
        self.constraint_var_map: Dict[int, Dict[int, int]] = {}

    def build(self) -> None:
        """Build the variable-constraint mapping."""
        self.point_to_vars.clear()
        self.free_points.clear()
        self.active_constraints.clear()
        self.constraint_var_map.clear()

        # Map free points to global variable indices
        idx = 0
        for point_id, point in self.graph.entity_nodes.items():
            if not point.fixed:
                self.point_to_vars[point_id] = [idx, idx + 1]
                self.free_points.append(point_id)
                idx += 2

        self.num_variables = idx

        # Collect active constraints and build per-constraint variable maps
        for constraint in self.graph.constraint_nodes.values():
            if constraint.active:
                self.active_constraints.append(constraint)
                self._build_constraint_var_map(constraint)

        self.num_equations = sum(c.num_equations() for c in self.active_constraints)

    def _build_constraint_var_map(self, constraint: Constraint) -> None:
        """Build a map from local entity index to global variable index.

        Also sets each point's fixed_idx attribute so constraints can
        directly access the correct position in the global variable vector.
        """
        local_to_global = {}
        for local_idx, entity in enumerate(constraint.entities):
            if entity.fixed:
                local_to_global[local_idx] = None
                entity.fixed_idx = -1  # Mark as fixed
            elif entity.id in self.point_to_vars:
                local_to_global[local_idx] = self.point_to_vars[entity.id]
                entity.fixed_idx = self.point_to_vars[entity.id][0]
            else:
                local_to_global[local_idx] = None
                entity.fixed_idx = -1
        self.constraint_var_map[constraint.id] = local_to_global

    def residual_vector(self, values: np.ndarray) -> np.ndarray:
        """Compute the full residual vector F(x)."""
        F = np.zeros(self.num_equations)
        eq_idx = 0

        for constraint in self.active_constraints:
            for _ in range(constraint.num_equations()):
                F[eq_idx] = constraint.residual(values)
                eq_idx += 1

        return F

    def jacobian_matrix(self, values: np.ndarray) -> np.ndarray:
        """Compute the dense Jacobian matrix J = dF/dx via finite differences."""
        F0 = self.residual_vector(values)
        J = np.zeros((self.num_equations, self.num_variables))

        for i in range(self.num_variables):
            values_plus = values.copy()
            values_plus[i] += 1e-7
            F_plus = self.residual_vector(values_plus)
            dF = (F_plus - F0) / 1e-7
            J[:, i] = dF

        return J

    def update_points(self, values: np.ndarray) -> None:
        """Update point coordinates from solved variable values."""
        for point_id, [x_idx, y_idx] in self.point_to_vars.items():
            point = self.graph.entity_nodes[point_id]
            point.x = values[x_idx]
            point.y = values[y_idx]


class NewtonRaphsonSolver:
    """Newton-Raphson solver for geometric constraint systems."""

    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        self.system: Optional[ConstraintSystem] = None
        self.history: List[float] = []

    def solve(
        self,
        graph: ConstraintGraph,
        initial_guess: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, bool, List[float]]:
        """Solve the constraint system.

        Args:
            graph: Constraint graph with entities and constraints
            initial_guess: Initial values for free variables (optional)

        Returns:
            Tuple of (solution_vector, converged, residual_history)
        """
        self.system = ConstraintSystem(graph)
        self.system.build()

        num_vars = self.system.num_variables

        if num_vars == 0:
            return np.array([]), True, []

        if initial_guess is not None:
            values = initial_guess.copy()
        else:
            values = np.zeros(num_vars)
            for point_id, [x_idx, y_idx] in self.system.point_to_vars.items():
                point = graph.entity_nodes[point_id]
                values[x_idx] = point.x
                values[y_idx] = point.y

        self.history = []
        self._log(f"Solving system: {self.system.num_equations} equations, "
                   f"{num_vars} variables")

        for iteration in range(self.config.max_iterations):
            F = self.system.residual_vector(values)
            residual_norm = np.linalg.norm(F)
            self.history.append(residual_norm)

            self._log(f"  Iter {iteration + 1}: residual = {residual_norm:.2e}")

            if residual_norm < self.config.tolerance:
                self._log(f"  Converged after {iteration + 1} iterations!")
                return values, True, self.history

            J = self.system.jacobian_matrix(values)

            # Gauss-Newton: solve (J^T J) delta = -J^T F
            try:
                JtJ = J.T @ J
                JtF = J.T @ (-F)
                reg = JtJ + 1e-8 * np.eye(num_vars)
                delta = np.linalg.solve(reg, JtF)
            except np.linalg.LinAlgError:
                self._log("  Singular matrix, using least-squares...")
                delta, _, _, _ = np.linalg.lstsq(J, -F, rcond=None)

            delta_norm = np.linalg.norm(delta)
            if delta_norm > self.config.step_limit:
                delta = delta * self.config.step_limit / delta_norm

            values = values + delta

        F = self.system.residual_vector(values)
        residual_norm = np.linalg.norm(F)
        self.history.append(residual_norm)
        converged = residual_norm < self.config.tolerance

        self._log(f"  {'Converged' if converged else 'Did not converge'}: "
                   f"final residual = {residual_norm:.2e}")

        return values, converged, self.history

    def _log(self, message: str) -> None:
        if self.config.verbose:
            print(message)

    def get_solution_points(self) -> Dict[int, Tuple[float, float]]:
        """Get solved point positions."""
        if self.system is None:
            return {}
        points = {}
        for point_id, [x_idx, y_idx] in self.system.point_to_vars.items():
            points[point_id] = (
                self.system.graph.entity_nodes[point_id].x,
                self.system.graph.entity_nodes[point_id].y,
            )
        return points

    def analyze_system(self, graph: ConstraintGraph) -> Dict:
        """Analyze constraint system before solving."""
        from .constraint_graph import DependencyAnalyzer, OverUnderAnalyzer

        over_under = OverUnderAnalyzer(graph)
        dep_analyzer = DependencyAnalyzer(graph)

        return {
            'constraint_analysis': over_under.check(),
            'dependency_analysis': dep_analyzer.analyze(),
        }
