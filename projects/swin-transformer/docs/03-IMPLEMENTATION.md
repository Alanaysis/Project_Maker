# Implementation: Swin Transformer

## Overview

This document describes the implementation details of our Swin Transformer. We focus on clarity and educational value while maintaining correctness.

## Implementation Strategy

### Phase 1: Core Components

1. **PatchEmbedding** - Convert images to patch embeddings
2. **WindowAttention** - Window-based self-attention
3. **ShiftedWindowTransformerBlock** - Complete transformer block
4. **SwinTransformer** - Full model

### Phase 2: Utilities

1. **window_partition** - Partition feature map into windows
2. **window_reverse** - Reverse window partition
3. **PatchMerging** - Downsample between stages

### Phase 3: Model Variants

1. **swin_tiny_patch4_window7_224** - Smallest variant
2. **swin_small_patch4_window7_224** - Medium variant
3. **swin_base_patch4_window7_224** - Large variant

## Detailed Implementation

### 1. Window Partition

**Challenge:** Efficiently partition feature map into non-overlapping windows.

**Solution:** Use tensor reshaping and permutation.

```python
def window_partition(x: torch.Tensor, window_size: int) -> torch.Tensor:
    """Partition input tensor into non-overlapping windows."""
    B, H, W, C = x.shape
    
    # Reshape to (B, H//w, w, W//w, w, C)
    x = x.view(B, H // window_size, window_size, 
                W // window_size, window_size, C)
    
    # Permute to (B, H//w, W//w, w, w, C)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
    
    # Flatten to (B * num_windows, w, w, C)
    x = x.view(-1, window_size, window_size, C)
    
    return x
```

**Key Points:**
- `view` creates non-overlapping windows
- `permute` rearranges to desired format
- `contiguous()` ensures memory layout for efficient operations
- `view(-1, ...)` flattens batch and window dimensions

### 2. Window Reverse

**Challenge:** Reverse window partition to original format.

**Solution:** Reverse the partition operations.

```python
def window_reverse(windows: torch.Tensor, window_size: int, 
                   H: int, W: int) -> torch.Tensor:
    """Reverse window partition to original tensor format."""
    B = int(windows.shape[0] / (H * W / window_size / window_size))
    
    # Reshape to (B, H//w, W//w, w, w, C)
    x = windows.view(B, H // window_size, W // window_size, 
                      window_size, window_size, -1)
    
    # Permute to (B, H//w, w, W//w, w, C)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
    
    # Reshape to (B, H, W, C)
    x = x.view(B, H, W, -1)
    
    return x
```

**Key Points:**
- Reverse permutation and reshaping
- Must match the exact operations of window_partition
- `contiguous()` for efficient memory access

### 3. Relative Position Bias

**Challenge:** Encode relative positions between tokens in a window.

**Solution:** Learnable bias table with index mapping.

```python
class WindowAttention(nn.Module):
    def __init__(self, dim, window_size, num_heads):
        # Bias table: (2*Wh-1) * (2*Ww-1), num_heads
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), 
                        num_heads)
        )
        
        # Compute index mapping
        self._compute_relative_position_index()
    
    def _compute_relative_position_index(self):
        Wh, Ww = self.window_size
        
        # Create coordinate grids
        coords_h = torch.arange(Wh)
        coords_w = torch.arange(Ww)
        coords = torch.stack(torch.meshgrid([coords_h, coords_w], indexing="ij"))
        coords_flatten = torch.flatten(coords, 1)  # (2, Wh*Ww)
        
        # Compute relative coordinates
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        
        # Shift to start from 0
        relative_coords[:, :, 0] += Wh - 1
        relative_coords[:, :, 1] += Ww - 1
        
        # Flatten to 1D index
        relative_coords[:, :, 0] *= 2 * Ww - 1
        relative_position_index = relative_coords.sum(-1)
        
        self.register_buffer("relative_position_index", relative_position_index)
```

**Key Points:**
- Bias table is learnable
- Index mapping is fixed (buffer, not parameter)
- Supports arbitrary window sizes
- Initialized with small values (trunc_normal_)

### 4. Shifted Window Attention

**Challenge:** Enable cross-window information flow while maintaining efficiency.

**Solution:** Cyclic shift with attention mask.

