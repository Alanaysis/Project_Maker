# Testing Guide

## Overview

This document describes the testing strategy and test cases for the image denoising system.

## Test Structure

```
tests/
├── test_model.py       # DnCNN model tests
├── test_noise.py       # Noise generation tests
└── test_evaluate.py    # Evaluation metrics tests
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_model.py -v
pytest tests/test_noise.py -v
pytest tests/test_evaluate.py -v
```

### Run Specific Test

```bash
pytest tests/test_model.py::TestDnCNN::test_model_creation -v
```

## Test Cases

### Model Tests (`test_model.py`)

#### TestDnCNN

| Test | Description | Expected |
|------|-------------|----------|
| `test_model_creation` | Create model with default params | Model instance created |
| `test_model_forward` | Forward pass produces correct shape | Output shape == Input shape |
| `test_model_denoise` | Denoise method subtracts noise | denoise(x) == x - forward(x) |
| `test_rgb_channels` | Model works with RGB images | Output shape matches input |
| `test_batch_processing` | Process batches correctly | Batch dimension preserved |
| `test_different_depths` | Various network depths work | All depths produce valid output |
| `test_parameter_count` | Parameters increase with depth | More layers = more parameters |
| `test_kaiming_initialization` | Weights initialized properly | Non-zero weight values |

#### TestDnCNNLight

| Test | Description | Expected |
|------|-------------|----------|
| `test_model_creation` | Create lightweight model | Model instance created |
| `test_fewer_parameters` | Light model has fewer params | light_params < standard_params |
| `test_forward_pass` | Forward pass works | Output shape matches input |

#### TestCreateModel

| Test | Description | Expected |
|------|-------------|----------|
| `test_create_dncnn` | Create DnCNN model | Returns DnCNN instance |
| `test_create_dncnn_light` | Create light model | Returns DnCNNLight instance |
| `test_invalid_model_type` | Invalid type raises error | ValueError raised |

### Noise Tests (`test_noise.py`)

#### TestGaussianNoise

| Test | Description | Expected |
|------|-------------|----------|
| `test_numpy_input` | Works with numpy arrays | Correct output shape |
| `test_torch_input` | Works with PyTorch tensors | Correct output shape |
| `test_noise_level` | Noise std matches sigma | std ≈ sigma/255 |
| `test_clipping` | Output clipped to [0,1] | Values in valid range |
| `test_no_clipping` | Output not clipped when disabled | Values may exceed [0,1] |

#### TestSaltPepperNoise

| Test | Description | Expected |
|------|-------------|----------|
| `test_numpy_input` | Works with numpy arrays | Correct output shape |
| `test_torch_input` | Works with PyTorch tensors | Correct output shape |
| `test_noise_amount` | Correct proportion corrupted | ~amount pixels changed |
| `test_salt_pepper_values` | Correct salt/pepper values | Salt=1.0, Pepper=0.0 |

#### TestSpeckleNoise

| Test | Description | Expected |
|------|-------------|----------|
| `test_basic_functionality` | Basic noise addition | Correct output shape |
| `test_multiplicative_nature` | Noise is multiplicative | Proportional to image |

#### TestNoiseGenerator

| Test | Description | Expected |
|------|-------------|----------|
| `test_default_gaussian` | Default generator works | Correct output |
| `test_fixed_sigma` | Fixed sigma returns constant | sigma == fixed_sigma |
| `test_random_sigma_range` | Random sigma in range | 10 ≤ sigma ≤ 50 |
| `test_invalid_noise_type` | Invalid type raises error | ValueError raised |
| `test_all_noise_types` | All types work | Correct output shape |

### Evaluation Tests (`test_evaluate.py`)

#### TestMSE

| Test | Description | Expected |
|------|-------------|----------|
| `test_identical_images` | MSE of same image | MSE == 0 |
| `test_known_mse` | Known difference | MSE == 1.0 |
| `test_partial_difference` | One pixel different | MSE == 1/N |

