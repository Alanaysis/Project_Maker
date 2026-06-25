# 布隆过滤器测试策略

## 1. 测试概述

### 1.1 测试目标

- 验证功能正确性
- 验证性能指标
- 验证边界条件
- 验证错误处理

### 1.2 测试类型

1. **单元测试**: 测试单个类和函数
2. **集成测试**: 测试组件交互
3. **性能测试**: 测试性能指标
4. **回归测试**: 验证修复和改进

### 1.3 测试工具

- **pytest**: 测试框架
- **pytest-cov**: 代码覆盖率
- **time**: 性能测量
- **random**: 测试数据生成

## 2. 单元测试

### 2.1 BitArray 测试

```python
class TestBitArray:
    def test_create(self):
        bits = BitArray(100)
        assert bits.size == 100

    def test_set_and_get(self):
        bits = BitArray(100)
        bits.set(42)
        assert bits.get(42) is True
        assert bits.get(43) is False

    def test_clear(self):
        bits = BitArray(100)
        bits.set(42)
        bits.clear(42)
        assert bits.get(42) is False

    def test_reset(self):
        bits = BitArray(100)
        bits.set(42)
        bits.reset()
        assert bits.get(42) is False

    def test_count_set_bits(self):
        bits = BitArray(100)
        bits.set(0)
        bits.set(1)
        bits.set(2)
        assert bits.count_set_bits() == 3

    def test_fill_ratio(self):
        bits = BitArray(100)
        bits.set(0)
        assert bits.fill_ratio() == 0.01

    def test_index_error(self):
        bits = BitArray(100)
        with pytest.raises(IndexError):
            bits.get(100)
        with pytest.raises(IndexError):
            bits.set(-1)
```

### 2.2 CountingArray 测试

```python
class TestCountingArray:
    def test_create(self):
        counters = CountingArray(100)
        assert counters.size == 100

    def test_increment(self):
        counters = CountingArray(100)
        counters.increment(42)
        assert counters.get(42) == 1

    def test_decrement(self):
        counters = CountingArray(100)
        counters.increment(42)
        counters.decrement(42)
        assert counters.get(42) == 0

    def test_max_count(self):
        counters = CountingArray(100, max_count=10)
        for _ in range(15):
            counters.increment(42)
        assert counters.get(42) == 10

    def test_decrement_underflow(self):
        counters = CountingArray(100)
        assert counters.decrement(42) is False

    def test_is_zero(self):
        counters = CountingArray(100)
        assert counters.is_zero(42) is True
        counters.increment(42)
        assert counters.is_zero(42) is False
```

### 2.3 HashFunction 测试

```python
class TestHashFunction:
    def test_consistency(self):
        hf = HashFunction(42)
        assert hf.hash("hello") == hf.hash("hello")

    def test_different_seeds(self):
        hf1 = HashFunction(1)
        hf2 = HashFunction(2)
        assert hf1.hash("hello") != hf2.hash("hello")

    def test_hash_to_index(self):
        hf = HashFunction(42)
        index = hf.hash_to_index("hello", 1000)
        assert 0 <= index < 1000

    def test_different_types(self):
        hf = HashFunction(42)
        assert hf.hash("hello") != hf.hash(12345)
        assert hf.hash(3.14) != hf.hash("3.14")
```

### 2.4 DoubleHashFunction 测试

```python
class TestDoubleHashFunction:
    def test_hash_count(self):
        dhf = DoubleHashFunction(7)
        assert dhf.hash_count == 7

    def test_hash_to_indices(self):
        dhf = DoubleHashFunction(7)
        indices = dhf.hash_to_indices("hello", 1000)
        assert len(indices) == 7
        assert all(0 <= i < 1000 for i in indices)

    def test_different_items(self):
        dhf = DoubleHashFunction(7)
        indices1 = dhf.hash_to_indices("hello", 1000)
        indices2 = dhf.hash_to_indices("world", 1000)
        assert indices1 != indices2
```

### 2.5 BloomFilter 测试

```python
class TestBloomFilter:
    def test_create_with_params(self):
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        assert bf.size > 0
        assert bf.hash_count > 0

    def test_add_and_contains(self):
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        bf.add("hello")
        assert "hello" in bf
        assert "world" not in bf

    def test_no_false_negatives(self):
        bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
        items = [f"item_{i}" for i in range(1000)]
        for item in items:
            bf.add(item)
        for item in items:
            assert item in bf

    def test_false_positive_rate(self):
        bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
        for i in range(10000):
            bf.add(f"item_{i}")
        test_size = 100000
        false_positives = sum(1 for i in range(test_size) if f"test_{i}" in bf)
        actual_fpr = false_positives / test_size
        assert actual_fpr < 0.02

    def test_clear(self):
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        bf.add("hello")
        bf.clear()
        assert "hello" not in bf
        assert bf.count == 0
```

### 2.6 CountingBloomFilter 测试

```python
class TestCountingBloomFilter:
    def test_add_and_remove(self):
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        cbf.add("hello")
        assert "hello" in cbf
        cbf.remove("hello")
        assert cbf.count == 0

    def test_remove_nonexistent(self):
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        assert cbf.remove("nonexistent") is False

    def test_remove_preserves_others(self):
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        cbf.add("hello")
        cbf.add("world")
        cbf.remove("hello")
        assert "world" in cbf

    def test_duplicate_add_and_remove(self):
        cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)
        cbf.add("hello")
        cbf.add("hello")
        assert cbf.count == 2
        cbf.remove("hello")
        assert cbf.count == 1
        assert "hello" in cbf
```

### 2.7 ScalableBloomFilter 测试

