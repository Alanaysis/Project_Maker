"""
Tests for U-Net Architecture.
"""

import pytest
import torch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.unet import UNet, SimpleUNet, SinusoidalPositionEmbeddings


class TestSinusoidalPositionEmbeddings:
    """Test cases for Sinusoidal Position Embeddings."""

    def test_output_shape(self):
        """Test that output shape is correct."""
        dim = 64
        batch_size = 8
        embeddings = SinusoidalPositionEmbeddings(dim)

        t = torch.randint(0, 100, (batch_size,))
        output = embeddings(t)

        assert output.shape == (batch_size, dim)

    def test_different_timesteps(self):
        """Test that different timesteps produce different embeddings."""
        dim = 64
        embeddings = SinusoidalPositionEmbeddings(dim)

        t1 = torch.tensor([0])
        t2 = torch.tensor([50])

        emb1 = embeddings(t1)
        emb2 = embeddings(t2)

        assert not torch.allclose(emb1, emb2)

    def test_deterministic(self):
        """Test that embeddings are deterministic."""
        dim = 64
        embeddings = SinusoidalPositionEmbeddings(dim)

        t = torch.tensor([42])
        emb1 = embeddings(t)
        emb2 = embeddings(t)

        assert torch.allclose(emb1, emb2)


class TestSimpleUNet:
    """Test cases for Simple U-Net."""

    def setup_method(self):
        """Setup test fixtures."""
        self.batch_size = 4
        self.channels = 1
        self.height = 28
        self.width = 28
        self.model = SimpleUNet(in_channels=1, out_channels=1)

    def test_output_shape(self):
        """Test that output shape matches input shape."""
        x = torch.randn(self.batch_size, self.channels, self.height, self.width)
        t = torch.randint(0, 100, (self.batch_size,))

        output = self.model(x, t)

        assert output.shape == x.shape

    def test_different_inputs(self):
        """Test that different inputs produce different outputs."""
        x1 = torch.randn(1, 1, 28, 28)
        x2 = torch.randn(1, 1, 28, 28)
        t = torch.tensor([50])

        out1 = self.model(x1, t)
        out2 = self.model(x2, t)

        assert not torch.allclose(out1, out2)

    def test_different_timesteps(self):
        """Test that different timesteps produce different outputs."""
        x = torch.randn(1, 1, 28, 28)
        t1 = torch.tensor([10])
        t2 = torch.tensor([90])

        out1 = self.model(x, t1)
        out2 = self.model(x, t2)

        assert not torch.allclose(out1, out2)

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        x = torch.randn(2, 1, 28, 28, requires_grad=True)
        t = torch.randint(0, 100, (2,))

        output = self.model(x, t)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None
        assert x.grad.shape == x.shape

    def test_parameter_count(self):
        """Test that model has reasonable number of parameters."""
        num_params = sum(p.numel() for p in self.model.parameters())
        # Simple UNet should have a reasonable number of parameters
        assert num_params > 100000  # At least 100K
        assert num_params < 10000000  # Less than 10M

    def test_training_mode(self):
        """Test that model can switch between training and eval modes."""
        self.model.train()
        assert self.model.training

        self.model.eval()
        assert not self.model.training


class TestUNet:
    """Test cases for Full U-Net."""

    def setup_method(self):
        """Setup test fixtures."""
        self.batch_size = 2
        self.channels = 1
        self.height = 28
        self.width = 28
        self.model = UNet(
            in_channels=1,
            out_channels=1,
            hidden_channels=[32, 64, 128],
            attention=True
        )

    def test_output_shape(self):
        """Test that output shape matches input shape."""
        x = torch.randn(self.batch_size, self.channels, self.height, self.width)
        t = torch.randint(0, 100, (self.batch_size,))

        output = self.model(x, t)

        assert output.shape == x.shape

    def test_different_inputs_produce_different_outputs(self):
        """Test that different inputs produce different outputs."""
        x1 = torch.randn(1, 1, 28, 28)
        x2 = torch.randn(1, 1, 28, 28)
        t = torch.tensor([50])

        out1 = self.model(x1, t)
        out2 = self.model(x2, t)

        assert not torch.allclose(out1, out2)

    def test_gradient_flow(self):
        """Test that gradients flow through the model."""
        x = torch.randn(1, 1, 28, 28, requires_grad=True)
        t = torch.randint(0, 100, (1,))

        output = self.model(x, t)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None

    def test_parameter_count(self):
        """Test that model has reasonable number of parameters."""
        num_params = sum(p.numel() for p in self.model.parameters())
        # Full UNet should have more parameters than simple version
        assert num_params > 500000  # At least 500K

    def test_attention_blocks(self):
        """Test that attention blocks are present."""
        # Check that attention modules exist
        has_attention = False
        for module in self.model.modules():
            if hasattr(module, 'attention'):
                has_attention = True
                break
        assert has_attention


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
