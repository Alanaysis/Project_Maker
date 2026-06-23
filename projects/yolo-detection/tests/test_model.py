"""
Tests for YOLO model architecture.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import YOLOv1, TinyYOLOv1, ConvBlock


class TestConvBlock:
    """Test ConvBlock module."""

    def test_conv_block_output_shape(self):
        """Test that ConvBlock produces correct output shape."""
        block = ConvBlock(3, 64, kernel_size=3, stride=1, padding=1)
        x = torch.randn(1, 3, 32, 32)
        out = block(x)
        assert out.shape == (1, 64, 32, 32)

    def test_conv_block_stride(self):
        """Test ConvBlock with stride."""
        block = ConvBlock(3, 64, kernel_size=3, stride=2, padding=1)
        x = torch.randn(1, 3, 32, 32)
        out = block(x)
        assert out.shape == (1, 64, 16, 16)

    def test_conv_block_batch(self):
        """Test ConvBlock with batch dimension."""
        block = ConvBlock(3, 32, kernel_size=3, padding=1)
        x = torch.randn(4, 3, 16, 16)
        out = block(x)
        assert out.shape == (4, 32, 16, 16)


class TestTinyYOLOv1:
    """Test TinyYOLOv1 model."""

    def test_model_creation(self):
        """Test that model can be created."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        assert model is not None

    def test_model_output_shape(self):
        """Test model output shape."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        x = torch.randn(1, 3, 448, 448)
        output = model(x)
        # Output should be (batch, S*S*(B*5+C))
        expected_size = 7 * 7 * (2 * 5 + 20)
        assert output.shape == (1, expected_size)

    def test_model_batch_processing(self):
        """Test model with batch of images."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        batch_size = 4
        x = torch.randn(batch_size, 3, 448, 448)
        output = model(x)
        expected_size = 7 * 7 * (2 * 5 + 20)
        assert output.shape == (batch_size, expected_size)

    def test_model_different_grid_sizes(self):
        """Test model with different grid sizes."""
        for grid_size in [5, 7, 9]:
            model = TinyYOLOv1(grid_size=grid_size, num_boxes=2, num_classes=10)
            x = torch.randn(1, 3, 448, 448)
            output = model(x)
            expected_size = grid_size * grid_size * (2 * 5 + 10)
            assert output.shape == (1, expected_size)

    def test_model_different_input_sizes(self):
        """Test model with different input sizes."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        for size in [224, 320, 448]:
            x = torch.randn(1, 3, size, size)
            output = model(x)
            expected_size = 7 * 7 * (2 * 5 + 20)
            assert output.shape == (1, expected_size)

    def test_model_gradient_flow(self):
        """Test that gradients flow through the model."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        x = torch.randn(1, 3, 448, 448, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()
        assert x.grad is not None
        assert x.grad.shape == x.shape

    def test_model_predict(self):
        """Test model predict method."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        x = torch.randn(1, 3, 448, 448)
        predictions = model.predict(x, confidence_threshold=0.01)
        assert len(predictions) == 1
        assert "boxes" in predictions[0]
        assert "scores" in predictions[0]
        assert "labels" in predictions[0]

    def test_model_parameter_count(self):
        """Test that model has reasonable number of parameters."""
        model = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        total_params = sum(p.numel() for p in model.parameters())
        # Should have parameters but not too many
        assert total_params > 1000
        assert total_params < 50_000_000  # Less than 50M for tiny model


class TestYOLOv1:
    """Test full YOLOv1 model."""

    def test_model_creation(self):
        """Test that model can be created."""
        model = YOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        assert model is not None

    def test_model_output_shape(self):
        """Test model output shape."""
        model = YOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        x = torch.randn(1, 3, 448, 448)
        output = model(x)
        expected_size = 7 * 7 * (2 * 5 + 20)
        assert output.shape == (1, expected_size)

    def test_model_parameter_count(self):
        """Test that full model has more parameters than tiny."""
        tiny = TinyYOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        full = YOLOv1(grid_size=7, num_boxes=2, num_classes=20)
        tiny_params = sum(p.numel() for p in tiny.parameters())
        full_params = sum(p.numel() for p in full.parameters())
        assert full_params > tiny_params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
