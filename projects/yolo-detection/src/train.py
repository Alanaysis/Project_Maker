"""
Training script for YOLO object detection.

Provides:
- Training loop with validation
- Learning rate scheduling
- Model checkpointing
- Training metrics logging
"""

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import time
import json
from pathlib import Path
from typing import Optional, Dict, List

from .model import YOLOv1, TinyYOLOv1
from .loss import YOLOLoss
from .dataset import SimpleDetectionDataset, create_dataloader


class Trainer:
    """
    YOLO training manager.

    Handles the complete training pipeline including:
    - Model initialization
    - Loss computation
    - Optimization
    - Learning rate scheduling
    - Checkpointing
    - Metrics logging

    Args:
        model: YOLO model instance
        train_loader: Training data loader
        val_loader: Validation data loader (optional)
        config: Training configuration dictionary
    """

    def __init__(
        self,
        model: torch.nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[Dict] = None,
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader

        # Default config
        self.config = {
            "learning_rate": 1e-3,
            "weight_decay": 5e-4,
            "epochs": 50,
            "lr_scheduler": "cosine",  # 'step', 'cosine', or 'none'
            "lr_step_size": 30,
            "lr_gamma": 0.1,
            "checkpoint_dir": "checkpoints",
            "save_every": 10,
            "grid_size": 7,
            "num_boxes": 2,
            "num_classes": 20,
            "lambda_coord": 5.0,
            "lambda_noobj": 0.5,
        }
        if config:
            self.config.update(config)

        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Loss function
        self.criterion = YOLOLoss(
            grid_size=self.config["grid_size"],
            num_boxes=self.config["num_boxes"],
            num_classes=self.config["num_classes"],
            lambda_coord=self.config["lambda_coord"],
            lambda_noobj=self.config["lambda_noobj"],
        )

        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.config["learning_rate"],
            weight_decay=self.config["weight_decay"],
        )

        # Learning rate scheduler
        self.scheduler = self._create_scheduler()

        # Training history
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "learning_rate": [],
        }

        # Checkpoint directory
        self.checkpoint_dir = Path(self.config["checkpoint_dir"])
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _create_scheduler(self):
        """Create learning rate scheduler."""
        scheduler_type = self.config["lr_scheduler"]

        if scheduler_type == "step":
            return optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=self.config["lr_step_size"],
                gamma=self.config["lr_gamma"],
            )
        elif scheduler_type == "cosine":
            return optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=self.config["epochs"]
            )
        else:
            return None

    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        epoch_losses = {
            "total": 0.0,
            "loc_xy": 0.0,
            "loc_wh": 0.0,
            "conf_obj": 0.0,
            "conf_noobj": 0.0,
            "class": 0.0,
        }
        num_batches = 0

        for batch_idx, (images, targets) in enumerate(self.train_loader):
            images = images.to(self.device)
            target_tensor = targets["target"].to(self.device)

            # Forward pass
            predictions = self.model(images)
            loss, loss_dict = self.criterion(predictions, target_tensor)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # Accumulate losses
            for key in epoch_losses:
                epoch_losses[key] += loss_dict[key]
            num_batches += 1

        # Average losses
        for key in epoch_losses:
            epoch_losses[key] /= max(num_batches, 1)

        return epoch_losses

    @torch.no_grad()
    def validate(self) -> Dict[str, float]:
        """Run validation."""
        if self.val_loader is None:
            return {}

        self.model.eval()
        epoch_losses = {
            "total": 0.0,
            "loc_xy": 0.0,
            "loc_wh": 0.0,
            "conf_obj": 0.0,
            "conf_noobj": 0.0,
            "class": 0.0,
        }
        num_batches = 0

        for images, targets in self.val_loader:
            images = images.to(self.device)
            target_tensor = targets["target"].to(self.device)

            predictions = self.model(images)
            _, loss_dict = self.criterion(predictions, target_tensor)

            for key in epoch_losses:
                epoch_losses[key] += loss_dict[key]
            num_batches += 1

        for key in epoch_losses:
            epoch_losses[key] /= max(num_batches, 1)

        return epoch_losses

    def save_checkpoint(self, epoch: int, filename: Optional[str] = None):
        """Save model checkpoint."""
        if filename is None:
            filename = f"checkpoint_epoch_{epoch}.pt"

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.config,
            "history": self.history,
        }

        if self.scheduler is not None:
            checkpoint["scheduler_state_dict"] = self.scheduler.state_dict()

        path = self.checkpoint_dir / filename
        torch.save(checkpoint, path)
        print(f"Checkpoint saved: {path}")

    def load_checkpoint(self, filepath: str):
        """Load model checkpoint."""
        checkpoint = torch.load(filepath, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        if self.scheduler is not None and "scheduler_state_dict" in checkpoint:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        self.history = checkpoint.get("history", self.history)

        return checkpoint["epoch"]

    def train(self, num_epochs: Optional[int] = None):
        """
        Run the complete training loop.

        Args:
            num_epochs: Number of epochs to train. If None, uses config.
        """
        epochs = num_epochs or self.config["epochs"]
        best_val_loss = float("inf")

        print(f"Training on {self.device}")
        print(f"Epochs: {epochs}")
        print(f"Training samples: {len(self.train_loader.dataset)}")
        if self.val_loader:
            print(f"Validation samples: {len(self.val_loader.dataset)}")
        print("-" * 50)

        for epoch in range(1, epochs + 1):
            start_time = time.time()

            # Train
            train_losses = self.train_epoch()
            self.history["train_loss"].append(train_losses["total"])

            # Validate
            val_losses = self.validate()
            if val_losses:
                self.history["val_loss"].append(val_losses["total"])

            # Update learning rate
            current_lr = self.optimizer.param_groups[0]["lr"]
            self.history["learning_rate"].append(current_lr)
            if self.scheduler is not None:
                self.scheduler.step()

            elapsed = time.time() - start_time

            # Print progress
            print(f"Epoch {epoch}/{epochs} ({elapsed:.1f}s)")
            print(f"  LR: {current_lr:.6f}")
            print(f"  Train Loss: {train_losses['total']:.4f}")
            if val_losses:
                print(f"  Val Loss: {val_losses['total']:.4f}")

            # Save checkpoint
            if epoch % self.config["save_every"] == 0:
                self.save_checkpoint(epoch)

            # Save best model
            if val_losses and val_losses["total"] < best_val_loss:
                best_val_loss = val_losses["total"]
                self.save_checkpoint(epoch, "best_model.pt")

        # Save final model
        self.save_checkpoint(epochs, "final_model.pt")

        # Save history
        history_path = self.checkpoint_dir / "training_history.json"
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)

        print("-" * 50)
        print("Training complete!")
        return self.history


