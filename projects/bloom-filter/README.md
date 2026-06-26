# Bloom Filter / 布隆过滤器

> **Efficient probabilistic deduplication using bit arrays and multiple hash functions**

## Project Description / 项目描述

A learning project implementing the Bloom Filter data structure in Go. The Bloom Filter is a space-efficient probabilistic data structure that tests whether an element is a member of a set with minimal memory usage.

实现布隆过滤器高效去重的学习项目。布隆过滤器是一种空间效率极高的概率型数据结构，用于判断元素是否存在于集合中。

**Key characteristics / 关键特性:**

| Property | Description |
|----------|-------------|
| **Space efficient** | Uses far less memory than a hash set |
| **O(k) operations** | Insert and query both take O(k) time |
| **No false negatives** | If an element was inserted, it will always be found |
| **Possible false positives** | An element not inserted may still be reported as present |

| 特性 | 说明 |
|------|------|
| **空间高效** | 比哈希集合使用更少的内存 |
| **O(k) 操作** | 插入和查询都是 O(k) 时间复杂度 |
| **无假阴性** | 已插入的元素一定被找到 |
| **可能假阳性** | 未插入的元素可能被误判为存在 |

## Learning Objectives / 学习目标

- Understand Bloom filter principles and trade-offs / 理解布隆过滤器原理与权衡
- Master hash function design using single-hash + salt technique / 掌握单哈希+盐值的哈希函数设计
- Learn false positive rate calculation and optimal parameter selection / 学会误判率计算与最优参数选择
- Implement counting Bloom filter variant supporting deletion / 实现支持删除的计数布隆过滤器变体
- Understand Bloom filter merging for distributed systems / 理解分布式系统中的布隆过滤器合并

## Bloom Filter Math / 布隆过滤器数学

### False Positive Rate Formula / 误判率公式

```
p = (1 - e^(-kn/m))^k
```

Where:
- `n` = number of inserted elements
- `m` = bit array size (number of bits)
- `k` = number of hash functions
- `p` = false positive rate

### Optimal Parameters / 最优参数

Given `n` (expected elements) and `p` (target false positive rate):

```
m = -(n * ln(p)) / (ln(2))^2     # optimal bit array size
k = (m / n) * ln(2) ≈ 0.693 * (m/n)  # optimal number of hash functions
```

### Bits per Element / 每元素比特数

| Target FP Rate | Bits per Element |
|---------------|-----------------|
| 10% (0.1)     | ~4.8            |
| 5% (0.05)     | ~6.3            |
| 1% (0.01)     | ~9.6            |
| 0.1% (0.001)  | ~14.4           |
| 0.01% (0.0001)| ~19.2           |

### Core Algorithm / 核心算法

```
Element Insertion / 元素插入:
  For each element:
    For i = 0 to k-1:
      pos = hash_i(element)
      bit_array[pos] = 1

Element Query / 元素查询:
  For each element:
    For i = 0 to k-1:
      pos = hash_i(element)
      if bit_array[pos] == 0:
        return "definitely not in set"
  return "might be in set"
```

## Implementation / 实现

### Core Components / 核心组件

| Component | Description |
|-----------|-------------|
| `BloomFilter` | Standard Bloom filter with bit array |
| `CountingBloomFilter` | Variant with counters supporting deletion |
| `NewOptimal()` | Create filter with optimal parameters |
| `Merge()` | Bitwise OR merge for distributed filtering |
| `CalculateOptimalParams()` | Utility for parameter calculation |

### Hash Function Design / 哈希函数设计

Uses the Kirsch-Mitzenmacher double-hashing technique:
1. Generate two base hashes from SHA-256
2. Derive `k` hash functions: `h(i) = (h1 + i * h2) mod m`
3. This provides k independent-looking hashes with only 2 SHA-256 calls

## How to Run Examples / 如何运行示例

```bash
# Run all examples
cd projects/bloom-filter
go run examples/main.go

# Run specific examples
go run examples/false_positive_rate.go
go run examples/optimal_size.go
go run examples/counting_bloom.go
```

## How to Run Tests / 如何运行测试

```bash
# Run all tests
go test ./tests/ -v

# Run with coverage
go test ./tests/ -v -cover

# Run specific test
go test ./tests/ -v -run TestBloomFilter_BasicOperations
```

## Project Structure / 项目结构

```
bloom-filter/
├── src/
│   └── bloomfilter.go          # Core implementation (BloomFilter + CountingBloomFilter)
├── examples/
│   ├── main.go                  # Combined demo (basic usage + FP demo + optimal size + counting)
│   ├── false_positive_rate.go   # False positive rate demonstration
│   ├── optimal_size.go           # Optimal parameter calculation
│   └── counting_bloom.go        # Counting Bloom filter demo
├── tests/
│   └── bloomfilter_test.go      # Comprehensive unit tests
├── README.md
└── go.mod
```

## Technical Details / 技术细节

### Counting Bloom Filter / 计数布隆过滤器

The counting variant replaces each bit with a small counter:
- **Pros**: Supports deletion of elements
- **Cons**: Uses more memory (8x for 8-bit counters), higher FP rate
- **Counter overflow**: Counters saturate at max value (255 for 8-bit)

### Bloom Filter Merging / 布隆过滤器合并

Multiple Bloom filters can be merged using bitwise OR:
- `filter1.Merge(filter2)` computes the union of both sets
- Useful in distributed systems where nodes maintain local filters
- Merged filter has higher FP rate than individual filters

### Memory Comparison / 内存对比

For 1,000,000 elements with 1% FP rate:

| Structure | Memory |
|-----------|--------|
| Bloom Filter | ~9.6 MB |
| Hash Set (strings) | ~50+ MB |
| Counting Bloom (8-bit) | ~76.8 MB |
| **Space savings** | **~80-95%** |

## References / 参考文献

1. Bloom, B. H. (1970). "Space/time trade-offs in hash coding with allowable errors". Communications of the ACM.
2. Kirsch, A., & Mitzenmacher, M. (2006). "Less hashing, same performance: Building a better Bloom filter".
3. Fan, L., et al. (2000). "Summary Cache: A Scalable Wide-Area Web Cache Sharing Protocol".
4. https://en.wikipedia.org/wiki/Bloom_filter

## License / 许可证

MIT License
