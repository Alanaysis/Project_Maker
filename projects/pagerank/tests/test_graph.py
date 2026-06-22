"""Tests for WebGraph class."""

import pytest
import numpy as np
from scipy import sparse

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph


class TestWebGraph:
    """Test cases for WebGraph."""

    def test_empty_graph(self):
        """Test empty graph creation."""
        graph = WebGraph()
        assert graph.num_pages == 0
        assert graph.page_names == {}

    def test_add_page(self):
        """Test adding pages to graph."""
        graph = WebGraph()
        idx1 = graph.add_page("A")
        idx2 = graph.add_page("B")

        assert graph.num_pages == 2
        assert idx1 == 0
        assert idx2 == 1
        assert graph.page_names == {0: "A", 1: "B"}

    def test_add_duplicate_page(self):
        """Test adding duplicate page returns same index."""
        graph = WebGraph()
        idx1 = graph.add_page("A")
        idx2 = graph.add_page("A")

        assert idx1 == idx2
        assert graph.num_pages == 1

    def test_add_link(self):
        """Test adding links between pages."""
        graph = WebGraph()
        graph.add_link("A", "B")
        graph.add_link("B", "C")

        assert graph.num_pages == 3
        assert graph.get_outgoing_links("A") == ["B"]
        assert graph.get_outgoing_links("B") == ["C"]
        assert graph.get_incoming_links("C") == ["B"]

    def test_build_adjacency_matrix(self):
        """Test adjacency matrix construction."""
        graph = WebGraph()
        graph.add_link("A", "B")
        graph.add_link("A", "C")
        graph.add_link("B", "C")

        adj = graph.build_adjacency_matrix()

        assert adj.shape == (3, 3)
        # A -> B, A -> C
        assert adj[0, 1] == 1
        assert adj[0, 2] == 1
        # B -> C
        assert adj[1, 2] == 1
        # No self-loops or reverse links
        assert adj[0, 0] == 0
        assert adj[1, 0] == 0

    def test_build_transition_matrix(self):
        """Test transition matrix construction."""
        graph = WebGraph()
        graph.add_link("A", "B")
        graph.add_link("A", "C")

        trans = graph.build_transition_matrix()

        # A has 2 outgoing links, so each gets 0.5
        # Note: transition matrix is column-stochastic (transposed)
        assert trans.shape == (3, 3)

    def test_dangling_node(self):
        """Test handling of dangling nodes (no outgoing links)."""
        graph = WebGraph()
        graph.add_link("A", "B")
        # B has no outgoing links

        trans = graph.build_transition_matrix()

        # B's column should distribute uniformly
        col_sum = trans[:, 1].sum()
        assert abs(col_sum - 1.0) < 1e-10

    def test_from_edges(self):
        """Test creating graph from edge list."""
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        graph = WebGraph.from_edges(edges)

        assert graph.num_pages == 3
        assert graph.get_outgoing_links("A") == ["B"]
        assert graph.get_outgoing_links("B") == ["C"]
        assert graph.get_outgoing_links("C") == ["A"]

    def test_get_page_index(self):
        """Test getting page index by name."""
        graph = WebGraph()
        graph.add_page("A")
        graph.add_page("B")

        assert graph.get_page_index("A") == 0
        assert graph.get_page_index("B") == 1
        assert graph.get_page_index("C") is None

    def test_complex_graph(self):
        """Test with a more complex graph structure."""
        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "C"),
            ("C", "A"),
            ("D", "C"),
        ]
        graph = WebGraph.from_edges(edges)

        assert graph.num_pages == 4
        assert set(graph.get_incoming_links("C")) == {"A", "B", "D"}
        assert graph.get_outgoing_links("A") == ["B", "C"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
