"""PageRank algorithm implementation with iterative method."""

import numpy as np
from scipy import sparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .graph import WebGraph


@dataclass
class PageRankResult:
    """Container for PageRank computation results."""
    scores: np.ndarray
    iterations: int
    converged: bool
    final_diff: float
    page_names: Dict[int, str]

    @property
    def ranked_pages(self) -> List[Tuple[str, float]]:
        """
        Get pages ranked by PageRank score.

        Returns:
            List of (page_name, score) tuples sorted by score descending
        """
        indices = np.argsort(-self.scores)
        return [
            (self.page_names[i], self.scores[i])
            for i in indices
        ]

    def get_score(self, page_name: str) -> Optional[float]:
        """
        Get PageRank score for a specific page.

        Args:
            page_name: Name of the page

        Returns:
            PageRank score or None if page not found
        """
        for idx, name in self.page_names.items():
            if name == page_name:
                return self.scores[idx]
        return None


class PageRank:
    """
    PageRank algorithm implementation.

    Implements the classic PageRank algorithm with:
    - Damping factor (typically 0.85)
    - Iterative computation
    - Convergence detection
    - Sparse matrix optimization

    The algorithm computes:
    PR(i) = (1-d)/N + d * sum(PR(j)/L(j)) for all j linking to i

    Where:
    - d is the damping factor
    - N is the total number of pages
    - L(j) is the number of outgoing links from page j
    """

    def __init__(self, damping_factor: float = 0.85):
        """
        Initialize PageRank calculator.

        Args:
            damping_factor: Probability of following a link (0 to 1)
        """
        if not 0 <= damping_factor <= 1:
            raise ValueError("Damping factor must be between 0 and 1")
        self.damping_factor = damping_factor

    def compute(
        self,
        graph: WebGraph,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        initial_scores: Optional[np.ndarray] = None
    ) -> PageRankResult:
        """
        Compute PageRank scores for a web graph.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold
            initial_scores: Optional initial PageRank scores

        Returns:
            PageRankResult with computed scores
        """
        n = graph.num_pages
        if n == 0:
            return PageRankResult(
                scores=np.array([]),
                iterations=0,
                converged=True,
                final_diff=0.0,
                page_names={}
            )

        # Build transition matrix
        transition = graph.build_transition_matrix()

        # Initialize scores
        if initial_scores is not None:
            if len(initial_scores) != n:
                raise ValueError(f"Initial scores length must be {n}")
            scores = initial_scores.copy()
        else:
            scores = np.ones(n) / n

        # Damping vector
        damping_vector = np.ones(n) * (1 - self.damping_factor) / n

        # Iterate
        converged = False
        final_diff = 0.0

        for iteration in range(max_iterations):
            # PageRank formula: PR = (1-d)/N + d * M * PR
            new_scores = damping_vector + self.damping_factor * (transition @ scores)

            # Normalize (should already be close to 1, but ensure precision)
            new_scores = new_scores / new_scores.sum()

            # Check convergence
            diff = np.abs(new_scores - scores).sum()
            final_diff = diff

            if diff < tolerance:
                converged = True
                scores = new_scores
                break

            scores = new_scores

        return PageRankResult(
            scores=scores,
            iterations=iteration + 1,
            converged=converged,
            final_diff=final_diff,
            page_names=graph.page_names
        )

    def compute_power_iteration(
        self,
        graph: WebGraph,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> PageRankResult:
        """
        Compute PageRank using power iteration method.

        This is an alternative implementation that directly computes
        the dominant eigenvector of the Google matrix.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold

        Returns:
            PageRankResult with computed scores
        """
        n = graph.num_pages
        if n == 0:
            return PageRankResult(
                scores=np.array([]),
                iterations=0,
                converged=True,
                final_diff=0.0,
                page_names={}
            )

        # Build Google matrix: G = d*M + (1-d)/N * ones
        transition = graph.build_transition_matrix()
        # Create dense ones matrix and convert to sparse
        ones_matrix = sparse.csr_matrix(np.ones((n, n)) / n)
        google_matrix = self.damping_factor * transition + (1 - self.damping_factor) * ones_matrix

        # Initialize with uniform distribution
        scores = np.ones(n) / n

        converged = False
        final_diff = 0.0

        for iteration in range(max_iterations):
            new_scores = google_matrix @ scores
            new_scores = new_scores / new_scores.sum()

            diff = np.abs(new_scores - scores).sum()
            final_diff = diff

            if diff < tolerance:
                converged = True
                scores = new_scores
                break

            scores = new_scores

        return PageRankResult(
            scores=scores,
            iterations=iteration + 1,
            converged=converged,
            final_diff=final_diff,
            page_names=graph.page_names
        )

    def compute_algebraic(
        self,
        graph: WebGraph
    ) -> PageRankResult:
        """
        Compute PageRank using direct algebraic solution.

        Solves: (I - d*M) * r = (1-d)/N * ones

        Note: This method may be less efficient for large graphs.

        Args:
            graph: WebGraph instance

        Returns:
            PageRankResult with computed scores
        """
        n = graph.num_pages
        if n == 0:
            return PageRankResult(
                scores=np.array([]),
                iterations=0,
                converged=True,
                final_diff=0.0,
                page_names={}
            )

        transition = graph.build_transition_matrix()

        # Build system: (I - d*M) * r = (1-d)/N * ones
        I = sparse.eye(n)
        A = I - self.damping_factor * transition
        b = np.ones(n) * (1 - self.damping_factor) / n

        # Solve using sparse solver
        from scipy.sparse.linalg import spsolve
        scores = spsolve(A.tocsc(), b)

        # Normalize
        scores = np.abs(scores)  # Ensure non-negative
        scores = scores / scores.sum()

        return PageRankResult(
            scores=scores,
            iterations=1,
            converged=True,
            final_diff=0.0,
            page_names=graph.page_names
        )