```python
class ShiftedWindowTransformerBlock(nn.Module):
    def _compute_attention_mask(self):
        H, W = self.input_resolution
        window_size = self.window_size
        shift_size = self.shift_size
        
        # Create region map
        img_mask = torch.zeros((1, H, W, 1))
        h_slices = (
            slice(0, -window_size),
            slice(-window_size, -shift_size),
            slice(-shift_size, None),
        )
        w_slices = (
            slice(0, -window_size),
            slice(-window_size, -shift_size),
            slice(-shift_size, None),
        )
        
        # Assign region IDs
        cnt = 0
        for h in h_slices:
            for w in w_slices:
                img_mask[:, h, w, :] = cnt
                cnt += 1
        
        # Partition into windows
        mask_windows = window_partition(img_mask, window_size)
        mask_windows = mask_windows.view(-1, window_size * window_size)
        
        # Compute attention mask
        attn_mask = mask_windows.unsqueeze(1) - mask_windows.unsqueeze(2)
        attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0))
        attn_mask = attn_mask.masked_fill(attn_mask == 0, float(0.0))
        
        self.register_buffer("attn_mask", attn_mask)
    
    def forward(self, x):
        # Cyclic shift
        if self.shift_size > 0:
            shifted_x = torch.roll(x, (-self.shift_size, -self.shift_size), (1, 2))
        
        # Window partition
        x_windows = window_partition(shifted_x, self.window_size)
        
        # Window attention with mask
        attn_windows = self.attn(x_windows, mask=self.attn_mask)
        
        # Window reverse
        shifted_x = window_reverse(attn_windows, self.window_size, H, W)
        
        # Reverse cyclic shift
        if self.shift_size > 0:
            x = torch.roll(shifted_x, (self.shift_size, self.shift_size), (1, 2))
```

**Key Points:**
- Cyclic shift moves border regions together
- Attention mask prevents cross-region attention
- Mask is precomputed (buffer) for efficiency
- Alternating regular/shifted in consecutive blocks

### 5. Patch Merging

**Challenge:** Downsample feature maps while increasing channels.

**Solution:** Extract 2x2 patches and concatenate.

```python
class PatchMerging(nn.Module):
    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        
        # Reshape to 2D
        x = x.view(B, H, W, C)
        
        # Extract 2x2 patches
        x0 = x[:, 0::2, 0::2, :]  # Top-left
        x1 = x[:, 1::2, 0::2, :]  # Bottom-left
        x2 = x[:, 0::2, 1::2, :]  # Top-right
        x3 = x[:, 1::2, 1::2, :]  # Bottom-right
        
        # Concatenate: 4*C channels
        x = torch.cat([x0, x1, x2, x3], dim=-1)
        
        # Normalize and project: 4*C -> 2*C
        x = self.norm(x)
        x = self.reduction(x)
        
        return x
```

**Key Points:**
- Non-overlapping 2x2 patches
- Concatenation preserves spatial information
- Linear projection reduces dimensionality
- Layer normalization for stability

### 6. Complete Model

**Challenge:** Combine all components into a coherent model.

**Solution:** Modular design with clear data flow.

```python
class SwinTransformer(nn.Module):
    def __init__(self, img_size, patch_size, embed_dim, 
                 depths, num_heads, window_size, num_classes):
        super().__init__()
        
        # Patch embedding
        self.patch_embed = PatchEmbedding(
            img_size=img_size,
            patch_size=patch_size,
            embed_dim=embed_dim,
        )
        
        # Build stages
        self.layers = nn.ModuleList()
        for i_layer in range(len(depths)):
            # Calculate dimension and resolution
            stage_dim = int(embed_dim * 2 ** i_layer)
            stage_resolution = (
                patches_resolution // (2 ** i_layer),
                patches_resolution // (2 ** i_layer),
            )
            
            # Downsample layer (except last stage)
            if i_layer < len(depths) - 1:
                downsample = PatchMerging(
                    input_resolution=stage_resolution,
                    dim=stage_dim,
                )
            else:
                downsample = None
            
            # Create stage
            stage = SwinTransformerStage(
                dim=stage_dim,
                input_resolution=stage_resolution,
                depth=depths[i_layer],
                num_heads=num_heads[i_layer],
                window_size=window_size,
                downsample=downsample,
            )
            self.layers.append(stage)
        
        # Final layers
        self.norm = nn.LayerNorm(self.num_features)
        self.avgpool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(self.num_features, num_classes)
    
    def forward(self, x):
        # Patch embedding
        x = self.patch_embed(x)
        
        # Process through stages
        for layer in self.layers:
            x = layer(x)
        
        # Classification
        x = self.norm(x)
        x = self.avgpool(x.transpose(1, 2)).flatten(1)
        x = self.head(x)
        
        return x
```

