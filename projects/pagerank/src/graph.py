"""Web Graph representation for PageRank algorithm."""

import numpy as np
from scipy import sparse
from typing import Dict, List, Set, Optional, Tuple


class WebGraph:
    """
    Represents a web graph structure for PageRank computation.

    Attributes:
        num_pages: Total number of pages in the graph
        adjacency: Sparse matrix representation of links
        page_names: Mapping of page indices to names
    """

    def __init__(self):
        """Initialize an empty web graph."""
        self._edges: List[Tuple[int, int]] = []
        self._page_names: Dict[int, str] = {}
        self._name_to_index: Dict[str, int] = {}
        self._next_index: int = 0

    def add_page(self, name: str) -> int:
        """
        Add a page to the graph.

        Args:
            name: Page name/identifier

        Returns:
            Page index
        """
        if name in self._name_to_index:
            return self._name_to_index[name]

        index = self._next_index
        self._next_index += 1
        self._page_names[index] = name
        self._name_to_index[name] = index
        return index

    def add_link(self, from_page: str, to_page: str) -> None:
        """
        Add a directed link from one page to another.

        Args:
            from_page: Source page name
            to_page: Target page name
        """
        from_idx = self.add_page(from_page)
        to_idx = self.add_page(to_page)
        self._edges.append((from_idx, to_idx))

    def build_adjacency_matrix(self) -> sparse.csr_matrix:
        """
        Build sparse adjacency matrix from edges.

        Returns:
            CSR sparse matrix where entry (i,j) = 1 if page i links to page j
        """
        if not self._edges:
            return sparse.csr_matrix((self.num_pages, self.num_pages))

        rows = [e[0] for e in self._edges]
        cols = [e[1] for e in self._edges]
        data = np.ones(len(self._edges))

        return sparse.csr_matrix(
            (data, (rows, cols)),
            shape=(self.num_pages, self.num_pages)
        )

    def build_transition_matrix(self) -> sparse.csr_matrix:
        """
        Build column-stochastic transition matrix.

        Each column is normalized so that it sums to 1.
        Pages with no outgoing links get uniform distribution.

        Returns:
            Column-stochastic sparse matrix
        """
        adj = self.build_adjacency_matrix()

        # Calculate out-degree for each page
        out_degree = np.array(adj.sum(axis=1)).flatten()

        # Handle dangling nodes (no outgoing links)
        dangling_mask = out_degree == 0
        out_degree[dangling_mask] = 1  # Avoid division by zero

        # Create diagonal matrix of inverse out-degrees
        inv_degree = sparse.diags(1.0 / out_degree)

        # Transition matrix: column-normalized
        transition = adj.T @ inv_degree

        # Handle dangling nodes: distribute uniformly
        dangling_pages = np.where(dangling_mask)[0]
        if len(dangling_pages) > 0:
            # For dangling nodes, their column should be uniform 1/N
            # Create a matrix where each dangling page's column is uniform
            rows = np.tile(np.arange(self.num_pages), len(dangling_pages))
            cols = np.repeat(dangling_pages, self.num_pages)
            data = np.ones(len(dangling_pages) * self.num_pages) / self.num_pages
            dangling_contribution = sparse.csr_matrix(
                (data, (rows, cols)),
                shape=(self.num_pages, self.num_pages)
            )
            transition = transition + dangling_contribution

        return transition

    @property
    def num_pages(self) -> int:
        """Get number of pages in the graph."""
        return self._next_index

    @property
    def page_names(self) -> Dict[int, str]:
        """Get mapping of page indices to names."""
        return self._page_names.copy()

    def get_page_index(self, name: str) -> Optional[int]:
        """
        Get page index by name.

        Args:
            name: Page name

        Returns:
            Page index or None if not found
        """
        return self._name_to_index.get(name)

    def get_outgoing_links(self, page: str) -> List[str]:
        """
        Get list of pages that the given page links to.

        Args:
            page: Page name

        Returns:
            List of target page names
        """
        page_idx = self._name_to_index.get(page)
        if page_idx is None:
            return []

        targets = []
        for from_idx, to_idx in self._edges:
            if from_idx == page_idx:
                targets.append(self._page_names[to_idx])
        return targets

    def get_incoming_links(self, page: str) -> List[str]:
        """
        Get list of pages that link to the given page.

        Args:
            page: Page name

        Returns:
            List of source page names
        """
        page_idx = self._name_to_index.get(page)
        if page_idx is None:
            return []

        sources = []
        for from_idx, to_idx in self._edges:
            if to_idx == page_idx:
                sources.append(self._page_names[from_idx])
        return sources

    @classmethod
    def from_edges(cls, edges: List[Tuple[str, str]]) -> 'WebGraph':
        """
        Create graph from list of edge tuples.

        Args:
            edges: List of (from_page, to_page) tuples

        Returns:
            WebGraph instance
        """
        graph = cls()
        for from_page, to_page in edges:
            graph.add_link(from_page, to_page)
        return graph

    def __repr__(self) -> str:
        return f"WebGraph(pages={self.num_pages}, links={len(self._edges)})"
