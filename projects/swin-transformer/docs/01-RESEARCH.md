# Research: Swin Transformer

## Overview

Swin Transformer (Shifted Window Transformer) is a hierarchical Vision Transformer architecture introduced by Microsoft Research Asia in 2021. It addresses the limitations of the original Vision Transformer (ViT) for dense prediction tasks like object detection and semantic segmentation.

**Paper:** "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows"
**Authors:** Ze Liu, Yutong Lin, Yue Cao, Han Hu, Yixuan Wei, Zheng Zhang, Stephen Lin, Baining Guo
**Published:** ICCV 2021 (Best Paper Award)
**arXiv:** 2103.14030

## Key Innovations

### 1. Hierarchical Feature Maps

Unlike ViT which produces a single-scale feature map, Swin Transformer builds hierarchical feature maps similar to CNNs:

```
Stage 1: 56x56 (1/4 resolution)
Stage 2: 28x28 (1/8 resolution)
Stage 3: 14x14 (1/16 resolution)
Stage 4: 7x7 (1/32 resolution)
```

This hierarchical structure makes it suitable for:
- Object detection (FPN, Mask R-CNN)
- Semantic segmentation (FCN, UperNet)
- Instance segmentation
- Other dense prediction tasks

### 2. Window-based Self-Attention

**Problem with ViT:** Global self-attention has quadratic complexity O(n²) with respect to the number of patches, making it computationally expensive for high-resolution images.

**Solution:** Compute self-attention within local windows of fixed size (e.g., 7x7):
- Divide feature map into non-overlapping windows
- Compute attention only within each window
- Complexity reduces to O(n) (linear)

**Example:**
- Image size: 224x224, Patch size: 4x4
- Number of patches: 56x56 = 3136
- Global attention: 3136² = 9,834,496 operations
- Window attention (7x7): 3136 × 49 = 153,664 operations (64x reduction!)

### 3. Shifted Window Mechanism

**Problem with Window Attention:** Windows are non-overlapping, so there's no information flow between windows.

**Solution:** Shift windows by half the window size between consecutive layers:

```
Layer 1 (Regular):     Layer 2 (Shifted):
+---+---+---+---+      +-----+-----+-----+
| 1 | 2 | 3 | 4 |      |  A  |  B  |  C  |
+---+---+---+---+      +-----+-----+-----+
| 5 | 6 | 7 | 8 |      |  D  |  E  |  F  |
+---+---+---+---+      +-----+-----+-----+
| 9 |10 |11 |12 |      |  G  |  H  |  I  |
+---+---+---+---+      +-----+-----+-----+
|13 |14 |15 |16 |      |  J  |  K  |  L  |
+---+---+---+---+      +-----+-----+-----+
```

This enables cross-window connections while maintaining linear complexity.

### 4. Efficient Batch Computation for Shifted Windows

The shifted window partitioning creates windows of different sizes at the borders. Instead of padding, Swin Transformer uses a clever cyclic-shift approach:

1. Shift the feature map cyclically
2. Apply attention mask to prevent cross-region attention
3. This allows efficient batch computation with standard window sizes

## Architecture Comparison

### ViT vs Swin Transformer

| Aspect | ViT | Swin Transformer |
|--------|-----|------------------|
| Feature Maps | Single-scale | Multi-scale (hierarchical) |
| Attention | Global | Local (window-based) |
| Complexity | O(n²) | O(n) |
| Position Encoding | Absolute | Relative position bias |
| Dense Prediction | Limited | Excellent |
| Pre-training | Large datasets needed | Works with smaller datasets |

### Swin Transformer Variants

| Model | Embed Dim | Depths | Heads | Params |
|-------|-----------|--------|-------|--------|
| Swin-T | 96 | 2,2,6,2 | 3,6,12,24 | 28M |
| Swin-S | 96 | 2,2,18,2 | 3,6,12,24 | 50M |
| Swin-B | 128 | 2,2,18,2 | 4,8,16,32 | 88M |
| Swin-L | 192 | 2,2,18,2 | 6,12,24,48 | 197M |

## Performance

### ImageNet Classification (Top-1 Accuracy)

| Model | Resolution | Pre-train | ImageNet |
|-------|------------|-----------|----------|
| Swin-T | 224 | ImageNet-1K | 81.3% |
| Swin-S | 224 | ImageNet-1K | 83.0% |
| Swin-B | 224 | ImageNet-1K | 83.5% |
| Swin-B | 384 | ImageNet-22K | 86.4% |
| Swin-L | 384 | ImageNet-22K | 87.3% |

### COCO Object Detection

| Model | Backbone | AP (box) | AP (mask) |
|-------|----------|----------|-----------|
| Cascade Mask R-CNN | Swin-T | 50.4 | 43.7 |
| Cascade Mask R-CNN | Swin-S | 51.9 | 45.0 |
| Cascade Mask R-CNN | Swin-B | 53.0 | 46.0 |
| HTC++ | Swin-L | 58.7 | 51.1 |

### ADE20K Semantic Segmentation

| Model | Backbone | mIoU |
|-------|----------|------|
| UperNet | Swin-T | 44.5 |
| UperNet | Swin-S | 47.6 |
| UperNet | Swin-B | 48.1 |
| UperNet | Swin-L | 53.5 |

## Related Work

### Vision Transformers

1. **ViT (2020):** First pure transformer for image classification
2. **DeiT (2021):** Data-efficient training of ViT
3. **PVT (2021):** Pyramid Vision Transformer
4. **Twins (2021):** Spatially separable self-attention
5. **CSwin (2022):** Cross-shaped windows

### Window Attention Variants

1. **Swin Transformer V2 (2022):** Improved training stability and efficiency
2. **Focal Transformer (2021):** Focal attention with fine-grained and coarse attention
3. **Shunted Transformer (2022):** Multi-scale token merging

## Key Takeaways

1. **Hierarchical design** is crucial for dense prediction tasks
2. **Window attention** reduces complexity from quadratic to linear
3. **Shifted windows** enable cross-window information flow
4. **Relative position bias** is more effective than absolute position encoding
5. **Swin Transformer** has become a standard backbone for vision tasks

## References

1. [Original Paper](https://arxiv.org/abs/2103.14030)
2. [GitHub Repository](https://github.com/microsoft/Swin-Transformer)
3. [Swin Transformer V2](https://arxiv.org/abs/2111.09883)