## Training Considerations

### 1. Initialization

```python
def _init_weights(self, m):
    if isinstance(m, nn.Linear):
        nn.init.trunc_normal_(m.weight, std=0.02)
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    elif isinstance(m, nn.LayerNorm):
        nn.init.constant_(m.bias, 0)
        nn.init.constant_(m.weight, 1.0)
```

**Key Points:**
- Truncated normal initialization for linear layers
- Zero bias initialization
- Standard LayerNorm initialization

### 2. Optimizer

**Recommended:** AdamW with weight decay

```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=0.05,
    betas=(0.9, 0.999),
)
```

### 3. Learning Rate Schedule

**Recommended:** Cosine annealing with warmup

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=num_epochs,
    eta_min=1e-6,
)
```

### 4. Data Augmentation

**Recommended:**
- Random resized crop
- Random horizontal flip
- Color jitter
- Mixup / CutMix
- Random erasing

### 5. Regularization

**Recommended:**
- Dropout (0.0 - 0.3)
- Stochastic depth (0.1 - 0.3)
- Label smoothing (0.1)
- Weight decay (0.05)

## Performance Optimization

### 1. Mixed Precision Training

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

with autocast():
    output = model(x)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 2. Gradient Accumulation

```python
accumulation_steps = 4

for i, (x, y) in enumerate(dataloader):
    with autocast():
        output = model(x)
        loss = criterion(output, y) / accumulation_steps
    
    scaler.scale(loss).backward()
    
    if (i + 1) % accumulation_steps == 0:
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
```

### 3. Distributed Training

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group("nccl")
model = DDP(model.to(local_rank), device_ids=[local_rank])
```

## Debugging Tips

### 1. Shape Mismatches

```python
def forward(self, x):
    print(f"Input: {x.shape}")
    x = self.patch_embed(x)
    print(f"After patch_embed: {x.shape}")
    for i, layer in enumerate(self.layers):
        x = layer(x)
        print(f"After stage {i}: {x.shape}")
    return x
```

### 2. Gradient Issues

```python
# Check gradient flow
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm={param.grad.norm():.4f}")
    else:
        print(f"{name}: no gradient!")
```

### 3. Memory Issues

```python
# Monitor memory usage
print(f"Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"Cached: {torch.cuda.memory_reserved() / 1e9:.2f} GB")
```

## Testing Strategy

### 1. Unit Tests

- Test each component individually
- Verify output shapes
- Check gradient flow
- Test edge cases

### 2. Integration Tests

- Test complete forward pass
- Verify end-to-end training
- Check determinism in eval mode

### 3. Performance Tests

- Measure throughput (images/second)
- Compare with reference implementation
- Profile memory usage

## Common Pitfalls

### 1. Window Size vs Resolution

**Problem:** Window size doesn't divide feature map resolution.

**Solution:** Ensure input resolution is divisible by window_size * 2^(num_stages-1).

### 2. Shift Size

**Problem:** Invalid shift size causes errors.

**Solution:** Ensure 0 <= shift_size < window_size.

### 3. Memory Layout

**Problem:** Non-contiguous tensors cause errors.

**Solution:** Call `.contiguous()` after permute operations.

### 4. Attention Mask

**Problem:** Incorrect mask causes wrong attention patterns.

**Solution:** Verify mask computation with small examples.

## Future Improvements

### 1. Sparse Attention

Combine window attention with sparse attention patterns for global context.

### 2. Dynamic Window Size

Adapt window size based on input resolution or task requirements.

### 3. Multi-Scale Windows

Use multiple window sizes in parallel for better feature extraction.

### 4. Efficient Kernels

Implement custom CUDA kernels for window operations.

### 5. Model Compression

Apply pruning, quantization, or knowledge distillation.
