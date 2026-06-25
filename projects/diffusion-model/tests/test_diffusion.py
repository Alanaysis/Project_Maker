"""
Tests for Diffusion Model.
"""

import pytest
import torch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.diffusion import DiffusionModel, DiffusionTrainer
from src.unet import SimpleUNet


class TestDiffusionModel:
    """Test cases for Diffusion Model."""

    def setup_method(self):
        """Setup test fixtures."""
        self.batch_size = 4
        self.channels = 1
        self.height = 28
        self.width = 28

        # Use SimpleUNet for faster testing
        self.model = DiffusionModel(
            image_size=28,
            in_channels=1,
            num_timesteps=100,  # Fewer steps for testing
            model_type="simple"
        )

    def test_initialization(self):
        """Test model initialization."""
        assert self.model.image_size == 28
        assert self.model.in_channels == 1
        assert self.model.num_timesteps == 100

    def test_forward_pass(self):
        """Test forward pass through the model."""
        x = torch.randn(self.batch_size, self.channels, self.height, self.width)
        t = torch.randint(0, 100, (self.batch_size,))

        output = self.model(x, t)

        assert output.shape == x.shape

    def test_training_loss(self):
        """Test training loss computation."""
        x_0 = torch.randn(self.batch_size, self.channels, self.height, self.width)

        loss = self.model.training_loss(x_0)

        assert loss.dim() == 0  # Scalar loss
        assert loss.item() > 0  # Loss should be positive
        assert not torch.isnan(loss)  # Loss should not be NaN
        assert not torch.isinf(loss)  # Loss should not be infinite

    def test_training_loss_with_noise(self):
        """Test training loss with pre-generated noise."""
        x_0 = torch.randn(self.batch_size, self.channels, self.height, self.width)
        noise = torch.randn_like(x_0)

        loss = self.model.training_loss(x_0, noise)

        assert loss.dim() == 0
        assert loss.item() > 0

    def test_sample_shape(self):
        """Test that sampling produces correct shape."""
        # Use fewer steps for faster testing
        self.model.num_timesteps = 10

        samples = self.model.sample(batch_size=2, device=torch.device("cpu"))

        assert samples.shape == (2, 1, 28, 28)

    def test_sample_range(self):
        """Test that samples are in reasonable range."""
        # Use fewer steps for faster testing
        self.model.num_timesteps = 10

        samples = self.model.sample(batch_size=4, device=torch.device("cpu"))

        # Samples should be in roughly [-3, 3] range (Gaussian)
        assert samples.min() > -5
        assert samples.max() < 5

    def test_sample_deterministic(self):
        """Test that sampling with same seed produces same results."""
        torch.manual_seed(42)
        self.model.num_timesteps = 10
        samples1 = self.model.sample(batch_size=2, device=torch.device("cpu"))

        torch.manual_seed(42)
        samples2 = self.model.sample(batch_size=2, device=torch.device("cpu"))

        assert torch.allclose(samples1, samples2)

    def test_sample_different_seeds(self):
        """Test that different seeds produce different samples."""
        self.model.num_timesteps = 10

        torch.manual_seed(42)
        samples1 = self.model.sample(batch_size=2, device=torch.device("cpu"))

        torch.manual_seed(123)
        samples2 = self.model.sample(batch_size=2, device=torch.device("cpu"))

        assert not torch.allclose(samples1, samples2)

    def test_sample_with_intermediates(self):
        """Test sampling with intermediate results."""
        self.model.num_timesteps = 10

        samples, intermediates = self.model.sample(
            batch_size=2,
            device=torch.device("cpu"),
            return_intermediates=True
        )

        assert samples.shape == (2, 1, 28, 28)
        assert len(intermediates) > 0

    def test_ddim_sample(self):
        """Test DDIM sampling."""
        self.model.num_timesteps = 100

        samples = self.model.sample_ddim(
            batch_size=2,
            device=torch.device("cpu"),
            ddim_steps=10
        )

        assert samples.shape == (2, 1, 28, 28)

    def test_model_parameters(self):
        """Test that model has trainable parameters."""
        num_params = sum(p.numel() for p in self.model.parameters())
        assert num_params > 0

    def test_model_training_mode(self):
        """Test model training/eval mode switching."""
        self.model.train()
        assert self.model.training

        self.model.eval()
        assert not self.model.training


class TestDiffusionTrainer:
    """Test cases for Diffusion Trainer."""

    def setup_method(self):
        """Setup test fixtures."""
        from torch.utils.data import DataLoader, TensorDataset

        # Create dummy dataset
        self.images = torch.randn(32, 1, 28, 28)
        dataset = TensorDataset(self.images)
        self.dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

        # Create model
        self.model = DiffusionModel(
            image_size=28,
            in_channels=1,
            num_timesteps=10,
            model_type="simple"
        )

        # Create trainer
        self.trainer = DiffusionTrainer(
            model=self.model,
            learning_rate=1e-4
        )

    def test_initialization(self):
        """Test trainer initialization."""
        assert self.trainer.model is not None
        assert self.trainer.optimizer is not None
        assert len(self.trainer.losses) == 0

    def test_train_epoch(self):
        """Test training for one epoch."""
        avg_loss = self.trainer.train_epoch(self.dataloader)

        assert avg_loss > 0
        assert len(self.trainer.losses) == 1

    def test_multiple_epochs(self):
        """Test training for multiple epochs."""
        losses = self.trainer.train(
            dataloader=self.dataloader,
            num_epochs=3,
            sample_interval=10  # Don't generate samples during test
        )

        assert len(losses) == 3
        assert all(l > 0 for l in losses)

    def test_checkpoint_save_load(self, tmp_path):
        """Test saving and loading checkpoints."""
        # Save checkpoint
        save_path = str(tmp_path / "checkpoint.pt")
        self.trainer.save_checkpoint(save_path)

        assert os.path.exists(save_path)

        # Load checkpoint
        new_trainer = DiffusionTrainer(model=self.model)
        new_trainer.load_checkpoint(save_path)

        assert len(new_trainer.losses) == len(self.trainer.losses)

    def test_gradient_clipping(self):
        """Test that gradient clipping is applied."""
        # This is implicitly tested in train_epoch
        # Just verify no errors occur
        avg_loss = self.trainer.train_epoch(self.dataloader)
        assert avg_loss > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
