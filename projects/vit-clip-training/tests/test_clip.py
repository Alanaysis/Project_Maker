"""
Unit Tests for CLIP Model

⭐ Key test cases:
1. Forward pass shape correctness
2. Image and text encoding
3. Loss computation
4. Different configurations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import torch

from src.models.clip import CLIPModel, create_clip_model, CLIPConfig


class TestCLIPModel:
    """Test cases for CLIPModel."""

    def test_forward_shape(self):
        """Test forward pass output shapes."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=512,
            projection_dim=512,
        )

        batch_size = 4
        images = torch.randn(batch_size, 3, 224, 224)
        texts = torch.randint(0, 49408, (batch_size, 77))

        outputs = model(images, texts)

        assert "logits_per_image" in outputs
        assert "logits_per_text" in outputs
        assert "image_embeddings" in outputs
        assert "text_embeddings" in outputs
        assert "loss" in outputs

        assert outputs["logits_per_image"].shape == (batch_size, batch_size)
        assert outputs["logits_per_text"].shape == (batch_size, batch_size)
        assert outputs["image_embeddings"].shape == (batch_size, 512)
        assert outputs["text_embeddings"].shape == (batch_size, 512)

    def test_encode_image(self):
        """Test image encoding."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=512,
            projection_dim=512,
        )

        images = torch.randn(4, 3, 224, 224)
        embeddings = model.encode_image(images)

        assert embeddings.shape == (4, 512)
        # Check normalization
        norms = torch.norm(embeddings, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)

    def test_encode_text(self):
        """Test text encoding."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=512,
            projection_dim=512,
        )

        texts = torch.randint(0, 49408, (4, 77))
        embeddings = model.encode_text(texts)

        assert embeddings.shape == (4, 512)
        # Check normalization
        norms = torch.norm(embeddings, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)

    def test_loss_computation(self):
        """Test loss computation."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=512,
            projection_dim=512,
        )

        images = torch.randn(4, 3, 224, 224)
        texts = torch.randint(0, 49408, (4, 77))

        outputs = model(images, texts, return_loss=True)

        assert "loss" in outputs
        assert outputs["loss"].dim() == 0  # Scalar
        assert outputs["loss"].item() > 0  # Positive loss

    def test_no_loss(self):
        """Test forward pass without loss."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=512,
            projection_dim=512,
        )

        images = torch.randn(4, 3, 224, 224)
        texts = torch.randint(0, 49408, (4, 77))

        outputs = model(images, texts, return_loss=False)

        assert "loss" not in outputs

    def test_temperature_parameter(self):
        """Test that temperature is learnable."""
        model = CLIPModel()

        # Initial temperature should be around 1/0.07
        temp = model.logit_scale.exp().item()
        assert 10 < temp < 20  # Around 14.3

        # Check it's a parameter
        assert isinstance(model.logit_scale, torch.nn.Parameter)

    def test_gradient_flow(self):
        """Test gradient flow through the model."""
        model = CLIPModel(
            image_model="vit_base",
            image_size=224,
            patch_size=32,
            embed_dim=256,
            projection_dim=256,
        )

        images = torch.randn(2, 3, 224, 224)
        texts = torch.randint(0, 49408, (2, 77))

        outputs = model(images, texts, return_loss=True)
        outputs["loss"].backward()

        # Check gradients exist
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"


class TestCreateCLIP:
    """Test cases for create_clip_model helper."""

    def test_create_vit_b32(self):
        """Test creating CLIP-ViT-B/32."""
        model = create_clip_model("vit_b32")
        assert isinstance(model, CLIPModel)

    def test_create_vit_b16(self):
        """Test creating CLIP-ViT-B/16."""
        model = create_clip_model("vit_b16")
        assert isinstance(model, CLIPModel)

    def test_create_vit_l14(self):
        """Test creating CLIP-ViT-L/14."""
        model = create_clip_model("vit_l14")
        assert isinstance(model, CLIPModel)

    def test_invalid_config(self):
        """Test invalid configuration raises error."""
        with pytest.raises(ValueError):
            create_clip_model("invalid_config")

    def test_custom_parameters(self):
        """Test creating model with custom parameters."""
        model = create_clip_model(
            "vit_b32",
            image_size=384,
            projection_dim=256,
        )
        assert isinstance(model, CLIPModel)


class TestCLIPConfig:
    """Test cases for CLIPConfig."""

    def test_configs_exist(self):
        """Test that all configs are defined."""
        assert hasattr(CLIPConfig, "VIT_B32")
        assert hasattr(CLIPConfig, "VIT_B16")
        assert hasattr(CLIPConfig, "VIT_L14")

    def test_config_keys(self):
        """Test that configs have required keys."""
        required_keys = [
            "image_model",
            "image_size",
            "patch_size",
            "embed_dim",
            "projection_dim",
        ]

        for config_name in ["VIT_B32", "VIT_B16", "VIT_L14"]:
            config = getattr(CLIPConfig, config_name)
            for key in required_keys:
                assert key in config, f"{config_name} missing {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