```python
class TestScalableBloomFilter:
    def test_scaling(self):
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)
        for i in range(1000):
            sbf.add(f"item_{i}")
        assert sbf.layer_count > 1

    def test_no_false_negatives(self):
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)
        items = [f"item_{i}" for i in range(1000)]
        for item in items:
            sbf.add(item)
        for item in items:
            assert item in sbf

    def test_layer_info(self):
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)
        for i in range(500):
            sbf.add(f"item_{i}")
        info = sbf.layer_info()
        assert len(info) == sbf.layer_count

    def test_clear(self):
        sbf = ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)
        for i in range(500):
            sbf.add(f"item_{i}")
        sbf.clear()
        assert sbf.layer_count == 1
        assert sbf.count == 0
```

## 3. 集成测试

### 3.1 端到端测试

```python
def test_end_to_end():
    # 创建过滤器
    bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)

    # 插入数据
    items = [f"item_{i}" for i in range(10000)]
    for item in items:
        bf.add(item)

    # 验证查询
    for item in items:
        assert item in bf

    # 验证误判率
    test_size = 100000
    false_positives = sum(1 for i in range(test_size) if f"test_{i}" in bf)
    actual_fpr = false_positives / test_size
    assert actual_fpr < 0.02
```

### 3.2 混合操作测试

```python
def test_mixed_operations():
    cbf = CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

    # 交替添加和删除
    for i in range(100):
        cbf.add(f"item_{i}")
        if i % 2 == 0:
            cbf.remove(f"item_{i}")

    # 验证剩余元素
    for i in range(100):
        if i % 2 == 0:
            assert cbf.count <= 100
        else:
            assert f"item_{i}" in cbf
```

## 4. 性能测试

### 4.1 插入性能测试

```python
def test_insert_performance():
    n = 100000
    items = [f"item_{i}" for i in range(n)]

    bf = BloomFilter(expected_items=n, false_positive_rate=0.01)

    start = time.perf_counter()
    for item in items:
        bf.add(item)
    elapsed = time.perf_counter() - start

    # 验证性能
    items_per_second = n / elapsed
    assert items_per_second > 10000  # 至少 10000 元素/秒
```

### 4.2 查询性能测试

```python
def test_query_performance():
    n = 100000
    bf = BloomFilter(expected_items=n, false_positive_rate=0.01)

    for i in range(n):
        bf.add(f"item_{i}")

    # 测试存在元素查询
    start = time.perf_counter()
    for i in range(n):
        _ = f"item_{i}" in bf
    existing_time = time.perf_counter() - start

    # 测试不存在元素查询
    start = time.perf_counter()
    for i in range(n):
        _ = f"test_{i}" in bf
    non_existing_time = time.perf_counter() - start

    # 验证性能
    ns_per_query = (existing_time * 1e9) / n
    assert ns_per_query < 1000  # 小于 1000 纳秒/查询
```

### 4.3 内存使用测试

```python
def test_memory_usage():
    n = 100000
    bf = BloomFilter(expected_items=n, false_positive_rate=0.01)
    mem = bf.memory_usage()

    # 验证内存使用
    expected_bytes = (bf.size + 7) // 8
    assert mem["bit_array_bytes"] == expected_bytes
    assert mem["bit_array_mb"] == expected_bytes / (1024 * 1024)
```

## 5. 边界条件测试

### 5.1 空过滤器测试

```python
def test_empty_filter():
    bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

    assert bf.count == 0
    assert bf.fill_ratio() == 0.0
    assert bf.estimated_false_positive_rate() == 0.0
    assert "hello" not in bf
```

### 5.2 单元素测试

```python
def test_single_element():
    bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)

    bf.add("hello")
    assert bf.count == 1
    assert "hello" in bf
    assert bf.fill_ratio() > 0.0
```

### 5.3 大量元素测试

```python
def test_large_number_of_elements():
    n = 100000
    bf = BloomFilter(expected_items=n, false_positive_rate=0.01)

    for i in range(n):
        bf.add(f"item_{i}")

    assert bf.count == n
    for i in range(n):
        assert f"item_{i}" in bf
```

## 6. 错误处理测试

### 6.1 无效参数测试

```python
def test_invalid_parameters():
    # 无效位数组大小
    with pytest.raises(ValueError):
        BloomFilter(size=0, hash_count=7)

    # 无效哈希函数数量
    with pytest.raises(ValueError):
        BloomFilter(size=10000, hash_count=0)

    # 无效误判率
    with pytest.raises(ValueError):
        BloomFilter(expected_items=1000, false_positive_rate=0.0)

    with pytest.raises(ValueError):
        BloomFilter(expected_items=1000, false_positive_rate=1.0)
```

### 6.2 索引越界测试

```python
def test_index_out_of_bounds():
    bits = BitArray(100)

    with pytest.raises(IndexError):
        bits.get(100)

    with pytest.raises(IndexError):
        bits.set(-1)

    with pytest.raises(IndexError):
        bits.clear(200)
```

## 7. 测试覆盖率

### 7.1 覆盖率目标

- 语句覆盖率: > 95%
- 分支覆盖率: > 90%
- 函数覆盖率: 100%

### 7.2 覆盖率报告

```bash
# 运行测试并生成覆盖率报告
pytest --cov=bloom_filter --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 8. 测试配置

### 8.1 pytest 配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### 8.2 测试夹具

```python
@pytest.fixture
def bloom_filter():
    return BloomFilter(expected_items=1000, false_positive_rate=0.01)

@pytest.fixture
def counting_bloom_filter():
    return CountingBloomFilter(expected_items=1000, false_positive_rate=0.01)

@pytest.fixture
def scalable_bloom_filter():
    return ScalableBloomFilter(initial_capacity=100, false_positive_rate=0.01)
```

## 9. 持续集成

### 9.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=bloom_filter --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```
