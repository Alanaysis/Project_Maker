"""Example: Training CLIP model on synthetic data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from src.clip_model import CLIP
from src.trainer import CLIPTrainer
from src.dataset import SyntheticDataset, create_dataloader


def main():
    # Model configuration
    model_config = {
        "embed_dim": 256,
        "image_hidden_dim": 128,
        "text_hidden_dim": 128,
        "vocab_size": 10000,
        "text_num_heads": 4,
        "text_num_layers": 4,
        "max_seq_length": 77,
        "temperature": 0.07,
        "learnable_temperature": True,
    }

    # Create model
    model = CLIP(**model_config)

    # Print model info
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )
    print(f"Model created with {total_params:,} parameters")
    print(f"Trainable parameters: {trainable_params:,}")

    # Create synthetic datasets
    train_dataset = SyntheticDataset(
        num_samples=100,
        vocab_size=model_config["vocab_size"],
    )
    val_dataset = SyntheticDataset(
        num_samples=20,
        vocab_size=model_config["vocab_size"],
    )

    # Create dataloaders
    train_loader = create_dataloader(train_dataset, batch_size=8, shuffle=True)
    val_loader = create_dataloader(val_dataset, batch_size=8, shuffle=False)

    # Create trainer
    trainer = CLIPTrainer(
        model=model,
        learning_rate=1e-4,
        weight_decay=0.01,
        device="auto",
    )

    # Train
    print("\nStarting training...")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=3,
        log_interval=5,
    )

    print("\nTraining completed!")
    print(f"Final loss: {history['history'][-1]['loss']:.4f}")

    # Test inference
    print("\nTesting inference...")
    model.eval()
    with torch.no_grad():
        # Create dummy inputs
        images = torch.randn(4, 3, 224, 224)
        input_ids = torch.randint(0, 10000, (4, 77))

        # Get embeddings
        image_embeds = model.encode_image(images)
        text_embeds = model.encode_text(input_ids)

        # Compute similarity
        similarity = model.get_similarity(images, input_ids)

        print(f"Image embeddings shape: {image_embeds.shape}")
        print(f"Text embeddings shape: {text_embeds.shape}")
        print(f"Similarity matrix shape: {similarity.shape}")
        print(f"\nSimilarity matrix:\n{similarity.numpy().round(3)}")


if __name__ == "__main__":
    main()
