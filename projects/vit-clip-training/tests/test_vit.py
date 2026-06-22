"""
Unit Tests for Vision Transformer (ViT)

⭐ Key test cases:
1. Forward pass shape correctness
2. Patch embedding computation
3. Different configurations
4. Gradient flow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import torch

from src.models.vit import VisionTransformer, PatchEmbedding, create_vit


class TestPatchEmbedding:
    """Test cases for PatchEmbedding."""

    def test_output_shape(self):
        """Test output shape is correct."""
        embed = PatchEmbedding(
            image_size=224,
            patch_size=16,
            in_channels=3,
            embed_dim=768,
        )
        x = torch.randn(2, 3, 224, 224)
        output = embed(x)

        # Expected: (batch, num_patches + 1, embed_dim)
        num_patches = (224 // 16) ** 2
        assert output.shape == (2, num_patches + 1, 768)

    def test_cls_token_prepended(self):
        """Test that CLS token is prepended."""
        embed = PatchEmbedding(
            image_size=224,
            patch_size=16,
            in_channels=3,
            embed_dim=768,
        )
        x = torch.randn(1, 3, 224, 224)
        output = embed(x)

        # First token should be CLS token
        cls_token = embed.cls_token.expand(1, -1, -1)
        assert torch.allclose(output[:, 0:1, :], cls_token + embed.position_embedding[:, 0:1, :], atol=1e-6)

    def test_different_patch_sizes(self):
        """Test with different patch sizes."""
        for patch_size in [8, 16, 32]:
            embed = PatchEmbedding(
                image_size=224,
                patch_size=patch_size,
                in_channels=3,
                embed_dim=768,
            )
            x = torch.randn(1, 3, 224, 224)
            output = embed(x)

            num_patches = (224 // patch_size) ** 2
            assert output.shape == (1, num_patches + 1, 768)


class TestVisionTransformer:
    """Test cases for VisionTransformer."""

    def test_forward_shape(self):
        """Test forward pass output shape."""
        model = VisionTransformer(
            image_size=224,
            patch_size=16,
            num_classes=1000,
            embed_dim=768,
            depth=12,
            num_heads=12,
        )
        x = torch.randn(2, 3, 224, 224)
        output = model(x)

        assert output.shape == (2, 1000)

    def test_return_features(self):
        """Test feature extraction mode."""
        model = VisionTransformer(
            image_size=224,
            patch_size=16,
            num_classes=1000,
            embed_dim=768,
            depth=12,
            num_heads=12,
        )
        x = torch.randn(2, 3, 224, 224)
        features = model(x, return_features=True)

        assert features.shape == (2, 768)

    def test_global_pool_cls(self):
        """Test CLS token pooling."""
        model = VisionTransformer(
            image_size=224,
            patch_size=16,
            embed_dim=768,
            depth=12,
            num_heads=12,
            global_pool="cls",
        )
        x = torch.randn(1, 3, 224, 224)
        features = model.forward_features(x)

        assert features.shape == (1, 768)

    def test_global_pool_mean(self):
        """Test mean pooling."""
        model = VisionTransformer(
            image_size=224,
            patch_size=16,
            embed_dim=768,
            depth=12,
            num_heads=12,
            global_pool="mean",
        )
        x = torch.randn(1, 3, 224, 224)
        features = model.forward_features(x)

        assert features.shape == (1, 768)

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = VisionTransformer(
            image_size=224,
            patch_size=16,
            embed_dim=384,
            depth=6,
            num_heads=6,
        )
        x = torch.randn(1, 3, 224, 224)
        output = model(x)
        loss = output.sum()
        loss.backward()

        # Check that gradients exist
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"

    def test_different_configs(self):
        """Test different model configurations."""
        configs = [
            {"embed_dim": 384, "depth": 12, "num_heads": 6},   # Small
            {"embed_dim": 768, "depth": 12, "num_heads": 12},  # Base
            {"embed_dim": 1024, "depth": 24, "num_heads": 16}, # Large
        ]

        for config in configs:
            model = VisionTransformer(
                image_size=224,
                patch_size=16,
                **config,
            )
            x = torch.randn(1, 3, 224, 224)
            output = model(x, return_features=True)

            assert output.shape == (1, config["embed_dim"])


class TestCreateViT:
    """Test cases for create_vit helper function."""

    def test_create_vit_small(self):
        """Test creating ViT-Small."""
        model = create_vit("vit_small")
        assert isinstance(model, VisionTransformer)

    def test_create_vit_base(self):
        """Test creating ViT-Base."""
        model = create_vit("vit_base")
        assert isinstance(model, VisionTransformer)

    def test_create_vit_large(self):
        """Test creating ViT-Large."""
        model = create_vit("vit_large")
        assert isinstance(model, VisionTransformer)

    def test_invalid_config(self):
        """Test invalid configuration raises error."""
        with pytest.raises(ValueError):
            create_vit("invalid_config")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
