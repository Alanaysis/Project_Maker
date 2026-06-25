# Implementation Details

## Overview

This document details the implementation of the image denoising system, focusing on key algorithms and design decisions.

## DnCNN Implementation

### Convolutional Blocks

```python
# First layer: Feature extraction
Conv2d(in_channels, num_features, kernel_size=3, padding=1) + ReLU

# Middle layers: Deep processing
[Conv2d(num_features, num_features, kernel_size=3, padding=1) + BatchNorm2d + ReLU] × (depth - 2)

# Last layer: Noise prediction
Conv2d(num_features, out_channels, kernel_size=3, padding=1)
```

**Key Points:**
- All convolutions use 3×3 kernels with padding=1 (same padding)
- No pooling layers (preserve spatial resolution)
- Batch normalization after each middle convolution
- ReLU activation (in-place for memory efficiency)

### Weight Initialization

```python
def _initialize_weights(self):
    for m in self.modules():
        if isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.BatchNorm2d):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)
```

**Rationale:**
- Kaiming initialization designed for ReLU activations
- Initializes weights based on fan-out mode
- Batch normalization initialized to identity transformation

### Residual Learning

The key innovation of DnCNN is predicting noise instead of clean images:

```python
def denoise(self, x):
    noise = self.forward(x)
    return x - noise
```

**Benefits:**
- Easier to learn noise patterns than image content
- Better gradient flow
- Works well with batch normalization

## Noise Generation

### Gaussian Noise

```python
def add_gaussian_noise(image, sigma=25.0):
    noise = np.random.randn(*image.shape) * (sigma / 255.0)
    noisy = image + noise
    return np.clip(noisy, 0, 1), noise
```

**Design Decisions:**
- Sigma in [0, 255] scale (standard convention)
- Divide by 255 for [0, 1] range images
- Clip output to valid range

### Noise Generator Class

```python
class NoiseGenerator:
    def __init__(self, noise_type, sigma_range, fixed_sigma=None):
        self.noise_type = noise_type
        self.sigma_range = sigma_range
        self.fixed_sigma = fixed_sigma

    def __call__(self, image, sigma=None):
        if sigma is None:
            sigma = self.get_random_sigma()
        return self._noise_fn(image, sigma=sigma)
```

**Features:**
- Configurable noise type
- Random or fixed noise levels
- Consistent interface for all noise types

## Dataset Implementation

### Patch Extraction

```python
def _extract_patch(self, image):
    _, h, w = image.shape
    top = np.random.randint(0, h - self.patch_size + 1)
    left = np.random.randint(0, w - self.patch_size + 1)
    return image[:, top:top+patch_size, left:left+patch_size]
```

**Benefits:**
- Reduces memory requirements
- Increases effective dataset size
- Allows training on larger images

### Data Augmentation

```python
def _augment(self, clean, noisy):
    # Random horizontal flip
    if np.random.rand() > 0.5:
        clean = clean[:, :, ::-1]
        noisy = noisy[:, :, ::-1]

    # Random vertical flip
    if np.random.rand() > 0.5:
        clean = clean[:, ::-1, :]
        noisy = noisy[:, ::-1, :]

    # Random 90-degree rotation
    k = np.random.randint(0, 4)
    if k > 0:
        clean = np.rot90(clean, k, axes=(1, 2))
        noisy = np.rot90(noisy, k, axes=(1, 2))

    return clean, noisy
```

**Important:** Augmentation must be applied consistently to both clean and noisy images.

## Training Implementation

### Loss Function

```python
# MSE loss for noise prediction
criterion = nn.MSELoss()

# Forward pass
noise_pred = model(noisy_image)
loss = criterion(noise_pred, actual_noise)
```

**Why MSE for noise prediction:**
- Directly measures noise estimation accuracy
- Differentiable and easy to optimize
- Works well with residual learning

### Optimizer Configuration

```python
optimizer = optim.Adam(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-5,  # L2 regularization
)
```

**Adam Benefits:**
- Adaptive learning rates
- Fast convergence
- Works well with default parameters

### Learning Rate Scheduling

```python
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode='min',
    factor=0.5,
    patience=5,
)
```

**Strategy:**
- Reduce LR when validation loss plateaus
- Multiply LR by factor (0.5)
- Wait for patience epochs before reducing

