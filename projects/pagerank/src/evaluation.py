"""Evaluation module for PageRank algorithm analysis."""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .graph import WebGraph
from .pagerank import PageRank, PageRankResult, ConvergenceAnalysis


@dataclass
class GraphStatistics:
    """Statistics about the web graph structure."""
    num_pages: int
    num_links: int
    density: float
    avg_out_degree: float
    max_out_degree: int
    min_out_degree: int
    num_dangling_nodes: int
    num_components: int
    avg_clustering_coefficient: float

    def __repr__(self) -> str:
        return (
            f"GraphStatistics(\n"
            f"  pages={self.num_pages},\n"
            f"  links={self.num_links},\n"
            f"  density={self.density:.4f},\n"
            f"  avg_out_degree={self.avg_out_degree:.2f},\n"
            f"  dangling_nodes={self.num_dangling_nodes},\n"
            f"  components={self.num_components}\n"
            f")"
        )


@dataclass
class DampingFactorAnalysis:
    """Analysis of damping factor impact on PageRank."""
    damping_factors: List[float]
    scores: Dict[float, np.ndarray]
    iterations: Dict[float, int]
    convergence_times: Dict[float, float]
    score_correlations: Dict[Tuple[float, float], float]


@dataclass
class RobustnessAnalysis:
    """Analysis of PageRank robustness to graph perturbations."""
    original_scores: np.ndarray
    perturbed_scores: List[np.ndarray]
    score_differences: List[float]
    rank_correlations: List[float]
    perturbation_types: List[str]


