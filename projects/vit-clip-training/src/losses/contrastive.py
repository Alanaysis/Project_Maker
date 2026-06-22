"""
Contrastive Learning Loss Functions

⭐ Contrastive Learning is the key to CLIP's success:
- Pulls together matching image-text pairs
- Pushes apart non-matching pairs
- Learns a shared embedding space for different modalities

💡 Key Loss Functions:
1. InfoNCE (CLIP's loss): Symmetric cross-entropy over similarity matrix
2. SupConLoss: Supervised contrastive loss with multiple positives
3. Triplet Loss: Anchor-positive-negative formulation

🎯 Why Contrastive Learning?
- Self-supervised: No manual labels needed
- Scalable: Works with billions of image-text pairs
- Transferable: Learned features transfer to many tasks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class ContrastiveLoss(nn.Module):
    """
    Basic contrastive loss (InfoNCE).

    ⭐ InfoNCE Loss:
    L = -log( exp(sim(a, p) / τ) / Σ exp(sim(a, n_i) / τ) )

    Where:
    - a: anchor embedding
    - p: positive embedding
    - n_i: negative embeddings
    - τ: temperature parameter

    💡 Temperature τ controls:
    - Low τ: Sharper distribution, focus on hard negatives
    - High τ: Smoother distribution, consider all negatives equally

    Example:
        >>> loss_fn = ContrastiveLoss(temperature=0.07)
        >>> embeddings = torch.randn(8, 512)  # 8 samples
        >>> labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])  # 4 pairs
        >>> loss = loss_fn(embeddings, labels)
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        features: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Compute contrastive loss.

        Args:
            features: Feature embeddings, shape (B, D)
            labels: Labels for supervised contrastive loss, shape (B,)
            mask: Binary mask for positive pairs, shape (B, B)

        Returns:
            Scalar loss
        """
        # Normalize features
        features = F.normalize(features, dim=1)

        # Compute similarity matrix
        similarity = features @ features.t() / self.temperature

        # Create mask for positive pairs
        if labels is not None:
            # Supervised: same label = positive pair
            mask = (labels.unsqueeze(0) == labels.unsqueeze(1)).float()
        elif mask is None:
            # Self-supervised: diagonal is positive (each sample is its own class)
            mask = torch.eye(features.shape[0], device=features.device)

        # Remove diagonal from mask (self-similarity)
        mask = mask - torch.eye(features.shape[0], device=features.device)

        # Compute log-softmax
        log_probs = F.log_softmax(similarity, dim=1)

        # Average log-probability of positive pairs
        # Avoid log(0) by adding small epsilon
        loss = -(mask * log_probs).sum() / (mask.sum() + 1e-8)

        return loss


class CLIPLoss(nn.Module):
    """
    CLIP's symmetric contrastive loss.

    ⭐ CLIP Loss is symmetric:
    L = (L_image_to_text + L_text_to_image) / 2

    Where:
    - L_image_to_text: For each image, classify the correct text
    - L_text_to_image: For each text, classify the correct image

    💡 Why symmetric?
    - Ensures both modalities are aligned
    - More stable training than asymmetric loss
    - Better gradient flow

    Example:
        >>> loss_fn = CLIPLoss(temperature=0.07)
        >>> image_features = torch.randn(32, 512)
        >>> text_features = torch.randn(32, 512)
        >>> loss = loss_fn(image_features, text_features)
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Compute CLIP contrastive loss.

        Args:
            image_features: Image embeddings, shape (B, D)
            text_features: Text embeddings, shape (B, D)
            labels: Optional labels for computing accuracy

        Returns:
            Dictionary with loss and optional accuracy
        """
        # Normalize features
        image_features = F.normalize(image_features, dim=1)
        text_features = F.normalize(text_features, dim=1)

        # Compute similarity matrix
        # ⭐ Scale by temperature
        logits_per_image = image_features @ text_features.t() / self.temperature
        logits_per_text = logits_per_image.t()

        # Labels: diagonal elements are positive pairs
        batch_size = image_features.shape[0]
        if labels is None:
            labels = torch.arange(batch_size, device=image_features.device)

        # Symmetric cross-entropy loss
        loss_i2t = F.cross_entropy(logits_per_image, labels)
        loss_t2i = F.cross_entropy(logits_per_text, labels)
        loss = (loss_i2t + loss_t2i) / 2

        return loss


class SupConLoss(nn.Module):
    """
    Supervised Contrastive Learning Loss.

    Paper: "Supervised Contrastive Learning" (Khosla et al., 2020)

    ⭐ Extension of InfoNCE:
    - Supports multiple positives per anchor
    - More general than standard contrastive loss
    - Can leverage label information

    💡 Use cases:
    - Multi-label classification
    - Metric learning with multiple positives
    - Semi-supervised learning

    Example:
        >>> loss_fn = SupConLoss(temperature=0.07)
        >>> features = torch.randn(8, 512)
        >>> labels = torch.tensor([0, 0, 1, 1, 0, 1, 2, 2])
        >>> loss = loss_fn(features, labels)
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        features: torch.Tensor,
        labels: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute supervised contrastive loss.

        Args:
            features: Feature embeddings, shape (B, D)
            labels: Labels, shape (B,)

        Returns:
            Scalar loss
        """
        # Normalize features
        features = F.normalize(features, dim=1)

        # Compute similarity matrix
        similarity = features @ features.t() / self.temperature

        # Create mask for positive pairs
        mask = (labels.unsqueeze(0) == labels.unsqueeze(1)).float()

        # Remove diagonal
        mask = mask - torch.eye(features.shape[0], device=features.device)

        # For numerical stability
        logits_max, _ = similarity.max(dim=1, keepdim=True)
        logits = similarity - logits_max.detach()

        # Compute log-sum-exp for denominator
        # Mask out self-similarity
        exp_logits = torch.exp(logits) * (1 - torch.eye(features.shape[0], device=features.device))
        log_sum_exp = torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-8)

        # Compute log probability
        log_probs = logits - log_sum_exp

        # Average log-probability of positive pairs
        # Number of positives per anchor
        num_positives = mask.sum(dim=1)
        # Avoid division by zero
        num_positives = torch.clamp(num_positives, min=1)

        loss = -(mask * log_probs).sum(dim=1) / num_positives
        loss = loss.mean()

        return loss


class NTXentLoss(nn.Module):
    """
    Normalized Temperature-scaled Cross-Entropy Loss (NT-Xent).

    Used in SimCLR and other self-supervised methods.

    ⭐ Key properties:
    - Uses cosine similarity
    - Temperature scaling
    - Large batch size is important

    Example:
        >>> loss_fn = NTXentLoss(temperature=0.5)
        >>> z_i = torch.randn(32, 128)  # Augmented view 1
        >>> z_j = torch.randn(32, 128)  # Augmented view 2
        >>> loss = loss_fn(z_i, z_j)
    """

    def __init__(self, temperature: float = 0.5):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        z_i: torch.Tensor,
        z_j: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute NT-Xent loss.

        Args:
            z_i: Embeddings from augmentation 1, shape (B, D)
            z_j: Embeddings from augmentation 2, shape (B, D)

        Returns:
            Scalar loss
        """
        batch_size = z_i.shape[0]

        # Normalize
        z_i = F.normalize(z_i, dim=1)
        z_j = F.normalize(z_j, dim=1)

        # Concatenate
        z = torch.cat([z_i, z_j], dim=0)  # (2B, D)

        # Compute similarity matrix
        similarity = z @ z.t() / self.temperature  # (2B, 2B)

        # Create mask for positive pairs
        # z_i[k] is positive with z_j[k]
        mask = torch.zeros(2 * batch_size, 2 * batch_size, device=z_i.device)
        mask[:batch_size, batch_size:] = torch.eye(batch_size)
        mask[batch_size:, :batch_size] = torch.eye(batch_size)

        # Remove self-similarity
        self_mask = torch.eye(2 * batch_size, device=z_i.device)
        mask = mask - self_mask

        # For numerical stability
        logits_max, _ = similarity.max(dim=1, keepdim=True)
        logits = similarity - logits_max.detach()

        # Compute log-sum-exp
        exp_logits = torch.exp(logits) * (1 - self_mask)
        log_sum_exp = torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-8)

        # Log probability
        log_probs = logits - log_sum_exp

        # Loss
        loss = -(mask * log_probs).sum() / (2 * batch_size)

        return loss


# Loss function registry
LOSS_REGISTRY = {
    "clip": CLIPLoss,
    "contrastive": ContrastiveLoss,
    "supcon": SupConLoss,
    "ntxent": NTXentLoss,
}


def create_loss(
    loss_name: str = "clip",
    **kwargs,
) -> nn.Module:
    """
    Create a loss function by name.

    Args:
        loss_name: Name of the loss function
        **kwargs: Additional arguments

    Returns:
        Loss function instance
    """
    if loss_name not in LOSS_REGISTRY:
        raise ValueError(f"Unknown loss: {loss_name}. Available: {list(LOSS_REGISTRY.keys())}")

    return LOSS_REGISTRY[loss_name](**kwargs)
