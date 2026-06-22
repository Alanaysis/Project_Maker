"""
Unit Tests for Contrastive Loss Functions

⭐ Key test cases:
1. Loss value is positive
2. Gradient computation
3. Different loss functions
4. Edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import torch

from src.losses.contrastive import (
    ContrastiveLoss,
    CLIPLoss,
    SupConLoss,
    NTXentLoss,
    create_loss,
)


class TestContrastiveLoss:
    """Test cases for ContrastiveLoss."""

    def test_loss_positive(self):
        """Test that loss is positive."""
        loss_fn = ContrastiveLoss(temperature=0.07)
        features = torch.randn(8, 128)
        labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])

        loss = loss_fn(features, labels)
        assert loss.item() > 0

    def test_loss_scalar(self):
        """Test that loss is a scalar."""
        loss_fn = ContrastiveLoss(temperature=0.07)
        features = torch.randn(8, 128)
        labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])

        loss = loss_fn(features, labels)
        assert loss.dim() == 0

    def test_gradient_flow(self):
        """Test gradient computation."""
        loss_fn = ContrastiveLoss(temperature=0.07)
        features = torch.randn(8, 128, requires_grad=True)
        labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])

        loss = loss_fn(features, labels)
        loss.backward()

        assert features.grad is not None

    def test_self_supervised(self):
        """Test self-supervised mode (no labels)."""
        loss_fn = ContrastiveLoss(temperature=0.07)
        features = torch.randn(8, 128)

        loss = loss_fn(features)
        assert loss.item() > 0

    def test_with_mask(self):
        """Test with custom mask."""
        loss_fn = ContrastiveLoss(temperature=0.07)
        features = torch.randn(4, 128)
        mask = torch.tensor([
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ], dtype=torch.float)

        loss = loss_fn(features, mask=mask)
        assert loss.item() > 0


class TestCLIPLoss:
    """Test cases for CLIPLoss."""

    def test_loss_positive(self):
        """Test that loss is positive."""
        loss_fn = CLIPLoss(temperature=0.07)
        image_features = torch.randn(8, 128)
        text_features = torch.randn(8, 128)

        loss = loss_fn(image_features, text_features)
        assert loss.item() > 0

    def test_loss_symmetric(self):
        """Test that loss is symmetric."""
        loss_fn = CLIPLoss(temperature=0.07)
        image_features = torch.randn(8, 128)
        text_features = torch.randn(8, 128)

        loss1 = loss_fn(image_features, text_features)
        loss2 = loss_fn(text_features, image_features)

        # Should be approximately equal (symmetric)
        assert abs(loss1.item() - loss2.item()) < 1e-5

    def test_gradient_flow(self):
        """Test gradient computation."""
        loss_fn = CLIPLoss(temperature=0.07)
        image_features = torch.randn(8, 128, requires_grad=True)
        text_features = torch.randn(8, 128, requires_grad=True)

        loss = loss_fn(image_features, text_features)
        loss.backward()

        assert image_features.grad is not None
        assert text_features.grad is not None

    def test_temperature_effect(self):
        """Test that temperature affects the loss."""
        image_features = torch.randn(8, 128)
        text_features = torch.randn(8, 128)

        loss_low_temp = CLIPLoss(temperature=0.01)(image_features, text_features)
        loss_high_temp = CLIPLoss(temperature=1.0)(image_features, text_features)

        # Different temperatures should give different losses
        assert abs(loss_low_temp.item() - loss_high_temp.item()) > 0.01


class TestSupConLoss:
    """Test cases for SupConLoss."""

    def test_loss_positive(self):
        """Test that loss is positive."""
        loss_fn = SupConLoss(temperature=0.07)
        features = torch.randn(8, 128)
        labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])

        loss = loss_fn(features, labels)
        assert loss.item() > 0

    def test_multiple_positives(self):
        """Test with multiple positives per class."""
        loss_fn = SupConLoss(temperature=0.07)
        features = torch.randn(12, 128)
        labels = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3])

        loss = loss_fn(features, labels)
        assert loss.item() > 0

    def test_gradient_flow(self):
        """Test gradient computation."""
        loss_fn = SupConLoss(temperature=0.07)
        features = torch.randn(8, 128, requires_grad=True)
        labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])

        loss = loss_fn(features, labels)
        loss.backward()

        assert features.grad is not None


class TestNTXentLoss:
    """Test cases for NTXentLoss."""

    def test_loss_positive(self):
        """Test that loss is positive."""
        loss_fn = NTXentLoss(temperature=0.5)
        z_i = torch.randn(8, 128)
        z_j = torch.randn(8, 128)

        loss = loss_fn(z_i, z_j)
        assert loss.item() > 0

    def test_gradient_flow(self):
        """Test gradient computation."""
        loss_fn = NTXentLoss(temperature=0.5)
        z_i = torch.randn(8, 128, requires_grad=True)
        z_j = torch.randn(8, 128, requires_grad=True)

        loss = loss_fn(z_i, z_j)
        loss.backward()

        assert z_i.grad is not None
        assert z_j.grad is not None

    def test_same_input_low_loss(self):
        """Test that same input gives lower loss."""
        loss_fn = NTXentLoss(temperature=0.5)
        z = torch.randn(8, 128)

        loss_same = loss_fn(z, z)
        loss_diff = loss_fn(z, torch.randn(8, 128))

        # Same input should give lower loss
        assert loss_same.item() < loss_diff.item()


class TestCreateLoss:
    """Test cases for create_loss helper."""

    def test_create_clip_loss(self):
        """Test creating CLIP loss."""
        loss_fn = create_loss("clip")
        assert isinstance(loss_fn, CLIPLoss)

    def test_create_contrastive_loss(self):
        """Test creating contrastive loss."""
        loss_fn = create_loss("contrastive")
        assert isinstance(loss_fn, ContrastiveLoss)

    def test_create_supcon_loss(self):
        """Test creating supervised contrastive loss."""
        loss_fn = create_loss("supcon")
        assert isinstance(loss_fn, SupConLoss)

    def test_create_ntxent_loss(self):
        """Test creating NT-Xent loss."""
        loss_fn = create_loss("ntxent")
        assert isinstance(loss_fn, NTXentLoss)

    def test_invalid_loss(self):
        """Test invalid loss name raises error."""
        with pytest.raises(ValueError):
            create_loss("invalid_loss")

    def test_custom_temperature(self):
        """Test creating loss with custom temperature."""
        loss_fn = create_loss("clip", temperature=0.1)
        assert loss_fn.temperature == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
