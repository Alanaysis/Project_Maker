"""Tests for advanced PageRank features: Personalized, Topic-Sensitive, Evaluation."""

import pytest
import numpy as np

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank, PageRankVariant, ConvergenceAnalysis, RankingQualityMetrics
from src.evaluation import PageRankEvaluator, GraphStatistics
from src.applications import (
    WebRankingSystem, WebPage,
    SocialNetworkAnalyzer, SocialUser,
    RecommendationSystem
)


class TestPersonalizedPageRank:
    """Test cases for Personalized PageRank."""

    def setup_method(self):
        """Set up test fixtures."""
        self.graph = WebGraph.from_edges([
            ("A", "B"), ("A", "C"),
            ("B", "C"),
            ("C", "A"),
            ("D", "C"),
        ])
        self.pr = PageRank(damping_factor=0.85)

    def test_personalized_basic(self):
        """Test basic personalized PageRank computation."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 1.0}
        )

        assert result.converged
        assert len(result.scores) == 4
        assert abs(result.scores.sum() - 1.0) < 1e-10
        assert result.variant == PageRankVariant.PERSONALIZED

    def test_personalized_bias_towards_target(self):
        """Test that personalized PageRank biases towards target pages."""
        # Standard PageRank
        standard = self.pr.compute(self.graph)

        # Personalized towards A
        personal = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 1.0}
        )

        # A should have higher score in personalized version
        a_idx = self.graph.get_page_index("A")
        assert personal.scores[a_idx] > standard.scores[a_idx]

    def test_personalized_multiple_targets(self):
        """Test personalized PageRank with multiple target pages."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 0.5, "B": 0.5}
        )

        assert result.converged
        a_idx = self.graph.get_page_index("A")
        b_idx = self.graph.get_page_index("B")

        # A and B should have higher scores than other pages
        c_idx = self.graph.get_page_index("C")
        d_idx = self.graph.get_page_index("D")
        assert result.scores[a_idx] > result.scores[c_idx]
        assert result.scores[b_idx] > result.scores[d_idx]

    def test_personalized_none_uses_uniform(self):
        """Test that None personalization uses uniform distribution."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector=None
        )

        # Should be similar to standard PageRank
        standard = self.pr.compute(self.graph)
        assert np.allclose(result.scores, standard.scores, atol=1e-6)

    def test_personalized_empty_vector(self):
        """Test personalized PageRank with empty vector."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={}
        )

        # Should fall back to uniform
        assert result.converged

    def test_personalized_invalid_page(self):
        """Test personalized PageRank with non-existent page."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"NonExistent": 1.0}
        )

        # Should fall back to uniform
        assert result.converged

    def test_personalized_scores_sum_to_one(self):
        """Test that personalized scores sum to 1."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 0.3, "C": 0.7}
        )

        assert abs(result.scores.sum() - 1.0) < 1e-10

    def test_personalized_convergence(self):
        """Test convergence of personalized PageRank."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 1.0},
            max_iterations=1000,
            tolerance=1e-10
        )

        assert result.converged
        assert result.final_diff < 1e-10

    def test_personalized_with_history(self):
        """Test personalized PageRank with convergence history tracking."""
        result = self.pr.compute_personalized(
            self.graph,
            personalization_vector={"A": 1.0},
            track_history=True
        )

        assert len(result.convergence_history) > 0
        # History should show decreasing differences
        for i in range(1, len(result.convergence_history)):
            assert result.convergence_history[i] <= result.convergence_history[i-1] * 1.1  # Allow small tolerance


class TestTopicSensitivePageRank:
    """Test cases for Topic-Sensitive PageRank."""

    def setup_method(self):
        """Set up test fixtures."""
        self.graph = WebGraph.from_edges([
            # News cluster
            ("CNN", "BBC"), ("BBC", "CNN"), ("CNN", "Reuters"),
            # Tech cluster
            ("TechCrunch", "Wired"), ("Wired", "TechCrunch"),
            # Cross-links
            ("CNN", "TechCrunch"), ("Wired", "BBC"),
        ])
        self.pr = PageRank(damping_factor=0.85)

    def test_topic_sensitive_basic(self):
        """Test basic topic-sensitive PageRank computation."""
        topics = {
            "News": ["CNN", "BBC"],
            "Tech": ["TechCrunch", "Wired"]
        }

        results = self.pr.compute_topic_sensitive(
            self.graph,
            topic_pages=topics
        )

        assert len(results) == 2
        assert "News" in results
        assert "Tech" in results

        for topic, result in results.items():
            assert result.converged
            assert result.variant == PageRankVariant.TOPIC_SENSITIVE

    def test_topic_sensitive_variant(self):
        """Test that results have correct variant type."""
        topics = {"News": ["CNN", "BBC"]}

        results = self.pr.compute_topic_sensitive(
            self.graph,
            topic_pages=topics
        )

        assert results["News"].variant == PageRankVariant.TOPIC_SENSITIVE

    def test_topic_sensitive_bias(self):
        """Test that topic-sensitive PageRank biases towards topic pages."""
        topics = {
            "News": ["CNN", "BBC"],
            "Tech": ["TechCrunch", "Wired"]
        }

        results = self.pr.compute_topic_sensitive(
            self.graph,
            topic_pages=topics
        )

        # News topic should rank news pages higher
        news_result = results["News"]
        cnn_idx = self.graph.get_page_index("CNN")
        tc_idx = self.graph.get_page_index("TechCrunch")

        assert news_result.scores[cnn_idx] > news_result.scores[tc_idx]

        # Tech topic should rank tech pages higher
        tech_result = results["Tech"]
        assert tech_result.scores[tc_idx] > tech_result.scores[cnn_idx]

    def test_topic_sensitive_with_weights(self):
        """Test topic-sensitive PageRank with custom weights."""
        topics = {
            "News": ["CNN", "BBC"],
            "Tech": ["TechCrunch", "Wired"]
        }
        weights = {
            "News": 0.7,
            "Tech": 0.3
        }

        results = self.pr.compute_topic_sensitive(
            self.graph,
            topic_pages=topics,
            topic_weights=weights
        )

        assert len(results) == 2

    def test_topic_sensitive_combined(self):
        """Test combined topic-sensitive PageRank."""
        topics = {
            "News": ["CNN", "BBC"],
            "Tech": ["TechCrunch", "Wired"]
        }

        result = self.pr.compute_topic_sensitive_combined(
            self.graph,
            topic_pages=topics
        )

        assert result.converged
        assert len(result.scores) == self.graph.num_pages
        assert abs(result.scores.sum() - 1.0) < 1e-10

    def test_topic_sensitive_combined_weights(self):
        """Test combined topic-sensitive PageRank with different weights."""
        topics = {
            "News": ["CNN", "BBC"],
            "Tech": ["TechCrunch", "Wired"]
        }

        # News-heavy
        news_heavy = self.pr.compute_topic_sensitive_combined(
            self.graph,
            topic_pages=topics,
            topic_weights={"News": 0.9, "Tech": 0.1}
        )

        # Tech-heavy
        tech_heavy = self.pr.compute_topic_sensitive_combined(
            self.graph,
            topic_pages=topics,
            topic_weights={"News": 0.1, "Tech": 0.9}
        )

        # Results should be different
        assert not np.allclose(news_heavy.scores, tech_heavy.scores, atol=1e-4)

    def test_topic_sensitive_single_topic(self):
        """Test topic-sensitive PageRank with single topic."""
        topics = {"News": ["CNN", "BBC"]}

        result = self.pr.compute_topic_sensitive_combined(
            self.graph,
            topic_pages=topics
        )

        assert result.converged


class TestPageRankEvaluation:
    """Test cases for PageRank evaluation module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.graph = WebGraph.from_edges([
            ("A", "B"), ("A", "C"),
            ("B", "C"),
            ("C", "A"),
            ("D", "C"),
        ])
        self.evaluator = PageRankEvaluator(damping_factor=0.85)

    def test_graph_statistics(self):
        """Test graph statistics computation."""
        stats = self.evaluator.analyze_graph(self.graph)

        assert isinstance(stats, GraphStatistics)
        assert stats.num_pages == 4
        assert stats.num_links == 5
        assert stats.density > 0
        assert stats.avg_out_degree > 0

    def test_graph_statistics_empty(self):
        """Test graph statistics for empty graph."""
        empty_graph = WebGraph()
        stats = self.evaluator.analyze_graph(empty_graph)

        assert stats.num_pages == 0
        assert stats.num_links == 0

    def test_convergence_analysis(self):
        """Test convergence analysis."""
        analysis = self.evaluator.analyze_convergence(self.graph)

        assert isinstance(analysis, ConvergenceAnalysis)
        assert analysis.converged
        assert analysis.iterations > 0
        assert len(analysis.convergence_history) > 0

    def test_convergence_history_decreasing(self):
        """Test that convergence history shows decreasing values."""
        analysis = self.evaluator.analyze_convergence(
            self.graph,
            max_iterations=100,
            tolerance=1e-10
        )

        # History should generally decrease
        for i in range(1, len(analysis.convergence_history)):
            assert analysis.convergence_history[i] <= analysis.convergence_history[i-1] * 1.01

    def test_damping_factor_analysis(self):
        """Test damping factor impact analysis."""
        analysis = self.evaluator.analyze_damping_factor_impact(
            self.graph,
            damping_factors=[0.5, 0.7, 0.85, 0.95]
        )

        assert len(analysis.damping_factors) == 4
        assert len(analysis.scores) == 4
        assert len(analysis.iterations) == 4

    def test_damping_factor_correlations(self):
        """Test that damping factor correlations are computed."""
        analysis = self.evaluator.analyze_damping_factor_impact(
            self.graph,
            damping_factors=[0.5, 0.85]
        )

        assert len(analysis.score_correlations) == 1
        corr = list(analysis.score_correlations.values())[0]
        assert -1 <= corr <= 1

    def test_robustness_analysis(self):
        """Test robustness analysis."""
        analysis = self.evaluator.analyze_robustness(
            self.graph,
            num_perturbations=3,
            perturbation_rate=0.2
        )

        assert len(analysis.perturbed_scores) == 3
        assert len(analysis.score_differences) == 3
        assert len(analysis.rank_correlations) == 3

    def test_algorithm_comparison(self):
        """Test comparison of different algorithms."""
        results = self.evaluator.compare_algorithms(self.graph)

        assert 'iterative' in results
        assert 'power_iteration' in results
        assert 'algebraic' in results

        # Results should be similar
        iter_scores = results['iterative'].scores
        power_scores = results['power_iteration'].scores
        algebraic_scores = results['algebraic'].scores

        assert np.allclose(iter_scores, power_scores, atol=1e-4)
        assert np.allclose(iter_scores, algebraic_scores, atol=1e-4)

    def test_sensitivity_analysis(self):
        """Test sensitivity analysis."""
        results = self.evaluator.sensitivity_analysis(
            self.graph,
            damping_factors=[0.5, 0.85],
            tolerances=[1e-4, 1e-8]
        )

        assert 'damping_factor_sensitivity' in results
        assert 'tolerance_sensitivity' in results
        assert 'score_variance' in results
        assert 'rank_stability' in results


