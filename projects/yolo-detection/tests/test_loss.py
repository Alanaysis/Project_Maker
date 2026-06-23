"""
Tests for YOLO loss function.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.loss import YOLOLoss, create_target_tensor


class TestYOLOLoss:
    """Test YOLO loss function."""

    def test_loss_creation(self):
        """Test that loss function can be created."""
        loss_fn = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
        assert loss_fn is not None

    def test_loss_computation(self):
        """Test basic loss computation."""
        loss_fn = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
        batch_size = 2
        output_size = 2 * 5 + 20  # B*5 + C

        predictions = torch.randn(batch_size, 7 * 7 * output_size)
        targets = torch.abs(torch.randn(batch_size, 7, 7, output_size))  # Positive values
        targets[..., 4] = torch.sigmoid(targets[..., 4])  # Confidence in [0, 1]
        targets[..., 9] = torch.sigmoid(targets[..., 9])  # Second box confidence

        total_loss, loss_dict = loss_fn(predictions, targets)

        assert not torch.isnan(total_loss)
        assert total_loss.item() > 0
        assert "total" in loss_dict
        assert "loc_xy" in loss_dict
        assert "loc_wh" in loss_dict
        assert "conf_obj" in loss_dict
        assert "conf_noobj" in loss_dict
        assert "class" in loss_dict

    def test_loss_with_zero_predictions(self):
        """Test loss when predictions are all zeros."""
        loss_fn = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
        batch_size = 1
        output_size = 2 * 5 + 20

        predictions = torch.zeros(batch_size, 7 * 7 * output_size)
        targets = torch.zeros(batch_size, 7, 7, output_size)

        total_loss, loss_dict = loss_fn(predictions, targets)
        assert total_loss.item() >= 0

    def test_loss_with_perfect_predictions(self):
        """Test loss when predictions match targets exactly."""
        loss_fn = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
        batch_size = 1
        output_size = 2 * 5 + 20

        # Create matching predictions and targets
        targets = torch.zeros(batch_size, 7, 7, output_size)
        targets[0, 3, 3, 0] = 0.5  # x
        targets[0, 3, 3, 1] = 0.5  # y
        targets[0, 3, 3, 2] = 0.3  # w
        targets[0, 3, 3, 3] = 0.3  # h
        targets[0, 3, 3, 4] = 1.0  # confidence
        targets[0, 3, 3, 10] = 1.0  # class

        predictions = targets.reshape(batch_size, -1).clone()

        total_loss, loss_dict = loss_fn(predictions, targets)
        # Loss should be very small for perfect predictions
        assert total_loss.item() < 1.0

    def test_loss_gradient_flow(self):
        """Test that gradients flow through loss."""
        loss_fn = YOLOLoss(grid_size=7, num_boxes=2, num_classes=20)
        batch_size = 1
        output_size = 2 * 5 + 20

        predictions = torch.randn(batch_size, 7 * 7 * output_size, requires_grad=True)
        targets = torch.zeros(batch_size, 7, 7, output_size)

        total_loss, _ = loss_fn(predictions, targets)
        total_loss.backward()

        assert predictions.grad is not None
        assert predictions.grad.shape == predictions.shape

    def test_loss_custom_weights(self):
        """Test loss with custom lambda weights."""
        loss_fn = YOLOLoss(
            grid_size=7, num_boxes=2, num_classes=20,
            lambda_coord=10.0, lambda_noobj=0.1
        )
        batch_size = 1
        output_size = 2 * 5 + 20

        predictions = torch.randn(batch_size, 7 * 7 * output_size)
        targets = torch.zeros(batch_size, 7, 7, output_size)

        total_loss, loss_dict = loss_fn(predictions, targets)
        assert total_loss.item() > 0

    def test_loss_different_grid_sizes(self):
        """Test loss with different grid sizes."""
        for grid_size in [5, 7, 9]:
            loss_fn = YOLOLoss(grid_size=grid_size, num_boxes=2, num_classes=10)
            output_size = 2 * 5 + 10

            predictions = torch.randn(1, grid_size * grid_size * output_size)
            targets = torch.zeros(1, grid_size, grid_size, output_size)

            total_loss, _ = loss_fn(predictions, targets)
            assert total_loss.item() > 0


class TestCreateTargetTensor:
    """Test target tensor creation."""

    def test_create_target_basic(self):
        """Test basic target tensor creation."""
        boxes = [[100.0, 100.0, 50.0, 50.0]]
        labels = [0]

        target = create_target_tensor(boxes, labels, grid_size=7, num_classes=20)

        assert target.shape == (7, 7, 30)  # S x S x (B*5 + C)
        # Check that some cell has an object
        assert target[..., 4].sum() > 0 or target[..., 9].sum() > 0

    def test_create_target_multiple_objects(self):
        """Test target creation with multiple objects."""
        boxes = [
            [100.0, 100.0, 50.0, 50.0],
            [300.0, 300.0, 60.0, 60.0],
        ]
        labels = [0, 1]

        target = create_target_tensor(boxes, labels, grid_size=7, num_classes=20)

        assert target.shape == (7, 7, 30)

    def test_create_target_coordinates(self):
        """Test that target coordinates are correct."""
        grid_size = 7
        image_size = 448
        cell_size = image_size / grid_size  # 64

        # Place object at center of cell (3, 3)
        x = 3 * cell_size + cell_size / 2  # Center of cell (3, 3)
        y = 3 * cell_size + cell_size / 2
        boxes = [[x, y, 40.0, 40.0]]
        labels = [0]

        target = create_target_tensor(boxes, labels, grid_size=grid_size, num_classes=20)

        # Check cell (3, 3) has the object
        assert target[3, 3, 4] == 1.0  # confidence
        assert target[3, 3, 10] == 1.0  # class 0 (at index B*5 + 0 = 10)

    def test_create_target_empty(self):
        """Test target creation with no objects."""
        boxes = []
        labels = []

        target = create_target_tensor(boxes, labels, grid_size=7, num_classes=20)

        assert target.shape == (7, 7, 30)
        assert target.sum() == 0

    def test_create_target_out_of_bounds(self):
        """Test target creation with out-of-bounds boxes."""
        boxes = [[-10.0, -10.0, 50.0, 50.0]]
        labels = [0]

        # Should not crash
        target = create_target_tensor(boxes, labels, grid_size=7, num_classes=20)
        assert target.shape == (7, 7, 30)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
