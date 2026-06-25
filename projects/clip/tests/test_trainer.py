"""Tests for CLIP trainer."""

import pytest
import torch
import sys
from pathlib import Path
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clip_model import CLIP
from src.trainer import CLIPTrainer
from src.dataset import SyntheticDataset


class TestCLIPTrainer:
    """Tests for CLIPTrainer."""

    @pytest.fixture
    def model(self):
        """Create a small model for testing."""
        return CLIP(embed_dim=128, vocab_size=5000)

    @pytest.fixture
    def trainer(self, model):
        """Create a trainer for testing."""
        return CLIPTrainer(
            model=model,
            learning_rate=1e-4,
            device="cpu",
        )

    @pytest.fixture
    def dataloader(self):
        """Create a test dataloader."""
        dataset = SyntheticDataset(num_samples=16, vocab_size=5000)
        return DataLoader(dataset, batch_size=4, shuffle=True)

    def test_train_step(self, trainer, dataloader):
        """Test single training step."""
        batch = next(iter(dataloader))
        metrics = trainer.train_step(
            images=batch["images"],
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
        )
        assert "loss" in metrics
        assert metrics["loss"] > 0
        assert trainer.global_step == 1

    def test_validate(self, trainer, dataloader):
        """Test validation loop."""
        val_metrics = trainer.validate(dataloader)
        assert "val_loss" in val_metrics
        assert "val_i2t_acc" in val_metrics
        assert "val_t2i_acc" in val_metrics

    def test_train_loop(self, trainer, dataloader):
        """Test full training loop."""
        history = trainer.train(
            train_loader=dataloader,
            val_loader=dataloader,
            num_epochs=2,
            log_interval=5,
        )
        assert "history" in history
        assert len(history["history"]) == 2
        assert trainer.epoch == 1

    def test_checkpoint_save_load(self, trainer, dataloader, tmp_path):
        """Test checkpoint save and load."""
        # Train for a step
        batch = next(iter(dataloader))
        trainer.train_step(
            images=batch["images"],
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
        )

        # Save checkpoint
        checkpoint_path = tmp_path / "test_checkpoint.pt"
        trainer.save_checkpoint(str(checkpoint_path))
        assert checkpoint_path.exists()

        # Load checkpoint
        new_trainer = CLIPTrainer(
            model=CLIP(embed_dim=128, vocab_size=5000),
            device="cpu",
        )
        new_trainer.load_checkpoint(str(checkpoint_path))
        assert new_trainer.global_step == 1

    def test_learning_rate_scheduler(self, trainer, dataloader):
        """Test learning rate changes during training."""
        initial_lr = trainer.optimizer.param_groups[0]["lr"]

        # Train for several steps
        for _ in range(10):
            batch = next(iter(dataloader))
            trainer.train_step(
                images=batch["images"],
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )

        current_lr = trainer.optimizer.param_groups[0]["lr"]
        # LR should change (decrease with cosine schedule)
        assert current_lr != initial_lr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
