"""Tests for DnCNN model."""

import pytest
import torch
import numpy as np

from src.model import DnCNN, DnCNNLight, create_model


class TestDnCNN:
    """Test suite for DnCNN model."""

    def test_model_creation(self):
        """Test model can be created with default parameters."""
        model = DnCNN(in_channels=1)
        assert isinstance(model, DnCNN)

    def test_model_forward(self):
        """Test forward pass produces correct output shape."""
        model = DnCNN(in_channels=1, depth=5, num_features=32)
        x = torch.randn(1, 1, 64, 64)
        output = model(x)
        assert output.shape == x.shape

    def test_model_denoise(self):
        """Test denoise method subtracts predicted noise."""
        model = DnCNN(in_channels=1, depth=5, num_features=32)
        x = torch.randn(1, 1, 64, 64)
        denoised = model.denoise(x)
        assert denoised.shape == x.shape

        # Verify denoise = input - noise
        noise = model(x)
        expected = x - noise
        assert torch.allclose(denoised, expected, atol=1e-6)

    def test_rgb_channels(self):
        """Test model works with RGB images."""
        model = DnCNN(in_channels=3, depth=5, num_features=32)
        x = torch.randn(1, 3, 64, 64)
        output = model(x)
        assert output.shape == x.shape

    def test_batch_processing(self):
        """Test model processes batches correctly."""
        model = DnCNN(in_channels=1, depth=5, num_features=32)
        x = torch.randn(4, 1, 32, 32)
        output = model(x)
        assert output.shape == x.shape

    def test_different_depths(self):
        """Test model with different depths."""
        for depth in [5, 9, 13, 17]:
            model = DnCNN(in_channels=1, depth=depth, num_features=32)
            x = torch.randn(1, 1, 32, 32)
            output = model(x)
            assert output.shape == x.shape

    def test_parameter_count(self):
        """Test parameter count increases with depth."""
        params_5 = sum(p.numel() for p in DnCNN(depth=5, num_features=32).parameters())
        params_17 = sum(p.numel() for p in DnCNN(depth=17, num_features=32).parameters())
        assert params_17 > params_5

    def test_kaiming_initialization(self):
        """Test weights are initialized with Kaiming method."""
        model = DnCNN(in_channels=1, depth=5, num_features=32)
        for name, param in model.named_parameters():
            if 'weight' in name and param.dim() == 4:
                # Check that weights are not all zeros
                assert param.abs().sum() > 0


class TestDnCNNLight:
    """Test suite for lightweight DnCNN variant."""

    def test_model_creation(self):
        """Test lightweight model creation."""
        model = DnCNNLight(in_channels=1)
        assert isinstance(model, DnCNNLight)

    def test_fewer_parameters(self):
        """Test lightweight model has fewer parameters than standard."""
        standard = DnCNN(in_channels=1, depth=8, num_features=32)
        light = DnCNNLight(in_channels=1, depth=8, num_features=32)
        standard_params = sum(p.numel() for p in standard.parameters())
        light_params = sum(p.numel() for p in light.parameters())
        assert light_params <= standard_params

    def test_forward_pass(self):
        """Test lightweight model forward pass."""
        model = DnCNNLight(in_channels=1, depth=5, num_features=16)
        x = torch.randn(1, 1, 32, 32)
        output = model(x)
        assert output.shape == x.shape


class TestCreateModel:
    """Test suite for model factory function."""

    def test_create_dncnn(self):
        """Test creating DnCNN model."""
        model = create_model("dncnn", in_channels=1, depth=5)
        assert isinstance(model, DnCNN)

    def test_create_dncnn_light(self):
        """Test creating lightweight model."""
        model = create_model("dncnn_light", in_channels=1, depth=5)
        assert isinstance(model, DnCNNLight)

    def test_invalid_model_type(self):
        """Test error on invalid model type."""
        with pytest.raises(ValueError):
            create_model("invalid_model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
