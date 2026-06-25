"""Tests for CLIP model."""

import pytest
import torch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clip_model import CLIP, create_clip_model
from src.encoders import ImageEncoder, TextEncoder
from src.contrastive_loss import ContrastiveLoss, CLIPLoss, contrastive_loss


class TestImageEncoder:
    """Tests for ImageEncoder."""

    def test_output_shape(self):
        """Test output shape is correct."""
        encoder = ImageEncoder(embed_dim=512)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)
        assert output.shape == (2, 512)

    def test_output_normalized(self):
        """Test output is normalized."""
        encoder = ImageEncoder(embed_dim=256)
        x = torch.randn(4, 3, 224, 224)
        output = encoder(x)
        norms = torch.norm(output, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_different_embed_dims(self):
        """Test different embedding dimensions."""
        for embed_dim in [128, 256, 512, 1024]:
            encoder = ImageEncoder(embed_dim=embed_dim)
            x = torch.randn(1, 3, 224, 224)
            output = encoder(x)
            assert output.shape == (1, embed_dim)

    def test_gradient_flow(self):
        """Test gradients flow through the model."""
        encoder = ImageEncoder(embed_dim=256)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)
        loss = output.sum()
        loss.backward()
        for param in encoder.parameters():
            assert param.grad is not None


class TestTextEncoder:
    """Tests for TextEncoder."""

    def test_output_shape(self):
        """Test output shape is correct."""
        encoder = TextEncoder(vocab_size=10000, embed_dim=512)
        input_ids = torch.randint(0, 10000, (2, 77))
        output = encoder(input_ids)
        assert output.shape == (2, 512)

    def test_output_normalized(self):
        """Test output is normalized."""
        encoder = TextEncoder(vocab_size=5000, embed_dim=256)
        input_ids = torch.randint(0, 5000, (4, 50))
        output = encoder(input_ids)
        norms = torch.norm(output, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_with_attention_mask(self):
        """Test with attention mask."""
        encoder = TextEncoder(vocab_size=10000, embed_dim=256)
        input_ids = torch.randint(0, 10000, (2, 77))
        attention_mask = torch.ones(2, 77)
        attention_mask[:, 50:] = 0  # Mask last tokens
        output = encoder(input_ids, attention_mask)
        assert output.shape == (2, 256)

    def test_gradient_flow(self):
        """Test gradients flow through the model."""
        encoder = TextEncoder(vocab_size=10000, embed_dim=256)
        input_ids = torch.randint(0, 10000, (2, 77))
        output = encoder(input_ids)
        loss = output.sum()
        loss.backward()
        for param in encoder.parameters():
            assert param.grad is not None


class TestContrastiveLoss:
    """Tests for contrastive loss functions."""

    def test_loss_shape(self):
        """Test loss is a scalar."""
        criterion = ContrastiveLoss(temperature=0.07)
        image_embeds = torch.randn(4, 256)
        text_embeds = torch.randn(4, 256)
        loss, i2t_loss, t2i_loss = criterion(image_embeds, text_embeds)
        assert loss.shape == ()
        assert i2t_loss.shape == ()
        assert t2i_loss.shape == ()

    def test_loss_positive(self):
        """Test loss is positive."""
        criterion = ContrastiveLoss(temperature=0.07)
        image_embeds = torch.randn(8, 256)
        text_embeds = torch.randn(8, 256)
        loss, _, _ = criterion(image_embeds, text_embeds)
        assert loss.item() > 0

    def test_perfect_alignment(self):
        """Test loss with perfectly aligned embeddings."""
        criterion = ContrastiveLoss(temperature=0.07)
        # Same embeddings should have low loss
        embeds = torch.randn(4, 256)
        embeds = torch.nn.functional.normalize(embeds, dim=-1)
        loss, _, _ = criterion(embeds, embeds)
        # Loss should be low (but not zero due to temperature)
        assert loss.item() < 1.0

    def test_clip_loss_metrics(self):
        """Test CLIPLoss returns metrics."""
        criterion = CLIPLoss(temperature=0.07)
        image_embeds = torch.randn(4, 256)
        text_embeds = torch.randn(4, 256)
        loss, metrics = criterion(image_embeds, text_embeds)
        assert "loss" in metrics
        assert "i2t_acc" in metrics
        assert "t2i_acc" in metrics
        assert "temperature" in metrics


class TestCLIPModel:
    """Tests for CLIP model."""

    def test_forward_pass(self):
        """Test forward pass."""
        model = CLIP(embed_dim=256, vocab_size=10000)
        images = torch.randn(2, 3, 224, 224)
        input_ids = torch.randint(0, 10000, (2, 77))
        loss, metrics = model(images, input_ids)
        assert loss.shape == ()
        assert "loss" in metrics

    def test_encode_image(self):
        """Test image encoding."""
        model = CLIP(embed_dim=256)
        images = torch.randn(4, 3, 224, 224)
        embeddings = model.encode_image(images)
        assert embeddings.shape == (4, 256)

    def test_encode_text(self):
        """Test text encoding."""
        model = CLIP(embed_dim=256, vocab_size=10000)
        input_ids = torch.randint(0, 10000, (4, 77))
        embeddings = model.encode_text(input_ids)
        assert embeddings.shape == (4, 256)

    def test_similarity(self):
        """Test similarity computation."""
        model = CLIP(embed_dim=256, vocab_size=10000)
        images = torch.randn(4, 3, 224, 224)
        input_ids = torch.randint(0, 10000, (4, 77))
        similarity = model.get_similarity(images, input_ids)
        assert similarity.shape == (4, 4)

    def test_factory_function(self):
        """Test factory function."""
        model = create_clip_model(embed_dim=128, vocab_size=5000)
        assert isinstance(model, CLIP)
        assert model.embed_dim == 128

    def test_gradient_flow(self):
        """Test gradients flow through the model."""
        model = CLIP(embed_dim=128, vocab_size=5000)
        images = torch.randn(2, 3, 224, 224)
        input_ids = torch.randint(0, 5000, (2, 77))
        loss, _ = model(images, input_ids)
        loss.backward()
        for param in model.parameters():
            assert param.grad is not None

    def test_different_batch_sizes(self):
        """Test different batch sizes."""
        model = CLIP(embed_dim=128, vocab_size=5000)
        for batch_size in [1, 2, 4, 8]:
            images = torch.randn(batch_size, 3, 224, 224)
            input_ids = torch.randint(0, 5000, (batch_size, 77))
            loss, _ = model(images, input_ids)
            assert loss.shape == ()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
