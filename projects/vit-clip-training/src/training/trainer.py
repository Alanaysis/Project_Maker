"""
CLIP Trainer Implementation

⭐ Training Loop:
1. Load image-text batch
2. Forward pass through image encoder
3. Forward pass through text encoder
4. Compute contrastive loss
5. Backward pass and optimizer step

💡 Training Tips:
- Use large batch sizes (256+) for contrastive learning
- Use learning rate warmup and cosine decay
- Use gradient clipping to prevent instability
- Mixed precision training for efficiency

🎯 Key Hyperparameters:
- Batch size: 256-32768 (larger is better)
- Learning rate: 1e-4 to 5e-4
- Temperature: 0.07 (learnable)
- Weight decay: 0.1-0.5
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.cuda.amp import GradScaler, autocast

from ..models.clip import CLIPModel, create_clip_model
from ..losses.contrastive import CLIPLoss, create_loss


logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """
    Training configuration.

    ⭐ Key parameters to tune:
    - batch_size: Larger batches give better negative samples
    - learning_rate: Too high causes instability, too low is slow
    - warmup_steps: Prevents early training instability
    - weight_decay: Regularization to prevent overfitting
    """

    # Model configuration
    model_config: str = "vit_b32"
    image_size: int = 224
    embed_dim: int = 512

    # Training hyperparameters
    batch_size: int = 32
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    max_epochs: int = 100
    warmup_steps: int = 1000
    max_grad_norm: float = 1.0

    # Loss configuration
    loss_type: str = "clip"
    temperature: float = 0.07

    # Mixed precision
    use_amp: bool = True

    # Checkpointing
    checkpoint_dir: str = "checkpoints"
    save_every: int = 1000
    log_every: int = 100

    # Device
    device: str = "auto"


class CLIPTrainer:
    """
    Trainer for CLIP model.

    Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                      Training Loop                      │
    ├─────────────────────────────────────────────────────────┤
    │ 1. Load batch (images, texts)                           │
    │ 2. Forward pass                                         │
    │    ├── Image encoder -> image embeddings                │
    │    └── Text encoder -> text embeddings                  │
    │ 3. Compute contrastive loss                             │
    │ 4. Backward pass                                        │
    │ 5. Gradient clipping                                    │
    │ 6. Optimizer step                                       │
    │ 7. Update temperature                                   │
    │ 8. Log metrics                                          │
    │ 9. Save checkpoint                                      │
    └─────────────────────────────────────────────────────────┘

    ⭐ Key Features:
    - Mixed precision training (AMP)
    - Gradient accumulation
    - Learning rate warmup and cosine decay
    - Automatic checkpointing
    - TensorBoard logging

    Example:
        >>> config = TrainingConfig(batch_size=32, max_epochs=10)
        >>> trainer = CLIPTrainer(config)
        >>> trainer.train(train_loader, val_loader)
    """

    def __init__(
        self,
        config: TrainingConfig,
        model: Optional[CLIPModel] = None,
        loss_fn: Optional[nn.Module] = None,
    ):
        self.config = config

        # Setup device
        if config.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(config.device)

        logger.info(f"Using device: {self.device}")

        # Create model
        if model is None:
            self.model = create_clip_model(
                config=config.model_config,
                image_size=config.image_size,
            )
        else:
            self.model = model

        self.model = self.model.to(self.device)

        # Create loss function
        if loss_fn is None:
            self.loss_fn = create_loss(
                loss_name=config.loss_type,
                temperature=config.temperature,
            )
        else:
            self.loss_fn = loss_fn

        # Create optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            betas=(0.9, 0.98),  # CLIP uses these beta values
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config.max_epochs,
            eta_min=config.learning_rate / 100,
        )

        # Mixed precision training
        self.scaler = GradScaler() if config.use_amp else None

        # Training state
        self.global_step = 0
        self.current_epoch = 0
        self.best_loss = float("inf")

        # Create checkpoint directory
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Training history
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "learning_rate": [],
        }

    def _get_lr_scale(self) -> float:
        """
        Compute learning rate scale with warmup.

        ⭐ Warmup is crucial for contrastive learning:
        - Prevents early training instability
        - Allows the model to learn basic features first
        - Typically 1-5% of total steps
        """
        if self.global_step < self.config.warmup_steps:
            return self.global_step / self.config.warmup_steps
        return 1.0

    def _update_lr(self):
        """Update learning rate with warmup and cosine decay."""
        lr_scale = self._get_lr_scale()
        for param_group in self.optimizer.param_groups:
            param_group["lr"] = self.config.learning_rate * lr_scale

    def train_step(
        self,
        batch: Tuple[torch.Tensor, torch.Tensor],
    ) -> Dict[str, float]:
        """
        Perform a single training step.

        Args:
            batch: Tuple of (images, texts)

        Returns:
            Dictionary of metrics
        """
        images, texts = batch
        images = images.to(self.device)
        texts = texts.to(self.device)

        # Forward pass with mixed precision
        if self.config.use_amp:
            with autocast():
                outputs = self.model(images, texts, return_loss=True)
                loss = outputs["loss"]
        else:
            outputs = self.model(images, texts, return_loss=True)
            loss = outputs["loss"]

        # Backward pass
        self.optimizer.zero_grad()

        if self.config.use_amp:
            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.max_grad_norm,
            )
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.max_grad_norm,
            )
            self.optimizer.step()

        # Update learning rate
        self._update_lr()

        # Compute metrics
        with torch.no_grad():
            # Compute accuracy
            batch_size = images.shape[0]
            labels = torch.arange(batch_size, device=self.device)
            logits_per_image = outputs["logits_per_image"]
            accuracy = (logits_per_image.argmax(dim=1) == labels).float().mean()

        return {
            "loss": loss.item(),
            "accuracy": accuracy.item(),
            "temperature": self.model.logit_scale.exp().item(),
            "learning_rate": self.optimizer.param_groups[0]["lr"],
        }

    @torch.no_grad()
    def validation_step(
        self,
        batch: Tuple[torch.Tensor, torch.Tensor],
    ) -> Dict[str, float]:
        """Perform a validation step."""
        images, texts = batch
        images = images.to(self.device)
        texts = texts.to(self.device)

        outputs = self.model(images, texts, return_loss=True)
        loss = outputs["loss"]

        # Compute accuracy
        batch_size = images.shape[0]
        labels = torch.arange(batch_size, device=self.device)
        logits_per_image = outputs["logits_per_image"]
        accuracy = (logits_per_image.argmax(dim=1) == labels).float().mean()

        return {
            "val_loss": loss.item(),
            "val_accuracy": accuracy.item(),
        }

    def train_epoch(
        self,
        train_loader: DataLoader,
    ) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        total_accuracy = 0
        num_batches = 0

        for batch_idx, batch in enumerate(train_loader):
            metrics = self.train_step(batch)

            total_loss += metrics["loss"]
            total_accuracy += metrics["accuracy"]
            num_batches += 1

            # Logging
            if (batch_idx + 1) % self.config.log_every == 0:
                logger.info(
                    f"Epoch {self.current_epoch} | "
                    f"Step {batch_idx + 1}/{len(train_loader)} | "
                    f"Loss: {metrics['loss']:.4f} | "
                    f"Acc: {metrics['accuracy']:.4f} | "
                    f"Temp: {metrics['temperature']:.4f}"
                )

            # Save checkpoint
            if (self.global_step + 1) % self.config.save_every == 0:
                self.save_checkpoint(f"step_{self.global_step}.pt")

            self.global_step += 1

        return {
            "train_loss": total_loss / num_batches,
            "train_accuracy": total_accuracy / num_batches,
        }

    @torch.no_grad()
    def validate(
        self,
        val_loader: DataLoader,
    ) -> Dict[str, float]:
        """Run validation."""
        self.model.eval()
        total_loss = 0
        total_accuracy = 0
        num_batches = 0

        for batch in val_loader:
            metrics = self.validation_step(batch)
            total_loss += metrics["val_loss"]
            total_accuracy += metrics["val_accuracy"]
            num_batches += 1

        return {
            "val_loss": total_loss / num_batches,
            "val_accuracy": total_accuracy / num_batches,
        }

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
    ) -> Dict[str, list]:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader (optional)

        Returns:
            Training history
        """
        logger.info("Starting training...")
        logger.info(f"Model config: {self.config.model_config}")
        logger.info(f"Batch size: {self.config.batch_size}")
        logger.info(f"Learning rate: {self.config.learning_rate}")
        logger.info(f"Max epochs: {self.config.max_epochs}")

        for epoch in range(self.config.max_epochs):
            self.current_epoch = epoch
            start_time = time.time()

            # Training
            train_metrics = self.train_epoch(train_loader)
            self.history["train_loss"].append(train_metrics["train_loss"])
            self.history["learning_rate"].append(self.optimizer.param_groups[0]["lr"])

            # Validation
            if val_loader is not None:
                val_metrics = self.validate(val_loader)
                self.history["val_loss"].append(val_metrics["val_loss"])

                logger.info(
                    f"Epoch {epoch} completed in {time.time() - start_time:.1f}s | "
                    f"Train Loss: {train_metrics['train_loss']:.4f} | "
                    f"Val Loss: {val_metrics['val_loss']:.4f}"
                )

                # Save best model
                if val_metrics["val_loss"] < self.best_loss:
                    self.best_loss = val_metrics["val_loss"]
                    self.save_checkpoint("best_model.pt")
            else:
                logger.info(
                    f"Epoch {epoch} completed in {time.time() - start_time:.1f}s | "
                    f"Train Loss: {train_metrics['train_loss']:.4f}"
                )

            # Update scheduler
            self.scheduler.step()

            # Save epoch checkpoint
            self.save_checkpoint(f"epoch_{epoch}.pt")

        logger.info("Training completed!")
        return self.history

    def save_checkpoint(self, filename: str):
        """Save training checkpoint."""
        checkpoint = {
            "epoch": self.current_epoch,
            "global_step": self.global_step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "best_loss": self.best_loss,
            "history": self.history,
            "config": self.config,
        }

        if self.scaler is not None:
            checkpoint["scaler_state_dict"] = self.scaler.state_dict()

        path = self.checkpoint_dir / filename
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint to {path}")

    def load_checkpoint(self, filename: str):
        """Load training checkpoint."""
        path = self.checkpoint_dir / filename
        if not path.exists():
            logger.warning(f"Checkpoint not found: {path}")
            return

        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.current_epoch = checkpoint["epoch"]
        self.global_step = checkpoint["global_step"]
        self.best_loss = checkpoint["best_loss"]
        self.history = checkpoint["history"]

        if self.scaler is not None and "scaler_state_dict" in checkpoint:
            self.scaler.load_state_dict(checkpoint["scaler_state_dict"])

        logger.info(f"Loaded checkpoint from {path}")

    @torch.no_grad()
    def compute_similarity(
        self,
        images: torch.Tensor,
        texts: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute similarity between images and texts.

        Args:
            images: Image tensors, shape (B1, C, H, W)
            texts: Text tensors, shape (B2, seq_len)

        Returns:
            Similarity matrix, shape (B1, B2)
        """
        self.model.eval()
        images = images.to(self.device)
        texts = texts.to(self.device)

        image_embeddings = self.model.encode_image(images)
        text_embeddings = self.model.encode_text(texts)

        return image_embeddings @ text_embeddings.t()
