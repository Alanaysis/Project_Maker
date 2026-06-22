"""Visualization tools for PageRank results."""

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import Optional, Tuple, List

from .graph import WebGraph
from .pagerank import PageRankResult


class PageRankVisualizer:
    """Visualize PageRank results and web graph structure."""

    @staticmethod
    def plot_ranked_pages(
        result: PageRankResult,
        top_n: int = 10,
        figsize: Tuple[int, int] = (10, 6),
        title: str = "PageRank Scores"
    ) -> plt.Figure:
        """
        Create bar chart of top pages by PageRank score.

        Args:
            result: PageRankResult instance
            top_n: Number of top pages to show
            figsize: Figure size
            title: Chart title

        Returns:
            matplotlib Figure object
        """
        ranked = result.ranked_pages[:top_n]
        pages = [p[0] for p in ranked]
        scores = [p[1] for p in ranked]

        fig, ax = plt.subplots(figsize=figsize)

        # Create horizontal bar chart
        y_pos = np.arange(len(pages))
        bars = ax.barh(y_pos, scores, color=plt.cm.viridis(np.linspace(0, 1, len(pages))))

        ax.set_yticks(y_pos)
        ax.set_yticklabels(pages)
        ax.invert_yaxis()
        ax.set_xlabel('PageRank Score')
        ax.set_title(title)

        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                    f'{score:.4f}', va='center', fontsize=9)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_graph(
        graph: WebGraph,
        result: Optional[PageRankResult] = None,
        figsize: Tuple[int, int] = (12, 10),
        title: str = "Web Graph with PageRank"
    ) -> plt.Figure:
        """
        Visualize the web graph with node sizes proportional to PageRank.

        Args:
            graph: WebGraph instance
            result: Optional PageRankResult for node sizing
            figsize: Figure size
            title: Graph title

        Returns:
            matplotlib Figure object
        """
        # Build NetworkX graph
        G = nx.DiGraph()

        page_names = graph.page_names
        for idx, name in page_names.items():
            G.add_node(name)

        # Add edges
        adj = graph.build_adjacency_matrix()
        rows, cols = adj.nonzero()
        for r, c in zip(rows, cols):
            G.add_edge(page_names[r], page_names[c])

        fig, ax = plt.subplots(figsize=figsize)

        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Node sizes based on PageRank
        if result is not None:
            node_sizes = []
            for node in G.nodes():
                score = result.get_score(node)
                if score is not None:
                    node_sizes.append(score * 5000)
                else:
                    node_sizes.append(100)
        else:
            node_sizes = 300

        # Node colors based on PageRank
        if result is not None:
            node_colors = []
            for node in G.nodes():
                score = result.get_score(node)
                if score is not None:
                    node_colors.append(score)
                else:
                    node_colors.append(0)
            cmap = plt.cm.YlOrRd
        else:
            node_colors = 'lightblue'
            cmap = None

        # Draw graph
        nx.draw_networkx_nodes(G, pos, ax=ax,
                               node_size=node_sizes,
                               node_color=node_colors,
                               cmap=cmap,
                               alpha=0.8)

        nx.draw_networkx_edges(G, pos, ax=ax,
                               edge_color='gray',
                               arrows=True,
                               arrowsize=20,
                               alpha=0.6,
                               connectionstyle='arc3,rad=0.1')

        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight='bold')

        ax.set_title(title, fontsize=14)
        ax.axis('off')

        # Add colorbar if using PageRank colors
        if result is not None and cmap is not None:
            sm = plt.cm.ScalarMappable(cmap=cmap,
                                       norm=plt.Normalize(vmin=0, vmax=max(result.scores)))
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='PageRank Score')

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_convergence(
        scores_history: List[np.ndarray],
        figsize: Tuple[int, int] = (10, 6),
        title: str = "PageRank Convergence"
    ) -> plt.Figure:
        """
        Plot convergence of PageRank scores over iterations.

        Args:
            scores_history: List of score arrays at each iteration
            figsize: Figure size
            title: Chart title

        Returns:
            matplotlib Figure object
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])

        iterations = range(len(scores_history))

        # Plot individual page scores
        for page_idx in range(scores_history[0].shape[0]):
            page_scores = [scores_history[i][page_idx] for i in iterations]
            ax1.plot(iterations, page_scores, alpha=0.7, label=f'Page {page_idx}')

        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('PageRank Score')
        ax1.set_title(title)
        ax1.legend(loc='upper right', fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Plot L1 norm of differences
        if len(scores_history) > 1:
            diffs = [np.abs(scores_history[i] - scores_history[i-1]).sum()
                     for i in range(1, len(scores_history))]
            ax2.plot(range(1, len(scores_history)), diffs, 'b-', linewidth=2)
            ax2.set_xlabel('Iteration')
            ax2.set_ylabel('L1 Difference')
            ax2.set_yscale('log')
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_damping_factor_comparison(
        graph: WebGraph,
        damping_factors: List[float] = [0.5, 0.7, 0.85, 0.95],
        figsize: Tuple[int, int] = (12, 6)
    ) -> plt.Figure:
        """
        Compare PageRank results with different damping factors.

        Args:
            graph: WebGraph instance
            damping_factors: List of damping factors to compare
            figsize: Figure size

        Returns:
            matplotlib Figure object
        """
        from .pagerank import PageRank

        fig, axes = plt.subplots(1, len(damping_factors), figsize=figsize)

        if len(damping_factors) == 1:
            axes = [axes]

        for ax, d in zip(axes, damping_factors):
            pr = PageRank(damping_factor=d)
            result = pr.compute(graph)

            ranked = result.ranked_pages[:10]
            pages = [p[0] for p in ranked]
            scores = [p[1] for p in ranked]

            y_pos = np.arange(len(pages))
            ax.barh(y_pos, scores, color=plt.cm.viridis(np.linspace(0, 1, len(pages))))
            ax.set_yticks(y_pos)
            ax.set_yticklabels(pages)
            ax.invert_yaxis()
            ax.set_xlabel('Score')
            ax.set_title(f'd = {d}')

        plt.suptitle('PageRank with Different Damping Factors', fontsize=14)
        plt.tight_layout()
        return fig
