"""Contrastive loss functions for CLIP training."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss for CLIP training.
    Uses symmetric cross-entropy loss over cosine similarities.
    """

    def __init__(self, temperature: float = 0.07):
        """
        Initialize contrastive loss.

        Args:
            temperature: Temperature parameter for softmax
        """
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        image_embeddings: torch.Tensor,
        text_embeddings: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Compute contrastive loss.

        Args:
            image_embeddings: Image embeddings [batch_size, embed_dim]
            text_embeddings: Text embeddings [batch_size, embed_dim]

        Returns:
            loss: Total contrastive loss
            image_to_text_loss: Loss for image-to-text direction
            text_to_image_loss: Loss for text-to-image direction
        """
        # Normalize embeddings
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # Compute cosine similarity matrix
        logits_per_image = torch.matmul(
            image_embeddings, text_embeddings.t()
        ) / self.temperature

        logits_per_text = logits_per_image.t()

        # Create labels (diagonal is positive pair)
        batch_size = image_embeddings.shape[0]
        labels = torch.arange(batch_size, device=image_embeddings.device)

        # Compute cross-entropy loss in both directions
        image_to_text_loss = F.cross_entropy(logits_per_image, labels)
        text_to_image_loss = F.cross_entropy(logits_per_text, labels)

        # Symmetric loss
        loss = (image_to_text_loss + text_to_image_loss) / 2

        return loss, image_to_text_loss, text_to_image_loss


class CLIPLoss(nn.Module):
    """
    CLIP-style contrastive loss with additional features.
    """

    def __init__(
        self,
        temperature: float = 0.07,
        learnable_temperature: bool = True,
    ):
        super().__init__()
        self.temperature = temperature

        # Learnable temperature parameter
        if learnable_temperature:
            self.logit_scale = nn.Parameter(
                torch.ones([]) * torch.log(torch.tensor(1.0 / temperature))
            )
        else:
            self.register_buffer(
                "logit_scale",
                torch.tensor(1.0 / temperature),
            )

    def forward(
        self,
        image_embeddings: torch.Tensor,
        text_embeddings: torch.Tensor,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Compute CLIP loss.

        Args:
            image_embeddings: Image embeddings [batch_size, embed_dim]
            text_embeddings: Text embeddings [batch_size, embed_dim]

        Returns:
            loss: Total loss
            metrics: Dictionary of loss components
        """
        # Normalize embeddings
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # Compute cosine similarity with learnable temperature
        logit_scale = self.logit_scale.exp()
        logits_per_image = logit_scale * torch.matmul(
            image_embeddings, text_embeddings.t()
        )
        logits_per_text = logits_per_image.t()

        # Labels
        batch_size = image_embeddings.shape[0]
        labels = torch.arange(batch_size, device=image_embeddings.device)

        # Compute loss
        image_to_text_loss = F.cross_entropy(logits_per_image, labels)
        text_to_image_loss = F.cross_entropy(logits_per_text, labels)
        loss = (image_to_text_loss + text_to_image_loss) / 2

        # Compute accuracy metrics
        with torch.no_grad():
            i2t_acc = (logits_per_image.argmax(dim=1) == labels).float().mean()
            t2i_acc = (logits_per_text.argmax(dim=1) == labels).float().mean()

        metrics = {
            "loss": loss.item(),
            "i2t_loss": image_to_text_loss.item(),
            "t2i_loss": text_to_image_loss.item(),
            "i2t_acc": i2t_acc.item(),
            "t2i_acc": t2i_acc.item(),
            "temperature": 1.0 / logit_scale.item(),
        }

        return loss, metrics


def contrastive_loss(
    image_embeddings: torch.Tensor,
    text_embeddings: torch.Tensor,
    temperature: float = 0.07,
) -> torch.Tensor:
    """
    Functional interface for contrastive loss.

    Args:
        image_embeddings: Image embeddings [batch_size, embed_dim]
        text_embeddings: Text embeddings [batch_size, embed_dim]
        temperature: Temperature parameter

    Returns:
        loss: Contrastive loss
    """
    criterion = ContrastiveLoss(temperature=temperature)
    loss, _, _ = criterion(image_embeddings, text_embeddings)
    return loss
