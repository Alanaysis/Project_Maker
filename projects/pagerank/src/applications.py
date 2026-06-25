"""Application modules for PageRank algorithm."""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from .graph import WebGraph
from .pagerank import PageRank, PageRankResult


@dataclass
class WebPage:
    """Represents a web page with metadata."""
    url: str
    title: str
    content: str
    links: List[str]
    category: Optional[str] = None


class WebRankingSystem:
    """
    Web page ranking system using PageRank.

    Implements web page ranking with:
    - Standard PageRank for link-based ranking
    - Personalized PageRank for user preferences
    - Topic-Sensitive PageRank for content relevance
    """

    def __init__(self, damping_factor: float = 0.85):
        """
        Initialize web ranking system.

        Args:
            damping_factor: PageRank damping factor
        """
        self.pagerank = PageRank(damping_factor=damping_factor)
        self.graph = WebGraph()
        self.pages: Dict[str, WebPage] = {}

    def add_page(self, page: WebPage) -> None:
        """
        Add a web page to the ranking system.

        Args:
            page: WebPage instance
        """
        self.pages[page.url] = page
        self.graph.add_page(page.url)

        # Add links
        for link in page.links:
            self.graph.add_link(page.url, link)

    def add_pages(self, pages: List[WebPage]) -> None:
        """Add multiple web pages."""
        for page in pages:
            self.add_page(page)

    def compute_ranking(self) -> PageRankResult:
        """
        Compute standard PageRank ranking.

        Returns:
            PageRankResult with page rankings
        """
        return self.pagerank.compute(self.graph)

    def compute_personalized_ranking(
        self,
        preferred_categories: Optional[List[str]] = None,
        preferred_pages: Optional[List[str]] = None
    ) -> PageRankResult:
        """
        Compute personalized PageRank ranking.

        Args:
            preferred_categories: List of preferred content categories
            preferred_pages: List of preferred page URLs

        Returns:
            PageRankResult with personalized rankings
        """
        # Build personalization vector
        personalization = {}

        if preferred_categories:
            for url, page in self.pages.items():
                if page.category in preferred_categories:
                    personalization[url] = 1.0

        if preferred_pages:
            for url in preferred_pages:
                if url in self.pages:
                    personalization[url] = personalization.get(url, 0) + 1.0

        if not personalization:
            return self.compute_ranking()

        # Normalize
        total = sum(personalization.values())
        personalization = {k: v / total for k, v in personalization.items()}

        return self.pagerank.compute_personalized(
            self.graph,
            personalization_vector=personalization
        )

    def compute_topic_ranking(
        self,
        topics: Dict[str, List[str]]
    ) -> Dict[str, PageRankResult]:
        """
        Compute topic-sensitive PageRank ranking.

        Args:
            topics: Dict mapping topic names to lists of seed URLs

        Returns:
            Dict mapping topics to PageRankResult
        """
        return self.pagerank.compute_topic_sensitive(
            self.graph,
            topic_pages=topics
        )


@dataclass
class SocialUser:
    """Represents a user in a social network."""
    user_id: str
    name: str
    interests: List[str]
    followers: List[str]
    following: List[str]


