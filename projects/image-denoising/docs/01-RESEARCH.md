# Image Denoising Research

## Overview

Image denoising is a fundamental problem in image processing that aims to recover a clean image from a noisy observation. This document covers the research background and key concepts.

## Noise Models

### 1. Gaussian Noise

The most common noise model in image processing.

**Mathematical Model:**
```
y = x + n, where n ~ N(0, σ²I)
```

- **Source**: Sensor noise, thermal noise, electronic noise
- **Characteristics**: Additive, signal-independent, zero-mean
- **Parameter**: σ (standard deviation) controls noise intensity

### 2. Salt & Pepper Noise

Also known as impulse noise.

**Mathematical Model:**
```
y(i,j) = 0 with probability p/2 (pepper)
y(i,j) = 1 with probability p/2 (salt)
y(i,j) = x(i,j) with probability 1-p
```

- **Source**: Transmission errors, dead pixels
- **Characteristics**: Random black and white pixels

### 3. Poisson Noise

Signal-dependent noise, common in low-light imaging.

**Mathematical Model:**
```
y ~ Poisson(x)
```

- **Source**: Photon counting, low-light conditions
- **Characteristics**: Signal-dependent, increases with intensity

### 4. Speckle Noise

Multiplicative noise in coherent imaging systems.

**Mathematical Model:**
```
y = x + x·n, where n ~ N(0, σ²)
```

- **Source**: SAR imaging, ultrasound, laser imaging
- **Characteristics**: Multiplicative, signal-dependent

## Traditional Denoising Methods

### 1. Spatial Domain Filters

| Method | Description | Pros | Cons |
|--------|-------------|------|------|
| Mean Filter | Average of local pixels | Simple, fast | Blurs edges |
| Median Filter | Median of local pixels | Preserves edges | Slow for large windows |
| Gaussian Filter | Weighted average | Smooth results | Blurs edges |

### 2. Transform Domain Methods

| Method | Description | Pros | Cons |
|--------|-------------|------|------|
| Wavelet Thresholding | Threshold wavelet coefficients | Multi-scale analysis | Ringing artifacts |
| BM3D | Block matching in 3D transform domain | State-of-the-art quality | Computationally expensive |
| NLM | Non-local means | Preserves details | Slow |

### 3. Optimization-Based Methods

| Method | Description | Pros | Cons |
|--------|-------------|------|------|
| TV Denoising | Total variation regularization | Preserves edges | Staircase effect |
| Dictionary Learning | Sparse representation | Adaptive | Requires training |

## Deep Learning Methods

### 1. Supervised Learning

| Method | Year | Architecture | Key Innovation |
|--------|------|--------------|----------------|
| DnCNN | 2017 | CNN + Residual Learning | Predict noise instead of image |
| FFDNet | 2018 | CNN with noise level map | Handle varying noise levels |
| RED | 2016 | CNN + Prior | Combine CNN with optimization |
| MemNet | 2017 | CNN + Memory | Long-term dependencies |

### 2. Unsupervised/Self-Supervised Learning

| Method | Year | Approach |
|--------|------|----------|
| Noise2Noise | 2018 | Train with noisy pairs only |
| Noise2Void | 2019 | Blind spot network |
| Noise2Self | 2019 | Self-supervised denoising |
| Noise2Fast | 2020 | Fast self-supervised |

## DnCNN Architecture

### Key Innovations

1. **Residual Learning**: Instead of learning to map noisy → clean, learn to predict the noise
   ```
   Denoised = Noisy - Predicted_Noise
   ```

2. **Deep Architecture**: 17 convolutional layers with batch normalization

3. **No Pooling**: Preserve spatial information (no downsampling)

### Architecture Details

```
Input: Noisy image y [B, C, H, W]

Layer 1: Conv2d(C, 64, 3×3) + ReLU
  → Feature extraction

Layers 2-16: [Conv2d(64, 64, 3×3) + BN + ReLU] × 15
  → Deep feature processing

Layer 17: Conv2d(64, C, 3×3)
  → Noise prediction

Output: Predicted noise R(y) [B, C, H, W]

Denoised image: x̂ = y - R(y)
```

### Loss Function

Training uses Mean Squared Error between predicted and actual noise:
```
L = (1/N) Σ ||R(yᵢ) - (yᵢ - xᵢ)||²
```

Where:
- R(yᵢ) is predicted noise
- yᵢ - xᵢ is actual noise
- N is number of training samples

## Evaluation Metrics

### 1. PSNR (Peak Signal-to-Noise Ratio)

```
PSNR = 10 · log₁₀(MAX² / MSE)
```

- Higher is better
- Typical range: 20-40 dB for denoising
- Unit: dB (decibels)

### 2. SSIM (Structural Similarity Index)

```
SSIM(x, y) = (2μₓμᵧ + c₁)(2σₓᵧ + c₂) / ((μₓ² + μᵧ² + c₁)(σₓ² + σᵧ² + c₂))
```

- Range: [-1, 1], higher is better
- Considers luminance, contrast, and structure
- More perceptually meaningful than PSNR

### 3. LPIPS (Learned Perceptual Image Patch Similarity)

- Uses deep features for comparison
- Better correlation with human perception
- Lower is better

## Benchmark Datasets

| Dataset | Description | Usage |
|---------|-------------|-------|
| BSD68 | 68 natural images | Standard benchmark |
| Set12 | 12 test images | Quick evaluation |
| CBSD68 | Color BSD68 | Color denoising |
| Urban100 | 100 urban images | Structure preservation |
| Kodak24 | 24 color images | Color denoising |

## State-of-the-Art Results

Typical PSNR (dB) on BSD68 dataset:

| Method | σ=15 | σ=25 | σ=50 |
|--------|------|------|------|
| BM3D | 31.07 | 28.57 | 25.62 |
| DnCNN | 31.73 | 29.23 | 26.23 |
| FFDNet | 31.63 | 29.19 | 26.29 |
| NAFNet | 31.81 | 29.32 | 26.39 |

## References

1. Zhang et al., "Beyond a Gaussian Denoiser: Residual Learning of Deep CNN for Image Denoising," IEEE TIP 2017
2. Lehtinen et al., "Noise2Noise: Learning Image Restoration without Clean Data," ICML 2018
3. Krull et al., "Noise2Void - Learning Denoising from Single Noisy Images," CVPR 2019
4. Dabov et al., "Image Denoising by Sparse 3-D Transform-Domain Collaborative Filtering," IEEE TIP 2007
