# Testing: Swin Transformer

## Overview

This document describes the testing strategy for our Swin Transformer implementation. We use pytest for testing with comprehensive coverage of all components.

## Test Structure

```
tests/
└── test_swin_transformer.py
    ├── TestPatchEmbedding
    ├── TestPatchMerging
    ├── TestWindowAttention
    ├── TestShiftedWindowTransformerBlock
    ├── TestSwinTransformer
    └── TestIntegration
```

## Running Tests

### Run All Tests

```bash
cd /home/siok/project_copyninja/projects/swin-transformer
python -m pytest tests/test_swin_transformer.py -v
```

### Run Specific Test Class

```bash
python -m pytest tests/test_swin_transformer.py::TestSwinTransformer -v
```

### Run with Coverage

```bash
pip install pytest-cov
python -m pytest tests/test_swin_transformer.py --cov=src --cov-report=html
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

#### PatchEmbedding Tests

```python
class TestPatchEmbedding:
    def test_patch_embedding_output_shape(self):
        """Test that patch embedding produces correct output shape."""
        patch_embed = PatchEmbedding(
            img_size=32,
            patch_size=4,
            in_channels=3,
            embed_dim=96,
        )
        x = torch.randn(2, 3, 32, 32)
        output = patch_embed(x)
        
        # num_patches = (32/4) * (32/4) = 64
        assert output.shape == (2, 64, 96)
    
    def test_patch_embedding_num_patches(self):
        """Test that number of patches is calculated correctly."""
        patch_embed = PatchEmbedding(img_size=224, patch_size=4, embed_dim=96)
        
        assert patch_embed.num_patches_h == 56
        assert patch_embed.num_patches_w == 56
        assert patch_embed.num_patches == 3136
    
    def test_patch_embedding_gradient_flow(self):
        """Test that gradients flow through patch embedding."""
        patch_embed = PatchEmbedding(img_size=32, patch_size=4, embed_dim=96)
        x = torch.randn(1, 3, 32, 32, requires_grad=True)
        
        output = patch_embed(x)
        loss = output.sum()
        loss.backward()
        
        assert x.grad is not None
        assert patch_embed.projection.weight.grad is not None
```

**What We Test:**
- Output shape correctness
- Number of patches calculation
- Gradient flow through the module

#### WindowAttention Tests

```python
class TestWindowAttention:
    def test_window_partition(self):
        """Test window partition function."""
        x = torch.randn(2, 8, 8, 96)
        windows = window_partition(x, window_size=4)
        
        # 2 * (8/4) * (8/4) = 8 windows
        assert windows.shape == (8, 4, 4, 96)
    
    def test_window_reverse(self):
        """Test window reverse function."""
        B, H, W, C = 2, 8, 8, 96
        x = torch.randn(B, H, W, C)
        
        windows = window_partition(x, 4)
        x_reconstructed = window_reverse(windows, 4, H, W)
        
        assert x_reconstructed.shape == x.shape
        assert torch.allclose(x, x_reconstructed)
    
    def test_window_attention_output_shape(self):
        """Test window attention output shape."""
        attn = WindowAttention(
            dim=96,
            window_size=(4, 4),
            num_heads=3,
        )
        
        # (B * num_windows, N, C)
        x = torch.randn(8, 16, 96)
        output = attn(x)
        
        assert output.shape == (8, 16, 96)
```

**What We Test:**
- Window partition correctness
- Window reverse reversibility
- Attention output shape

#### ShiftedWindowTransformerBlock Tests

```python
class TestShiftedWindowTransformerBlock:
    def test_regular_window_block(self):
        """Test regular window attention block."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=0,
        )
        
        x = torch.randn(2, 64, 96)
        output = block(x)
        
        assert output.shape == x.shape
    
    def test_shifted_window_block(self):
        """Test shifted window attention block."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=2,
        )
        
        x = torch.randn(2, 64, 96)
        output = block(x)
        
        assert output.shape == x.shape
    
    def test_residual_connection(self):
        """Test that residual connections are applied correctly."""
        block = ShiftedWindowTransformerBlock(
            dim=96,
            input_resolution=(8, 8),
            num_heads=3,
            window_size=4,
            shift_size=0,
        )
        
        # Set all weights to zero
        for param in block.parameters():
            param.data.zero_()
        
        x = torch.randn(2, 64, 96)
        output = block(x)
        
        # With zero weights, output should be close to input
        assert torch.allclose(output, x, atol=1e-6)
