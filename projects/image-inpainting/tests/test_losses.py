"""
Tests for loss functions.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.losses import ReconstructionLoss, AdversarialLoss, InpaintingLoss


class TestReconstructionLoss:
    """Test suite for reconstruction loss."""

    def test_l1_loss_identical(self):
        """Test that L1 loss is 0 for identical inputs."""
        loss_fn = ReconstructionLoss(loss_type="l1")
        x = torch.randn(1, 3, 64, 64)
        loss = loss_fn(x, x.clone())
        assert loss.item() < 1e-6

    def test_l2_loss_identical(self):
        """Test that L2 loss is 0 for identical inputs."""
        loss_fn = ReconstructionLoss(loss_type="l2")
        x = torch.randn(1, 3, 64, 64)
        loss = loss_fn(x, x.clone())
        assert loss.item() < 1e-6

    def test_l1_loss_known_difference(self):
        """Test L1 loss with known difference."""
        loss_fn = ReconstructionLoss(loss_type="l1")
        pred = torch.ones(1, 3, 4, 4)
        target = torch.zeros(1, 3, 4, 4)
        loss = loss_fn(pred, target)
        assert abs(loss.item() - 1.0) < 1e-6

    def test_l2_loss_known_difference(self):
        """Test L2 loss with known difference."""
        loss_fn = ReconstructionLoss(loss_type="l2")
        pred = torch.ones(1, 3, 4, 4) * 2
        target = torch.zeros(1, 3, 4, 4)
        loss = loss_fn(pred, target)
        assert abs(loss.item() - 4.0) < 1e-6  # (2-0)^2 = 4

    def test_masked_loss(self):
        """Test loss computation with mask."""
        loss_fn = ReconstructionLoss(loss_type="l1")
        pred = torch.ones(1, 3, 8, 8)
        target = torch.zeros(1, 3, 8, 8)
        mask = torch.zeros(1, 1, 8, 8)
        mask[:, :, 0:4, 0:4] = 1.0  # Only compute loss in top-left

        loss = loss_fn(pred, target, mask)
        assert abs(loss.item() - 1.0) < 1e-6  # Loss should be 1 only in masked region

    def test_masked_loss_ignores_known(self):
        """Test that masked loss ignores known regions."""
        loss_fn = ReconstructionLoss(loss_type="l1")
        pred = torch.cat([torch.ones(1, 3, 4, 4), torch.zeros(1, 3, 4, 4)], dim=3)
        target = torch.zeros(1, 3, 4, 8)
        mask = torch.zeros(1, 1, 4, 8)
        mask[:, :, :, 0:4] = 1.0  # Only left half

        loss = loss_fn(pred, target, mask)
        # Left half: |1-0| = 1, Right half: ignored
        assert abs(loss.item() - 1.0) < 1e-6

    def test_invalid_loss_type(self):
        """Test that invalid loss type raises error."""
        with pytest.raises(ValueError):
            ReconstructionLoss(loss_type="invalid")


class TestAdversarialLoss:
    """Test suite for adversarial loss."""

    def test_hinge_discriminator_loss(self):
        """Test hinge loss for discriminator."""
        loss_fn = AdversarialLoss(loss_type="hinge")
        real_pred = torch.ones(1, 1, 8, 8) * 2  # Correctly classified as real
        fake_pred = torch.ones(1, 1, 8, 8) * -2  # Correctly classified as fake
        loss = loss_fn.discriminator_loss(real_pred, fake_pred)
        assert loss.item() < 1e-6  # Should be ~0 when correctly classified

    def test_hinge_generator_loss(self):
        """Test hinge loss for generator."""
        loss_fn = AdversarialLoss(loss_type="hinge")
        fake_pred = torch.ones(1, 1, 8, 8) * 2  # Discriminator thinks it's real
        loss = loss_fn.generator_loss(fake_pred)
        assert loss.item() < 0  # Generator wants to minimize this (negative is good)

    def test_nonsaturating_loss(self):
        """Test non-saturating GAN loss."""
        loss_fn = AdversarialLoss(loss_type="non-saturating")
        real_pred = torch.ones(1, 1, 4, 4) * 5
        fake_pred = torch.ones(1, 1, 4, 4) * -5
        loss = loss_fn.discriminator_loss(real_pred, fake_pred)
        assert loss.item() >= 0

    def test_invalid_loss_type(self):
        """Test that invalid loss type raises error."""
        with pytest.raises(ValueError):
            AdversarialLoss(loss_type="invalid")


class TestInpaintingLoss:
    """Test suite for combined inpainting loss."""

    def test_generator_loss_components(self):
        """Test that generator loss returns all components."""
        loss_fn = InpaintingLoss(lambda_rec=1.0, lambda_adv=0.001)
        pred = torch.randn(1, 3, 64, 64)
        target = torch.randn(1, 3, 64, 64)
        mask = torch.ones(1, 1, 64, 64)
        fake_pred = torch.randn(1, 1, 8, 8)

        total, rec, adv = loss_fn.generator_loss(pred, target, mask, fake_pred)
        assert total.dim() == 0, "Total loss should be scalar"
        assert rec.dim() == 0
        assert adv.dim() == 0

    def test_loss_weights(self):
        """Test that loss weights affect the total loss."""
        # High reconstruction weight
        loss_fn1 = InpaintingLoss(lambda_rec=10.0, lambda_adv=0.0)
        # High adversarial weight
        loss_fn2 = InpaintingLoss(lambda_rec=0.0, lambda_adv=10.0)

        pred = torch.randn(1, 3, 64, 64)
        target = torch.randn(1, 3, 64, 64)
        mask = torch.ones(1, 1, 64, 64)
        fake_pred = torch.randn(1, 1, 8, 8)

        total1, rec1, adv1 = loss_fn1.generator_loss(pred, target, mask, fake_pred)
        total2, rec2, adv2 = loss_fn2.generator_loss(pred, target, mask, fake_pred)

        # With lambda_adv=0, total should equal rec loss
        assert abs(total1.item() - 10.0 * rec1.item()) < 1e-4
        # With lambda_rec=0, total should equal adv loss
        assert abs(total2.item() - 10.0 * adv2.item()) < 1e-4

    def test_discriminator_loss(self):
        """Test discriminator loss computation."""
        loss_fn = InpaintingLoss()
        real_pred = torch.randn(1, 1, 8, 8)
        fake_pred = torch.randn(1, 1, 8, 8)

        d_loss = loss_fn.discriminator_loss(real_pred, fake_pred)
        assert d_loss.dim() == 0
        assert d_loss.item() >= 0