class SocialNetworkAnalyzer:
    """
    Social network analysis using PageRank.

    Implements:
    - Influence ranking
    - Community detection
    - Recommendation based on network structure
    """

    def __init__(self, damping_factor: float = 0.85):
        """
        Initialize social network analyzer.

        Args:
            damping_factor: PageRank damping factor
        """
        self.pagerank = PageRank(damping_factor=damping_factor)
        self.graph = WebGraph()
        self.users: Dict[str, SocialUser] = {}

    def add_user(self, user: SocialUser) -> None:
        """
        Add a user to the social network.

        Args:
            user: SocialUser instance
        """
        self.users[user.user_id] = user
        self.graph.add_page(user.user_id)

        # Add follow relationships (follower -> followed)
        for followed in user.following:
            self.graph.add_link(user.user_id, followed)

    def add_users(self, users: List[SocialUser]) -> None:
        """Add multiple users."""
        for user in users:
            self.add_user(user)

    def compute_influence_ranking(self) -> PageRankResult:
        """
        Compute influence ranking using PageRank.

        Users with more followers (incoming links) rank higher.
        Followers who are themselves influential contribute more.

        Returns:
            PageRankResult with influence rankings
        """
        return self.pagerank.compute(self.graph)

    def compute_personalized_influence(
        self,
        seed_users: List[str]
    ) -> PageRankResult:
        """
        Compute personalized influence ranking.

        Ranks users based on proximity to seed users in the network.

        Args:
            seed_users: List of user IDs to use as seeds

        Returns:
            PageRankResult with personalized rankings
        """
        personalization = {uid: 1.0 / len(seed_users) for uid in seed_users}
        return self.pagerank.compute_personalized(
            self.graph,
            personalization_vector=personalization
        )

    def compute_topic_influence(
        self,
        topic_users: Dict[str, List[str]]
    ) -> Dict[str, PageRankResult]:
        """
        Compute topic-specific influence rankings.

        Args:
            topic_users: Dict mapping topic names to lists of influential users

        Returns:
            Dict mapping topics to PageRankResult
        """
        return self.pagerank.compute_topic_sensitive(
            self.graph,
            topic_pages=topic_users
        )

    def get_recommendations(
        self,
        user_id: str,
        max_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get user recommendations based on network structure.

        Recommends users who are:
        1. Not already followed
        2. Followed by users the target user follows
        3. High PageRank in the network

        Args:
            user_id: Target user ID
            max_recommendations: Maximum number of recommendations

        Returns:
            List of (user_id, score) tuples
        """
        if user_id not in self.users:
            return []

        user = self.users[user_id]
        following_set = set(user.following)
        following_set.add(user_id)  # Don't recommend self

        # Compute personalized PageRank from user's perspective
        result = self.pagerank.compute_personalized(
            self.graph,
            personalization_vector={user_id: 1.0}
        )

        # Filter out already followed users
        recommendations = []
        for page, score in result.ranked_pages:
            if page not in following_set:
                recommendations.append((page, score))
                if len(recommendations) >= max_recommendations:
                    break

        return recommendations

    def detect_communities(
        self,
        num_communities: int = 3
    ) -> Dict[int, List[str]]:
        """
        Detect communities using personalized PageRank.

        Uses multiple seed nodes to identify community structure.

        Args:
            num_communities: Number of communities to detect

        Returns:
            Dict mapping community IDs to lists of user IDs
        """
        # Select seed nodes (users with highest degree)
        adj = self.graph.build_adjacency_matrix()
        degrees = np.array(adj.sum(axis=1)).flatten()
        seed_indices = np.argsort(-degrees)[:num_communities]

        communities = {}
        page_names = self.graph.page_names

        for i, seed_idx in enumerate(seed_indices):
            seed_user = page_names[seed_idx]

            # Compute personalized PageRank from seed
            result = self.pagerank.compute_personalized(
                self.graph,
                personalization_vector={seed_user: 1.0}
            )

            # Assign users to community based on highest score
            for page, score in result.ranked_pages[:len(self.users) // num_communities + 1]:
                if page not in [u for comm in communities.values() for u in comm]:
                    communities.setdefault(i, []).append(page)

        return communities


class RecommendationSystem:
    """
    Recommendation system using PageRank.

    Implements collaborative filtering using:
    - User-item bipartite graph
    - Personalized PageRank for recommendations
    - Topic-sensitive recommendations
    """

    def __init__(self, damping_factor: float = 0.85):
        """
        Initialize recommendation system.

        Args:
            damping_factor: PageRank damping factor
        """
        self.pagerank = PageRank(damping_factor=damping_factor)
        self.graph = WebGraph()
        self.users: Set[str] = set()
        self.items: Set[str] = set()
        self.ratings: Dict[Tuple[str, str], float] = {}

    def add_interaction(
        self,
        user_id: str,
        item_id: str,
        rating: float = 1.0
    ) -> None:
        """
        Add a user-item interaction.

        Args:
            user_id: User identifier
            item_id: Item identifier
            rating: Interaction strength (default 1.0)
        """
        self.users.add(user_id)
        self.items.add(item_id)
        self.ratings[(user_id, item_id)] = rating

        # Add to graph: user -> item (positive interaction)
        self.graph.add_link(f"user_{user_id}", f"item_{item_id}")

    def add_similar_items(
        self,
        item1_id: str,
        item2_id: str,
        similarity: float = 1.0
    ) -> None:
        """
        Add similarity relationship between items.

        Args:
            item1_id: First item
            item2_id: Second item
            similarity: Similarity strength
        """
        self.graph.add_link(f"item_{item1_id}", f"item_{item2_id}")
        self.graph.add_link(f"item_{item2_id}", f"item_{item1_id}")

    def add_user_similarity(
        self,
        user1_id: str,
        user2_id: str,
        similarity: float = 1.0
    ) -> None:
        """
        Add similarity relationship between users.

        Args:
            user1_id: First user
            user2_id: Second user
            similarity: Similarity strength
        """
        self.graph.add_link(f"user_{user1_id}", f"user_{user2_id}")
        self.graph.add_link(f"user_{user2_id}", f"user_{user1_id}")

    def recommend(
        self,
        user_id: str,
        num_recommendations: int = 10,
        exclude_rated: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Generate recommendations for a user.

        Args:
            user_id: Target user
            num_recommendations: Number of items to recommend
            exclude_rated: Whether to exclude already rated items

        Returns:
            List of (item_id, score) tuples
        """
        # Compute personalized PageRank from user
        result = self.pagerank.compute_personalized(
            self.graph,
            personalization_vector={f"user_{user_id}": 1.0}
        )

        # Extract item scores
        recommendations = []
        rated_items = set()
        if exclude_rated:
            rated_items = {item for (user, item), _ in self.ratings.items()
                          if user == user_id}

        for page, score in result.ranked_pages:
            if page.startswith("item_"):
                item_id = page[5:]  # Remove "item_" prefix
                if item_id not in rated_items:
                    recommendations.append((item_id, score))
                    if len(recommendations) >= num_recommendations:
                        break

        return recommendations

    def recommend_similar(
        self,
        item_id: str,
        num_recommendations: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find similar items using PageRank.

        Args:
            item_id: Target item
            num_recommendations: Number of similar items

        Returns:
            List of (item_id, score) tuples
        """
        # Compute personalized PageRank from item
        result = self.pagerank.compute_personalized(
            self.graph,
            personalization_vector={f"item_{item_id}": 1.0}
        )

        # Extract similar items
        similar = []
        for page, score in result.ranked_pages:
            if page.startswith("item_"):
                similar_item_id = page[5:]
                if similar_item_id != item_id:
                    similar.append((similar_item_id, score))
                    if len(similar) >= num_recommendations:
                        break

        return similar

    def recommend_by_topic(
        self,
        user_id: str,
        topic_items: Dict[str, List[str]],
        num_recommendations: int = 10
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Generate topic-specific recommendations.

        Args:
            user_id: Target user
            topic_items: Dict mapping topics to item lists
            num_recommendations: Number of items per topic

        Returns:
            Dict mapping topics to recommendation lists
        """
        results = {}

        for topic, items in topic_items.items():
            # Create personalization combining user and topic items
            personalization = {f"user_{user_id}": 1.0}
            for item in items:
                personalization[f"item_{item}"] = 0.5

            result = self.pagerank.compute_personalized(
                self.graph,
                personalization_vector=personalization
            )

            # Extract recommendations
            topic_recs = []
            for page, score in result.ranked_pages:
                if page.startswith("item_"):
                    item_id = page[5:]
                    if item_id not in items:  # Exclude seed items
                        topic_recs.append((item_id, score))
                        if len(topic_recs) >= num_recommendations:
                            break

            results[topic] = topic_recs

        return results