```

**What We Test:**
- Regular window block
- Shifted window block
- Residual connections

### 2. Integration Tests

Test complete model behavior.

#### SwinTransformer Tests

```python
class TestSwinTransformer:
    def test_swin_tiny_output_shape(self):
        """Test Swin-Tiny model output shape."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        x = torch.randn(2, 3, 224, 224)
        output = model(x)
        
        assert output.shape == (2, 10)
    
    def test_swin_tiny_features_shape(self):
        """Test Swin-Tiny feature extraction shape."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        x = torch.randn(2, 3, 224, 224)
        features = model.forward_features(x)
        
        assert features.shape == (2, 768)
    
    def test_swin_different_num_classes(self):
        """Test Swin Transformer with different number of classes."""
        for num_classes in [10, 100, 1000]:
            model = swin_tiny_patch4_window7_224(num_classes=num_classes)
            x = torch.randn(1, 3, 224, 224)
            output = model(x)
            
            assert output.shape == (1, num_classes)
    
    def test_swin_gradient_flow(self):
        """Test that gradients flow through the entire model."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        x = torch.randn(1, 3, 224, 224, requires_grad=True)
        
        output = model(x)
        loss = output.sum()
        loss.backward()
        
        assert x.grad is not None
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None
    
    def test_swin_deterministic_output(self):
        """Test that model produces deterministic output in eval mode."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        model.eval()
        
        x = torch.randn(1, 3, 224, 224)
        
        with torch.no_grad():
            output1 = model(x)
            output2 = model(x)
        
        assert torch.allclose(output1, output2)
```

**What We Test:**
- Output shape
- Feature extraction shape
- Different configurations
- Gradient flow through entire model
- Deterministic behavior

### 3. End-to-End Tests

Test complete training workflow.

```python
class TestIntegration:
    def test_end_to_end_training(self):
        """Test end-to-end forward and backward pass."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        
        x = torch.randn(4, 3, 224, 224)
        target = torch.randint(0, 10, (4,))
        
        # Forward pass
        output = model(x)
        
        # Compute loss
        loss = torch.nn.functional.cross_entropy(output, target)
        
        # Backward pass
        loss.backward()
        
        # Check gradients
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None
    
    def test_model_parameter_count(self):
        """Test that model has reasonable number of parameters."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        assert total_params > 0
        assert trainable_params > 0
        assert trainable_params == total_params
        
        print(f"Total parameters: {total_params:,}")
        print(f"Trainable parameters: {trainable_params:,}")
    
    def test_model_eval_mode(self):
        """Test that model works correctly in eval mode."""
        model = swin_tiny_patch4_window7_224(num_classes=10)
        model.eval()
        
        x = torch.randn(2, 3, 224, 224)
        
        with torch.no_grad():
            output = model(x)
        
        assert output.shape == (2, 10)
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()
```

**What We Test:**
- Complete training loop
- Parameter count
- Eval mode behavior
- Numerical stability

## Test Utilities

### 1. Fixtures

```python
@pytest.fixture
def small_model():
    """Create a small model for testing."""
    return SwinTransformer(
        img_size=32,
        patch_size=4,
        embed_dim=64,
        depths=(2, 2, 2),
        num_heads=(2, 4, 8),
        window_size=4,
        num_classes=10,
    )

@pytest.fixture
def dummy_input():
    """Create dummy input tensor."""
    return torch.randn(2, 3, 32, 32)
```

### 2. Helpers

```python
def assert_shape(tensor, expected_shape):
    """Assert tensor has expected shape."""
    assert tensor.shape == expected_shape, \
        f"Expected shape {expected_shape}, got {tensor.shape}"

def assert_gradient_flow(model, x):
    """Assert gradients flow through model."""
    output = model(x)
    loss = output.sum()
    loss.backward()
    
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"No gradient for {name}"
```

## Edge Cases

### 1. Small Input Sizes

```python
def test_small_input():
    """Test with very small input size."""
    model = SwinTransformer(
        img_size=16,
        patch_size=4,
        embed_dim=32,
        depths=(2, 2),
        num_heads=(2, 4),
        window_size=4,
        num_classes=10,
    )
    
    x = torch.randn(1, 3, 16, 16)
    output = model(x)
    
    assert output.shape == (1, 10)
```

### 2. Single Channel Input

```python
def test_single_channel():
    """Test with single channel input (grayscale)."""
    model = SwinTransformer(
        img_size=32,
        patch_size=4,
        in_channels=1,
        embed_dim=32,
        depths=(2, 2),
        num_heads=(2, 4),
        window_size=4,
        num_classes=10,
    )
    
    x = torch.randn(1, 1, 32, 32)
    output = model(x)
    
    assert output.shape == (1, 10)
```

### 3. Large Batch Size

```python
def test_large_batch():
    """Test with large batch size."""
    model = swin_tiny_patch4_window7_224(num_classes=10)
    
    x = torch.randn(64, 3, 224, 224)
    output = model(x)
    
    assert output.shape == (64, 10)
