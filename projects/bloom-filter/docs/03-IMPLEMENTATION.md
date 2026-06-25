# 布隆过滤器实现细节

## 1. 位数组实现

### 1.1 BitArray

使用 Python 整数数组实现紧凑的位数组存储。

**数据结构:**
```python
class BitArray:
    BITS_PER_WORD = 64

    def __init__(self, size: int):
        self._size = size
        word_count = (size + 63) // 64
        self._words = [0] * word_count
```

**位操作:**
```python
def get(self, index: int) -> bool:
    word_index = index // 64
    bit_offset = index % 64
    return bool(self._words[word_index] & (1 << bit_offset))

def set(self, index: int) -> None:
    word_index = index // 64
    bit_offset = index % 64
    self._words[word_index] |= (1 << bit_offset)
```

**内存优化:**
- 每个 Python 整数存储 64 位
- 相比 list[bool] 节省约 8 倍内存
- 使用位操作进行高效访问

### 1.2 CountingArray

使用 Python 列表实现计数数组。

**数据结构:**
```python
class CountingArray:
    def __init__(self, size: int, max_count: int = 255):
        self._size = size
        self._max_count = max_count
        self._counters = [0] * size
```

**计数操作:**
```python
def increment(self, index: int) -> bool:
    if self._counters[index] >= self._max_count:
        return False
    self._counters[index] += 1
    return True

def decrement(self, index: int) -> bool:
    if self._counters[index] <= 0:
        return False
    self._counters[index] -= 1
    return True
```

**溢出保护:**
- 最大计数值限制为 255 (8 位)
- 计数器满时返回 False
- 计数器空时返回 False

## 2. 哈希函数实现

### 2.1 单个哈希函数

使用 SHA-256 作为基础哈希函数。

**实现:**
```python
class HashFunction:
    def __init__(self, seed: int = 0):
        self._seed = seed

    def hash(self, item: Any) -> int:
        data = self._to_bytes(item)
        seed_bytes = struct.pack(">Q", self._seed & 0xFFFFFFFFFFFFFFFF)
        h = hashlib.sha256(seed_bytes + data).digest()
        return struct.unpack(">Q", h[:8])[0]
```

**特点:**
- 使用 SHA-256 保证哈希质量
- 通过种子值生成不同哈希函数
- 支持多种数据类型

### 2.2 双重哈希函数

使用双重哈希技术生成 k 个哈希值。

**实现:**
```python
class DoubleHashFunction:
    def __init__(self, hash_count: int):
        self._hash_count = hash_count
        self._h1 = HashFunction(seed=0x5BD1E995)
        self._h2 = HashFunction(seed=0x1B873593)

    def hash(self, item: Any, index: int) -> int:
        h1 = self._h1.hash(item)
        h2 = self._h2.hash(item)
        MOD = (1 << 64) - 1
        return (h1 + index * h2) % MOD

    def hash_to_indices(self, item: Any, size: int) -> list[int]:
        return [self.hash_to_index(item, size, i) for i in range(self._hash_count)]
```

**优势:**
1. 只需计算两个哈希值
2. 计算效率高
3. 哈希值之间具有良好的独立性

### 2.3 MurmurHash3 实现

提供 MurmurHash3 的纯 Python 实现。

**实现:**
```python
def mmh3_hash(item: Any, seed: int = 0) -> int:
    data = HashFunction._to_bytes(item)

    c1 = 0xCC9E2D51
    c2 = 0x1B873593
    r1 = 15
    r2 = 13
    m = 5
    n = 0xE6546B64

    hash_val = seed & 0xFFFFFFFF
    length = len(data)

    # 处理 4 字节块
    nblocks = length // 4
    for i in range(nblocks):
        k = struct.unpack("<I", data[i * 4 : (i + 1) * 4])[0]
        k = (k * c1) & 0xFFFFFFFF
        k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF
        hash_val ^= k
        hash_val = ((hash_val << r2) | (hash_val >> (32 - r2))) & 0xFFFFFFFF
        hash_val = (hash_val * m + n) & 0xFFFFFFFF

    # 处理尾部
    # ...

    # 最终混合
    hash_val ^= length
    hash_val ^= hash_val >> 16
    hash_val = (hash_val * 0x85EBCA6B) & 0xFFFFFFFF
    hash_val ^= hash_val >> 13
    hash_val = (hash_val * 0xC2B2AE35) & 0xFFFFFFFF
    hash_val ^= hash_val >> 16

    return hash_val
```

## 3. 布隆过滤器实现

### 3.1 标准布隆过滤器

**核心实现:**
```python
class BloomFilter:
    def add(self, item: Any) -> None:
        indices = self._hash_fn.hash_to_indices(item, self._size)
        for index in indices:
            self._bits.set(index)
        self._count += 1

    def __contains__(self, item: Any) -> bool:
        indices = self._hash_fn.hash_to_indices(item, self._size)
        return all(self._bits.get(index) for index in indices)
```

