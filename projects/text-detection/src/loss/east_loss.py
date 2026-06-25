"""
Loss Functions for EAST Text Detection

Implements score loss (BCE) and geometry loss (IoU + angle).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class EASTLoss(nn.Module):
    """
    Loss function for EAST text detector.

    Combines:
    - Score loss: Binary Cross-Entropy for text/non-text classification
    - Geometry loss: IoU loss for RBOX geometry + smooth L1 for angle

    Args:
        lambda_score: Weight for score loss
        lambda_geo: Weight for geometry loss
    """

    def __init__(self, lambda_score: float = 1.0, lambda_geo: float = 1.0):
        super().__init__()
        self.lambda_score = lambda_score
        self.lambda_geo = lambda_geo

    def forward(self, pred_score: torch.Tensor, pred_geo: torch.Tensor,
                gt_score: torch.Tensor, gt_geo: torch.Tensor,
                mask: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Compute EAST loss.

        Args:
            pred_score: [B, 1, H, W] predicted score map
            pred_geo: [B, 5, H, W] predicted geometry (top, right, bottom, left, angle)
            gt_score: [B, 1, H, W] ground truth score map (0 or 1)
            gt_geo: [B, 5, H, W] ground truth geometry
            mask: [B, 1, H, W] mask (1 for text region, 0 for background)

        Returns:
            total_loss: Combined loss
            score_loss: Score classification loss
            geo_loss: Geometry regression loss
        """
        # Score loss: Binary Cross-Entropy
        score_loss = F.binary_cross_entropy(pred_score, gt_score, reduction='mean')

        # Geometry loss: only compute on text regions
        # Mask for valid geometry regions
        geo_mask = mask.expand_as(pred_geo)

        if geo_mask.sum() == 0:
            geo_loss = torch.tensor(0.0, device=pred_score.device)
        else:
            # RBOX geometry loss
            pred_dists = pred_geo[:, :4, :, :]  # top, right, bottom, left
            gt_dists = gt_geo[:, :4, :, :]

            # IoU-like loss for distances
            pred_area = (pred_dists[:, 0] + pred_dists[:, 2]) * \
                        (pred_dists[:, 1] + pred_dists[:, 3])
            gt_area = (gt_dists[:, 0] + gt_dists[:, 2]) * \
                      (gt_dists[:, 1] + gt_dists[:, 3])

            # Intersection
            h_inter = torch.min(pred_dists[:, 0], gt_dists[:, 0]) + \
                      torch.min(pred_dists[:, 2], gt_dists[:, 2])
            w_inter = torch.min(pred_dists[:, 1], gt_dists[:, 1]) + \
                      torch.min(pred_dists[:, 3], gt_dists[:, 3])
            inter = h_inter * w_inter

            # IoU
            union = pred_area + gt_area - inter
            iou = inter / (union + 1e-6)

            # IoU loss
            iou_loss = (1 - iou) * mask[:, 0]
            iou_loss = iou_loss.sum() / (mask.sum() + 1e-6)

            # Angle loss: smooth L1
            pred_angle = pred_geo[:, 4, :, :]
            gt_angle = gt_geo[:, 4, :, :]
            angle_loss = F.smooth_l1_loss(pred_angle * mask[:, 0],
                                          gt_angle * mask[:, 0],
                                          reduction='sum') / (mask.sum() + 1e-6)

            geo_loss = iou_loss + angle_loss

        # Total loss
        total_loss = self.lambda_score * score_loss + self.lambda_geo * geo_loss

        return total_loss, score_loss, geo_loss


class DBLoss(nn.Module):
    """
    Loss function for DBNet text detector.

    Combines:
    - Probability map loss: BCE + Dice loss
    - Threshold map loss: L1 loss on text region
    - Binary map loss: BCE + Dice loss on binarized map

    Args:
        alpha: Weight for binary map loss
        beta: Weight for threshold map loss
    """

    def __init__(self, alpha: float = 1.0, beta: float = 10.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta

    def dice_loss(self, pred: torch.Tensor, target: torch.Tensor,
                  mask: torch.Tensor) -> torch.Tensor:
        """Compute Dice loss."""
        pred_flat = pred[mask > 0].flatten()
        target_flat = target[mask > 0].flatten()

        if len(pred_flat) == 0:
            return torch.tensor(0.0, device=pred.device)

        intersection = (pred_flat * target_flat).sum()
        union = pred_flat.sum() + target_flat.sum()

        return 1 - (2 * intersection + 1e-6) / (union + 1e-6)

    def forward(self, prob_map: torch.Tensor, thresh_map: torch.Tensor,
                binary_map: torch.Tensor, gt_prob: torch.Tensor,
                gt_thresh: torch.Tensor, mask: torch.Tensor,
                thresh_mask: torch.Tensor) -> Tuple[torch.Tensor, ...]:
        """
        Compute DBNet loss.

        Args:
            prob_map: [B, 1, H, W] predicted probability map
            thresh_map: [B, 1, H, W] predicted threshold map
            binary_map: [B, 1, H, W] binarized map
            gt_prob: [B, 1, H, W] ground truth probability map
            gt_thresh: [B, 1, H, W] ground truth threshold map
            mask: [B, 1, H, W] mask (1 for text region, 0 for background)
            thresh_mask: [B, 1, H, W] threshold mask (shrunk text region)

        Returns:
            total_loss: Combined loss
            prob_loss: Probability map loss
            thresh_loss: Threshold map loss
            binary_loss: Binary map loss
        """
        # Probability map loss: BCE + Dice
        bce_loss = F.binary_cross_entropy(prob_map * mask, gt_prob * mask,
                                           reduction='sum') / (mask.sum() + 1e-6)
        dice = self.dice_loss(prob_map, gt_prob, mask)
        prob_loss = bce_loss + dice

        # Threshold map loss: L1 on text region
        thresh_loss = F.l1_loss(thresh_map * thresh_mask, gt_thresh * thresh_mask,
                                 reduction='sum') / (thresh_mask.sum() + 1e-6)

        # Binary map loss: BCE + Dice
        binary_bce = F.binary_cross_entropy(binary_map * mask, gt_prob * mask,
                                             reduction='sum') / (mask.sum() + 1e-6)
        binary_dice = self.dice_loss(binary_map, gt_prob, mask)
        binary_loss = binary_bce + binary_dice

        # Total loss
        total_loss = prob_loss + self.alpha * binary_loss + self.beta * thresh_loss

        return total_loss, prob_loss, thresh_loss, binary_loss