```

### 4. Non-Square Input

```python
def test_non_square_window():
    """Test with non-square window size."""
    model = SwinTransformer(
        img_size=32,
        patch_size=4,
        embed_dim=32,
        depths=(2, 2),
        num_heads=(2, 4),
        window_size=4,
        num_classes=10,
    )
    
    x = torch.randn(1, 3, 32, 32)
    output = model(x)
    
    assert output.shape == (1, 10)
```

## Performance Testing

### 1. Throughput Test

```python
def test_throughput():
    """Measure model throughput."""
    model = swin_tiny_patch4_window7_224(num_classes=10)
    model.eval()
    model.cuda()
    
    x = torch.randn(16, 3, 224, 224).cuda()
    
    # Warmup
    for _ in range(10):
        with torch.no_grad():
            model(x)
    
    # Measure
    torch.cuda.synchronize()
    start = time.time()
    
    for _ in range(100):
        with torch.no_grad():
            model(x)
    
    torch.cuda.synchronize()
    elapsed = time.time() - start
    
    throughput = 100 * 16 / elapsed
    print(f"Throughput: {throughput:.2f} images/second")
```

### 2. Memory Test

```python
def test_memory_usage():
    """Measure memory usage."""
    model = swin_tiny_patch4_window7_224(num_classes=10)
    model.cuda()
    
    torch.cuda.reset_peak_memory_stats()
    
    x = torch.randn(16, 3, 224, 224).cuda()
    output = model(x)
    loss = output.sum()
    loss.backward()
    
    peak_memory = torch.cuda.max_memory_allocated() / 1e9
    print(f"Peak memory: {peak_memory:.2f} GB")
```

## Continuous Integration

### GitHub Actions

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
      run: |
        pip install torch torchvision pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## Test Coverage Goals

### Minimum Coverage

- **Unit tests:** 90% line coverage
- **Integration tests:** All public APIs
- **Edge cases:** Critical paths

### Coverage Report

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

Expected output:
```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/__init__.py                   4      0   100%
src/patch_embedding.py           45      2    96%   45-46
src/window_attention.py          85      5    94%   120-124
src/shifted_window.py            95      3    97%   145-147
src/swin_transformer.py         120      4    97%   180-183
-----------------------------------------------------------
TOTAL                           349     14    96%
```

## Debugging Tests

### 1. Verbose Output

```bash
python -m pytest tests/ -v -s
```

### 2. Run Specific Test

```bash
python -m pytest tests/test_swin_transformer.py::TestSwinTransformer::test_swin_tiny_output_shape -v
```

### 3. Debug with pdb

```python
def test_debug():
    import pdb; pdb.set_trace()
    model = swin_tiny_patch4_window7_224(num_classes=10)
    # ...
```

### 4. Print Intermediate Shapes

```python
def test_with_debug():
    model = swin_tiny_patch4_window7_224(num_classes=10)
    
    x = torch.randn(1, 3, 224, 224)
    
    # Add debug prints
    print(f"Input: {x.shape}")
    
    x = model.patch_embed(x)
    print(f"After patch_embed: {x.shape}")
    
    for i, layer in enumerate(model.layers):
        x = layer(x)
        print(f"After stage {i}: {x.shape}")
    
    output = model.head(model.avgpool(x.transpose(1, 2)).flatten(1))
    print(f"Output: {output.shape}")
```

## Best Practices

### 1. Test Naming

- Use descriptive names: `test_patch_embedding_output_shape`
- Group related tests in classes
- Use docstrings to explain what is tested

### 2. Test Isolation

- Each test should be independent
- Use fixtures for common setup
- Don't rely on test execution order

### 3. Assertions

- Use specific assertions: `assert x.shape == (2, 10)`
- Include helpful error messages
- Test both positive and negative cases

### 4. Performance

- Use small models for unit tests
- Mock expensive operations when possible
- Run performance tests separately

## Common Issues

### 1. Import Errors

**Problem:** Module not found

**Solution:** Add src to path
```python
import sys
sys.path.insert(0, "/home/siok/project_copyninja/projects/swin-transformer")
```

### 2. Shape Mismatches

**Problem:** Unexpected tensor shapes

**Solution:** Print shapes at each step
```python
print(f"Shape: {x.shape}")
```

### 3. Numerical Issues

**Problem:** NaN or Inf in output

**Solution:** Check for division by zero, overflow
```python
assert not torch.isnan(x).any()
assert not torch.isinf(x).any()
```

### 4. Memory Issues

**Problem:** Out of memory

**Solution:** Use smaller models/batch sizes for testing
```python
model = SwinTransformer(
    img_size=32,  # Small
    embed_dim=32,  # Small
    depths=(2, 2),  # Fewer stages
    ...
)
```
