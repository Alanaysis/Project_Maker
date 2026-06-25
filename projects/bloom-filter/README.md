# 布隆过滤器 (Bloom Filter)

用 Python 实现的高效布隆过滤器库，包含标准布隆过滤器、计数布隆过滤器和可扩展布隆过滤器。

## 项目简介

布隆过滤器是一种概率型数据结构，用于高效地判断一个元素是否存在于集合中。

**核心特性:**
- 空间效率极高: 使用位数组存储，远小于哈希表
- 查询和插入都是 O(k): k 为哈希函数数量
- 可能产生假阳性 (false positive): 判断存在时可能误判
- 绝不会产生假阴性 (false negative): 判断不存在时一定不存在

## 功能实现

| 功能 | 状态 | 说明 |
|------|------|------|
| 标准布隆过滤器 | 完成 | 多哈希函数 + 位数组 + 插入/查询 |
| 计数布隆过滤器 | 完成 | 支持删除操作 |
| 可扩展布隆过滤器 | 完成 | 动态扩容 |
| 性能分析 | 完成 | 误判率计算 + 最优参数 |
| 实际应用 | 完成 | URL去重/垃圾邮件/数据库优化 |

## 快速开始

### 安装

```bash
cd projects/bloom-filter
pip install -r requirements.txt
```

### 基本使用

```python
from bloom_filter import BloomFilter

# 创建布隆过滤器 (自动计算最优参数)
bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)

# 插入元素
bf.add("hello")
bf.add("world")

# 查询元素
print("hello" in bf)  # True
print("world" in bf)  # True
print("rust" in bf)   # False (大概率)
```

### 计数布隆过滤器 (支持删除)

```python
from bloom_filter import CountingBloomFilter

# 创建计数布隆过滤器
cbf = CountingBloomFilter(expected_items=10000, false_positive_rate=0.01)

# 插入元素
cbf.add("hello")
cbf.add("world")

# 删除元素
cbf.remove("hello")

# 查询
print("hello" in cbf)  # False
print("world" in cbf)  # True
```

### 可扩展布隆过滤器 (动态扩容)

```python
from bloom_filter import ScalableBloomFilter

# 创建可扩展布隆过滤器
sbf = ScalableBloomFilter(initial_capacity=1000, false_positive_rate=0.01)

# 插入大量元素 (自动扩容)
for i in range(100000):
    sbf.add(f"item_{i}")

print(f"层数: {sbf.layer_count}")
print(f"总元素: {sbf.count}")
```

## 应用场景

### 1. URL 去重

```python
from bloom_filter import BloomFilter

url_filter = BloomFilter(expected_items=1000000, false_positive_rate=0.01)

if url not in url_filter:
    url_filter.add(url)
    # 处理新 URL
```

### 2. 垃圾邮件过滤

```python
spam_filter = BloomFilter(expected_items=10000, false_positive_rate=0.001)

for keyword in spam_keywords:
    spam_filter.add(keyword)

if any(word in spam_filter for word in email_words):
    # 标记为垃圾邮件
```

### 3. 数据库查询优化

```python
db_filter = BloomFilter(expected_items=1000000, false_positive_rate=0.01)

if key in db_filter:
    # 可能存在，查询数据库
    result = database.get(key)
else:
    # 一定不存在，跳过查询
    pass
```

## 性能分析

### 误判率计算

```python
from bloom_filter import optimal_size, optimal_hash_count, false_positive_rate

n = 10000  # 预期元素数量
p = 0.01   # 期望误判率

m = optimal_size(n, p)  # 最优位数组大小
k = optimal_hash_count(m, n)  # 最优哈希函数数量

print(f"位数组大小: {m}")
print(f"哈希函数数量: {k}")
```

### 最优参数表

| 元素数量 | 误判率 | 位数组大小 | 哈希函数数 | 每元素比特 |
|---------|--------|-----------|-----------|-----------|
| 1,000 | 0.01 | 9,586 | 7 | 9.6 |
| 10,000 | 0.01 | 95,858 | 7 | 9.6 |
| 100,000 | 0.01 | 958,576 | 7 | 9.6 |
| 1,000,000 | 0.01 | 9,585,759 | 7 | 9.6 |

### 内存使用

| 类型 | 每元素字节 (p=0.01) | 特点 |
|------|-------------------|------|
| 标准布隆过滤器 | 9.6 | 最省内存 |
| 计数布隆过滤器 | 76.8 | 支持删除 |
| 可扩展布隆过滤器 | ~12 | 动态扩容 |

## 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 实际应用示例
python examples/applications.py

# 性能分析示例
python examples/performance.py
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_bloom_filter.py

# 生成覆盖率报告
pytest --cov=bloom_filter --cov-report=html
```

## 项目结构

```
bloom-filter/
├── src/
│   └── bloom_filter/
│       ├── __init__.py           # 包入口
│       ├── bit_array.py          # 位数组和计数数组
│       ├── hash_functions.py     # 哈希函数
│       ├── bloom_filter.py       # 标准布隆过滤器
│       ├── counting_bloom_filter.py  # 计数布隆过滤器
│       ├── scalable_bloom_filter.py  # 可扩展布隆过滤器
│       ├── analysis.py           # 性能分析工具
│       └── main.py              # 演示程序
├── tests/
│   ├── test_bloom_filter.py      # 标准布隆过滤器测试
│   ├── test_counting_bloom_filter.py  # 计数布隆过滤器测试
│   ├── test_scalable_bloom_filter.py  # 可扩展布隆过滤器测试
│   └── test_analysis.py         # 性能分析测试
├── examples/
│   ├── basic_usage.py           # 基本使用示例
│   ├── applications.py         # 实际应用示例
│   └── performance.py          # 性能分析示例
├── docs/
│   ├── 01-RESEARCH.md          # 研究文档
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试策略
│   └── 05-DEVELOPMENT.md       # 开发指南
├── README.md
└── requirements.txt
```

## 数学原理

### 误判率公式

```
p ~ (1 - e^(-kn/m))^k
```

### 最优参数

```
m = -(n * ln(p)) / (ln(2))^2
k = (m / n) * ln(2)
```

## 参考文献

1. Bloom, B. H. (1970). Space/time trade-offs in hash coding with allowable errors.
2. Fan, L., et al. (2000). Summary Cache: A Scalable Wide-Area Web Cache Sharing Protocol.
3. Almeida, P. S., et al. (2007). Scalable Bloom Filters.
4. https://en.wikipedia.org/wiki/Bloom_filter

## 许可证

MIT License
