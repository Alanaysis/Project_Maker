"""PageRank algorithm implementation with iterative method."""

import numpy as np
from scipy import sparse
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from .graph import WebGraph


class PageRankVariant(Enum):
    """PageRank algorithm variants."""
    STANDARD = "standard"
    PERSONALIZED = "personalized"
    TOPIC_SENSITIVE = "topic_sensitive"


@dataclass
class PageRankResult:
    """Container for PageRank computation results."""
    scores: np.ndarray
    iterations: int
    converged: bool
    final_diff: float
    page_names: Dict[int, str]
    variant: PageRankVariant = PageRankVariant.STANDARD
    convergence_history: List[float] = field(default_factory=list)

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

    def top_k(self, k: int = 10) -> List[Tuple[str, float]]:
        """Get top-k pages by PageRank score."""
        return self.ranked_pages[:k]

    def get_percentile(self, page_name: str) -> Optional[float]:
        """
        Get percentile rank of a page (0 = highest, 100 = lowest).

        Args:
            page_name: Name of the page

        Returns:
            Percentile rank or None if page not found
        """
        score = self.get_score(page_name)
        if score is None:
            return None
        rank = sum(1 for s in self.scores if s > score)
        return (rank / len(self.scores)) * 100


@dataclass
class ConvergenceAnalysis:
    """Analysis of PageRank convergence behavior."""
    iterations: int
    converged: bool
    final_diff: float
    convergence_history: List[float]
    spectral_radius: Optional[float] = None
    convergence_rate: Optional[float] = None

    @property
    def is_linear_convergence(self) -> bool:
        """Check if convergence appears linear."""
        if len(self.convergence_history) < 3:
            return False
        # Check if ratio of consecutive differences is roughly constant
        ratios = []
        for i in range(2, len(self.convergence_history)):
            if self.convergence_history[i-1] > 0:
                ratios.append(self.convergence_history[i] / self.convergence_history[i-1])
        if not ratios:
            return False
        # Linear convergence: ratio is roughly constant
        return np.std(ratios) < 0.1 * np.mean(ratios)

    @property
    def estimated_spectral_radius(self) -> Optional[float]:
        """Estimate spectral radius from convergence history."""
        if len(self.convergence_history) < 3:
            return None
        # Estimate from last few iterations
        recent = self.convergence_history[-5:]
        if len(recent) < 2 or recent[-2] == 0:
            return None
        return recent[-1] / recent[-2]


@dataclass
class RankingQualityMetrics:
    """Metrics for evaluating PageRank ranking quality."""
    kendall_tau: float  # Kendall's tau correlation with ground truth
    spearman_rho: float  # Spearman's rank correlation
    ndcg: float  # Normalized Discounted Cumulative Gain
    precision_at_k: Dict[int, float]  # Precision at various k values
    recall_at_k: Dict[int, float]  # Recall at various k values

    def __repr__(self) -> str:
        return (
            f"RankingQualityMetrics(\n"
            f"  kendall_tau={self.kendall_tau:.4f},\n"
            f"  spearman_rho={self.spearman_rho:.4f},\n"
            f"  ndcg={self.ndcg:.4f},\n"
            f"  precision_at_k={self.precision_at_k},\n"
            f"  recall_at_k={self.recall_at_k}\n"
            f")"
        )


