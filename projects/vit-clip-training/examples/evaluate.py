"""
CLIP Evaluation Example

This script demonstrates how to evaluate a trained CLIP model.

⭐ Evaluation Tasks:
1. Image-to-Text Retrieval
2. Text-to-Image Retrieval
3. Zero-shot Classification
4. Representation Quality Analysis

💡 Key Metrics:
- Recall@K (R@1, R@5, R@10)
- Median Rank
- Zero-shot Accuracy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import logging

from src.models.clip import CLIPModel, create_clip_model
from src.utils.metrics import CLIPMetrics, compute_retrieval_metrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def demo_retrieval_metrics():
    """Demonstrate retrieval metrics computation."""
    logger.info("=" * 60)
    logger.info("CLIP Evaluation Demo")
    logger.info("=" * 60)

    # Create synthetic embeddings
    batch_size = 50
    embed_dim = 512

    logger.info(f"\nCreating synthetic embeddings...")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Embedding dim: {embed_dim}")

    # Simulate image and text embeddings
    # In practice, these would come from the CLIP model
    image_features = torch.randn(batch_size, embed_dim)
    text_features = torch.randn(batch_size, embed_dim)

    # Add some correlation between matching pairs
    # This simulates a partially trained model
    for i in range(batch_size):
        noise = torch.randn(embed_dim) * 0.5
        text_features[i] = image_features[i] + noise

    # Compute retrieval metrics
    logger.info("\nComputing retrieval metrics...")
    metrics = CLIPMetrics()

    i2t_metrics, t2i_metrics = metrics.compute_retrieval(
        image_features, text_features
    )

    logger.info("\nImage-to-Text Retrieval:")
    logger.info(f"  {i2t_metrics}")

    logger.info("\nText-to-Image Retrieval:")
    logger.info(f"  {t2i_metrics}")

    # Compute similarity distribution
    logger.info("\nSimilarity Distribution:")
    dist = metrics.compute_similarity_distribution(
        image_features, text_features
    )
    logger.info(f"  Positive mean: {dist['positive_mean']:.4f}")
    logger.info(f"  Positive std: {dist['positive_std']:.4f}")
    logger.info(f"  Negative mean: {dist['negative_mean']:.4f}")
    logger.info(f"  Negative std: {dist['negative_std']:.4f}")
    logger.info(f"  Gap: {dist['gap']:.4f}")

    return i2t_metrics, t2i_metrics


def demo_zero_shot_classification():
    """Demonstrate zero-shot classification."""
    logger.info("\n" + "=" * 60)
    logger.info("Zero-shot Classification Demo")
    logger.info("=" * 60)

    # Setup
    num_classes = 10
    num_samples = 100
    embed_dim = 512

    logger.info(f"\nSetup:")
    logger.info(f"  Classes: {num_classes}")
    logger.info(f"  Samples: {num_samples}")
    logger.info(f"  Embedding dim: {embed_dim}")

    # Create class embeddings (simulating text encoder)
    class_features = torch.randn(num_classes, embed_dim)
    class_features = torch.nn.functional.normalize(class_features, dim=1)

    # Create image embeddings with some matching to classes
    image_features = torch.randn(num_samples, embed_dim)
    labels = torch.randint(0, num_classes, (num_samples,))

    # Make some images match their class
    for i in range(num_samples):
        if torch.rand(1).item() > 0.5:  # 50% match
            noise = torch.randn(embed_dim) * 0.3
            image_features[i] = class_features[labels[i]] + noise

    # Compute zero-shot accuracy
    metrics = CLIPMetrics()
    results = metrics.compute_zero_shot_accuracy(
        image_features, class_features, labels
    )

    logger.info("\nZero-shot Results:")
    logger.info(f"  Top-1 Accuracy: {results['accuracy']:.4f}")
    logger.info(f"  Top-5 Accuracy: {results['top5_accuracy']:.4f}")

    return results


def demo_model_inference():
    """Demonstrate model inference."""
    logger.info("\n" + "=" * 60)
    logger.info("Model Inference Demo")
    logger.info("=" * 60)

    # Create a small model for demo
    logger.info("\nCreating CLIP model...")
    model = create_clip_model(
        config="vit_b32",
        image_size=224,
    )
    model.eval()

    # Create dummy inputs
    batch_size = 4
    images = torch.randn(batch_size, 3, 224, 224)
    texts = torch.randint(0, 49408, (batch_size, 77))

    logger.info(f"  Image shape: {images.shape}")
    logger.info(f"  Text shape: {texts.shape}")

    # Forward pass
    logger.info("\nRunning inference...")
    with torch.no_grad():
        outputs = model(images, texts, return_loss=True)

    logger.info("\nOutputs:")
    logger.info(f"  Logits shape: {outputs['logits_per_image'].shape}")
    logger.info(f"  Image embeddings shape: {outputs['image_embeddings'].shape}")
    logger.info(f"  Text embeddings shape: {outputs['text_embeddings'].shape}")
    logger.info(f"  Loss: {outputs['loss'].item():.4f}")

    # Compute similarity
    similarity = outputs['logits_per_image']
    logger.info("\nSimilarity Matrix:")
    logger.info(f"  Shape: {similarity.shape}")
    logger.info(f"  Mean: {similarity.mean().item():.4f}")
    logger.info(f"  Std: {similarity.std().item():.4f}")

    return outputs


def main():
    """Run all evaluation demos."""
    # Demo retrieval metrics
    demo_retrieval_metrics()

    # Demo zero-shot classification
    demo_zero_shot_classification()

    # Demo model inference
    demo_model_inference()

    logger.info("\n" + "=" * 60)
    logger.info("Evaluation Demo Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
