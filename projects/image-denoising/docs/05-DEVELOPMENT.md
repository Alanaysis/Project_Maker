# Development Guide

## Overview

This guide covers development setup, coding standards, and contribution guidelines for the image denoising project.

## Development Setup

### Prerequisites

- Python 3.8+
- pip or conda
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd image-denoising

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements.txt
```

### IDE Setup

**VS Code:**
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

**PyCharm:**
1. Set Python interpreter to virtual environment
2. Enable pytest as test runner
3. Configure Black as formatter

## Code Style

### Python Version

- Use Python 3.8+ features
- Type hints for all function signatures
- f-strings for formatting

### Formatting

```bash
# Format code with Black
black src/ tests/ examples/

# Check formatting
black --check src/ tests/ examples/
```

### Linting

```bash
# Lint with flake8
flake8 src/ tests/ examples/ --max-line-length=100

# Type checking with mypy (optional)
mypy src/
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module | snake_case | `noise.py` |
| Class | PascalCase | `DnCNN` |
| Function | snake_case | `add_gaussian_noise` |
| Variable | snake_case | `noise_level` |
| Constant | UPPER_CASE | `DEFAULT_SIGMA` |
| Private | _prefix | `_initialize_weights` |

## Project Structure

```
image-denoising/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── model.py           # DnCNN architecture
│   ├── noise.py           # Noise utilities
│   ├── dataset.py         # Dataset handling
│   ├── train.py           # Training pipeline
│   ├── evaluate.py        # Evaluation metrics
│   └── inference.py       # Inference utilities
├── tests/                 # Test files
├── examples/              # Example scripts
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── README.md              # Project overview
└── LEARNING_NOTES.md      # Learning notes
```

## Adding New Features

### 1. Add New Noise Type

```python
# In src/noise.py

def add_new_noise(image, param1, param2):
    """Add new noise type.

    Args:
        image: Input image
        param1: First parameter
        param2: Second parameter

    Returns:
        Tuple of (noisy_image, noise)
    """
    # Implementation
    pass

# Register in NoiseGenerator
NoiseGenerator.NOISE_FUNCTIONS["new_noise"] = add_new_noise
```

### 2. Add New Model Variant

```python
# In src/model.py

class NewModel(nn.Module):
    """New model variant.

    Args:
        in_channels: Input channels
        out_channels: Output channels
    """

    def __init__(self, in_channels=1, out_channels=1):
        super().__init__()
        # Define layers

    def forward(self, x):
        # Forward pass
        pass

    def denoise(self, x):
        return x - self.forward(x)

# Register in create_model factory
def create_model(model_type, **kwargs):
    if model_type == "new_model":
        return NewModel(**kwargs)
```

### 3. Add New Metric

```python
# In src/evaluate.py

def calculate_new_metric(image1, image2):
    """Calculate new metric.

    Args:
        image1: Reference image
        image2: Test image

    Returns:
        Metric value
    """
    # Implementation
    pass

# Add to calculate_metrics
def calculate_metrics(clean, denoised):
    return {
        'mse': calculate_mse(clean, denoised),
        'psnr': calculate_psnr(clean, denoised),
        'ssim': calculate_ssim(clean, denoised),
        'new_metric': calculate_new_metric(clean, denoised),
    }
```

## Testing Guidelines

### Writing Tests

```python
import pytest
import numpy as np

from src.module import function_to_test


class TestFunction:
    """Test suite for function_to_test."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = np.random.rand(1, 64, 64)

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result.shape == input_data.shape

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with zeros
        zeros = np.zeros((1, 64, 64))
        result = function_to_test(zeros)
        assert not np.any(np.isnan(result))

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_to_test(None)
```

### Test Naming

```
test_<function_name>_<scenario>
test_<function_name>_<scenario>_<condition>
```

Examples:
- `test_add_gaussian_noise_numpy_input`
- `test_calculate_psnr_identical_images`
- `test_model_forward_batch_processing`

## Debugging

### Common Issues

**1. Shape Mismatch**
```python
# Debug shape issues
print(f"Input shape: {x.shape}")
print(f"Expected shape: (B, C, H, W)")
```

**2. NaN Values**
```python
# Check for NaN
assert not torch.isnan(output).any(), "Output contains NaN"
assert not torch.isinf(output).any(), "Output contains Inf"
```

**3. Memory Issues**
```python
# Monitor memory
import torch
print(f"GPU memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
```

### Debug Mode

```python
# Enable anomaly detection for debugging
with torch.autograd.detect_anomaly():
    loss.backward()
```

## Performance Optimization

### Profiling

```python
import cProfile

def profile_training():
    cProfile.run('trainer.train(train_loader, val_loader, num_epochs=1)')
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
    pass
```

### GPU Profiling

```bash
# PyTorch profiler
python -m torch.utils.bottleneck train.py
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: int, param2: str) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is negative

    Example:
        >>> result = function_name(1, "test")
        >>> print(result)
        True
    """
```

### Documentation Generation

```bash
# Generate documentation
pip install sphinx
sphinx-quickstart docs/
make html
```

## Release Process

### Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Release Checklist

1. [ ] All tests pass
2. [ ] Code formatted with Black
3. [ ] No linting errors
4. [ ] Documentation updated
5. [ ] Version number updated
6. [ ] CHANGELOG updated
7. [ ] Git tag created

```bash
# Example release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit PR

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added

## Checklist
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No linting errors
```

## Troubleshooting

### Common Problems

| Problem | Solution |
|---------|----------|
| ImportError | Check PYTHONPATH or install package |
| CUDA out of memory | Reduce batch size or use CPU |
| NaN in loss | Lower learning rate |
| Slow training | Use GPU, increase batch size |
| Poor results | Train longer, try different architecture |

### Getting Help

1. Check documentation
2. Search existing issues
3. Create new issue with details
4. Include error messages and code
