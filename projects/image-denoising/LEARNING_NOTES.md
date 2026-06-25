# Learning Notes - Image Denoising

## Key Concepts Learned

### 1. Image Denoising Fundamentals

**What is Image Denoising?**
- Recovering clean image from noisy observation
- Ill-posed problem: infinite possible solutions
- Requires prior knowledge about image/noise characteristics

**Noise Models:**
- Gaussian: Additive, signal-independent (most common)
- Salt & Pepper: Random black/white pixels
- Poisson: Signal-dependent, common in low-light
- Speckle: Multiplicative, in coherent imaging

### 2. DnCNN Architecture

**Key Innovation: Residual Learning**
```
Instead of: Noisy → Clean (difficult)
Learn: Noisy → Noise (easier)
Then: Clean = Noisy - Predicted_Noise
```

**Why Residual Learning Works:**
1. Noise patterns are simpler than image content
2. Better gradient flow through network
3. Works well with batch normalization

**Architecture Details:**
- 17 convolutional layers
- No pooling (preserve spatial info)
- Batch normalization for stability
- 3×3 kernels with same padding

### 3. Training Techniques

**Loss Function:**
- MSE between predicted and actual noise
- Directly optimizes noise estimation

**Optimizer:**
- Adam with weight decay (L2 regularization)
- Adaptive learning rates

**Learning Rate Scheduling:**
- ReduceLROnPlateau: Reduce when validation loss plateaus
- Helps converge to better minima

**Data Augmentation:**
- Random flips and rotations
- Applied consistently to clean/noisy pairs
- Increases effective dataset size

### 4. Evaluation Metrics

**PSNR (Peak Signal-to-Noise Ratio):**
```
PSNR = 10 × log₁₀(MAX² / MSE)
```
- Higher is better
- Typical range: 20-40 dB
- Simple but not perceptually meaningful

**SSIM (Structural Similarity Index):**
```
SSIM = (2μ₁μ₂ + c₁)(2σ₁₂ + c₂) / ((μ₁² + μ₂² + c₁)(σ₁² + σ₂² + c₂))
```
- Range: [-1, 1], higher is better
- Considers luminance, contrast, structure
- More perceptually meaningful

### 5. Implementation Insights

**Noise Addition:**
```python
# Sigma in [0, 255] scale, divide for [0, 1] images
noise = np.random.randn(*shape) * (sigma / 255.0)
noisy = clean + noise
```

**Weight Initialization:**
```python
# Kaiming initialization for ReLU networks
nn.init.kaiming_normal_(weight, mode='fan_out', nonlinearity='relu')
```

**Batch Normalization:**
- Stabilizes training
- Reduces internal covariate shift
- Allows higher learning rates

## Challenges and Solutions

### Challenge 1: Understanding Residual Learning

**Problem:** Why predict noise instead of clean image?

**Solution:**
- Noise patterns are simpler and more consistent
- Clean images have complex, varied structures
- Residual learning provides better gradient flow
- Empirically shown to converge faster

### Challenge 2: Noise Level Selection

**Problem:** What noise levels to train on?

**Solution:**
- Train on range of noise levels (5-50)
- Random sigma per sample during training
- Fixed sigma for validation
- Test on multiple levels for evaluation

### Challenge 3: Large Image Processing

**Problem:** Images too large for GPU memory

**Solution:**
- Patch-based training (random crops)
- Tiled inference with blending
- Overlap between tiles for smooth results

### Challenge 4: Evaluation Consistency

**Problem:** Metrics vary with random noise

**Solution:**
- Use fixed random seeds for reproducibility
- Average over multiple samples
- Report mean and standard deviation

## Code Patterns Learned

### Pattern 1: Factory Function

```python
def create_model(model_type, **kwargs):
    if model_type == "dncnn":
        return DnCNN(**kwargs)
    elif model_type == "dncnn_light":
        return DnCNNLight(**kwargs)
    else:
        raise ValueError(f"Unknown: {model_type}")
```

