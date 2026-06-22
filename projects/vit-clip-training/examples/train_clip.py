"""
CLIP Training Example

This script demonstrates how to train a CLIP model using the framework.

⭐ Key Steps:
1. Create synthetic dataset (or load real data)
2. Initialize CLIP model
3. Setup training configuration
4. Run training loop

💡 Tips for real training:
- Use a large dataset (CC3M, LAION-400M)
- Use multiple GPUs for data parallelism
- Monitor training with TensorBoard
- Use gradient accumulation for larger effective batch sizes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import logging
from torch.utils.data import DataLoader

from src.models.clip import CLIPModel, create_clip_model
from src.data.dataset import SyntheticDataset, create_dataloader
from src.training.trainer import CLIPTrainer, TrainingConfig
from src.losses.contrastive import CLIPLoss

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def main():
    """Main training function."""
    logger.info("=" * 60)
    logger.info("CLIP Training Example")
    logger.info("=" * 60)

    # Training configuration
    config = TrainingConfig(
        model_config="vit_b32",
        image_size=224,
        batch_size=8,  # Small batch size for demo
        learning_rate=3e-4,
        max_epochs=3,
        warmup_steps=100,
        use_amp=torch.cuda.is_available(),
        checkpoint_dir="checkpoints/demo",
        save_every=500,
        log_every=10,
    )

    logger.info(f"Configuration:")
    logger.info(f"  Model: {config.model_config}")
    logger.info(f"  Image size: {config.image_size}")
    logger.info(f"  Batch size: {config.batch_size}")
    logger.info(f"  Learning rate: {config.learning_rate}")
    logger.info(f"  Max epochs: {config.max_epochs}")

    # Create synthetic dataset
    logger.info("\nCreating synthetic dataset...")
    train_dataset = SyntheticDataset(
        num_samples=100,
        image_size=config.image_size,
    )
    val_dataset = SyntheticDataset(
        num_samples=20,
        image_size=config.image_size,
    )

    # Create data loaders
    train_loader = create_dataloader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0,  # Use 0 for multiprocessing compatibility
    )
    val_loader = create_dataloader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
    )

    logger.info(f"  Train samples: {len(train_dataset)}")
    logger.info(f"  Val samples: {len(val_dataset)}")
    logger.info(f"  Train batches: {len(train_loader)}")
    logger.info(f"  Val batches: {len(val_loader)}")

    # Create model
    logger.info("\nCreating CLIP model...")
    model = create_clip_model(
        config=config.model_config,
        image_size=config.image_size,
    )

    # Print model summary
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"  Total parameters: {total_params:,}")
    logger.info(f"  Trainable parameters: {trainable_params:,}")

    # Create trainer
    logger.info("\nInitializing trainer...")
    trainer = CLIPTrainer(
        config=config,
        model=model,
    )

    # Start training
    logger.info("\nStarting training...")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
    )

    # Print final results
    logger.info("\n" + "=" * 60)
    logger.info("Training Complete!")
    logger.info("=" * 60)
    logger.info(f"Final train loss: {history['train_loss'][-1]:.4f}")
    if history['val_loss']:
        logger.info(f"Final val loss: {history['val_loss'][-1]:.4f}")
    logger.info(f"Best val loss: {trainer.best_loss:.4f}")

    # Save final model
    trainer.save_checkpoint("final_model.pt")
    logger.info("\nModel saved to checkpoints/demo/final_model.pt")

    return history


if __name__ == "__main__":
    main()
