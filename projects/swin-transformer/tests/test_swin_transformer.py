"""Tests for Swin Transformer implementation.

This module contains comprehensive tests for all components of the
Swin Transformer implementation, including:
- Patch embedding
- Window attention
- Shifted window mechanism
- Complete model forward pass
"""

import sys
import pytest
import torch

# Add src to path for imports
sys.path.insert(0, "/home/siok/project_copyninja/projects/swin-transformer")

from src.patch_embedding import PatchEmbedding, PatchMerging
from src.window_attention import WindowAttention, window_partition, window_reverse
from src.shifted_window import ShiftedWindowTransformerBlock
from src.swin_transformer import SwinTransformer, swin_tiny_patch4_window7_224


class TestPatchEmbedding:
    """Tests for PatchEmbedding module."""

    def test_patch_embedding_output_shape(self):
        """Test that patch embedding produces correct output shape."""
        # Create a small test case
        patch_embed = PatchEmbedding(
            img_size=32,
            patch_size=4,
            in_channels=3,
            embed_dim=96,
        )

        # Create random input
        x = torch.randn(2, 3, 32, 32)

        # Forward pass
        output = patch_embed(x)

        # Check output shape
        # num_patches = (32/4) * (32/4) = 8 * 8 = 64
        assert output.shape == (2, 64, 96), f"Expected (2, 64, 96), got {output.shape}"

    def test_patch_embedding_num_patches(self):
        """Test that number of patches is calculated correctly."""
        patch_embed = PatchEmbedding(img_size=224, patch_size=4, embed_dim=96)

        assert patch_embed.num_patches_h == 56
        assert patch_embed.num_patches_w == 56
        assert patch_embed.num_patches == 3136

    def test_patch_embedding_gradient_flow(self):
        """Test that gradients flow through patch embedding."""
        patch_embed = PatchEmbedding(img_size=32, patch_size=4, embed_dim=96)
        x = torch.randn(1, 3, 32, 32, requires_grad=True)

        output = patch_embed(x)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None, "Gradients should flow to input"
        assert patch_embed.projection.weight.grad is not None, "Gradients should flow to projection weights"


class TestPatchMerging:
    """Tests for PatchMerging module."""

    def test_patch_merging_output_shape(self):
        """Test that patch merging produces correct output shape."""
        patch_merger = PatchMerging(input_resolution=(8, 8), dim=96)

        # Input: (B, H*W, C) = (2, 64, 96)
        x = torch.randn(2, 64, 96)

        # Output should be (B, H/2*W/2, 2*C) = (2, 16, 192)
        output = patch_merger(x)

        assert output.shape == (2, 16, 192), f"Expected (2, 16, 192), got {output.shape}"

    def test_patch_merging_spatial_reduction(self):
        """Test that spatial dimensions are reduced by 2x."""
        patch_merger = PatchMerging(input_resolution=(16, 16), dim=192)

        # Input: (B, H*W, C) = (1, 256, 192)
        x = torch.randn(1, 256, 192)

        # Output: (B, H/2*W/2, 2*C) = (1, 64, 384)
        output = patch_merger(x)

        assert output.shape == (1, 64, 384)


class TestWindowAttention:
    """Tests for WindowAttention module."""

    def test_window_partition(self):
        """Test window partition function."""
        # Input: (B, H, W, C)
        x = torch.randn(2, 8, 8, 96)

        # Partition into 4x4 windows
        windows = window_partition(x, window_size=4)

        # Should have 2 * (8/4) * (8/4) = 2 * 2 * 2 = 8 windows
        # Each window is (4, 4, 96)
        assert windows.shape == (8, 4, 4, 96), f"Expected (8, 4, 4, 96), got {windows.shape}"

    def test_window_reverse(self):
        """Test window reverse function."""
        # Create windows
        B, H, W, C = 2, 8, 8, 96
        window_size = 4
        x = torch.randn(B, H, W, C)

        # Partition into windows
        windows = window_partition(x, window_size)

        # Reverse back to original format
        x_reconstructed = window_reverse(windows, window_size, H, W)

        # Should match original shape
        assert x_reconstructed.shape == x.shape, f"Shape mismatch: {x_reconstructed.shape} vs {x.shape}"

        # Values should be preserved
        assert torch.allclose(x, x_reconstructed), "Values should be preserved after partition and reverse"

    def test_window_attention_output_shape(self):
        """Test window attention output shape."""
        window_size = 4
        num_heads = 3
        dim = 96

        attn = WindowAttention(
            dim=dim,
            window_size=(window_size, window_size),
            num_heads=num_heads,
        )

        # Input: (B * num_windows, N, C)
        # N = window_size * window_size = 16
        x = torch.randn(8, 16, dim)

        output = attn(x)

        assert output.shape == (8, 16, dim), f"Expected (8, 16, {dim}), got {output.shape}"

    def test_window_attention_with_mask(self):
        """Test window attention with attention mask."""
        window_size = 4
        num_heads = 3
        dim = 96
        num_windows = 4

        attn = WindowAttention(
            dim=dim,
            window_size=(window_size, window_size),
            num_heads=num_heads,
        )

        # Create a simple mask
        N = window_size * window_size
        mask = torch.zeros(num_windows, N, N)

        # Input: (B * num_windows, N, C)
        x = torch.randn(8, N, dim)

        output = attn(x, mask=mask)

        assert output.shape == (8, N, dim)


