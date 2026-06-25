"""Training utilities for CLIP model."""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Optional, Dict, List
import time
import json
from pathlib import Path

from .clip_model import CLIP


class CLIPTrainer:
    """
    Trainer for CLIP model.
    """

    def __init__(
        self,
        model: CLIP,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 1000,
        max_steps: int = 100000,
        device: str = "auto",
    ):
        self.model = model
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.warmup_steps = warmup_steps
        self.max_steps = max_steps

        # Device setup
        if device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        else:
            self.device = torch.device(device)

        self.model = self.model.to(self.device)

        # Optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=max_steps,
            eta_min=learning_rate * 0.1,
        )

        # Training state
        self.global_step = 0
        self.epoch = 0
        self.best_loss = float("inf")
        self.training_history: List[Dict] = []

    def train_step(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> Dict:
        """
        Single training step.

        Args:
            images: Input images
            input_ids: Token IDs
            attention_mask: Attention mask

        Returns:
            Dictionary of metrics
        """
        self.model.train()

        # Move to device
        images = images.to(self.device)
        input_ids = input_ids.to(self.device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        # Forward pass
        loss, metrics = self.model(images, input_ids, attention_mask)

        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        self.optimizer.step()
        self.scheduler.step()

        self.global_step += 1

        return metrics

    def validate(
        self,
        val_loader: DataLoader,
    ) -> Dict:
        """
        Validation loop.

        Args:
            val_loader: Validation data loader

        Returns:
            Dictionary of validation metrics
        """
        self.model.eval()
        total_metrics = {}
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                images = batch["images"].to(self.device)
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch.get("attention_mask")
                if attention_mask is not None:
                    attention_mask = attention_mask.to(self.device)

                _, metrics = self.model(images, input_ids, attention_mask)

                # Accumulate metrics
                for key, value in metrics.items():
                    if key not in total_metrics:
                        total_metrics[key] = 0.0
                    total_metrics[key] += value

                num_batches += 1

        # Average metrics
        avg_metrics = {
            f"val_{k}": v / num_batches for k, v in total_metrics.items()
        }

        return avg_metrics

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 10,
        save_dir: Optional[str] = None,
        log_interval: int = 100,
    ) -> Dict:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of training epochs
            save_dir: Directory to save checkpoints
            log_interval: Logging interval

        Returns:
            Training history
        """
        if save_dir:
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)

        for epoch in range(num_epochs):
            self.epoch = epoch
            epoch_metrics = {}
            num_batches = 0
            start_time = time.time()

            for batch_idx, batch in enumerate(train_loader):
                metrics = self.train_step(
                    images=batch["images"],
                    input_ids=batch["input_ids"],
                    attention_mask=batch.get("attention_mask"),
                )

                # Accumulate metrics
                for key, value in metrics.items():
                    if key not in epoch_metrics:
                        epoch_metrics[key] = 0.0
                    epoch_metrics[key] += value

                num_batches += 1

                # Logging
                if (batch_idx + 1) % log_interval == 0:
                    avg_loss = epoch_metrics["loss"] / num_batches
                    print(
                        f"Epoch {epoch + 1}/{num_epochs}, "
                        f"Step {batch_idx + 1}/{len(train_loader)}, "
                        f"Loss: {avg_loss:.4f}"
                    )

            # Average epoch metrics
            avg_metrics = {
                k: v / num_batches for k, v in epoch_metrics.items()
            }
            avg_metrics["epoch"] = epoch + 1
            avg_metrics["time"] = time.time() - start_time

            # Validation
            if val_loader:
                val_metrics = self.validate(val_loader)
                avg_metrics.update(val_metrics)

            self.training_history.append(avg_metrics)

            # Print epoch summary
            print(
                f"\nEpoch {epoch + 1}/{num_epochs} - "
                f"Loss: {avg_metrics['loss']:.4f}, "
                f"I2T Acc: {avg_metrics.get('i2t_acc', 0):.4f}, "
                f"T2I Acc: {avg_metrics.get('t2i_acc', 0):.4f}"
            )

            if val_loader:
                print(
                    f"  Val Loss: {avg_metrics.get('val_loss', 0):.4f}, "
                    f"Val I2T Acc: {avg_metrics.get('val_i2t_acc', 0):.4f}"
                )

            # Save checkpoint
            if save_dir and avg_metrics["loss"] < self.best_loss:
                self.best_loss = avg_metrics["loss"]
                self.save_checkpoint(save_path / "best_model.pt")

            if save_dir:
                self.save_checkpoint(save_path / "last_model.pt")

        return {"history": self.training_history}

    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "global_step": self.global_step,
            "epoch": self.epoch,
            "best_loss": self.best_loss,
        }
        torch.save(checkpoint, path)

    def load_checkpoint(self, path: str) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.global_step = checkpoint["global_step"]
        self.epoch = checkpoint["epoch"]
        self.best_loss = checkpoint["best_loss"]