def train_simple(
    num_epochs: int = 5,
    batch_size: int = 4,
    learning_rate: float = 1e-3,
    num_train_samples: int = 50,
    num_val_samples: int = 10,
    grid_size: int = 7,
    num_classes: int = 5,
) -> Dict:
    """
    Simple training function for quick testing.

    Creates a tiny model and synthetic dataset for fast iteration.

    Args:
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        num_train_samples: Number of training samples
        num_val_samples: Number of validation samples
        grid_size: YOLO grid size
        num_classes: Number of classes

    Returns:
        Training history dictionary
    """
    # Create model
    model = TinyYOLOv1(
        grid_size=grid_size,
        num_boxes=2,
        num_classes=num_classes,
    )

    # Create datasets
    train_dataset = SimpleDetectionDataset(
        num_samples=num_train_samples,
        grid_size=grid_size,
        num_classes=num_classes,
    )
    val_dataset = SimpleDetectionDataset(
        num_samples=num_val_samples,
        grid_size=grid_size,
        num_classes=num_classes,
        seed=123,
    )

    # Create data loaders
    train_loader = create_dataloader(train_dataset, batch_size=batch_size)
    val_loader = create_dataloader(val_dataset, batch_size=batch_size, shuffle=False)

    # Configure training
    config = {
        "learning_rate": learning_rate,
        "epochs": num_epochs,
        "grid_size": grid_size,
        "num_classes": num_classes,
        "checkpoint_dir": "checkpoints/simple_train",
        "save_every": max(1, num_epochs // 2),
    }

    # Train
    trainer = Trainer(model, train_loader, val_loader, config)
    history = trainer.train()

    return history


if __name__ == "__main__":
    print("Starting simple YOLO training...")
    history = train_simple(
        num_epochs=3,
        batch_size=2,
        num_train_samples=20,
        num_val_samples=5,
    )
    print("\nFinal train loss:", history["train_loss"][-1])
    if history["val_loss"]:
        print("Final val loss:", history["val_loss"][-1])
