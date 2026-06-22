"""
Metrics for CLIP Evaluation

⭐ Key Evaluation Metrics:
1. Image-to-Text Retrieval (I2T): Given an image, find matching text
2. Text-to-Image Retrieval (T2I): Given text, find matching image
3. Zero-shot Classification: Classify images using text descriptions

💡 Retrieval Metrics:
- Recall@K: Percentage of queries where the correct match is in top K
- Median Rank: Median position of the correct match
- Mean Rank: Mean position of the correct match

🎯 Zero-shot Classification:
- Encode class descriptions as text embeddings
- Encode images as image embeddings
- Compute cosine similarity
- Predict class with highest similarity
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RetrievalMetrics:
    """Container for retrieval metrics."""

    # Recall@K
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float

    # Rank metrics
    median_rank: float
    mean_rank: float

    # Additional info
    num_queries: int

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "R@1": self.recall_at_1,
            "R@5": self.recall_at_5,
            "R@10": self.recall_at_10,
            "Median Rank": self.median_rank,
            "Mean Rank": self.mean_rank,
        }

    def __str__(self) -> str:
        return (
            f"Recall@1: {self.recall_at_1:.4f} | "
            f"Recall@5: {self.recall_at_5:.4f} | "
            f"Recall@10: {self.recall_at_10:.4f} | "
            f"Median Rank: {self.median_rank:.1f} | "
            f"Mean Rank: {self.mean_rank:.1f}"
        )


class CLIPMetrics:
    """
    Compute CLIP evaluation metrics.

    ⭐ Supports:
    1. Image-to-Text Retrieval
    2. Text-to-Image Retrieval
    3. Zero-shot Classification
    4. Representation quality metrics

    Example:
        >>> metrics = CLIPMetrics()
        >>> image_features = torch.randn(100, 512)
        >>> text_features = torch.randn(100, 512)
        >>> results = metrics.compute_retrieval(image_features, text_features)
        >>> print(results)
    """

    def __init__(self, device: str = "cpu"):
        self.device = device

    def compute_retrieval(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
        k_values: List[int] = [1, 5, 10],
    ) -> Tuple[RetrievalMetrics, RetrievalMetrics]:
        """
        Compute image-to-text and text-to-image retrieval metrics.

        Args:
            image_features: Image embeddings, shape (N, D)
            text_features: Text embeddings, shape (N, D)
            k_values: List of K values for Recall@K

        Returns:
            Tuple of (I2T metrics, T2I metrics)
        """
        # Normalize features
        image_features = F.normalize(image_features, dim=1)
        text_features = F.normalize(text_features, dim=1)

        # Compute similarity matrix
        similarity = image_features @ text_features.t()  # (N, N)

        # Image-to-Text retrieval
        i2t_metrics = self._compute_recall_metrics(
            similarity, k_values
        )

        # Text-to-Image retrieval
        t2i_metrics = self._compute_recall_metrics(
            similarity.t(), k_values
        )

        return i2t_metrics, t2i_metrics

    def _compute_recall_metrics(
        self,
        similarity: torch.Tensor,
        k_values: List[int],
    ) -> RetrievalMetrics:
        """
        Compute recall metrics from similarity matrix.

        Args:
            similarity: Similarity matrix, shape (N, N)
            k_values: List of K values

        Returns:
            RetrievalMetrics
        """
        num_queries = similarity.shape[0]

        # Get rankings (indices that would sort the similarity)
        rankings = similarity.argsort(dim=1, descending=True)

        # Find rank of correct match (diagonal)
        correct_ranks = []
        for i in range(num_queries):
            # Find where the correct match (i) appears in the ranking
            rank = (rankings[i] == i).nonzero(as_tuple=True)[0].item()
            correct_ranks.append(rank + 1)  # 1-indexed

        correct_ranks = torch.tensor(correct_ranks, dtype=torch.float)

        # Compute Recall@K
        recall_at_k = {}
        for k in k_values:
            recall = (correct_ranks <= k).float().mean().item()
            recall_at_k[k] = recall

        # Compute median and mean rank
        median_rank = correct_ranks.median().item()
        mean_rank = correct_ranks.mean().item()

        return RetrievalMetrics(
            recall_at_1=recall_at_k.get(1, 0.0),
            recall_at_5=recall_at_k.get(5, 0.0),
            recall_at_10=recall_at_k.get(10, 0.0),
            median_rank=median_rank,
            mean_rank=mean_rank,
            num_queries=num_queries,
        )

    def compute_zero_shot_accuracy(
        self,
        image_features: torch.Tensor,
        class_features: torch.Tensor,
        labels: torch.Tensor,
    ) -> Dict[str, float]:
        """
        Compute zero-shot classification accuracy.

        ⭐ Zero-shot classification:
        1. Encode class descriptions as text embeddings
        2. Encode images as image embeddings
        3. Predict class with highest cosine similarity

        Args:
            image_features: Image embeddings, shape (N, D)
            class_features: Class embeddings, shape (C, D)
            labels: Ground truth labels, shape (N,)

        Returns:
            Dictionary with accuracy metrics
        """
        # Normalize
        image_features = F.normalize(image_features, dim=1)
        class_features = F.normalize(class_features, dim=1)

        # Compute similarity
        similarity = image_features @ class_features.t()  # (N, C)

        # Get predictions
        predictions = similarity.argmax(dim=1)

        # Compute accuracy
        correct = (predictions == labels).float()
        accuracy = correct.mean().item()

        # Top-5 accuracy
        top5_preds = similarity.topk(5, dim=1).indices
        top5_correct = (top5_preds == labels.unsqueeze(1)).any(dim=1).float()
        top5_accuracy = top5_correct.mean().item()

        return {
            "accuracy": accuracy,
            "top5_accuracy": top5_accuracy,
        }

    def compute_similarity_distribution(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> Dict[str, float]:
        """
        Analyze the distribution of similarities.

        💡 Useful for understanding model behavior:
        - Positive pairs should have high similarity
        - Negative pairs should have low similarity
        - Gap between positive and negative indicates discrimination ability

        Args:
            image_features: Image embeddings, shape (N, D)
            text_features: Text embeddings, shape (N, D)

        Returns:
            Dictionary with distribution statistics
        """
        # Normalize
        image_features = F.normalize(image_features, dim=1)
        text_features = F.normalize(text_features, dim=1)

        # Compute similarity
        similarity = image_features @ text_features.t()

        # Get positive and negative similarities
        batch_size = image_features.shape[0]
        pos_mask = torch.eye(batch_size, device=similarity.device)
        neg_mask = 1 - pos_mask

        pos_sim = similarity[pos_mask.bool()]
        neg_sim = similarity[neg_mask.bool()]

        return {
            "positive_mean": pos_sim.mean().item(),
            "positive_std": pos_sim.std().item(),
            "negative_mean": neg_sim.mean().item(),
            "negative_std": neg_sim.std().item(),
            "gap": (pos_sim.mean() - neg_sim.mean()).item(),
        }


def compute_retrieval_metrics(
    image_features: torch.Tensor,
    text_features: torch.Tensor,
    k_values: List[int] = [1, 5, 10],
) -> Tuple[RetrievalMetrics, RetrievalMetrics]:
    """
    Convenience function to compute retrieval metrics.

    Args:
        image_features: Image embeddings, shape (N, D)
        text_features: Text embeddings, shape (N, D)
        k_values: List of K values for Recall@K

    Returns:
        Tuple of (I2T metrics, T2I metrics)
    """
    metrics = CLIPMetrics()
    return metrics.compute_retrieval(image_features, text_features, k_values)


def compute_accuracy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    top_k: int = 1,
) -> float:
    """
    Compute top-K accuracy.

    Args:
        logits: Prediction logits, shape (N, C)
        labels: Ground truth labels, shape (N,)
        top_k: K for top-K accuracy

    Returns:
        Accuracy value
    """
    with torch.no_grad():
        # Get top-K predictions
        _, pred = logits.topk(top_k, dim=1)

        # Check if correct label is in top-K predictions
        correct = pred.eq(labels.view(-1, 1).expand_as(pred))

        # Compute accuracy
        accuracy = correct.any(dim=1).float().mean().item()

    return accuracy