class TestRankingQuality:
    """Test cases for ranking quality evaluation."""

    def test_identical_rankings(self):
        """Test ranking quality for identical rankings."""
        ranking = [("A", 0.4), ("B", 0.3), ("C", 0.2), ("D", 0.1)]

        from src.pagerank import PageRank
        metrics = PageRank.evaluate_ranking_quality(ranking, ranking)

        assert metrics.kendall_tau == 1.0
        assert metrics.spearman_rho == 1.0

    def test_reversed_rankings(self):
        """Test ranking quality for reversed rankings."""
        ranking1 = [("A", 0.4), ("B", 0.3), ("C", 0.2), ("D", 0.1)]
        ranking2 = [("D", 0.4), ("C", 0.3), ("B", 0.2), ("A", 0.1)]

        from src.pagerank import PageRank
        metrics = PageRank.evaluate_ranking_quality(ranking1, ranking2)

        assert metrics.kendall_tau == -1.0

    def test_partial_overlap(self):
        """Test ranking quality with partial overlap."""
        ranking1 = [("A", 0.4), ("B", 0.3), ("C", 0.2)]
        ranking2 = [("A", 0.4), ("X", 0.3), ("B", 0.2)]

        from src.pagerank import PageRank
        metrics = PageRank.evaluate_ranking_quality(ranking1, ranking2)

        assert -1 <= metrics.kendall_tau <= 1
        assert -1 <= metrics.spearman_rho <= 1

    def test_precision_recall_at_k(self):
        """Test precision and recall at k."""
        ranking1 = [("A", 0.4), ("B", 0.3), ("C", 0.2), ("D", 0.1)]
        ranking2 = [("A", 0.4), ("B", 0.3), ("X", 0.2), ("Y", 0.1)]

        from src.pagerank import PageRank
        metrics = PageRank.evaluate_ranking_quality(
            ranking1, ranking2, k_values=[1, 2, 3]
        )

        assert 1 in metrics.precision_at_k
        assert 1 in metrics.recall_at_k


