"""
Loss Functions for Image Inpainting Training.

This module implements the loss functions used to train the context encoder
for image inpainting:

1. **ReconstructionLoss**: Measures pixel-level difference between the
   inpainted image and the ground truth. Available variants:
   - L1 loss (mean absolute error) - sharper results, preferred for inpainting
   - L2 loss (mean squared error) - smoother results, penalizes outliers more

2. **AdversarialLoss**: Uses a discriminator to provide perceptual feedback.
   - Hinge loss (standard for modern GANs)
   - Non-saturating GAN loss

3. **InpaintingLoss**: Combines reconstruction and adversarial losses with
   configurable weights. The total loss is:
   L_total = lambda_rec * L_rec + lambda_adv * L_adv

Key Concepts:
- L1 vs L2: L1 produces sharper results because it doesn't "average" predictions
- Adversarial loss pushes the generator toward more realistic outputs
- The balance between reconstruction and adversarial loss is critical:
  too much adversarial -> artifacts, too much reconstruction -> blurry
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class ReconstructionLoss(nn.Module):
    """Pixel-level reconstruction loss for image inpainting.

    Computes the difference between the inpainted image and the ground truth,
    typically only in the masked region (where inpainting was applied).

    Args:
        loss_type: Type of reconstruction loss ('l1' or 'l2').
            - 'l1': Mean Absolute Error (|x - y|)
            - 'l2': Mean Squared Error ((x - y)^2)
        reduction: Reduction method ('mean', 'sum', or 'none').

    Note:
        L1 loss is generally preferred for image inpainting because:
        1. It produces sharper results (no "averaging" effect)
        2. It's more robust to outliers
        3. It encourages the network to commit to a single prediction
    """

    def __init__(self, loss_type: str = "l1", reduction: str = "mean"):
        super().__init__()
        if loss_type not in ("l1", "l2"):
            raise ValueError(f"Unknown loss type: {loss_type}. Use 'l1' or 'l2'.")
        self.loss_type = loss_type
        self.reduction = reduction

    def forward(
        self,
        predicted: torch.Tensor,
        target: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Compute reconstruction loss.

        Args:
            predicted: Inpainted image (B, C, H, W).
            target: Ground truth image (B, C, H, W).
            mask: Optional binary mask (B, 1, H, W) or (1, H, W).
                If provided, loss is computed only in masked regions.

        Returns:
            Scalar loss value (if reduction != 'none') or element-wise loss.
        """
        if self.loss_type == "l1":
            loss = torch.abs(predicted - target)
        else:  # l2
            loss = (predicted - target) ** 2

        if mask is not None:
            # Expand mask to match image channels
            if mask.dim() == 3:
                mask = mask.unsqueeze(0)
            mask_expanded = mask.expand_as(loss)
            loss = loss * mask_expanded

            if self.reduction == "mean":
                # Normalize by number of masked pixels (avoid division by zero)
                num_masked = mask_expanded.sum()
                if num_masked > 0:
                    return loss.sum() / num_masked
                return torch.tensor(0.0, device=predicted.device)
            elif self.reduction == "sum":
                return loss.sum()
            return loss

        # No mask: compute loss over entire image
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class AdversarialLoss(nn.Module):
    """Adversarial loss for GAN-based inpainting.

    Provides two loss types:
    1. Hinge loss: Standard for modern GANs, more stable training
       - Discriminator: max(0, 1-D(real)) + max(0, 1+D(fake))
       - Generator: -D(fake)

    2. Non-saturating GAN loss: Original GAN formulation but with
       non-saturating gradient for generator
       - Discriminator: -log(D(real)) - log(1-D(fake))
       - Generator: -log(D(fake))

    Args:
        loss_type: Type of adversarial loss ('hinge' or 'non-saturating').
    """

    def __init__(self, loss_type: str = "hinge"):
        super().__init__()
        if loss_type not in ("hinge", "non-saturating"):
            raise ValueError(f"Unknown loss type: {loss_type}. Use 'hinge' or 'non-saturating'.")
        self.loss_type = loss_type

    def discriminator_loss(
        self,
        real_pred: torch.Tensor,
        fake_pred: torch.Tensor,
    ) -> torch.Tensor:
        """Compute discriminator loss.

        Args:
            real_pred: Discriminator output for real images.
            fake_pred: Discriminator output for fake (inpainted) images.

        Returns:
            Scalar discriminator loss.
        """
        if self.loss_type == "hinge":
            real_loss = F.relu(1.0 - real_pred).mean()
            fake_loss = F.relu(1.0 + fake_pred).mean()
            return (real_loss + fake_loss) / 2.0
        else:  # non-saturating
            real_loss = F.softplus(-real_pred).mean()
            fake_loss = F.softplus(fake_pred).mean()
            return (real_loss + fake_loss) / 2.0

    def generator_loss(self, fake_pred: torch.Tensor) -> torch.Tensor:
        """Compute generator (adversarial) loss.

        Args:
            fake_pred: Discriminator output for fake (inpainted) images.

        Returns:
            Scalar generator loss.
        """
        if self.loss_type == "hinge":
            return -fake_pred.mean()
        else:  # non-saturating
            return F.softplus(-fake_pred).mean()


