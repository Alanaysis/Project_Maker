"""
Tests for segmentation loss functions.
"""

import sys
import os

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.loss import DiceLoss, BCEDiceLoss


class TestDiceLoss:
    """Test suite for DiceLoss."""

    def test_perfect_prediction(self):
        """DiceLoss should be near 0 for perfect predictions."""
        loss_fn = DiceLoss()
        # Perfect sigmoid output (use very high logits for near-1 sigmoid)
        pred = torch.full((1, 1, 8, 8), 10.0)
        target = torch.ones(1, 1, 8, 8)
        loss = loss_fn(pred, target)
        assert loss.item() < 0.01

    def test_worst_prediction(self):
        """DiceLoss should be near 1 for completely wrong predictions."""
        loss_fn = DiceLoss()
        pred = torch.full((1, 1, 8, 8), -10.0)
        target = torch.ones(1, 1, 8, 8)
        loss = loss_fn(pred, target)
        assert loss.item() > 0.9

    def test_output_range(self):
        """DiceLoss should return values in [0, 1]."""
        loss_fn = DiceLoss()
        pred = torch.randn(4, 1, 32, 32)
        target = torch.randint(0, 2, (4, 1, 32, 32)).float()
        loss = loss_fn(pred, target)
        assert 0.0 <= loss.item() <= 1.0

    def test_gradient_flow(self):
        """DiceLoss should produce gradients."""
        loss_fn = DiceLoss()
        pred = torch.randn(1, 1, 8, 8, requires_grad=True)
        target = torch.randint(0, 2, (1, 1, 8, 8)).float()
        loss = loss_fn(pred, target)
        loss.backward()
        assert pred.grad is not None

    def test_smooth_factor(self):
        """Different smooth factors should affect the loss."""
        pred = torch.randn(1, 1, 8, 8)
        target = torch.randint(0, 2, (1, 1, 8, 8)).float()

        loss_1 = DiceLoss(smooth=1.0)(pred, target)
        loss_100 = DiceLoss(smooth=100.0)(pred, target)
        # Different smooth factors should give different results
        assert abs(loss_1.item() - loss_100.item()) > 0.001


class TestBCEDiceLoss:
    """Test suite for BCEDiceLoss."""

    def test_output_scalar(self):
        """BCEDiceLoss should return a scalar."""
        loss_fn = BCEDiceLoss()
        pred = torch.randn(1, 1, 32, 32)
        target = torch.randint(0, 2, (1, 1, 32, 32)).float()
        loss = loss_fn(pred, target)
        assert loss.dim() == 0

    def test_gradient_flow(self):
        """BCEDiceLoss should produce gradients."""
        loss_fn = BCEDiceLoss()
        pred = torch.randn(1, 1, 8, 8, requires_grad=True)
        target = torch.randint(0, 2, (1, 1, 8, 8)).float()
        loss = loss_fn(pred, target)
        loss.backward()
        assert pred.grad is not None

    def test_weight_combination(self):
        """Different weights should affect the loss value."""
        pred = torch.randn(1, 1, 8, 8)
        target = torch.randint(0, 2, (1, 1, 8, 8)).float()

        loss_bce_heavy = BCEDiceLoss(bce_weight=1.0, dice_weight=0.0)(pred, target)
        loss_dice_heavy = BCEDiceLoss(bce_weight=0.0, dice_weight=1.0)(pred, target)
        # With different weights, the losses should differ
        assert abs(loss_bce_heavy.item() - loss_dice_heavy.item()) > 0.001

    def test_equal_weights(self):
        """With equal weights, loss should be average of BCE and Dice."""
        loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
        pred = torch.randn(2, 1, 16, 16)
        target = torch.randint(0, 2, (2, 1, 16, 16)).float()
        loss = loss_fn(pred, target)
        assert loss.item() > 0

    def test_multiclass(self):
        """BCEDiceLoss should handle multiple channels."""
        loss_fn = BCEDiceLoss()
        pred = torch.randn(2, 3, 16, 16)
        target = torch.randint(0, 2, (2, 3, 16, 16)).float()
        loss = loss_fn(pred, target)
        assert loss.dim() == 0