**Benefits:**
- Clean interface
- Easy to extend
- Centralized creation logic

### Pattern 2: Configurable Generator

```python
class NoiseGenerator:
    NOISE_FUNCTIONS = {"gaussian": add_gaussian_noise, ...}

    def __call__(self, image, sigma=None):
        sigma = sigma or self.get_random_sigma()
        return self._noise_fn(image, sigma=sigma)
```

**Benefits:**
- Flexible configuration
- Consistent interface
- Easy to add new types

### Pattern 3: Metric Tracking

```python
class MetricTracker:
    def __init__(self, window_size=100):
        self.history = {}
        self._windows = {}

    def update(self, metrics):
        for name, value in metrics.items():
            self.history[name].append(value)
            self._windows[name].append(value)
            # Keep window size limited
```

**Benefits:**
- Moving average for smooth tracking
- Historical data for analysis
- Clean summary interface

## PyTorch Best Practices

### 1. Device Management

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
inputs = inputs.to(device)
```

### 2. Training Mode

```python
model.train()  # Enable dropout, batchnorm
model.eval()   # Disable dropout, batchnorm
```

### 3. Gradient Management

```python
optimizer.zero_grad()  # Clear gradients
loss.backward()        # Compute gradients
optimizer.step()       # Update weights
```

### 4. No Gradient Context

```python
with torch.no_grad():
    # Inference code (saves memory)
    output = model(input)
```

### 5. Mixed Precision (Optional)

```python
scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    output = model(input)
    loss = criterion(output, target)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

## Mathematics Behind DnCNN

### 1. Noise Model

```
y = x + n
```
Where:
- y: noisy image
- x: clean image
- n: noise

### 2. Residual Learning

Network learns R(y) ≈ n

Denoised image: x̂ = y - R(y)

### 3. Loss Function

```
L = (1/N) Σᵢ ||R(yᵢ) - nᵢ||²
```

Where nᵢ = yᵢ - xᵢ (actual noise)

### 4. Gradient Flow

```
∂L/∂θ = (2/N) Σᵢ (R(yᵢ) - nᵢ) × ∂R(yᵢ)/∂θ
```

Direct gradient path from loss to all parameters.

## Performance Optimization Tips

### 1. Data Loading

```python
DataLoader(
    dataset,
    batch_size=16,
    num_workers=4,      # Parallel loading
    pin_memory=True,    # Faster GPU transfer
    prefetch_factor=2,  # Prefetch batches
)
```

### 2. Model Optimization

```python
# Compile model (PyTorch 2.0+)
model = torch.compile(model)

# Use channels_last memory format
model = model.to(memory_format=torch.channels_last)
```

### 3. Training Optimization

```python
# Gradient accumulation
for i, (inputs, targets) in enumerate(loader):
    outputs = model(inputs)
    loss = criterion(outputs, targets) / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## Future Learning Paths

### 1. Advanced Architectures
- FFDNet: Fast and flexible denoising
- NAFNet: Nonlinear activation free network
- SwinIR: Swin transformer for restoration

### 2. Self-Supervised Methods
- Noise2Noise: No clean data needed
- Noise2Void: Single image training
- Noise2Self: Self-supervised approach

### 3. Real-World Applications
- Medical imaging denoising
- Low-light photography
- Astronomical image processing
- Video denoising

### 4. Deployment
- ONNX export
- TensorRT optimization
- Mobile deployment (TFLite, Core ML)

## Resources

### Papers
1. Zhang et al., "Beyond a Gaussian Denoiser," IEEE TIP 2017
2. Lehtinen et al., "Noise2Noise," ICML 2018
3. Krull et al., "Noise2Void," CVPR 2019

### Tutorials
- PyTorch Image Denoising Tutorial
- Deep Learning for Image Denoising (Stanford CS231n)

### Code References
- [Official DnCNN implementation](https://github.com/cszn/DnCNN)
- [PyTorch examples](https://github.com/pytorch/examples)
