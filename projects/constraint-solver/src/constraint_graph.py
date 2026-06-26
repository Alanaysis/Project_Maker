"""Constraint graph builder and propagation engine.

The constraint graph represents the dependency structure between
geometric entities and constraints. It is used for:
- Ordering constraint resolution (which constraints to solve first)
- Detecting over/under-constrained systems
- Propagating known values through the constraint network
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional, Any
from .entities import Point
from .constraints import Constraint, ConstraintType


class ConstraintGraph:
    """Graph representation of constraints and entities.

    The constraint graph has two types of nodes:
    - Entity nodes: Points, Lines, Circles
    - Constraint nodes: Distance, Angle, Parallel, etc.

    Edges connect constraints to the entities they involve.

    This graph is used for:
    1. Dependency analysis (topological ordering)
    2. Constraint propagation (finding solvable subsets)
    3. Detecting over/under-constrained systems
    """

    def __init__(self):
        self.entity_nodes: Dict[int, Point] = {}
        self.constraint_nodes: Dict[int, Constraint] = {}
        # Adjacency: entity_id -> set of constraint_ids
        self.entity_to_constraints: Dict[int, Set[int]] = defaultdict(set)
        # Adjacency: constraint_id -> set of entity_ids
        self.constraint_to_entities: Dict[int, Set[int]] = defaultdict(set)
        # Constraint dependency graph: constraint_id -> set of constraint_ids
        self.constraint_dependencies: Dict[int, Set[int]] = defaultdict(set)

    def add_entity(self, entity: Point) -> None:
        """Add an entity node to the graph.

        Args:
            entity: Point entity to add
        """
        self.entity_nodes[entity.id] = entity
        if entity.id not in self.entity_to_constraints:
            self.entity_to_constraints[entity.id] = set()

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint node to the graph and connect to entities.

        Args:
            constraint: Constraint to add
        """
        self.constraint_nodes[constraint.id] = constraint
        self.constraint_to_entities[constraint.id] = set()

        for entity in constraint.entities:
            self.entity_to_constraints[entity.id].add(constraint.id)
            self.constraint_to_entities[constraint.id].add(entity.id)
            if entity.id not in self.entity_nodes:
                self.entity_nodes[entity.id] = entity

    def remove_constraint(self, constraint_id: int) -> None:
        """Remove a constraint from the graph.

        Args:
            constraint_id: ID of constraint to remove
        """
        if constraint_id not in self.constraint_nodes:
            return

        constraint = self.constraint_nodes[constraint_id]
        for entity_id in self.constraint_to_entities.get(constraint_id, set()):
            self.entity_to_constraints[entity_id].discard(constraint_id)

        del self.constraint_nodes[constraint_id]
        del self.constraint_to_entities[constraint_id]

    def get_connected_entities(self, constraint_id: int) -> List[Point]:
        """Get all entities connected to a constraint.

        Args:
            constraint_id: ID of the constraint

        Returns:
            List of Point entities
        """
        entity_ids = self.constraint_to_entities.get(constraint_id, set())
        return [self.entity_nodes[eid] for eid in entity_ids if eid in self.entity_nodes]

    def get_connected_constraints(self, entity_id: int) -> List[Constraint]:
        """Get all constraints connected to an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            List of Constraint objects
        """
        constraint_ids = self.entity_to_constraints.get(entity_id, set())
        return [
            self.constraint_nodes[cid]
            for cid in constraint_ids
            if cid in self.constraint_nodes
        ]

    def get_entities_for_type(self, constraint_type: ConstraintType) -> List[Constraint]:
        """Get all constraints of a specific type.

        Args:
            constraint_type: Type to filter by

        Returns:
            List of matching constraints
        """
        return [
            c for c in self.constraint_nodes.values()
            if c.constraint_type == constraint_type
        ]


class ConstraintPropagationEngine:
    """Constraint propagation engine for geometric constraint solving.

    Propagation works by identifying which entities/constraints have
    enough known values to be directly computed (without numerical iteration).

    The engine uses a worklist algorithm:
    1. Find constraints with enough known inputs
    2. Compute outputs and mark entities as known
    3. Repeat until no more progress can be made
    4. Return remaining unconstrained entities for numerical solving
    """

    def __init__(self, graph: ConstraintGraph):
        self.graph = graph
        self.known_entities: Set[int] = set()
        self.propagated_constraints: Set[int] = set()

    def propagate(self) -> Tuple[Set[int], Set[int]]:
        """Run constraint propagation.

        Uses a worklist algorithm to propagate known values through
        the constraint network.

        Returns:
            Tuple of (propagated_constraint_ids, remaining_constraint_ids)
        """
        # Initialize with fixed points
        for entity_id, entity in self.graph.entity_nodes.items():
            if entity.fixed:
                self.known_entities.add(entity_id)

        worklist = list(self.known_entities)
        self.propagated_constraints = set()

        while worklist:
            entity_id = worklist.pop(0)
            connected_constraints = self.graph.get_connected_constraints(entity_id)

            for constraint in connected_constraints:
                if constraint.id in self.propagated_constraints:
                    continue

                if self._can_satisfy(constraint):
                    self.propagated_constraints.add(constraint.id)
                    # Mark connected entities as known
                    for eid in self.graph.constraint_to_entities.get(constraint.id, set()):
                        if eid not in self.known_entities:
                            self.known_entities.add(eid)
                            worklist.append(eid)

        all_constraint_ids = set(self.graph.constraint_nodes.keys())
        remaining = all_constraint_ids - self.propagated_constraints
        return self.propagated_constraints, remaining

    def _can_satisfy(self, constraint: Constraint) -> bool:
        """Check if a constraint can be satisfied by propagation.

        A constraint can be propagated if enough of its connected
        entities have known positions.

        Args:
            constraint: The constraint to check

        Returns:
            True if the constraint can be directly evaluated
        """
        connected_ids = self.graph.constraint_to_entities.get(constraint.id, set())
        known_count = sum(1 for eid in connected_ids if eid in self.known_entities)
        # Need at least 2 entities known for most constraints
        return known_count >= 2

    def reset(self) -> None:
        """Reset the propagation state."""
        self.known_entities.clear()
        self.propagated_constraints.clear()