class TestWebRankingApplication:
    """Test cases for web ranking application."""

    def test_web_ranking_basic(self):
        """Test basic web ranking functionality."""
        system = WebRankingSystem()

        pages = [
            WebPage(url="A", title="Page A", content="", links=["B"]),
            WebPage(url="B", title="Page B", content="", links=["A"]),
        ]

        system.add_pages(pages)
        result = system.compute_ranking()

        assert result.converged
        assert len(result.scores) == 2

    def test_web_ranking_personalized(self):
        """Test personalized web ranking."""
        system = WebRankingSystem()

        pages = [
            WebPage(url="A", title="Page A", content="", links=["B"], category="tech"),
            WebPage(url="B", title="Page B", content="", links=["A"], category="news"),
        ]

        system.add_pages(pages)

        result = system.compute_personalized_ranking(
            preferred_categories=["tech"]
        )

        assert result.converged


class TestSocialNetworkApplication:
    """Test cases for social network application."""

    def test_social_network_basic(self):
        """Test basic social network analysis."""
        analyzer = SocialNetworkAnalyzer()

        users = [
            SocialUser(user_id="A", name="Alice", interests=[], followers=["B"], following=["B"]),
            SocialUser(user_id="B", name="Bob", interests=[], followers=["A"], following=["A"]),
        ]

        analyzer.add_users(users)
        result = analyzer.compute_influence_ranking()

        assert result.converged
        assert len(result.scores) == 2

    def test_social_network_recommendations(self):
        """Test social network recommendations."""
        analyzer = SocialNetworkAnalyzer()

        users = [
            SocialUser(user_id="A", name="Alice", interests=[], followers=["B"], following=["B"]),
            SocialUser(user_id="B", name="Bob", interests=[], followers=["A", "C"], following=["A", "C"]),
            SocialUser(user_id="C", name="Charlie", interests=[], followers=["B"], following=["B"]),
        ]

        analyzer.add_users(users)
        recs = analyzer.get_recommendations("A", max_recommendations=2)

        assert len(recs) <= 2


