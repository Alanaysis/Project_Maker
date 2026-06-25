# Architecture: Swin Transformer

## Overview

This document describes the architecture of our Swin Transformer implementation. The design follows the original paper while being clean and educational.

## Core Pipeline

```
Image (224x224x3)
    ↓
Patch Embedding (4x4 patches → 96-dim embeddings)
    ↓
Stage 1: 2x ShiftedWindowTransformerBlock (56x56, dim=96)
    ↓
Patch Merging (56x56 → 28x28, dim=192)
    ↓
Stage 2: 2x ShiftedWindowTransformerBlock (28x28, dim=192)
    ↓
Patch Merging (28x28 → 14x14, dim=384)
    ↓
Stage 3: 6x ShiftedWindowTransformerBlock (14x14, dim=384)
    ↓
Patch Merging (14x14 → 7x7, dim=768)
    ↓
Stage 4: 2x ShiftedWindowTransformerBlock (7x7, dim=768)
    ↓
Layer Norm → Global Average Pooling
    ↓
Classification Head (768 → num_classes)
```

## Module Structure

```
projects/swin-transformer/
├── src/
│   ├── __init__.py
│   ├── patch_embedding.py      # Patch embedding and merging
│   ├── window_attention.py     # Window-based self-attention
│   ├── shifted_window.py       # Shifted window transformer block
│   └── swin_transformer.py     # Main model
├── tests/
│   └── test_swin_transformer.py
└── examples/
    └── example_usage.py
```

## Detailed Component Design

### 1. PatchEmbedding

**Purpose:** Convert input image into patch embeddings.

**Input:** (B, C, H, W) - Batch of images
**Output:** (B, num_patches, embed_dim) - Patch embeddings

**Implementation:**
```python
class PatchEmbedding(nn.Module):
    def __init__(self, img_size, patch_size, in_channels, embed_dim):
        # Use Conv2d with kernel_size=stride=patch_size
        self.projection = nn.Conv2d(in_channels, embed_dim, 
                                     kernel_size=patch_size, 
                                     stride=patch_size)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, x):
        x = self.projection(x)  # (B, C, H, W) -> (B, embed_dim, H/p, W/p)
        x = x.flatten(2)        # -> (B, embed_dim, num_patches)
        x = x.transpose(1, 2)   # -> (B, num_patches, embed_dim)
        x = self.norm(x)
        return x
```

**Key Points:**
- Conv2d with stride=patch_size creates non-overlapping patches
- Layer normalization stabilizes training
- No learnable position embedding (relative position bias in attention)

### 2. PatchMerging

**Purpose:** Downsample feature maps between stages (2x reduction).

**Input:** (B, H*W, C)
**Output:** (B, H/2*W/2, 2*C)

**Implementation:**
```python
class PatchMerging(nn.Module):
    def forward(self, x):
        # Reshape to 2D
        x = x.view(B, H, W, C)
        
        # Extract 2x2 patches
        x0 = x[:, 0::2, 0::2, :]  # Top-left
        x1 = x[:, 1::2, 0::2, :]  # Bottom-left
        x2 = x[:, 0::2, 1::2, :]  # Top-right
        x3 = x[:, 1::2, 1::2, :]  # Bottom-right
        
        # Concatenate and project
        x = torch.cat([x0, x1, x2, x3], dim=-1)  # 4*C
        x = self.norm(x)
        x = self.reduction(x)  # 4*C -> 2*C
        return x
```

**Key Points:**
- Non-overlapping 2x2 patch merging
- Doubles feature dimension while halving spatial resolution
- Creates hierarchical feature maps

### 3. WindowAttention

**Purpose:** Compute self-attention within local windows.

**Input:** (B * num_windows, window_size * window_size, C)
**Output:** (B * num_windows, window_size * window_size, C)