class DependencyAnalyzer:
    """Analyzes dependency ordering for constraint resolution.

    Uses topological sorting to determine the order in which
    constraints should be resolved. Also detects:
    - Over-constrained systems (too many constraints)
    - Under-constrained systems (too few constraints / degrees of freedom)
    - Cycles in the constraint graph (cannot be solved by propagation alone)
    """

    def __init__(self, graph: ConstraintGraph):
        self.graph = graph
        self.variable_count = 0
        self.constraint_count = 0
        self.degrees_of_freedom = 0

    def analyze(self) -> Dict[str, Any]:
        """Perform full dependency analysis.

        Returns:
            Dictionary with analysis results:
            - dof: Degrees of freedom
            - status: 'under-constrained', 'constrained', or 'over-constrained'
            - ordering: Topological ordering of constraints (if possible)
            - cycles: List of cycles found in the constraint graph
            - solvable: Whether the system can be solved
        """
        result = {}

        # Count variables and constraints
        self._count_variables()
        self._count_constraints()
        self.degrees_of_freedom = self.variable_count - self.constraint_count

        # Determine constraint status
        if self.degrees_of_freedom > 0:
            result['status'] = 'under-constrained'
            result['dof'] = self.degrees_of_freedom
        elif self.degrees_of_freedom == 0:
            result['status'] = 'constrained'
            result['dof'] = 0
        else:
            result['status'] = 'over-constrained'
            result['dof'] = self.degrees_of_freedom

        # Try topological ordering
        result['ordering'], result['cycles'] = self._topological_order()

        # Check solvability
        result['solvable'] = (
            self.degrees_of_freedom >= 0
            and len(result['cycles']) == 0
        )

        return result

    def _count_variables(self) -> None:
        """Count the number of free variables in the system."""
        free_points = [
            p for p in self.graph.entity_nodes.values()
            if not p.fixed
        ]
        self.variable_count = len(free_points) * 2  # x and y for each point

    def _count_constraints(self) -> None:
        """Count the number of active constraints."""
        self.constraint_count = sum(
            1 for c in self.graph.constraint_nodes.values()
            if c.active
        )

    def _topological_order(self) -> Tuple[List[int], List[List[int]]]:
        """Compute topological ordering of constraints.

        Uses Kahn's algorithm for topological sorting.
        Returns ordering and any cycles found.

        Returns:
            Tuple of (ordering, cycles)
        """
        # Build adjacency for constraint dependency graph
        in_degree = defaultdict(int)
        adj = defaultdict(set)

        all_ids = list(self.graph.constraint_nodes.keys())
        for cid in all_ids:
            if cid not in in_degree:
                in_degree[cid] = 0

        # Build dependencies based on shared entities
        for cid in all_ids:
            entities = self.graph.constraint_to_entities.get(cid, set())
            for other_id, other_entities in self.graph.constraint_to_entities.items():
                if other_id != cid and entities & other_entities:
                    if other_id not in adj[cid]:
                        adj[cid].add(other_id)
                        in_degree[other_id] += 1

        # Kahn's algorithm
        queue = deque([cid for cid in all_ids if in_degree[cid] == 0])
        ordering = []

        while queue:
            cid = queue.popleft()
            ordering.append(cid)
            for neighbor in adj[cid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Any remaining nodes are part of cycles
        cycles = []
        remaining = [cid for cid in all_ids if cid not in ordering]
        if remaining:
            cycles.append(remaining)

        return ordering, cycles


class OverUnderAnalyzer:
    """Detects over-constrained and under-constrained systems.

    Uses counting methods and graph-based analysis to determine
    if a constraint system has the right number of constraints.
    """

    def __init__(self, graph: ConstraintGraph):
        self.graph = graph

    def check(self) -> Dict[str, Any]:
        """Check if the system is over/under/constrained.

        Returns:
            Dictionary with analysis results
        """
        result = {}

        # Count free variables
        free_points = [
            p for p in self.graph.entity_nodes.values()
            if not p.fixed
        ]
        num_variables = len(free_points) * 2

        # Count active constraints
        active_constraints = [
            c for c in self.graph.constraint_nodes.values()
            if c.active
        ]
        num_constraints = len(active_constraints)

        # Simple count check
        if num_constraints > num_variables:
            result['status'] = 'over-constrained'
            result['excess_constraints'] = num_constraints - num_variables
        elif num_constraints < num_variables:
            result['status'] = 'under-constrained'
            result['missing_constraints'] = num_variables - num_constraints
        else:
            result['status'] = 'constrained'

        result['num_variables'] = num_variables
        result['num_constraints'] = num_constraints
        result['degrees_of_freedom'] = num_variables - num_constraints
        result['free_points'] = len(free_points)
        result['fixed_points'] = len(self.graph.entity_nodes) - len(free_points)

        return result
