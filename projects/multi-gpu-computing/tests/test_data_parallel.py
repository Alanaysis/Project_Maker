"""
Tests for Data Parallel training.
"""

import pytest
import numpy as np
from src.core.tensor import GPUTensor, get_device
from src.core.data_parallel import (
    SimpleLayer,
    SimpleModel,
    DataParallelTrainer,
)


class TestSimpleLayer:
    """Test SimpleLayer."""

    def test_forward(self):
        layer = SimpleLayer(3, 2, get_device(0))
        x = GPUTensor(np.random.randn(4, 3).astype(np.float32))
        y = layer.forward(x)

        assert y.shape == (4, 2)

    def test_backward(self):
        layer = SimpleLayer(3, 2, get_device(0))
        x = GPUTensor(np.random.randn(4, 3).astype(np.float32))
        y = layer.forward(x)

        grad_out = GPUTensor(np.ones((4, 2), dtype=np.float32))
        grad_in = layer.backward(grad_out)

        assert grad_in.shape == (4, 3)
        assert layer.weight_grad is not None
        assert layer.bias_grad is not None

    def test_zero_grad(self):
        layer = SimpleLayer(3, 2, get_device(0))
        x = GPUTensor(np.random.randn(4, 3).astype(np.float32))
        y = layer.forward(x)
        layer.backward(GPUTensor(np.ones((4, 2))))

        assert layer.weight_grad is not None
        layer.zero_grad()
        assert layer.weight_grad is None


class TestSimpleModel:
    """Test SimpleModel."""

    def test_forward(self):
        model = SimpleModel(10, 20, 5, get_device(0))
        x = GPUTensor(np.random.randn(8, 10).astype(np.float32))
        y = model.forward(x)

        assert y.shape == (8, 5)

    def test_backward(self):
        model = SimpleModel(10, 20, 5, get_device(0))
        x = GPUTensor(np.random.randn(8, 10).astype(np.float32))
        y = model.forward(x)

        grad_out = GPUTensor(np.ones((8, 5), dtype=np.float32))
        model.backward(grad_out)

        params = model.get_params_and_grads()
        for param, grad in params:
            assert grad is not None

    def test_params_count(self):
        model = SimpleModel(10, 20, 5, get_device(0))
        params = model.get_params_and_grads()
        # 2 layers, each with weight and bias = 4 params
        assert len(params) == 4


class TestDataParallelTrainer:
    """Test DataParallelTrainer."""

    def test_init(self):
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=2,
        )
        assert len(trainer.models) == 2

    def test_shard_data(self):
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=4,
        )

        X = np.random.randn(100, 10).astype(np.float32)
        y = np.random.randn(100, 5).astype(np.float32)

        shards = trainer._shard_data(X, y)

        assert len(shards) == 4
        # All samples should be covered
        total_samples = sum(s[0].shape[0] for s in shards)
        assert total_samples == 100

    def test_train_step(self):
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=2,
            learning_rate=0.001,
        )

        X = np.random.randn(32, 10).astype(np.float32)
        y = np.random.randn(32, 5).astype(np.float32)

        loss = trainer.train_step(X, y)

        assert isinstance(loss, float)
        assert loss > 0

    def test_train_decreases_loss(self):
        """Training should decrease loss over multiple steps."""
        np.random.seed(42)
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=2,
            learning_rate=0.001,
        )

        # Generate linear data
        X = np.random.randn(100, 10).astype(np.float32)
        w_true = np.random.randn(10, 5).astype(np.float32)
        y = X @ w_true + 0.1 * np.random.randn(100, 5).astype(np.float32)

        # Train for several steps
        losses = []
        for _ in range(20):
            indices = np.random.choice(100, 32, replace=False)
            loss = trainer.train_step(X[indices], y[indices])
            losses.append(loss)

        # Loss should decrease
        assert losses[-1] < losses[0]

    def test_all_models_same_after_sync(self):
        """After AllReduce, all models should have the same parameters."""
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=4,
            learning_rate=0.001,
        )

        X = np.random.randn(32, 10).astype(np.float32)
        y = np.random.randn(32, 5).astype(np.float32)

        trainer.train_step(X, y)

        # Check that all models have the same weights
        params_0 = trainer.models[0].get_params_and_grads()
        for rank in range(1, 4):
            params_r = trainer.models[rank].get_params_and_grads()
            for (p0, _), (pr, _) in zip(params_0, params_r):
                np.testing.assert_array_almost_equal(p0.data, pr.data, decimal=5)

    def test_get_stats(self):
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=2,
        )

        X = np.random.randn(32, 10).astype(np.float32)
        y = np.random.randn(32, 5).astype(np.float32)

        trainer.train_step(X, y)
        stats = trainer.get_stats()

        assert "total_time" in stats
        assert "comm_time" in stats
        assert "comm_percentage" in stats
        assert stats["steps"] == 1

    def test_train_multi_epoch(self):
        trainer = DataParallelTrainer(
            model_fn=lambda device: SimpleModel(10, 20, 5, device),
            world_size=2,
            learning_rate=0.001,
        )

        X = np.random.randn(100, 10).astype(np.float32)
        y = np.random.randn(100, 5).astype(np.float32)

        stats = trainer.train(X, y, epochs=3, batch_size=32, verbose=False)

        assert stats["steps"] > 0
        assert len(stats["losses"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