class TestShiftedWindowTransformerBlock:
    """Tests for ShiftedWindowTransformerBlock."""

    def test_regular_window_block(self):
        """Test regular window attention block (shift_size=0)."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=0,  # Regular window attention
        )

        # Input: (B, H*W, C)
        x = torch.randn(2, 64, 96)

        output = block(x)

        assert output.shape == x.shape, f"Expected {x.shape}, got {output.shape}"

    def test_shifted_window_block(self):
        """Test shifted window attention block."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=2,  # Shifted window attention
        )

        # Input: (B, H*W, C)
        x = torch.randn(2, 64, 96)

        output = block(x)

        assert output.shape == x.shape, f"Expected {x.shape}, got {output.shape}"

    def test_residual_connection(self):
        """Test that residual connections are applied correctly."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=0,
        )

        # Set all weights to zero to test residual connection
        for param in block.parameters():
            param.data.zero_()

        x = torch.randn(2, 64, 96)

        # With zero weights, output should be close to input (residual)
        output = block(x)

        # The output should be approximately equal to input
        # (MLP with zero weights gives 0, so output = x + 0 = x)
        assert torch.allclose(output, x, atol=1e-6), "Residual connection should preserve input when weights are zero"


class TestSwinTransformer:
    """Tests for complete Swin Transformer model."""

    def test_swin_tiny_output_shape(self):
        """Test Swin-Tiny model output shape."""
        model = swin_tiny_patch4_window7_224(num_classes=10)

        # Input: (B, C, H, W) for 224x224 image
        x = torch.randn(2, 3, 224, 224)

        output = model(x)

        assert output.shape == (2, 10), f"Expected (2, 10), got {output.shape}"

    def test_swin_tiny_features_shape(self):
        """Test Swin-Tiny feature extraction shape."""
        model = swin_tiny_patch4_window7_224(num_classes=10)

        x = torch.randn(2, 3, 224, 224)

        features = model.forward_features(x)

        # Swin-Tiny has embed_dim=96, final stage has 96*8=768 channels
        assert features.shape == (2, 768), f"Expected (2, 768), got {features.shape}"

    def test_swin_custom_input_size(self):
        """Test Swin Transformer with custom input size."""
        model = SwinTransformer(
            img_size=128,
            patch_size=4,
            in_channels=3,
            num_classes=10,
            embed_dim=64,
            depths=(2, 2, 6, 2),
            num_heads=(2, 4, 8, 16),
            window_size=4,
        )

        x = torch.randn(2, 3, 128, 128)

        output = model(x)

        assert output.shape == (2, 10)

    def test_swin_different_num_classes(self):
        """Test Swin Transformer with different number of classes."""
        for num_classes in [10, 100, 1000]:
            model = swin_tiny_patch4_window7_224(num_classes=num_classes)
            x = torch.randn(1, 3, 224, 224)

            output = model(x)

            assert output.shape == (1, num_classes), f"Expected (1, {num_classes}), got {output.shape}"

    def test_swin_gradient_flow(self):
        """Test that gradients flow through the entire model."""
        model = swin_tiny_patch4_window7_224(num_classes=10)

        x = torch.randn(1, 3, 224, 224, requires_grad=True)

        output = model(x)
        loss = output.sum()
        loss.backward()

        # Check that gradients exist
        assert x.grad is not None, "Gradients should flow to input"

        # Check that all parameters have gradients
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} should have gradients"

    def test_swin_deterministic_output(self):
        """Test that model produces deterministic output in eval mode."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        model.eval()

        x = torch.randn(1, 3, 224, 224)

        with torch.no_grad():
            output1 = model(x)
            output2 = model(x)

        assert torch.allclose(output1, output2), "Output should be deterministic in eval mode"


class TestIntegration:
    """Integration tests for the complete pipeline."""

    def test_end_to_end_training(self):
        """Test end-to-end forward and backward pass."""
        model = swin_tiny_patch4_window7_224(num_classes=10)

        # Create dummy data
        x = torch.randn(4, 3, 224, 224)
        target = torch.randint(0, 10, (4,))

        # Forward pass
        output = model(x)

        # Compute loss
        loss = torch.nn.functional.cross_entropy(output, target)

        # Backward pass
        loss.backward()

        # Check that all parameters have gradients
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} should have gradients"

    def test_model_parameter_count(self):
        """Test that model has reasonable number of parameters."""
        model = swin_tiny_patch4_window7_224(num_classes=10)

        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        # Swin-Tiny should have around 28M parameters
        assert total_params > 0, "Model should have parameters"
        assert trainable_params > 0, "Model should have trainable parameters"
        assert trainable_params == total_params, "All parameters should be trainable"

        print(f"Total parameters: {total_params:,}")
        print(f"Trainable parameters: {trainable_params:,}")

    def test_model_eval_mode(self):
        """Test that model works correctly in eval mode."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        model.eval()

        x = torch.randn(2, 3, 224, 224)

        with torch.no_grad():
            output = model(x)

        assert output.shape == (2, 10)
        assert not torch.isnan(output).any(), "Output should not contain NaN"
        assert not torch.isinf(output).any(), "Output should not contain Inf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