**参数计算:**
```python
@classmethod
def _optimal_size(cls, n: int, p: float) -> int:
    m = -(n * math.log(p)) / cls.LN2_SQUARED
    return math.ceil(m)

@classmethod
def _optimal_hash_count(cls, m: int, n: int) -> int:
    k = (m / n) * cls.LN2
    return max(1, round(k))
```

### 3.2 计数布隆过滤器

**核心实现:**
```python
class CountingBloomFilter:
    def add(self, item: Any) -> bool:
        indices = self._hash_fn.hash_to_indices(item, self._size)
        success = True
        for index in indices:
            if not self._counters.increment(index):
                success = False
        self._count += 1
        return success

    def remove(self, item: Any) -> bool:
        indices = self._hash_fn.hash_to_indices(item, self._size)
        if any(self._counters.get(index) == 0 for index in indices):
            return False
        for index in indices:
            self._counters.decrement(index)
        self._count -= 1
        return True
```

**删除安全性:**
- 删除前检查所有计数器是否大于 0
- 避免计数器下溢
- 返回 False 表示元素可能不存在

### 3.3 可扩展布隆过滤器

**核心实现:**
```python
class ScalableBloomFilter:
    def add(self, item: Any) -> None:
        current_layer = self._layers[-1]
        if current_layer.is_full():
            self._add_layer()
            current_layer = self._layers[-1]

        if item not in self:
            current_layer.filter.add(item)
            self._total_count += 1
        else:
            current_layer.filter.add(item)
            self._total_count += 1

    def __contains__(self, item: Any) -> bool:
        return any(item in layer.filter for layer in self._layers)
```

**扩容策略:**
```python
def _add_layer(self) -> None:
    layer_index = len(self._layers)
    capacity = int(self._initial_capacity * (self._scaling_factor ** layer_index))
    layer_fpr = self._false_positive_rate * (self._tightening_ratio ** layer_index)
    layer_fpr = max(layer_fpr, 1e-10)

    bloom = BloomFilter(expected_items=capacity, false_positive_rate=layer_fpr)
    layer = _FilterLayer(filter=bloom, capacity=capacity)
    self._layers.append(layer)
```

## 4. 性能分析实现

### 4.1 误判率计算

**理论公式:**
```python
def false_positive_rate(m: int, k: int, n: int) -> float:
    if n == 0:
        return 0.0
    exponent = -k * n / m
    return (1 - math.exp(exponent)) ** k
```

**实际测量:**
```python
def measure_fpr(bf, test_size=100000):
    false_positives = sum(
        1 for i in range(test_size) if f"test_{i}" in bf
    )
    return false_positives / test_size
```

### 4.2 基准测试

**插入基准:**
```python
def benchmark_insert(filter_factory, items):
    bf = filter_factory()
    start = time.perf_counter()
    for item in items:
        bf.add(item)
    end = time.perf_counter()
    elapsed = end - start
    return {
        "count": len(items),
        "total_time": elapsed,
        "items_per_second": len(items) / elapsed,
    }
```

**查询基准:**
```python
def benchmark_query(filter_factory, existing, non_existing):
    bf = filter_factory()
    for item in existing:
        bf.add(item)

    start = time.perf_counter()
    for item in existing:
        _ = item in bf
    existing_time = time.perf_counter() - start

    start = time.perf_counter()
    for item in non_existing:
        _ = item in bf
    non_existing_time = time.perf_counter() - start

    return {
        "existing_time": existing_time,
        "non_existing_time": non_existing_time,
    }
```

## 5. 内存优化

### 5.1 位数组优化

- 使用 Python 整数数组而非 list[bool]
- 每个整数存储 64 位
- 使用位操作进行高效访问

### 5.2 计数数组优化

- 每个计数器使用 1 字节
- 使用 Python 列表存储
- 支持最大计数值限制

### 5.3 哈希函数优化

- 使用双重哈希技术
- 只需计算两个哈希值
- 避免重复计算

## 6. 错误处理

### 6.1 参数验证

```python
if size <= 0:
    raise ValueError(f"size must be positive, got {size}")
if not (0 < false_positive_rate < 1):
    raise ValueError(f"false_positive_rate must be in (0, 1), got {false_positive_rate}")
```

### 6.2 边界条件

- 空过滤器的误判率为 0
- 索引越界检查
- 计数器下溢保护

### 6.3 类型检查

```python
@staticmethod
def _to_bytes(item: Any) -> bytes:
    if isinstance(item, bytes):
        return item
    if isinstance(item, str):
        return item.encode("utf-8")
    if isinstance(item, (int, float)):
        return str(item).encode("utf-8")
    return str(item).encode("utf-8")
```

## 7. 性能优化

### 7.1 批量操作

```python
def add_many(self, items: Iterator[Any]) -> int:
    count = 0
    for item in items:
        self.add(item)
        count += 1
    return count
```

### 7.2 预计算哈希值

```python
def hash_to_indices(self, item: Any, size: int) -> list[int]:
    return [self.hash_to_index(item, size, i) for i in range(self._hash_count)]
```

### 7.3 填充率计算

```python
def count_set_bits(self) -> int:
    count = 0
    for word in self._words:
        count += bin(word).count("1")
    return count
```