**Implementation:**
```python
class WindowAttention(nn.Module):
    def __init__(self, dim, window_size, num_heads):
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2*Wh-1) * (2*Ww-1), num_heads)
        )
        self.qkv = nn.Linear(dim, dim * 3)
    
    def forward(self, x, mask=None):
        # QKV projection
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)
        
        # Attention scores
        attn = q @ k.transpose(-2, -1) * scale
        
        # Add relative position bias
        attn += relative_position_bias
        
        # Optional mask for shifted windows
        if mask is not None:
            attn += mask
        
        # Softmax and apply to values
        attn = softmax(attn)
        out = attn @ v
        
        return self.proj(out)
```

**Key Points:**
- Multi-head attention within windows
- Relative position bias (learnable)
- Optional attention mask for shifted windows
- Linear complexity O(n) instead of O(n²)

### 4. ShiftedWindowTransformerBlock

**Purpose:** Complete transformer block with window attention.

**Input:** (B, H*W, C)
**Output:** (B, H*W, C)

**Implementation:**
```python
class ShiftedWindowTransformerBlock(nn.Module):
    def __init__(self, dim, input_resolution, num_heads, 
                 window_size, shift_size):
        self.norm1 = nn.LayerNorm(dim)
        self.attn = WindowAttention(dim, window_size, num_heads)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = MLP(dim, dim * mlp_ratio)
        
        if shift_size > 0:
            self._compute_attention_mask()
    
    def forward(self, x):
        # Shortcut
        shortcut = x
        
        # Window attention
        x = self.norm1(x)
        x = x.view(B, H, W, C)
        
        # Cyclic shift for shifted window
        if self.shift_size > 0:
            x = torch.roll(x, (-shift_size, -shift_size), (1, 2))
        
        # Window partition and attention
        windows = window_partition(x, window_size)
        attn_windows = self.attn(windows, mask)
        x = window_reverse(attn_windows, window_size, H, W)
        
        # Reverse cyclic shift
        if self.shift_size > 0:
            x = torch.roll(x, (shift_size, shift_size), (1, 2))
        
        # Residual connection
        x = shortcut + x.view(B, H*W, C)
        
        # MLP with residual
        x = x + self.mlp(self.norm2(x))
        
        return x
```

**Key Points:**
- Alternating regular/shifted window attention
- Cyclic shift with attention mask
- Pre-norm architecture (LayerNorm before attention)
- Residual connections

### 5. SwinTransformer

**Purpose:** Complete model for image classification.

**Input:** (B, C, H, W) - Batch of images
**Output:** (B, num_classes) - Classification logits

**Implementation:**
```python
class SwinTransformer(nn.Module):
    def __init__(self, img_size, patch_size, embed_dim, 
                 depths, num_heads, window_size, num_classes):
        self.patch_embed = PatchEmbedding(img_size, patch_size, embed_dim)
        
        self.layers = nn.ModuleList()
        for i in range(len(depths)):
            stage = SwinTransformerStage(
                dim=embed_dim * 2**i,
                depth=depths[i],
                num_heads=num_heads[i],
                window_size=window_size,
                downsample=PatchMerging if i < len(depths)-1 else None,
            )
            self.layers.append(stage)
        
        self.norm = nn.LayerNorm(final_dim)
        self.head = nn.Linear(final_dim, num_classes)
    
    def forward(self, x):
        x = self.patch_embed(x)
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x)
        x = x.mean(dim=1)  # Global average pooling
        x = self.head(x)
        return x
```

**Key Points:**
- Hierarchical feature extraction
- Patch merging between stages
- Global average pooling for classification
- Configurable depths and dimensions

## Data Flow

### Forward Pass