class PageRankEvaluator:
    """Evaluator for analyzing PageRank algorithm behavior."""

    def __init__(self, damping_factor: float = 0.85):
        """
        Initialize evaluator.

        Args:
            damping_factor: Damping factor for PageRank computation
        """
        self.pagerank = PageRank(damping_factor=damping_factor)

    def analyze_graph(self, graph: WebGraph) -> GraphStatistics:
        """
        Analyze graph structure statistics.

        Args:
            graph: WebGraph instance

        Returns:
            GraphStatistics with graph metrics
        """
        import networkx as nx

        n = graph.num_pages

        # Handle empty graph
        if n == 0:
            return GraphStatistics(
                num_pages=0,
                num_links=0,
                density=0.0,
                avg_out_degree=0.0,
                max_out_degree=0,
                min_out_degree=0,
                num_dangling_nodes=0,
                num_components=0,
                avg_clustering_coefficient=0.0
            )

        adj = graph.build_adjacency_matrix()

        # Basic stats
        num_links = adj.nnz
        density = num_links / (n * (n - 1)) if n > 1 else 0.0

        # Out-degree stats
        out_degrees = np.array(adj.sum(axis=1)).flatten()
        avg_out_degree = float(out_degrees.mean())
        max_out_degree = int(out_degrees.max())
        min_out_degree = int(out_degrees.min())
        num_dangling_nodes = int((out_degrees == 0).sum())

        # Build NetworkX graph for advanced metrics
        G = nx.DiGraph()
        page_names = graph.page_names
        for idx, name in page_names.items():
            G.add_node(name)

        rows, cols = adj.nonzero()
        for r, c in zip(rows, cols):
            G.add_edge(page_names[r], page_names[c])

        # Connected components
        num_components = nx.number_weakly_connected_components(G)

        # Clustering coefficient
        avg_clustering = nx.average_clustering(G.to_undirected()) if n > 0 else 0.0

        return GraphStatistics(
            num_pages=n,
            num_links=num_links,
            density=density,
            avg_out_degree=avg_out_degree,
            max_out_degree=max_out_degree,
            min_out_degree=min_out_degree,
            num_dangling_nodes=num_dangling_nodes,
            num_components=num_components,
            avg_clustering_coefficient=avg_clustering
        )

    def analyze_damping_factor_impact(
        self,
        graph: WebGraph,
        damping_factors: List[float] = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
    ) -> DampingFactorAnalysis:
        """
        Analyze impact of different damping factors.

        Args:
            graph: WebGraph instance
            damping_factors: List of damping factors to test

        Returns:
            DampingFactorAnalysis with comparison metrics
        """
        scores = {}
        iterations = {}

        for d in damping_factors:
            pr = PageRank(damping_factor=d)
            result = pr.compute(graph)
            scores[d] = result.scores
            iterations[d] = result.iterations

        # Compute correlations between different damping factors
        correlations = {}
        for i, d1 in enumerate(damping_factors):
            for d2 in damping_factors[i+1:]:
                corr = np.corrcoef(scores[d1], scores[d2])[0, 1]
                correlations[(d1, d2)] = corr

        return DampingFactorAnalysis(
            damping_factors=damping_factors,
            scores=scores,
            iterations=iterations,
            convergence_times={},  # Could add timing if needed
            score_correlations=correlations
        )

    def analyze_convergence(
        self,
        graph: WebGraph,
        max_iterations: int = 200,
        tolerance: float = 1e-10
    ) -> ConvergenceAnalysis:
        """
        Analyze convergence behavior in detail.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum iterations
            tolerance: Convergence threshold

        Returns:
            ConvergenceAnalysis with detailed metrics
        """
        return self.pagerank.analyze_convergence(
            graph, max_iterations, tolerance
        )

    def analyze_robustness(
        self,
        graph: WebGraph,
        num_perturbations: int = 5,
        perturbation_rate: float = 0.1
    ) -> RobustnessAnalysis:
        """
        Analyze robustness of PageRank to graph perturbations.

        Args:
            graph: WebGraph instance
            num_perturbations: Number of perturbations to test
            perturbation_rate: Fraction of edges to perturb

        Returns:
            RobustnessAnalysis with robustness metrics
        """
        # Compute original PageRank
        original_result = self.pagerank.compute(graph)
        original_scores = original_result.scores

        perturbed_scores = []
        score_diffs = []
        rank_corrs = []
        perturbation_types = []

        # Test edge removal
        edges = list(zip(*graph.build_adjacency_matrix().nonzero()))
        num_edges = len(edges)
        num_remove = max(1, int(num_edges * perturbation_rate))

        for i in range(num_perturbations):
            # Randomly remove edges
            rng = np.random.RandomState(i)
            remove_indices = rng.choice(num_edges, size=num_remove, replace=False)

            # Create perturbed graph
            perturbed_graph = WebGraph()
            page_names = graph.page_names
            for idx, (r, c) in enumerate(edges):
                if idx not in remove_indices:
                    perturbed_graph.add_link(page_names[r], page_names[c])

            # Compute PageRank on perturbed graph
            perturbed_result = self.pagerank.compute(perturbed_graph)

            # Align scores (pages might be in different order)
            aligned_scores = np.zeros_like(original_scores)
            for j, name in page_names.items():
                score = perturbed_result.get_score(name)
                if score is not None:
                    aligned_scores[j] = score

            perturbed_scores.append(aligned_scores)
            score_diffs.append(float(np.abs(original_scores - aligned_scores).mean()))

            # Rank correlation
            orig_rank = np.argsort(-original_scores)
            pert_rank = np.argsort(-aligned_scores)
            corr = np.corrcoef(orig_rank, pert_rank)[0, 1]
            rank_corrs.append(float(corr))
            perturbation_types.append("edge_removal")

        return RobustnessAnalysis(
            original_scores=original_scores,
            perturbed_scores=perturbed_scores,
            score_differences=score_diffs,
            rank_correlations=rank_corrs,
            perturbation_types=perturbation_types
        )

    def compare_algorithms(
        self,
        graph: WebGraph,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Dict[str, PageRankResult]:
        """
        Compare different PageRank algorithm implementations.

        Args:
            graph: WebGraph instance
            max_iterations: Maximum iterations
            tolerance: Convergence threshold

        Returns:
            Dict mapping algorithm names to results
        """
        results = {}

        # Standard iterative
        results['iterative'] = self.pagerank.compute(
            graph, max_iterations, tolerance
        )

        # Power iteration
        results['power_iteration'] = self.pagerank.compute_power_iteration(
            graph, max_iterations, tolerance
        )

        # Algebraic
        results['algebraic'] = self.pagerank.compute_algebraic(graph)

        return results

    def sensitivity_analysis(
        self,
        graph: WebGraph,
        damping_factors: List[float] = [0.5, 0.7, 0.85, 0.95],
        tolerances: List[float] = [1e-4, 1e-6, 1e-8, 1e-10]
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on algorithm parameters.

        Args:
            graph: WebGraph instance
            damping_factors: List of damping factors to test
            tolerances: List of tolerances to test

        Returns:
            Dict with sensitivity analysis results
        """
        results = {
            'damping_factor_sensitivity': {},
            'tolerance_sensitivity': {},
            'score_variance': {},
            'rank_stability': {}
        }

        # Damping factor sensitivity
        for d in damping_factors:
            pr = PageRank(damping_factor=d)
            result = pr.compute(graph)
            results['damping_factor_sensitivity'][d] = {
                'scores': result.scores,
                'iterations': result.iterations,
                'converged': result.converged
            }

        # Tolerance sensitivity
        for tol in tolerances:
            result = self.pagerank.compute(graph, tolerance=tol)
            results['tolerance_sensitivity'][tol] = {
                'iterations': result.iterations,
                'final_diff': result.final_diff,
                'converged': result.converged
            }

        # Score variance across damping factors
        all_scores = np.array([results['damping_factor_sensitivity'][d]['scores']
                              for d in damping_factors])
        results['score_variance'] = {
            'mean_variance': float(np.mean(np.var(all_scores, axis=0))),
            'max_variance': float(np.max(np.var(all_scores, axis=0))),
            'per_page_variance': np.var(all_scores, axis=0).tolist()
        }

        # Rank stability
        rankings = []
        for d in damping_factors:
            scores = results['damping_factor_sensitivity'][d]['scores']
            rankings.append(np.argsort(-scores))

        # Compute average rank correlation
        correlations = []
        for i in range(len(rankings)):
            for j in range(i+1, len(rankings)):
                corr = np.corrcoef(rankings[i], rankings[j])[0, 1]
                correlations.append(corr)

        results['rank_stability'] = {
            'mean_correlation': float(np.mean(correlations)),
            'min_correlation': float(np.min(correlations)),
            'max_correlation': float(np.max(correlations))
        }

        return results
