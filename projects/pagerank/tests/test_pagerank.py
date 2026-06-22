"""Tests for PageRank algorithm."""

import pytest
import numpy as np

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank, PageRankResult


class TestPageRank:
    """Test cases for PageRank algorithm."""

    def test_simple_triangle(self):
        """Test PageRank on a simple triangle graph (A->B->C->A)."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph)

        assert result.converged
        assert len(result.scores) == 3

        # In a symmetric cycle, all pages should have equal rank
        assert abs(result.scores[0] - result.scores[1]) < 1e-6
        assert abs(result.scores[1] - result.scores[2]) < 1e-6

        # Scores should sum to 1
        assert abs(result.scores.sum() - 1.0) < 1e-10

    def test_star_graph(self):
        """Test PageRank on a star graph (center receives many links)."""
        edges = [
            ("A", "Center"),
            ("B", "Center"),
            ("C", "Center"),
            ("D", "Center"),
        ]
        graph = WebGraph.from_edges(edges)

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph)

        assert result.converged

        # Center should have highest rank
        center_score = result.get_score("Center")
        assert center_score is not None
        assert center_score > result.get_score("A")
        assert center_score > result.get_score("B")

    def test_chain_graph(self):
        """Test PageRank on a chain graph (A->B->C->D)."""
        edges = [("A", "B"), ("B", "C"), ("C", "D")]
        graph = WebGraph.from_edges(edges)

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph)

        assert result.converged

        # D should have highest rank (receives link from C)
        ranked = result.ranked_pages
        assert ranked[0][0] == "D"

    def test_damping_factor_effect(self):
        """Test that different damping factors produce different results."""
        # Use a non-symmetric graph where damping factor matters
        graph = WebGraph.from_edges([
            ("A", "B"), ("A", "C"),
            ("B", "C"),
            ("C", "A"),
            ("D", "C"),
        ])

        pr_low = PageRank(damping_factor=0.5)
        pr_high = PageRank(damping_factor=0.95)

        result_low = pr_low.compute(graph)
        result_high = pr_high.compute(graph)

        # Results should be different (though both valid)
        assert not np.allclose(result_low.scores, result_high.scores, atol=1e-4)

    def test_invalid_damping_factor(self):
        """Test that invalid damping factors raise error."""
        with pytest.raises(ValueError):
            PageRank(damping_factor=-0.1)

        with pytest.raises(ValueError):
            PageRank(damping_factor=1.1)

    def test_empty_graph(self):
        """Test PageRank on empty graph."""
        graph = WebGraph()
        pr = PageRank()

        result = pr.compute(graph)

        assert result.converged
        assert len(result.scores) == 0
        assert result.iterations == 0

    def test_single_page(self):
        """Test PageRank with single page."""
        graph = WebGraph()
        graph.add_page("A")

        pr = PageRank()
        result = pr.compute(graph)

        assert result.converged
        assert len(result.scores) == 1
        assert abs(result.scores[0] - 1.0) < 1e-10

    def test_convergence_detection(self):
        """Test that convergence is properly detected."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph, max_iterations=1000, tolerance=1e-10)

        assert result.converged
        assert result.iterations < 1000
        assert result.final_diff < 1e-10

    def test_max_iterations(self):
        """Test that algorithm stops at max iterations."""
        # Use a larger graph that requires more iterations to converge
        edges = []
        for i in range(10):
            for j in range(5):
                target = (i + j + 1) % 10
                edges.append((f"Page{i}", f"Page{target}"))
        graph = WebGraph.from_edges(edges)

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph, max_iterations=2, tolerance=1e-20)

        # Should stop at max iterations without converging
        assert result.iterations == 2
        assert not result.converged

    def test_ranked_pages(self):
        """Test ranked_pages property."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank()
        result = pr.compute(graph)

        ranked = result.ranked_pages

        # Should return all pages
        assert len(ranked) == 3

        # Should be sorted by score descending
        for i in range(len(ranked) - 1):
            assert ranked[i][1] >= ranked[i + 1][1]

    def test_get_score(self):
        """Test get_score method."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "A")])

        pr = PageRank()
        result = pr.compute(graph)

        assert result.get_score("A") is not None
        assert result.get_score("B") is not None
        assert result.get_score("C") is None

    def test_power_iteration(self):
        """Test power iteration method produces same results."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank(damping_factor=0.85)
        result_iterative = pr.compute(graph)
        result_power = pr.compute_power_iteration(graph)

        # Results should be very similar
        assert np.allclose(result_iterative.scores, result_power.scores, atol=1e-6)

    def test_algebraic_method(self):
        """Test algebraic method produces same results."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank(damping_factor=0.85)
        result_iterative = pr.compute(graph)
        result_algebraic = pr.compute_algebraic(graph)

        # Results should be very similar
        assert np.allclose(result_iterative.scores, result_algebraic.scores, atol=1e-6)

    def test_wikipedia_example(self):
        """Test with Wikipedia's PageRank example."""
        # Classic example from Wikipedia
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
            ("D", "C"),
        ]
        graph = WebGraph.from_edges(edges)

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph)

        assert result.converged

        # C should have highest rank (most incoming links)
        ranked = result.ranked_pages
        assert ranked[0][0] == "C"

    def test_initial_scores(self):
        """Test computation with custom initial scores."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank()
        initial = np.array([0.1, 0.6, 0.3])
        result = pr.compute(graph, initial_scores=initial)

        assert result.converged
        assert abs(result.scores.sum() - 1.0) < 1e-10

    def test_invalid_initial_scores(self):
        """Test that invalid initial scores raise error."""
        graph = WebGraph.from_edges([("A", "B"), ("B", "A")])

        pr = PageRank()

        with pytest.raises(ValueError):
            pr.compute(graph, initial_scores=np.array([0.5, 0.5, 0.5]))  # Wrong length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