class TestRecommendationSystem:
    """Test cases for recommendation system."""

    def test_recommendation_basic(self):
        """Test basic recommendation functionality."""
        rec_system = RecommendationSystem()

        rec_system.add_interaction("user1", "item1", 5.0)
        rec_system.add_interaction("user1", "item2", 4.0)
        rec_system.add_interaction("user2", "item1", 4.0)
        rec_system.add_interaction("user2", "item3", 5.0)

        recs = rec_system.recommend("user1", num_recommendations=2)

        assert len(recs) <= 2
        # Should not recommend already rated items
        for item, _ in recs:
            assert item != "item1"
            assert item != "item2"

    def test_recommendation_similar_items(self):
        """Test finding similar items."""
        rec_system = RecommendationSystem()

        rec_system.add_interaction("user1", "item1", 5.0)
        rec_system.add_interaction("user1", "item2", 4.0)
        rec_system.add_similar_items("item1", "item2")

        similar = rec_system.recommend_similar("item1", num_recommendations=2)

        assert len(similar) <= 2

    def test_recommendation_topic_based(self):
        """Test topic-based recommendations."""
        rec_system = RecommendationSystem()

        rec_system.add_interaction("user1", "tech1", 5.0)
        rec_system.add_interaction("user1", "sci1", 4.0)

        topics = {
            "Tech": ["tech1", "tech2"],
            "Science": ["sci1", "sci2"]
        }

        topic_recs = rec_system.recommend_by_topic(
            "user1",
            topic_items=topics,
            num_recommendations=2
        )

        assert "Tech" in topic_recs
        assert "Science" in topic_recs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