### Training Loop

```python
for epoch in range(num_epochs):
    # Train
    model.train()
    for noisy, clean, noise in train_loader:
        noise_pred = model(noisy)
        loss = criterion(noise_pred, noise)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # Validate
    model.eval()
    with torch.no_grad():
        val_loss, val_psnr, val_ssim = validate(val_loader)

    # Update scheduler
    scheduler.step(val_loss)

    # Save best model
    if val_loss < best_val_loss:
        save_checkpoint()
```

## Evaluation Implementation

### PSNR Calculation

```python
def calculate_psnr(image1, image2, data_range=1.0):
    mse = np.mean((image1 - image2) ** 2)
    if mse == 0:
        return float('inf')
    return 10 * np.log10(data_range ** 2 / mse)
```

**Formula:**
```
PSNR = 10 × log₁₀(MAX² / MSE)
```

### SSIM Calculation

```python
def calculate_ssim(image1, image2, window_size=7):
    # Calculate local means
    mu1 = uniform_filter(image1, size=window_size)
    mu2 = uniform_filter(image2, size=window_size)

    # Calculate local variances and covariance
    sigma1_sq = uniform_filter(image1**2) - mu1**2
    sigma2_sq = uniform_filter(image2**2) - mu2**2
    sigma12 = uniform_filter(image1 * image2) - mu1 * mu2

    # SSIM formula
    numerator = (2*mu1*mu2 + c1) * (2*sigma12 + c2)
    denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)

    return np.mean(numerator / denominator)
```

**SSIM Components:**
1. **Luminance**: Comparison of mean intensities
2. **Contrast**: Comparison of variances
3. **Structure**: Comparison of normalized patterns

## Inference Implementation

### Tiled Processing

For large images that don't fit in memory:

```python
def _denoise_tiled(self, image, tile_size=256, overlap=32):
    c, h, w = image.shape
    stride = tile_size - overlap

    output = np.zeros_like(image)
    weight_map = np.zeros((1, h, w))

    for i in range(n_tiles_h):
        for j in range(n_tiles_w):
            # Extract tile
            tile = image[:, top:bottom, left:right]

            # Denoise tile
            denoised_tile = self._denoise_single(tile)

            # Blend with weight map
            output[:, top:bottom, left:right] += denoised_tile * weight
            weight_map[:, top:bottom, left:right] += weight

    return output / weight_map
```

**Blending Strategy:**
- Use higher weights in tile center
- Taper weights at edges
- Smooth overlap between tiles

### Batch Processing

```python
def denoise_batch(self, images, batch_size=8):
    results = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        batch_tensor = torch.stack(batch)
        denoised = model(batch_tensor)
        results.extend(denoised)
    return results
```

## Error Handling

### Input Validation

```python
def validate_input(image):
    if not isinstance(image, (np.ndarray, torch.Tensor)):
        raise TypeError("Input must be numpy array or torch tensor")

    if image.ndim not in [2, 3]:
        raise ValueError("Input must be 2D or 3D array")

    if isinstance(image, np.ndarray) and image.dtype == np.uint8:
        # Convert to float
        image = image.astype(np.float32) / 255.0
```

### Shape Handling

```python
def normalize_shape(image):
    if image.ndim == 2:
        # [H, W] -> [1, H, W]
        return image[np.newaxis, :]

    if image.ndim == 3 and image.shape[2] in [1, 3, 4]:
        # [H, W, C] -> [C, H, W]
        return np.transpose(image, (2, 0, 1))

    return image
```

## Performance Optimization

### Memory Efficiency
- Use in-place ReLU operations
- Gradient checkpointing for very deep models
- Patch-based training instead of full images

### Computational Efficiency
- Batch normalization for faster convergence
- No spatial pooling (preserve resolution)
- Efficient tensor operations

### GPU Acceleration
```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
inputs = inputs.to(device)
```

## Testing Strategy

### Unit Tests
- Test each component independently
- Verify output shapes and value ranges
- Check edge cases and error handling

### Integration Tests
- Test complete training pipeline
- Verify checkpoint save/load
- Test inference on various image sizes

### Performance Tests
- Measure training speed
- Benchmark inference latency
- Compare with reference implementations