```
Input: (B, 3, 224, 224)
    ↓
PatchEmbedding:
    - Conv2d(3, 96, kernel=4, stride=4)
    - (B, 96, 56, 56)
    - Flatten: (B, 3136, 96)
    ↓
Stage 1 (2 blocks, window=7):
    - Input: (B, 3136, 96)
    - Reshape: (B, 56, 56, 96)
    - Window partition: (B*64, 49, 96)
    - Attention: (B*64, 49, 96)
    - Window reverse: (B, 56, 56, 96)
    - Reshape: (B, 3136, 96)
    ↓
PatchMerging:
    - Input: (B, 3136, 96)
    - Reshape: (B, 56, 56, 96)
    - Extract 2x2 patches: (B, 28, 28, 384)
    - Linear: (B, 28, 28, 192)
    - Flatten: (B, 784, 192)
    ↓
Stage 2 (2 blocks, window=7):
    - Input: (B, 784, 192)
    - Similar to Stage 1
    ↓
PatchMerging:
    - (B, 784, 192) → (B, 196, 384)
    ↓
Stage 3 (6 blocks, window=7):
    - Input: (B, 196, 384)
    - Similar processing
    ↓
PatchMerging:
    - (B, 196, 384) → (B, 49, 768)
    ↓
Stage 4 (2 blocks, window=7):
    - Input: (B, 49, 768)
    - Final processing
    ↓
Layer Norm:
    - (B, 49, 768) → (B, 49, 768)
    ↓
Global Average Pooling:
    - (B, 49, 768) → (B, 768)
    ↓
Classification Head:
    - (B, 768) → (B, num_classes)
```

### Backward Pass

Gradients flow through:
1. Classification head
2. Global average pooling
3. Layer norm
4. Each stage (in reverse order)
5. Patch merging
6. Patch embedding
7. Input image

## Design Decisions

### 1. Relative Position Bias vs Absolute Position Encoding

**Decision:** Use relative position bias (learnable)

**Rationale:**
- More flexible than fixed absolute positions
- Better generalization to different input sizes
- Used in the original Swin Transformer paper

### 2. Pre-norm vs Post-norm

**Decision:** Pre-norm (LayerNorm before attention/MLP)

**Rationale:**
- More stable training
- Better gradient flow
- Standard in modern transformers

### 3. Window Size

**Decision:** Default window_size=7

**Rationale:**
- Good balance between local and global context
- Efficient computation
- Used in original paper

### 4. Shift Size

**Decision:** shift_size = window_size // 2

**Rationale:**
- Maximum overlap between windows
- Enables cross-window information flow
- Standard in Swin Transformer

### 5. Patch Merging vs Strided Convolution

**Decision:** Patch merging (concatenate + linear)

**Rationale:**
- More parameter efficient
- Better preserves spatial information
- Used in original paper

## Complexity Analysis

### Time Complexity

**Window Attention:**
- Let N = H * W (number of patches)
- Let w = window_size
- Let C = embedding dimension
- Let h = number of heads

**Per Window:**
- QKV projection: O(w² × C)
- Attention: O(w² × w² × C) = O(w⁴ × C)
- Total per window: O(w⁴ × C)

**All Windows:**
- Number of windows: N / w²
- Total: O(N × w² × C)

**Compared to Global Attention:**
- Global: O(N² × C)
- Window: O(N × w² × C)
- Speedup: N / w²

**Example (224x224 image, w=7):**
- N = 3136
- Global: 3136² = 9.8M
- Window: 3136 × 49 = 153K
- **64x speedup!**

### Space Complexity

**Window Attention:**
- Attention matrix per window: O(w⁴)
- Total: O(N × w²)

**Compared to Global Attention:**
- Global: O(N²)
- Window: O(N × w²)
- **N / w² reduction**

## Trade-offs

### Advantages

1. **Efficiency:** Linear complexity for high-resolution images
2. **Hierarchy:** Multi-scale feature maps for dense prediction
3. **Flexibility:** Configurable depths, dimensions, window sizes
4. **Performance:** State-of-the-art on multiple benchmarks

### Limitations

1. **Window boundary:** Information flow limited by window size
2. **Shifted window:** Adds complexity for cross-window connections
3. **Fixed window size:** May not be optimal for all tasks
4. **Memory:** Still requires significant memory for high-resolution images

## Future Improvements

1. **Dynamic window size:** Adapt window size based on input
2. **Sparse attention:** Combine with sparse attention patterns
3. **Multi-scale windows:** Use different window sizes in parallel
4. **Efficient implementation:** Optimize CUDA kernels for window operations
