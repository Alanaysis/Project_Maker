"""
Tests for Loss Functions
"""

import sys
import os
import torch
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.loss.east_loss import EASTLoss, DBLoss


class TestEASTLoss:
    """Test EAST loss function."""

    def test_loss_computation(self):
        """Test basic loss computation."""
        loss_fn = EASTLoss()

        # Create test tensors
        pred_score = torch.sigmoid(torch.randn(2, 1, 16, 16))
        pred_geo = torch.sigmoid(torch.randn(2, 5, 16, 16))
        gt_score = torch.randint(0, 2, (2, 1, 16, 16)).float()
        gt_geo = torch.rand(2, 5, 16, 16) * 100
        mask = torch.ones(2, 1, 16, 16)

        total, score_loss, geo_loss = loss_fn(pred_score, pred_geo,
                                               gt_score, gt_geo, mask)

        assert total.dim() == 0  # Scalar
        assert total.item() >= 0
        assert score_loss.item() >= 0
        assert geo_loss.item() >= 0

    def test_loss_with_empty_mask(self):
        """Test loss with empty mask (no text regions)."""
        loss_fn = EASTLoss()

        pred_score = torch.sigmoid(torch.randn(2, 1, 16, 16))
        pred_geo = torch.sigmoid(torch.randn(2, 5, 16, 16))
        gt_score = torch.zeros(2, 1, 16, 16)
        gt_geo = torch.zeros(2, 5, 16, 16)
        mask = torch.zeros(2, 1, 16, 16)

        total, score_loss, geo_loss = loss_fn(pred_score, pred_geo,
                                               gt_score, gt_geo, mask)

        assert total.item() >= 0

    def test_loss_weights(self):
        """Test loss with different weights."""
        loss_fn = EASTLoss(lambda_score=2.0, lambda_geo=0.5)

        pred_score = torch.sigmoid(torch.randn(1, 1, 16, 16))
        pred_geo = torch.sigmoid(torch.randn(1, 5, 16, 16))
        gt_score = torch.randint(0, 2, (1, 1, 16, 16)).float()
        gt_geo = torch.rand(1, 5, 16, 16) * 100
        mask = torch.ones(1, 1, 16, 16)

        total, _, _ = loss_fn(pred_score, pred_geo, gt_score, gt_geo, mask)
        assert total.item() >= 0

    def test_gradient_flow(self):
        """Test gradients flow through loss."""
        loss_fn = EASTLoss()

        # Create raw logits that require gradients
        raw_score = torch.randn(1, 1, 8, 8, requires_grad=True)
        raw_geo = torch.randn(1, 5, 8, 8, requires_grad=True)

        pred_score = torch.sigmoid(raw_score)
        pred_geo = torch.sigmoid(raw_geo)
        gt_score = torch.randint(0, 2, (1, 1, 8, 8)).float()
        gt_geo = torch.rand(1, 5, 8, 8) * 100
        mask = torch.ones(1, 1, 8, 8)

        total, _, _ = loss_fn(pred_score, pred_geo, gt_score, gt_geo, mask)
        total.backward()

        assert raw_score.grad is not None
        assert raw_geo.grad is not None


class TestDBLoss:
    """Test DBNet loss function."""

    def test_loss_computation(self):
        """Test basic loss computation."""
        loss_fn = DBLoss()

        pred_prob = torch.sigmoid(torch.randn(2, 1, 32, 32))
        pred_thresh = torch.sigmoid(torch.randn(2, 1, 32, 32))
        pred_binary = torch.sigmoid(torch.randn(2, 1, 32, 32))
        gt_prob = torch.randint(0, 2, (2, 1, 32, 32)).float()
        gt_thresh = torch.rand(2, 1, 32, 32)
        mask = torch.ones(2, 1, 32, 32)
        thresh_mask = torch.ones(2, 1, 32, 32)

        total, prob_loss, thresh_loss, binary_loss = loss_fn(
            pred_prob, pred_thresh, pred_binary,
            gt_prob, gt_thresh, mask, thresh_mask
        )

        assert total.dim() == 0
        assert total.item() >= 0

    def test_loss_weights(self):
        """Test loss with different weights."""
        loss_fn = DBLoss(alpha=2.0, beta=5.0)

        pred_prob = torch.sigmoid(torch.randn(1, 1, 16, 16))
        pred_thresh = torch.sigmoid(torch.randn(1, 1, 16, 16))
        pred_binary = torch.sigmoid(torch.randn(1, 1, 16, 16))
        gt_prob = torch.randint(0, 2, (1, 1, 16, 16)).float()
        gt_thresh = torch.rand(1, 1, 16, 16)
        mask = torch.ones(1, 1, 16, 16)
        thresh_mask = torch.ones(1, 1, 16, 16)

        total, _, _, _ = loss_fn(
            pred_prob, pred_thresh, pred_binary,
            gt_prob, gt_thresh, mask, thresh_mask
        )

        assert total.item() >= 0

    def test_dice_loss(self):
        """Test dice loss component."""
        loss_fn = DBLoss()

        pred = torch.sigmoid(torch.randn(2, 1, 16, 16))
        target = torch.randint(0, 2, (2, 1, 16, 16)).float()
        mask = torch.ones(2, 1, 16, 16)

        dice = loss_fn.dice_loss(pred, target, mask)
        assert 0 <= dice.item() <= 2  # Dice loss range

    def test_empty_mask(self):
        """Test loss with empty mask."""
        loss_fn = DBLoss()

        pred_prob = torch.sigmoid(torch.randn(1, 1, 16, 16))
        pred_thresh = torch.sigmoid(torch.randn(1, 1, 16, 16))
        pred_binary = torch.sigmoid(torch.randn(1, 1, 16, 16))
        gt_prob = torch.zeros(1, 1, 16, 16)
        gt_thresh = torch.zeros(1, 1, 16, 16)
        mask = torch.zeros(1, 1, 16, 16)
        thresh_mask = torch.zeros(1, 1, 16, 16)

        total, _, _, _ = loss_fn(
            pred_prob, pred_thresh, pred_binary,
            gt_prob, gt_thresh, mask, thresh_mask
        )

        assert not torch.isnan(total)
        assert not torch.isinf(total)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
