#!/usr/bin/env python3
"""
Basic Data Parallel Training Example
======================================

This example demonstrates the core data parallel training loop:
1. Create a simple model
2. Split data across GPUs (simulated)
3. Compute gradients on each GPU
4. AllReduce to synchronize gradients
5. Update parameters

Usage:
    python examples/basic_training.py
"""

import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tensor import GPUTensor, get_device
from src.core.data_parallel import SimpleModel, DataParallelTrainer
from src.utils.logger import setup_logger


def generate_data(n_samples: int = 500, input_dim: int = 16, output_dim: int = 4):
    """Generate synthetic linear regression data."""
    np.random.seed(42)
    X = np.random.randn(n_samples, input_dim).astype(np.float32)
    w_true = np.random.randn(input_dim, output_dim).astype(np.float32)
    y = X @ w_true + 0.1 * np.random.randn(n_samples, output_dim).astype(np.float32)
    return X, y, w_true


def main():
    logger = setup_logger("basic_training")

    # Configuration
    INPUT_DIM = 16
    HIDDEN_DIM = 32
    OUTPUT_DIM = 4
    NUM_GPUS = 4
    LEARNING_RATE = 0.001
    EPOCHS = 10
    BATCH_SIZE = 32

    logger.info("=" * 60)
    logger.info("BASIC DATA PARALLEL TRAINING EXAMPLE")
    logger.info("=" * 60)

    # 1. Generate data
    logger.info("\n[Step 1] Generating synthetic data...")
    X, y, w_true = generate_data(500, INPUT_DIM, OUTPUT_DIM)
    logger.info(f"  Data shape: X={X.shape}, y={y.shape}")
    logger.info(f"  True weights shape: {w_true.shape}")

    # 2. Create trainer with data parallelism
    logger.info(f"\n[Step 2] Creating DataParallelTrainer with {NUM_GPUS} GPUs...")
    trainer = DataParallelTrainer(
        model_fn=lambda device: SimpleModel(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, device),
        world_size=NUM_GPUS,
        learning_rate=LEARNING_RATE,
        backend="simulation",
        allreduce_algo="ring",
    )

    # 3. Train
    logger.info(f"\n[Step 3] Training for {EPOCHS} epochs...")
    logger.info(f"  Batch size: {BATCH_SIZE}")
    logger.info(f"  Learning rate: {LEARNING_RATE}")
    logger.info(f"  AllReduce algorithm: Ring")
    logger.info("")

    stats = trainer.train(X, y, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=True)

    # 4. Print results
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING RESULTS")
    logger.info("=" * 60)
    logger.info(f"  Total steps: {stats['steps']}")
    logger.info(f"  Final loss: {stats['losses'][-1]:.6f}")
    logger.info(f"  Initial loss: {stats['losses'][0]:.6f}")
    logger.info(f"  Loss reduction: {(1 - stats['losses'][-1]/stats['losses'][0])*100:.1f}%")
    logger.info(f"  Total time: {stats['total_time']:.3f}s")
    logger.info(f"  Communication time: {stats['comm_time']:.3f}s")
    logger.info(f"  Communication overhead: {stats['comm_percentage']:.1f}%")

    # 5. Verify all models are synchronized
    logger.info("\n[Step 5] Verifying model synchronization...")
    model0_params = trainer.models[0].get_params_and_grads()
    all_synced = True
    for rank in range(1, NUM_GPUS):
        model_r_params = trainer.models[rank].get_params_and_grads()
        for (p0, _), (pr, _) in zip(model0_params, model_r_params):
            if not np.allclose(p0.data, pr.data, atol=1e-5):
                all_synced = False
                break

    if all_synced:
        logger.info("  All models are synchronized! (as expected after AllReduce)")
    else:
        logger.warning("  WARNING: Models are NOT synchronized!")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
