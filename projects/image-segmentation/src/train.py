"""
Training utilities for U-Net segmentation model.

Provides a simple training loop with:
- Training and validation steps
- Learning rate scheduling
- Metrics tracking (loss, IoU, Dice)
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .unet import UNet
from .loss import BCEDiceLoss


def compute_iou(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Compute Intersection over Union (IoU) metric.

    Args:
        pred: Predicted logits of shape (B, C, H, W).
        target: Ground truth masks of shape (B, C, H, W).
        threshold: Threshold for binarizing predictions.

    Returns:
        Mean IoU score across the batch.
    """
    pred_binary = (torch.sigmoid(pred) > threshold).float()
    intersection = (pred_binary * target).sum()
    union = pred_binary.sum() + target.sum() - intersection
    if union == 0:
        return 1.0
    return (intersection / union).item()


def compute_dice_coefficient(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Compute Dice coefficient (F1 score for segmentation).

    Args:
        pred: Predicted logits of shape (B, C, H, W).
        target: Ground truth masks of shape (B, C, H, W).
        threshold: Threshold for binarizing predictions.

    Returns:
        Mean Dice coefficient across the batch.
    """
    pred_binary = (torch.sigmoid(pred) > threshold).float()
    intersection = (pred_binary * target).sum()
    total = pred_binary.sum() + target.sum()
    if total == 0:
        return 1.0
    return (2.0 * intersection / total).item()


class Trainer:
    """Simple trainer for U-Net segmentation model.

    Handles the training loop, validation, and metric tracking.

    Args:
        model: The U-Net model to train.
        learning_rate: Learning rate for the optimizer (default: 1e-3).
        device: Device to use for training (default: 'cpu').
        loss_fn: Loss function (default: BCEDiceLoss).
    """

    def __init__(
        self,
        model: UNet,
        learning_rate: float = 1e-3,
        device: str = "cpu",
        loss_fn: Optional[nn.Module] = None,
    ):
        self.model = model.to(device)
        self.device = device
        self.loss_fn = loss_fn or BCEDiceLoss()
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", patience=5, factor=0.5
        )

        self.train_losses: List[float] = []
        self.val_losses: List[float] = []
        self.val_ious: List[float] = []

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Train for one epoch.

        Args:
            dataloader: Training data loader.

        Returns:
            Average training loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for images, masks in dataloader:
            images = images.to(self.device)
            masks = masks.to(self.device)

            # Forward pass
            predictions = self.model(images)
            loss = self.loss_fn(predictions, masks)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        self.train_losses.append(avg_loss)
        return avg_loss

    @torch.no_grad()
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Validate the model.

        Args:
            dataloader: Validation data loader.

        Returns:
            Dictionary with validation metrics (loss, iou, dice).
        """
        self.model.eval()
        total_loss = 0.0
        total_iou = 0.0
        total_dice = 0.0
        n_batches = 0

        for images, masks in dataloader:
            images = images.to(self.device)
            masks = masks.to(self.device)

            predictions = self.model(images)
            loss = self.loss_fn(predictions, masks)

            total_loss += loss.item()
            total_iou += compute_iou(predictions, masks)
            total_dice += compute_dice_coefficient(predictions, masks)
            n_batches += 1

        n = max(n_batches, 1)
        metrics = {
            "loss": total_loss / n,
            "iou": total_iou / n,
            "dice": total_dice / n,
        }

        self.val_losses.append(metrics["loss"])
        self.val_ious.append(metrics["iou"])

        # Update learning rate scheduler
        self.scheduler.step(metrics["loss"])

        return metrics

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        n_epochs: int = 10,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """Train the model for multiple epochs.

        Args:
            train_loader: Training data loader.
            val_loader: Optional validation data loader.
            n_epochs: Number of training epochs.
            verbose: Whether to print progress.

        Returns:
            Dictionary with training history (train_losses, val_losses, val_ious).
        """
        for epoch in range(n_epochs):
            train_loss = self.train_epoch(train_loader)

            if verbose:
                msg = f"Epoch {epoch + 1}/{n_epochs} - Train Loss: {train_loss:.4f}"

            if val_loader is not None:
                val_metrics = self.validate(val_loader)
                if verbose:
                    msg += (
                        f" - Val Loss: {val_metrics['loss']:.4f}"
                        f" - Val IoU: {val_metrics['iou']:.4f}"
                        f" - Val Dice: {val_metrics['dice']:.4f}"
                    )

            if verbose:
                print(msg)

        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "val_ious": self.val_ious,
        }