class InpaintingLoss(nn.Module):
    """Combined loss for image inpainting training.

    Combines reconstruction loss and adversarial loss:
        L_total = lambda_rec * L_rec + lambda_adv * L_adv

    This is the total loss used to train the generator. The discriminator
    is trained separately using only the adversarial loss.

    Args:
        lambda_rec: Weight for reconstruction loss (default: 1.0).
        lambda_adv: Weight for adversarial loss (default: 0.001).
        rec_loss_type: Type of reconstruction loss ('l1' or 'l2').
        adv_loss_type: Type of adversarial loss ('hinge' or 'non-saturating').

    Note on weight balancing:
        The adversarial loss weight (lambda_adv) is typically much smaller
        than the reconstruction weight because:
        1. Adversarial loss can be much larger in magnitude
        2. Too much adversarial influence can cause artifacts
        3. Reconstruction provides the "correct" baseline, adversarial adds "realism"
    """

    def __init__(
        self,
        lambda_rec: float = 1.0,
        lambda_adv: float = 0.001,
        rec_loss_type: str = "l1",
        adv_loss_type: str = "hinge",
    ):
        super().__init__()
        self.lambda_rec = lambda_rec
        self.lambda_adv = lambda_adv
        self.rec_loss = ReconstructionLoss(loss_type=rec_loss_type)
        self.adv_loss = AdversarialLoss(loss_type=adv_loss_type)

    def generator_loss(
        self,
        predicted: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor,
        fake_pred: torch.Tensor,
    ) -> tuple:
        """Compute total generator loss.

        Args:
            predicted: Inpainted image from generator (B, C, H, W).
            target: Ground truth image (B, C, H, W).
            mask: Binary mask (B, 1, H, W) or (1, H, W).
            fake_pred: Discriminator output for inpainted image.

        Returns:
            Tuple of (total_loss, rec_loss, adv_loss) for logging.
        """
        rec = self.rec_loss(predicted, target, mask)
        adv = self.adv_loss.generator_loss(fake_pred)
        total = self.lambda_rec * rec + self.lambda_adv * adv
        return total, rec, adv

    def discriminator_loss(
        self,
        real_pred: torch.Tensor,
        fake_pred: torch.Tensor,
    ) -> torch.Tensor:
        """Compute discriminator loss.

        Args:
            real_pred: Discriminator output for real images.
            fake_pred: Discriminator output for inpainted images.

        Returns:
            Scalar discriminator loss.
        """
        return self.adv_loss.discriminator_loss(real_pred, fake_pred)
