"""Training pipeline for DnCNN image denoising.

Implements:
- MSE loss for noise prediction
- Learning rate scheduling
- Checkpoint saving
- Training metrics logging
"""

from typing import Optional, Dict, Tuple
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

from .model import DnCNN, create_model
from .evaluate import calculate_psnr, calculate_ssim


class Trainer:
    """Trainer for DnCNN image denoising model.

    The model is trained to predict the noise in the image:
        Loss = MSE(predicted_noise, actual_noise)

    Args:
        model: DnCNN model instance
        device: Device to use for training ("cpu" or "cuda")
        learning_rate: Initial learning rate
        weight_decay: L2 regularization weight
    """

    def __init__(
        self,
        model: nn.Module,
        device: str = "cpu",
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-5,
    ):
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate

        # Loss function: MSE for noise prediction
        self.criterion = nn.MSELoss()

        # Optimizer: Adam with weight decay
        self.optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        # Learning rate scheduler: ReduceLROnPlateau
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
        )

        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'val_psnr': [],
            'val_ssim': [],
            'lr': [],
        }

        self.best_val_loss = float('inf')
        self.epoch = 0

    def train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch.

        Args:
            train_loader: Training data loader

        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        pbar = tqdm(train_loader, desc=f"Epoch {self.epoch + 1}")
        for noisy, clean, noise_gt in pbar:
            # Move to device
            noisy = noisy.to(self.device)
            noise_gt = noise_gt.to(self.device)

            # Forward pass: predict noise
            noise_pred = self.model(noisy)

            # Compute loss: MSE between predicted and actual noise
            loss = self.criterion(noise_pred, noise_gt)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            # Update progress bar
            pbar.set_postfix({'loss': f"{loss.item():.4f}"})

        avg_loss = total_loss / num_batches
        return avg_loss

    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> Tuple[float, float, float]:
        """Validate the model.

        Args:
            val_loader: Validation data loader

        Returns:
            Tuple of (average_loss, average_psnr, average_ssim)
        """
        self.model.eval()
        total_loss = 0.0
        total_psnr = 0.0
        total_ssim = 0.0
        num_batches = 0

        for noisy, clean, noise_gt in val_loader:
            noisy = noisy.to(self.device)
            clean = clean.to(self.device)
            noise_gt = noise_gt.to(self.device)

            # Predict noise
            noise_pred = self.model(noisy)

            # Compute loss
            loss = self.criterion(noise_pred, noise_gt)
            total_loss += loss.item()

            # Get denoised image
            denoised = noisy - noise_pred

            # Calculate metrics on CPU
            denoised_cpu = denoised.cpu().numpy()
            clean_cpu = clean.cpu().numpy()

            batch_psnr = 0.0
            batch_ssim = 0.0
            batch_size = denoised_cpu.shape[0]

            for i in range(batch_size):
                batch_psnr += calculate_psnr(clean_cpu[i], denoised_cpu[i])
                batch_ssim += calculate_ssim(clean_cpu[i], denoised_cpu[i])

            total_psnr += batch_psnr / batch_size
            total_ssim += batch_ssim / batch_size
            num_batches += 1

        avg_loss = total_loss / num_batches
        avg_psnr = total_psnr / num_batches
        avg_ssim = total_ssim / num_batches

        return avg_loss, avg_psnr, avg_ssim

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 50,
        save_dir: str = "checkpoints",
        save_every: int = 5,
        early_stopping_patience: int = 15,
    ) -> Dict[str, list]:
        """Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of epochs to train
            save_dir: Directory to save checkpoints
            save_every: Save checkpoint every N epochs
            early_stopping_patience: Stop if no improvement for N epochs

        Returns:
            Training history dictionary
        """
        # Create save directory
        os.makedirs(save_dir, exist_ok=True)

        # Early stopping counter
        patience_counter = 0

        print(f"\nStarting training for {num_epochs} epochs")
        print(f"Device: {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print("=" * 60)

        start_time = time.time()

        for epoch in range(num_epochs):
            self.epoch = epoch

            # Train
            train_loss = self.train_epoch(train_loader)
            self.history['train_loss'].append(train_loss)

            # Validate
            val_loss, val_psnr, val_ssim = self.validate(val_loader)
            self.history['val_loss'].append(val_loss)
            self.history['val_psnr'].append(val_psnr)
            self.history['val_ssim'].append(val_ssim)

            # Update learning rate
            self.scheduler.step(val_loss)
            current_lr = self.optimizer.param_groups[0]['lr']
            self.history['lr'].append(current_lr)

            # Print epoch summary
            elapsed = time.time() - start_time
            print(f"\nEpoch {epoch + 1}/{num_epochs} ({elapsed:.0f}s)")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Val PSNR: {val_psnr:.2f} dB")
            print(f"  Val SSIM: {val_ssim:.4f}")
            print(f"  Learning Rate: {current_lr:.6f}")

            # Save best model
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                patience_counter = 0
                self.save_checkpoint(os.path.join(save_dir, "best_model.pth"))
                print("  -> New best model saved!")
            else:
                patience_counter += 1

            # Save periodic checkpoint
            if (epoch + 1) % save_every == 0:
                self.save_checkpoint(os.path.join(save_dir, f"checkpoint_epoch_{epoch + 1}.pth"))

            # Early stopping
            if patience_counter >= early_stopping_patience:
                print(f"\nEarly stopping triggered after {epoch + 1} epochs")
                break

        total_time = time.time() - start_time
        print(f"\nTraining completed in {total_time:.0f}s")
        print(f"Best validation loss: {self.best_val_loss:.4f}")

        return self.history

    def save_checkpoint(self, filepath: str):
        """Save model checkpoint.

        Args:
            filepath: Path to save checkpoint
        """
        checkpoint = {
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_loss': self.best_val_loss,
            'history': self.history,
        }
        torch.save(checkpoint, filepath)

    def load_checkpoint(self, filepath: str):
        """Load model checkpoint.

        Args:
            filepath: Path to checkpoint file
        """
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.epoch = checkpoint['epoch']
        self.best_val_loss = checkpoint['best_val_loss']
        self.history = checkpoint['history']
        print(f"Loaded checkpoint from epoch {self.epoch + 1}")


def train_model(
    train_loader: DataLoader,
    val_loader: DataLoader,
    model_type: str = "dncnn",
    in_channels: int = 1,
    depth: int = 17,
    num_features: int = 64,
    num_epochs: int = 50,
    learning_rate: float = 1e-3,
    device: str = "cpu",
    save_dir: str = "checkpoints",
) -> Tuple[nn.Module, Dict[str, list]]:
    """High-level function to train a denoising model.

    Args:
        train_loader: Training data loader
        val_loader: Validation data loader
        model_type: Type of model to train
        in_channels: Number of input channels
        depth: Network depth
        num_features: Number of features
        num_epochs: Number of training epochs
        learning_rate: Initial learning rate
        device: Device to use
        save_dir: Directory to save checkpoints

    Returns:
        Tuple of (trained_model, training_history)
    """
    # Create model
    model = create_model(
        model_type=model_type,
        in_channels=in_channels,
        depth=depth,
        num_features=num_features,
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        device=device,
        learning_rate=learning_rate,
    )

    # Train
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        save_dir=save_dir,
    )

    return model, history


if __name__ == "__main__":
    # Test training pipeline
    from .dataset import create_dataloaders

    print("Testing Training Pipeline")
    print("=" * 40)

    # Create small dataloaders for testing
    train_loader, val_loader = create_dataloaders(
        batch_size=4,
        patch_size=64,
        num_workers=0,
    )

    # Create model
    model = create_model(model_type="dncnn", in_channels=1, depth=5, num_features=32)

    # Create trainer
    trainer = Trainer(model=model, device="cpu", learning_rate=1e-3)

    # Train for 2 epochs
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=2,
        save_dir="/tmp/test_checkpoints",
    )

    print("\nTraining history:")
    for key, values in history.items():
        if values:
            print(f"  {key}: {values[-1]:.4f}")
