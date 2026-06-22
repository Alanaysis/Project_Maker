"""
Verification Script

This script verifies that the ViT/CLIP training framework can run correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

def test_vit():
    """Test Vision Transformer."""
    print("Testing Vision Transformer...")
    from src.models.vit import VisionTransformer, create_vit

    # Test with small model
    model = create_vit("vit_small", image_size=224, patch_size=16)
    x = torch.randn(2, 3, 224, 224)

    # Forward pass
    output = model(x)
    print(f"  Input shape: {x.shape}")
    print(f"  Output shape: {output.shape}")
    assert output.shape == (2, 1000), f"Expected (2, 1000), got {output.shape}"

    # Feature extraction
    features = model(x, return_features=True)
    print(f"  Features shape: {features.shape}")
    assert features.shape == (2, 384), f"Expected (2, 384), got {features.shape}"

    # Gradient check
    loss = output.sum()
    loss.backward()
    print("  Gradient check passed!")

    print("✓ Vision Transformer test passed!\n")
    return True


def test_text_encoder():
    """Test Text Encoder."""
    print("Testing Text Encoder...")
    from src.models.text_encoder import TextTransformer

    model = TextTransformer(vocab_size=49408, max_seq_len=77, embed_dim=512, depth=6, num_heads=8)
    tokens = torch.randint(0, 49408, (2, 77))

    # Forward pass
    output = model(tokens)
    print(f"  Input shape: {tokens.shape}")
    print(f"  Output shape: {output.shape}")
    assert output.shape == (2, 512), f"Expected (2, 512), got {output.shape}"

    print("✓ Text Encoder test passed!\n")
    return True


def test_clip():
    """Test CLIP Model."""
    print("Testing CLIP Model...")
    from src.models.clip import CLIPModel, create_clip_model

    model = create_clip_model(
        "vit_b32",
        image_size=224,
    )

    images = torch.randn(2, 3, 224, 224)
    texts = torch.randint(0, 49408, (2, 77))

    # Forward pass
    outputs = model(images, texts)

    print(f"  Logits shape: {outputs['logits_per_image'].shape}")
    print(f"  Image embeddings shape: {outputs['image_embeddings'].shape}")
    print(f"  Text embeddings shape: {outputs['text_embeddings'].shape}")
    print(f"  Loss: {outputs['loss'].item():.4f}")

    # Check shapes
    assert outputs['logits_per_image'].shape == (2, 2)
    assert outputs['image_embeddings'].shape == (2, 512)
    assert outputs['text_embeddings'].shape == (2, 512)

    # Gradient check
    outputs['loss'].backward()
    print("  Gradient check passed!")

    print("✓ CLIP Model test passed!\n")
    return True


def test_contrastive_loss():
    """Test Contrastive Loss."""
    print("Testing Contrastive Loss...")
    from src.losses.contrastive import CLIPLoss, ContrastiveLoss, SupConLoss, NTXentLoss

    # Test CLIPLoss
    loss_fn = CLIPLoss(temperature=0.07)
    image_features = torch.randn(8, 128)
    text_features = torch.randn(8, 128)
    loss = loss_fn(image_features, text_features)
    print(f"  CLIPLoss: {loss.item():.4f}")
    assert loss.item() > 0

    # Test ContrastiveLoss
    loss_fn = ContrastiveLoss(temperature=0.07)
    features = torch.randn(8, 128)
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    loss = loss_fn(features, labels)
    print(f"  ContrastiveLoss: {loss.item():.4f}")
    assert loss.item() > 0

    # Test SupConLoss
    loss_fn = SupConLoss(temperature=0.07)
    loss = loss_fn(features, labels)
    print(f"  SupConLoss: {loss.item():.4f}")
    assert loss.item() > 0

    # Test NTXentLoss
    loss_fn = NTXentLoss(temperature=0.5)
    z_i = torch.randn(8, 128)
    z_j = torch.randn(8, 128)
    loss = loss_fn(z_i, z_j)
    print(f"  NTXentLoss: {loss.item():.4f}")
    assert loss.item() > 0

    print("✓ Contrastive Loss test passed!\n")
    return True


def test_dataset():
    """Test Dataset."""
    print("Testing Dataset...")
    from src.data.dataset import SyntheticDataset, create_dataloader

    # Test synthetic dataset
    dataset = SyntheticDataset(num_samples=100, image_size=224)
    image, text = dataset[0]
    print(f"  Image shape: {image.shape}")
    print(f"  Text shape: {text.shape}")

    # Test dataloader
    dataloader = create_dataloader(dataset, batch_size=8, num_workers=0)
    batch_images, batch_texts = next(iter(dataloader))
    print(f"  Batch image shape: {batch_images.shape}")
    print(f"  Batch text shape: {batch_texts.shape}")

    print("✓ Dataset test passed!\n")
    return True


def test_metrics():
    """Test Metrics."""
    print("Testing Metrics...")
    from src.utils.metrics import CLIPMetrics, compute_retrieval_metrics

    # Create synthetic embeddings
    image_features = torch.randn(50, 512)
    text_features = torch.randn(50, 512)

    # Add some correlation
    for i in range(50):
        text_features[i] = image_features[i] + torch.randn(512) * 0.3

    # Compute retrieval metrics
    i2t_metrics, t2i_metrics = compute_retrieval_metrics(image_features, text_features)

    print(f"  I2T Recall@1: {i2t_metrics.recall_at_1:.4f}")
    print(f"  I2T Recall@5: {i2t_metrics.recall_at_5:.4f}")
    print(f"  T2I Recall@1: {t2i_metrics.recall_at_1:.4f}")
    print(f"  T2I Recall@5: {t2i_metrics.recall_at_5:.4f}")

    print("✓ Metrics test passed!\n")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("ViT/CLIP Training Framework Verification")
    print("=" * 60)
    print()

    tests = [
        test_vit,
        test_text_encoder,
        test_clip,
        test_contrastive_loss,
        test_dataset,
        test_metrics,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