#### TestPSNR

| Test | Description | Expected |
|------|-------------|----------|
| `test_identical_images` | PSNR of same image | PSNR == inf |
| `test_known_psnr` | Known MSE | PSNR matches formula |
| `test_higher_psnr_better` | Less noise = higher PSNR | psnr_small > psnr_large |

#### TestSSIM

| Test | Description | Expected |
|------|-------------|----------|
| `test_identical_images` | SSIM of same image | SSIM ≈ 1.0 |
| `test_different_images` | Very different images | SSIM < 0.5 |
| `test_ssim_range` | SSIM in valid range | -1 ≤ SSIM ≤ 1 |
| `test_torch_input` | Works with tensors | Valid SSIM value |
| `test_higher_ssim_better` | Less noise = higher SSIM | ssim_small > ssim_large |

#### TestCalculateMetrics

| Test | Description | Expected |
|------|-------------|----------|
| `test_returns_all_metrics` | All metrics returned | mse, psnr, ssim present |
| `test_metrics_types` | Correct return types | All values are floats |

#### TestMetricTracker

| Test | Description | Expected |
|------|-------------|----------|
| `test_update` | Track metrics | Current values correct |
| `test_moving_average` | Average calculation | Average is correct |
| `test_window_size` | Window limit enforced | Only recent values averaged |
| `test_summary` | Summary generation | All keys present |
| `test_empty_tracker` | Empty tracker returns 0 | Returns 0.0 |

## Test Utilities

### Creating Test Images

```python
def create_test_image(size=64):
    """Create a synthetic test image."""
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    xx, yy = np.meshgrid(x, y)
    image = (xx + yy) / 2
    return image[np.newaxis, :].astype(np.float32)
```

### Adding Known Noise

```python
def add_known_noise(image, sigma=25):
    """Add noise with known sigma for testing."""
    np.random.seed(42)  # Reproducible
    noise = np.random.randn(*image.shape).astype(np.float32) * (sigma / 255.0)
    noisy = image + noise
    return np.clip(noisy, 0, 1), noise
```

## Integration Tests

### Training Pipeline Test

```python
def test_training_pipeline():
    """Test complete training loop."""
    # Create small dataset
    train_loader, val_loader = create_dataloaders(
        batch_size=4,
        patch_size=32,
        num_workers=0,
    )

    # Create model
    model = create_model("dncnn", depth=5, num_features=16)

    # Train for 2 epochs
    trainer = Trainer(model=model, device="cpu")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=2,
    )

    # Verify training occurred
    assert len(history['train_loss']) == 2
    assert history['train_loss'][-1] < history['train_loss'][0]
```

### Inference Test

```python
def test_inference():
    """Test image denoising inference."""
    model = DnCNN(in_channels=1, depth=5, num_features=16)
    denoiser = Denoiser(model=model, device="cpu", tile_size=None)

    # Test single image
    noisy = np.random.rand(64, 64).astype(np.float32)
    denoised = denoiser.denoise_image(noisy)

    assert denoised.shape == noisy.shape
    assert denoised.min() >= 0.0
    assert denoised.max() <= 1.0
```

## Performance Benchmarks

### Expected Test Times

| Test Suite | Expected Time | Notes |
|------------|---------------|-------|
| test_model | ~10s | Multiple forward passes |
| test_noise | ~5s | Noise generation |
| test_evaluate | ~5s | Metric calculations |
| **Total** | **~20s** | On CPU |

### Memory Usage

- Model tests: ~100MB
- Training test: ~500MB
- Inference test: ~200MB

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=src
```

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -v -s  # Show print statements
```

### Run Failed Tests Only

```bash
pytest tests/ --lf  # Run last failed
```

### Debug with pdb

```bash
pytest tests/ --pdb  # Drop into debugger on failure
```

## Test Coverage

Target coverage: >90%

Generate coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```
