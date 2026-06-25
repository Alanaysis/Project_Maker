"""Example usage of Swin Transformer.

This script demonstrates how to use the Swin Transformer implementation
for image classification, including:
1. Model creation
2. Forward pass
3. Feature extraction
4. Understanding the architecture
"""

import sys
sys.path.insert(0, "/home/siok/project_copyninja/projects/swin-transformer")

import torch
from src.swin_transformer import (
    SwinTransformer,
    swin_tiny_patch4_window7_224,
    swin_small_patch4_window7_224,
    swin_base_patch4_window7_224,
)


def example_basic_usage():
    """Basic usage example."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Create a Swin-Tiny model for 10-class classification
    model = swin_tiny_patch4_window7_224(num_classes=10)

    # Create a dummy input image (batch_size=1, channels=3, height=224, width=224)
    x = torch.randn(1, 3, 224, 224)

    # Forward pass
    output = model(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output (logits): {output}")


def example_feature_extraction():
    """Feature extraction example."""
    print("\n" + "=" * 60)
    print("Example 2: Feature Extraction")
    print("=" * 60)

    model = swin_tiny_patch4_window7_224(num_classes=10)

    x = torch.randn(1, 3, 224, 224)

    # Extract features (before classification head)
    features = model.forward_features(x)

    print(f"Input shape: {x.shape}")
    print(f"Feature shape: {features.shape}")
    print(f"Feature dimension: {features.shape[1]}")

    # You can use these features for downstream tasks
    # like object detection, segmentation, etc.


def example_different_model_sizes():
    """Compare different model sizes."""
    print("\n" + "=" * 60)
    print("Example 3: Different Model Sizes")
    print("=" * 60)

    configs = {
        "Swin-Tiny": swin_tiny_patch4_window7_224,
        "Swin-Small": swin_small_patch4_window7_224,
        "Swin-Base": swin_base_patch4_window7_224,
    }

    x = torch.randn(1, 3, 224, 224)

    for name, model_fn in configs.items():
        model = model_fn(num_classes=10)
        output = model(x)

        total_params = sum(p.numel() for p in model.parameters())

        print(f"\n{name}:")
        print(f"  Parameters: {total_params:,}")
        print(f"  Output shape: {output.shape}")


def example_custom_model():
    """Custom model configuration example."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Model Configuration")
    print("=" * 60)

    # Create a custom Swin Transformer
    model = SwinTransformer(
        img_size=64,  # Smaller input size
        patch_size=4,
        in_channels=3,
        num_classes=100,  # 100 classes
        embed_dim=64,  # Smaller embedding dimension
        depths=(2, 2, 2),  # Fewer stages
        num_heads=(2, 4, 8),
        window_size=4,
        mlp_ratio=2.0,
    )

    x = torch.randn(2, 3, 64, 64)
    output = model(x)

    print(f"Custom model configuration:")
    print(f"  Image size: 64x64")
    print(f"  Patch size: 4")
    print(f"  Embedding dim: 64")
    print(f"  Stages: 3 (depths: (2, 2, 2))")
    print(f"  Window size: 4")
    print(f"\nInput shape: {x.shape}")
    print(f"Output shape: {output.shape}")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total_params:,}")


def example_architecture_details():
    """Show architecture details."""
    print("\n" + "=" * 60)
    print("Example 5: Architecture Details")
    print("=" * 60)

    model = swin_tiny_patch4_window7_224(num_classes=10)

    print("\nModel Architecture:")
    print("-" * 40)

    # Count parameters by layer
    total_params = 0
    for name, param in model.named_parameters():
        total_params += param.numel()

    print(f"Total parameters: {total_params:,}")

    # Show model structure
    print("\nModel Structure:")
    print("-" * 40)

    # Patch embedding
    print(f"Patch Embedding:")
    print(f"  - Image size: 224x224")
    print(f"  - Patch size: 4x4")
    print(f"  - Num patches: {model.patch_embed.num_patches}")
    print(f"  - Embedding dim: 96")

    # Stages
    print(f"\nStages:")
    for i, layer in enumerate(model.layers):
        if hasattr(layer, 'downsample') and layer.downsample is not None:
            downsample = "with downsampling"
        else:
            downsample = "no downsampling"
        print(f"  Stage {i}: {layer.depth} blocks, {downsample}")


def example_window_attention():
    """Demonstrate window attention mechanism."""
    print("\n" + "=" * 60)
    print("Example 6: Window Attention Mechanism")
    print("=" * 60)

    from src.window_attention import window_partition, window_reverse

    # Create a small feature map
    B, H, W, C = 1, 8, 8, 96
    x = torch.randn(B, H, W, C)

    print(f"Original feature map: {x.shape}")

    # Partition into windows
    window_size = 4
    windows = window_partition(x, window_size)
    print(f"After window partition: {windows.shape}")

    num_windows = windows.shape[0]
    print(f"Number of windows: {num_windows}")
    print(f"Window size: {window_size}x{window_size}")

    # Reverse window partition
    x_reconstructed = window_reverse(windows, window_size, H, W)
    print(f"After window reverse: {x_reconstructed.shape}")

    # Verify reconstruction
    assert torch.allclose(x, x_reconstructed), "Window partition should be reversible"
    print("Window partition is reversible!")


def example_shifted_window():
    """Demonstrate shifted window mechanism."""
    print("\n" + "=" * 60)
    print("Example 7: Shifted Window Mechanism")
    print("=" * 60)

    from src.shifted_window import ShiftedWindowTransformerBlock

    # Create a block with regular window attention
    print("\nRegular Window Attention (shift_size=0):")
    block_regular = ShiftedWindowTransformerBlock(
        dim=96,
        input_resolution=(8, 8),
        num_heads=3,
        window_size=4,
        shift_size=0,  # Regular window
    )

    x = torch.randn(1, 64, 96)
    output_regular = block_regular(x)
    print(f"  Input: {x.shape}")
    print(f"  Output: {output_regular.shape}")

    # Create a block with shifted window attention
    print("\nShifted Window Attention (shift_size=2):")
    block_shifted = ShiftedWindowTransformerBlock(
        dim=96,
        input_resolution=(8, 8),
        num_heads=3,
        window_size=4,
        shift_size=2,  # Shifted window
    )

    output_shifted = block_shifted(x)
    print(f"  Input: {x.shape}")
    print(f"  Output: {output_shifted.shape}")

    print("\nShifted window enables cross-window information flow!")


def example_batch_processing():
    """Batch processing example."""
    print("\n" + "=" * 60)
    print("Example 8: Batch Processing")
    print("=" * 60)

    model = swin_tiny_patch4_window7_224(num_classes=10)
    model.eval()

    # Process multiple images at once
    batch_sizes = [1, 4, 8, 16]

    for batch_size in batch_sizes:
        x = torch.randn(batch_size, 3, 224, 224)

        with torch.no_grad():
            output = model(x)

        print(f"Batch size {batch_size:2d}: input {x.shape} -> output {output.shape}")


def main():
    """Run all examples."""
    print("Swin Transformer Examples")
    print("=" * 60)

    example_basic_usage()
    example_feature_extraction()
    example_different_model_sizes()
    example_custom_model()
    example_architecture_details()
    example_window_attention()
    example_shifted_window()
    example_batch_processing()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
