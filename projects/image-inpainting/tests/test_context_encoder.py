"""
Tests for Context Encoder (UNetGenerator and PatchDiscriminator).
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.context_encoder import UNetGenerator, PatchDiscriminator, weights_init


class TestUNetGenerator:
    """Test suite for the U-Net generator."""

    @pytest.fixture
    def generator(self):
        """Create a U-Net generator for 128x128 images."""
        return UNetGenerator(in_channels=4, out_channels=3, ngf=32)

    @pytest.fixture
    def small_generator(self):
        """Create a small U-Net generator for 64x64 images."""
        return UNetGenerator(in_channels=4, out_channels=3, ngf=16, num_downsamples=5)

    def test_output_shape(self, generator):
        """Test that generator produces correct output shape."""
        x = torch.randn(1, 4, 128, 128)
        output = generator(x)
        assert output.shape == (1, 3, 128, 128), f"Expected (1,3,128,128), got {output.shape}"

    def test_output_shape_64x64(self, small_generator):
        """Test that generator works with 64x64 images."""
        x = torch.randn(1, 4, 64, 64)
        output = small_generator(x)
        assert output.shape == (1, 3, 64, 64), f"Expected (1,3,64,64), got {output.shape}"

    def test_batch_processing(self, generator):
        """Test that generator works with batches."""
        x = torch.randn(4, 4, 128, 128)
        output = generator(x)
        assert output.shape == (4, 3, 128, 128)

    def test_output_range(self, generator):
        """Test that output values are in [-1, 1] range (Tanh activation)."""
        x = torch.randn(1, 4, 128, 128)
        output = generator(x)
        assert output.min() >= -1.0 - 1e-6, f"Min value {output.min()} below -1"
        assert output.max() <= 1.0 + 1e-6, f"Max value {output.max()} above 1"

    def test_gradient_flow(self, generator):
        """Test that gradients flow through the generator."""
        x = torch.randn(1, 4, 128, 128, requires_grad=True)
        output = generator(x)
        loss = output.sum()
        loss.backward()
        assert x.grad is not None, "Gradients should flow to input"
        assert x.grad.shape == x.shape

    def test_weight_initialization(self, generator):
        """Test weight initialization function."""
        generator.apply(weights_init)
        for name, param in generator.named_parameters():
            if "weight" in name and param.dim() >= 2:
                assert param.abs().sum() > 0, f"Weights in {name} should not be all zeros"


class TestPatchDiscriminator:
    """Test suite for the PatchGAN discriminator."""

    @pytest.fixture
    def discriminator(self):
        """Create a PatchGAN discriminator for testing."""
        return PatchDiscriminator(in_channels=6, ndf=32)

    def test_output_shape(self, discriminator):
        """Test that discriminator produces spatial output map."""
        x = torch.randn(1, 6, 128, 128)
        output = discriminator(x)
        assert output.dim() == 4, f"Expected 4D output, got {output.dim()}D"
        assert output.shape[0] == 1, "Batch size should be preserved"
        assert output.shape[1] == 1, "Output should have 1 channel"

    def test_batch_processing(self, discriminator):
        """Test discriminator with batch input."""
        x = torch.randn(4, 6, 128, 128)
        output = discriminator(x)
        assert output.shape[0] == 4

    def test_differentiable(self, discriminator):
        """Test that discriminator is differentiable."""
        x = torch.randn(1, 6, 128, 128, requires_grad=True)
        output = discriminator(x)
        loss = output.mean()
        loss.backward()
        assert x.grad is not None

    def test_real_fake_separation(self, discriminator):
        """Test that discriminator can output different values for real vs fake."""
        real = torch.randn(1, 6, 128, 128)
        fake = torch.randn(1, 6, 128, 128)
        with torch.no_grad():
            real_pred = discriminator(real)
            fake_pred = discriminator(fake)
        assert not torch.allclose(real_pred, fake_pred), \
            "Discriminator should produce different outputs for different inputs"


class TestGeneratorDiscriminatorInteraction:
    """Test that generator and discriminator work together."""

    def test_end_to_end(self):
        """Test full forward pass: generator -> discriminator."""
        gen = UNetGenerator(in_channels=4, out_channels=3, ngf=16, num_downsamples=5)
        disc = PatchDiscriminator(in_channels=6, ndf=16)

        masked_image = torch.randn(1, 3, 64, 64)
        mask = torch.zeros(1, 1, 64, 64)
        mask[:, :, 16:48, 16:48] = 1.0
        gen_input = torch.cat([masked_image, mask], dim=1)

        fake_image = gen(gen_input)
        assert fake_image.shape == (1, 3, 64, 64)

        disc_input = torch.cat([fake_image, masked_image], dim=1)
        pred = disc(disc_input)
        assert pred.shape[0] == 1

    def test_backward_pass(self):
        """Test that loss can backpropagate through both networks."""
        gen = UNetGenerator(in_channels=4, out_channels=3, ngf=16, num_downsamples=5)
        disc = PatchDiscriminator(in_channels=6, ndf=16)

        masked_image = torch.randn(1, 3, 64, 64)
        mask = torch.zeros(1, 1, 64, 64)
        gen_input = torch.cat([masked_image, mask], dim=1)

        fake_image = gen(gen_input)
        disc_input = torch.cat([fake_image, masked_image], dim=1)
        pred = disc(disc_input)

        loss = pred.mean()
        loss.backward()

        for name, param in gen.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for generator param {name}"
