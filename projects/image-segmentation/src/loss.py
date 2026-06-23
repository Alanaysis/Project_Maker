"""
Loss functions for image segmentation.

Implements common loss functions used in semantic segmentation:
- DiceLoss: Overlap-based loss, good for imbalanced classes.
- BCEDiceLoss: Combination of Binary Cross-Entropy and Dice loss.
"""

import torch
import torch.nn as nn


class DiceLoss(nn.Module):
    """Dice loss for segmentation tasks.

    The Dice coefficient measures the overlap between the predicted
    segmentation and the ground truth. Dice loss = 1 - Dice coefficient.

    Dice = 2 * |A ∩ B| / (|A| + |B|)

    This loss is particularly useful for segmentation tasks with class
    imbalance, as it focuses on the overlap rather than pixel-wise accuracy.

    Args:
        smooth: Smoothing factor to avoid division by zero (default: 1.0).

    Example:
        >>> loss_fn = DiceLoss()
        >>> pred = torch.randn(1, 1, 128, 128)
        >>> target = torch.randint(0, 2, (1, 1, 128, 128)).float()
        >>> loss = loss_fn(pred, target)
    """

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Compute Dice loss.

        Args:
            pred: Predicted logits of shape (B, C, H, W).
            target: Ground truth masks of shape (B, C, H, W) with values in [0, 1].

        Returns:
            Scalar Dice loss.
        """
        pred = torch.sigmoid(pred)

        # Flatten spatial dimensions
        pred_flat = pred.view(pred.size(0), pred.size(1), -1)
        target_flat = target.view(target.size(0), target.size(1), -1)

        # Compute intersection and union
        intersection = (pred_flat * target_flat).sum(dim=2)
        union = pred_flat.sum(dim=2) + target_flat.sum(dim=2)

        # Dice coefficient
        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)

        # Return dice loss (1 - dice coefficient)
        return 1.0 - dice.mean()


class BCEDiceLoss(nn.Module):
    """Combined Binary Cross-Entropy and Dice loss.

    Combines the pixel-wise BCE loss with the overlap-based Dice loss.
    This gives the benefits of both: BCE provides stable gradients while
    Dice handles class imbalance.

    Args:
        bce_weight: Weight for BCE loss component (default: 0.5).
        dice_weight: Weight for Dice loss component (default: 0.5).
        smooth: Smoothing factor for Dice loss (default: 1.0).

    Example:
        >>> loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
        >>> pred = torch.randn(1, 1, 128, 128)
        >>> target = torch.randint(0, 2, (1, 1, 128, 128)).float()
        >>> loss = loss_fn(pred, target)
    """

    def __init__(
        self,
        bce_weight: float = 0.5,
        dice_weight: float = 0.5,
        smooth: float = 1.0,
    ):
        super().__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss(smooth=smooth)

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Compute combined BCE + Dice loss.

        Args:
            pred: Predicted logits of shape (B, C, H, W).
            target: Ground truth masks of shape (B, C, H, W) with values in [0, 1].

        Returns:
            Scalar combined loss.
        """
        bce_loss = self.bce(pred, target)
        dice_loss = self.dice(pred, target)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss
