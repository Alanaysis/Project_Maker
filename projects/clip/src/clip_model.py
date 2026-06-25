"""CLIP model implementation."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple

from .encoders import ImageEncoder, TextEncoder
from .contrastive_loss import CLIPLoss


class CLIP(nn.Module):
    """
    CLIP: Contrastive Language-Image Pre-training

    A model that learns visual concepts from natural language supervision.
    """

    def __init__(
        self,
        embed_dim: int = 512,
        image_hidden_dim: int = 256,
        text_hidden_dim: int = 256,
        vocab_size: int = 10000,
        text_num_heads: int = 8,
        text_num_layers: int = 6,
        max_seq_length: int = 77,
        temperature: float = 0.07,
        learnable_temperature: bool = True,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        # Encoders
        self.image_encoder = ImageEncoder(
            embed_dim=embed_dim,
            hidden_dim=image_hidden_dim,
        )

        self.text_encoder = TextEncoder(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            hidden_dim=text_hidden_dim,
            num_heads=text_num_heads,
            num_layers=text_num_layers,
            max_seq_length=max_seq_length,
        )

        # Loss function
        self.loss_fn = CLIPLoss(
            temperature=temperature,
            learnable_temperature=learnable_temperature,
        )

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode images to embeddings.

        Args:
            images: Input images [batch_size, channels, height, width]

        Returns:
            Image embeddings [batch_size, embed_dim]
        """
        return self.image_encoder(images)

    def encode_text(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Encode text to embeddings.

        Args:
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            Text embeddings [batch_size, embed_dim]
        """
        return self.text_encoder(input_ids, attention_mask)

    def forward(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Forward pass for training.

        Args:
            images: Input images [batch_size, channels, height, width]
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            loss: Contrastive loss
            metrics: Dictionary of metrics
        """
        # Encode images and text
        image_embeddings = self.encode_image(images)
        text_embeddings = self.encode_text(input_ids, attention_mask)

        # Compute loss
        loss, metrics = self.loss_fn(image_embeddings, text_embeddings)

        return loss, metrics

    def get_similarity(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Compute similarity between images and text.

        Args:
            images: Input images [batch_size, channels, height, width]
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            Similarity matrix [batch_size, batch_size]
        """
        image_embeddings = self.encode_image(images)
        text_embeddings = self.encode_text(input_ids, attention_mask)

        # Normalize
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # Compute cosine similarity
        similarity = torch.matmul(image_embeddings, text_embeddings.t())

        return similarity

    def zero_shot_classify(
        self,
        images: torch.Tensor,
        class_descriptions: list,
        tokenizer=None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Perform zero-shot classification.

        Args:
            images: Input images [batch_size, channels, height, width]
            class_descriptions: List of class description strings
            tokenizer: Tokenizer for text encoding

        Returns:
            probabilities: Class probabilities [batch_size, num_classes]
            predictions: Predicted class indices [batch_size]
        """
        if tokenizer is None:
            raise ValueError("Tokenizer is required for zero-shot classification")

        # Encode images
        image_embeddings = self.encode_image(images)

        # Encode class descriptions
        text_inputs = tokenizer(
            class_descriptions,
            padding=True,
            truncation=True,
            return_tensors="pt",
        ).to(images.device)

        text_embeddings = self.encode_text(
            text_inputs["input_ids"],
            text_inputs.get("attention_mask"),
        )

        # Normalize
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # Compute similarity
        similarity = torch.matmul(image_embeddings, text_embeddings.t())

        # Apply temperature scaling
        temperature = self.loss_fn.logit_scale.exp()
        logits = similarity * temperature

        # Get probabilities
        probabilities = F.softmax(logits, dim=-1)
        predictions = logits.argmax(dim=-1)

        return probabilities, predictions


def create_clip_model(
    embed_dim: int = 512,
    vocab_size: int = 10000,
    **kwargs,
) -> CLIP:
    """
    Factory function to create a CLIP model.

    Args:
        embed_dim: Embedding dimension
        vocab_size: Vocabulary size
        **kwargs: Additional arguments

    Returns:
        CLIP model instance
    """
    return CLIP(
        embed_dim=embed_dim,
        vocab_size=vocab_size,
        **kwargs,
    )