class PageRank:
    """
    PageRank algorithm implementation.

    Implements the classic PageRank algorithm with:
    - Damping factor (typically 0.85)
    - Iterative computation
    - Convergence detection
    - Sparse matrix optimization
    - Personalized PageRank
    - Topic-Sensitive PageRank

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
        initial_scores: Optional[np.ndarray] = None,
        track_history: bool = False
    ) -> PageRankResult:
        """
        Compute PageRank scores for a web graph.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold
            initial_scores: Optional initial PageRank scores
            track_history: Whether to track convergence history

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
                page_names={},
                variant=PageRankVariant.STANDARD
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
        convergence_history = []

        for iteration in range(max_iterations):
            # PageRank formula: PR = (1-d)/N + d * M * PR
            new_scores = damping_vector + self.damping_factor * (transition @ scores)

            # Normalize (should already be close to 1, but ensure precision)
            new_scores = new_scores / new_scores.sum()

            # Check convergence
            diff = np.abs(new_scores - scores).sum()
            final_diff = diff

            if track_history:
                convergence_history.append(diff)

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
            page_names=graph.page_names,
            variant=PageRankVariant.STANDARD,
            convergence_history=convergence_history
        )

    def compute_personalized(
        self,
        graph: WebGraph,
        personalization_vector: Optional[Dict[str, float]] = None,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        track_history: bool = False
    ) -> PageRankResult:
        """
        Compute Personalized PageRank scores.

        Personalized PageRank biases the random walk towards a set of
        preferred pages defined by the personalization vector.

        Formula:
        PR(i) = (1-d) * p(i) + d * sum(PR(j)/L(j))

        Where p(i) is the personalization probability for page i.

        Args:
            graph: WebGraph instance
            personalization_vector: Dict mapping page names to preference weights.
                                   If None, uses uniform distribution (standard PageRank).
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold
            track_history: Whether to track convergence history

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
                page_names={},
                variant=PageRankVariant.PERSONALIZED
            )

        # Build personalization vector
        if personalization_vector is None:
            p = np.ones(n) / n
        else:
            p = np.zeros(n)
            page_names = graph.page_names
            name_to_idx = {v: k for k, v in page_names.items()}

            for name, weight in personalization_vector.items():
                if name in name_to_idx:
                    p[name_to_idx[name]] = weight

            # Normalize to probability distribution
            total = p.sum()
            if total > 0:
                p = p / total
            else:
                p = np.ones(n) / n

        # Build transition matrix
        transition = graph.build_transition_matrix()

        # Initialize scores
        scores = np.ones(n) / n

        # Iterate
        converged = False
        final_diff = 0.0
        convergence_history = []

        for iteration in range(max_iterations):
            # Personalized PageRank formula: PR = (1-d)*p + d * M * PR
            new_scores = (1 - self.damping_factor) * p + self.damping_factor * (transition @ scores)

            # Normalize
            new_scores = new_scores / new_scores.sum()

            # Check convergence
            diff = np.abs(new_scores - scores).sum()
            final_diff = diff

            if track_history:
                convergence_history.append(diff)

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
            page_names=graph.page_names,
            variant=PageRankVariant.PERSONALIZED,
            convergence_history=convergence_history
        )

    def compute_topic_sensitive(
        self,
        graph: WebGraph,
        topic_pages: Dict[str, List[str]],
        topic_weights: Optional[Dict[str, float]] = None,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        track_history: bool = False
    ) -> Dict[str, PageRankResult]:
        """
        Compute Topic-Sensitive PageRank scores.

        Topic-Sensitive PageRank computes separate PageRank vectors for
        different topics, then combines them based on topic relevance.

        Args:
            graph: WebGraph instance
            topic_pages: Dict mapping topic names to lists of seed pages
            topic_weights: Optional dict mapping topic names to weights.
                          If None, uses uniform weights.
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold
            track_history: Whether to track convergence history

        Returns:
            Dict mapping topic names to PageRankResult
        """
        results = {}

        # Compute weights
        if topic_weights is None:
            topic_weights = {topic: 1.0 / len(topic_pages) for topic in topic_pages}

        # Normalize weights
        total_weight = sum(topic_weights.values())
        topic_weights = {k: v / total_weight for k, v in topic_weights.items()}

        # Compute personalized PageRank for each topic
        for topic, pages in topic_pages.items():
            # Create personalization vector for this topic
            personalization = {page: 1.0 / len(pages) for page in pages}

            result = self.compute_personalized(
                graph,
                personalization_vector=personalization,
                max_iterations=max_iterations,
                tolerance=tolerance,
                track_history=track_history
            )
            result.variant = PageRankVariant.TOPIC_SENSITIVE
            results[topic] = result

        return results

    def compute_topic_sensitive_combined(
        self,
        graph: WebGraph,
        topic_pages: Dict[str, List[str]],
        topic_weights: Optional[Dict[str, float]] = None,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> PageRankResult:
        """
        Compute combined Topic-Sensitive PageRank scores.

        This computes a single PageRank vector by combining topic-specific
        PageRank vectors weighted by topic importance.

        Args:
            graph: WebGraph instance
            topic_pages: Dict mapping topic names to lists of seed pages
            topic_weights: Optional dict mapping topic names to weights
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold

        Returns:
            PageRankResult with combined scores
        """
        n = graph.num_pages
        if n == 0:
            return PageRankResult(
                scores=np.array([]),
                iterations=0,
                converged=True,
                final_diff=0.0,
                page_names={},
                variant=PageRankVariant.TOPIC_SENSITIVE
            )

        # Compute per-topic PageRank
        topic_results = self.compute_topic_sensitive(
            graph, topic_pages, topic_weights, max_iterations, tolerance
        )

        # Compute weights
        if topic_weights is None:
            topic_weights = {topic: 1.0 / len(topic_pages) for topic in topic_pages}

        total_weight = sum(topic_weights.values())
        topic_weights = {k: v / total_weight for k, v in topic_weights.items()}

        # Combine scores
        combined_scores = np.zeros(n)
        for topic, result in topic_results.items():
            weight = topic_weights.get(topic, 0.0)
            combined_scores += weight * result.scores

        # Normalize
        combined_scores = combined_scores / combined_scores.sum()

        return PageRankResult(
            scores=combined_scores,
            iterations=max(r.iterations for r in topic_results.values()),
            converged=all(r.converged for r in topic_results.values()),
            final_diff=max(r.final_diff for r in topic_results.values()),
            page_names=graph.page_names,
            variant=PageRankVariant.TOPIC_SENSITIVE
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
        convergence_history = []

        for iteration in range(max_iterations):
            new_scores = google_matrix @ scores
            new_scores = new_scores / new_scores.sum()

            diff = np.abs(new_scores - scores).sum()
            final_diff = diff
            convergence_history.append(diff)

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
            page_names=graph.page_names,
            variant=PageRankVariant.STANDARD,
            convergence_history=convergence_history
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

    def analyze_convergence(
        self,
        graph: WebGraph,
        max_iterations: int = 200,
        tolerance: float = 1e-10
    ) -> ConvergenceAnalysis:
        """
        Analyze convergence behavior of PageRank algorithm.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum number of iterations
            tolerance: Convergence threshold

        Returns:
            ConvergenceAnalysis with detailed convergence metrics
        """
        result = self.compute(
            graph,
            max_iterations=max_iterations,
            tolerance=tolerance,
            track_history=True
        )

        return ConvergenceAnalysis(
            iterations=result.iterations,
            converged=result.converged,
            final_diff=result.final_diff,
            convergence_history=result.convergence_history
        )

    @staticmethod
    def evaluate_ranking_quality(
        computed_ranking: List[Tuple[str, float]],
        ground_truth_ranking: List[Tuple[str, float]],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> RankingQualityMetrics:
        """
        Evaluate quality of PageRank ranking against ground truth.

        Args:
            computed_ranking: List of (page_name, score) tuples
            ground_truth_ranking: List of (page_name, score) tuples
            k_values: List of k values for precision@k and recall@k

        Returns:
            RankingQualityMetrics with evaluation metrics
        """
        # Extract page names in order
        computed_pages = [p[0] for p in computed_ranking]
        truth_pages = [p[0] for p in ground_truth_ranking]

        # Create rank mappings
        computed_rank = {page: i for i, page in enumerate(computed_pages)}
        truth_rank = {page: i for i, page in enumerate(truth_pages)}

        # Common pages
        common_pages = set(computed_pages) & set(truth_pages)
        if not common_pages:
            return RankingQualityMetrics(
                kendall_tau=0.0,
                spearman_rho=0.0,
                ndcg=0.0,
                precision_at_k={k: 0.0 for k in k_values},
                recall_at_k={k: 0.0 for k in k_values}
            )

        # Kendall's tau
        concordant = 0
        discordant = 0
        pages_list = list(common_pages)
        for i in range(len(pages_list)):
            for j in range(i + 1, len(pages_list)):
                p1, p2 = pages_list[i], pages_list[j]
                computed_order = computed_rank[p1] - computed_rank[p2]
                truth_order = truth_rank[p1] - truth_rank[p2]

                if computed_order * truth_order > 0:
                    concordant += 1
                elif computed_order * truth_order < 0:
                    discordant += 1

        total_pairs = concordant + discordant
        kendall_tau = (concordant - discordant) / total_pairs if total_pairs > 0 else 0.0

        # Spearman's rho (simplified using rank differences)
        rank_diffs_squared = 0
        n = len(common_pages)
        for page in common_pages:
            d = computed_rank[page] - truth_rank[page]
            rank_diffs_squared += d * d
        spearman_rho = 1 - (6 * rank_diffs_squared) / (n * (n * n - 1)) if n > 1 else 0.0

        # NDCG
        dcg = 0.0
        for i, page in enumerate(computed_pages[:n]):
            if page in truth_rank:
                relevance = 1.0 / (1.0 + truth_rank[page])
                dcg += relevance / np.log2(i + 2)

        # Ideal DCG
        ideal_dcg = 0.0
        for i in range(min(n, len(truth_pages))):
            relevance = 1.0 / (1.0 + i)
            ideal_dcg += relevance / np.log2(i + 2)

        ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0.0

        # Precision@k and Recall@k
        precision_at_k = {}
        recall_at_k = {}

        relevant_in_truth = set(truth_pages[:max(k_values)]) if truth_pages else set()

        for k in k_values:
            computed_at_k = set(computed_pages[:k])
            relevant_at_k = set(truth_pages[:k]) if len(truth_pages) >= k else set(truth_pages)

            if k > 0:
                precision_at_k[k] = len(computed_at_k & relevant_at_k) / k
                recall_at_k[k] = len(computed_at_k & relevant_in_truth) / len(relevant_in_truth) if relevant_in_truth else 0.0
            else:
                precision_at_k[k] = 0.0
                recall_at_k[k] = 0.0

        return RankingQualityMetrics(
            kendall_tau=kendall_tau,
            spearman_rho=spearman_rho,
            ndcg=ndcg,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k
        )
