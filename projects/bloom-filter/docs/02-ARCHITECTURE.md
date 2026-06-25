# 布隆过滤器架构设计文档

## 1. 系统架构

### 1.1 模块结构

```
bloom_filter/
├── __init__.py           # 包入口，导出公共 API
├── bit_array.py          # 位数组和计数数组实现
├── hash_functions.py     # 哈希函数实现
├── bloom_filter.py       # 标准布隆过滤器
├── counting_bloom_filter.py  # 计数布隆过滤器
├── scalable_bloom_filter.py  # 可扩展布隆过滤器
├── analysis.py           # 性能分析工具
└── main.py              # 演示程序
```

### 1.2 依赖关系

```
analysis.py
    ├── bloom_filter.py
    ├── counting_bloom_filter.py
    └── scalable_bloom_filter.py
            |
            ├── bloom_filter.py
            |       |
            |       ├── bit_array.py
            |       └── hash_functions.py
            |
            └── bit_array.py
                    |
                    └── (CountingArray)
```

### 1.3 类层次结构

```
BitArray (基础位数组)
|
├── BloomFilter (标准布隆过滤器)
|
├── CountingBloomFilter (计数布隆过滤器)
|   └── uses CountingArray
|
└── ScalableBloomFilter (可扩展布隆过滤器)
    └── uses multiple BloomFilter instances
```

## 2. 核心组件

### 2.1 BitArray (位数组)

**职责:**
- 存储位数据
- 提供位操作接口
- 优化内存使用

**设计决策:**
- 使用 Python 整数数组存储，每个整数存储 64 位
- 相比 list[bool] 节省约 8 倍内存
- 使用位操作进行高效访问

**接口:**
```python
class BitArray:
    def get(index: int) -> bool
    def set(index: int) -> None
    def clear(index: int) -> None
    def reset() -> None
    def count_set_bits() -> int
    def fill_ratio() -> float
```

### 2.2 CountingArray (计数数组)

**职责:**
- 存储计数数据
- 提供计数操作接口
- 支持最大计数值限制

**设计决策:**
- 每个计数器使用 1 字节 (最大 255)
- 使用 Python 列表存储
- 提供原子性的增减操作

**接口:**
```python
class CountingArray:
    def get(index: int) -> int
    def increment(index: int) -> bool
    def decrement(index: int) -> bool
    def is_zero(index: int) -> bool
    def reset() -> None
```

### 2.3 HashFunction (哈希函数)

**职责:**
- 计算哈希值
- 支持不同数据类型
- 提供索引映射

**设计决策:**
- 使用 SHA-256 作为基础哈希函数
- 通过种子值生成不同哈希函数
- 支持字符串、整数、浮点数等类型

**接口:**
```python
class HashFunction:
    def hash(item: Any) -> int
    def hash_to_index(item: Any, size: int) -> int
```

### 2.4 DoubleHashFunction (双重哈希函数)

**职责:**
- 从两个基础哈希函数生成 k 个哈希值
- 提供批量索引计算

**设计决策:**
- 使用双重哈希技术: hi(x) = (h1(x) + i * h2(x)) mod m
- 只需计算两个哈希值即可生成任意多个
- 使用大质数模运算避免溢出

**接口:**
```python
class DoubleHashFunction:
    def hash(item: Any, index: int) -> int
    def hash_to_index(item: Any, size: int, index: int) -> int
    def hash_to_indices(item: Any, size: int) -> list[int]
```

## 3. 布隆过滤器实现

### 3.1 BloomFilter (标准布隆过滤器)

**职责:**
- 管理位数组
- 提供插入和查询接口
- 计算误判率

**设计决策:**
- 支持手动指定参数或自动计算最优参数
- 使用 DoubleHashFunction 生成哈希值
- 提供批量操作接口

**状态:**
- `_bits`: BitArray 实例
- `_hash_fn`: DoubleHashFunction 实例
- `_size`: 位数组大小
- `_hash_count`: 哈希函数数量
- `_count`: 已插入元素数量

**接口:**
```python
class BloomFilter:
    def add(item: Any) -> None
    def __contains__(item: Any) -> bool
    def clear() -> None
    def estimated_false_positive_rate() -> float
    def memory_usage() -> dict
```

### 3.2 CountingBloomFilter (计数布隆过滤器)

**职责:**
- 管理计数数组
- 提供插入、查询和删除接口
- 处理计数器溢出

**设计决策:**
- 使用 CountingArray 替代 BitArray
- 删除前检查元素是否存在
- 支持最大计数值限制

**状态:**
- `_counters`: CountingArray 实例
- `_hash_fn`: DoubleHashFunction 实例
- `_size`: 计数器数组大小
- `_hash_count`: 哈希函数数量
- `_count`: 已插入元素数量

**接口:**
```python
class CountingBloomFilter:
    def add(item: Any) -> bool
    def __contains__(item: Any) -> bool
    def remove(item: Any) -> bool
    def clear() -> None
    def estimated_false_positive_rate() -> float
```

### 3.3 ScalableBloomFilter (可扩展布隆过滤器)

**职责:**
- 管理多个布隆过滤器层
- 自动扩容
- 保证总体误判率

**设计决策:**
- 使用多个 BloomFilter 实例组成层
- 每层容量递增，误判率递减
- 查询时检查所有层

**状态:**
- `_layers`: 过滤器层列表
- `_initial_capacity`: 初始容量
- `_false_positive_rate`: 目标误判率
- `_scaling_factor`: 扩容因子
- `_tightening_ratio`: 收紧比例

**接口:**
```python
class ScalableBloomFilter:
    def add(item: Any) -> None
    def __contains__(item: Any) -> bool
    def clear() -> None
    def layer_info() -> list[dict]
    def estimated_false_positive_rate() -> float
```

## 4. 性能分析模块

### 4.1 分析函数

| 函数 | 用途 |
|------|------|
| `optimal_size()` | 计算最优位数组大小 |
| `optimal_hash_count()` | 计算最优哈希函数数量 |
| `false_positive_rate()` | 计算误判率 |
| `compare_filters()` | 比较不同过滤器 |
| `benchmark_insert()` | 插入性能基准 |
| `benchmark_query()` | 查询性能基准 |
| `parameter_sweep()` | 参数扫描分析 |

### 4.2 基准测试

**插入基准:**
- 测量插入 N 个元素的总时间
- 计算每秒插入元素数
- 计算每个元素的纳秒数

**查询基准:**
- 测量查询存在元素的时间
- 测量查询不存在元素的时间
- 计算误判率

## 5. 设计模式

### 5.1 工厂模式

通过参数自动创建最优配置:
```python
bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
```

### 5.2 策略模式

支持不同的哈希函数实现:
```python
# 可以替换为其他哈希函数
hash_fn = DoubleHashFunction(hash_count=7)
```

### 5.3 组合模式

可扩展布隆过滤器使用组合模式管理多层:
```python
class ScalableBloomFilter:
    _layers: list[_FilterLayer]
```

## 6. 错误处理

### 6.1 参数验证

- 位数组大小必须为正数
- 哈希函数数量必须为正数
- 误判率必须在 (0, 1) 范围内
- 最大计数值必须在 (0, 255] 范围内

### 6.2 边界条件

- 空过滤器的误判率为 0
- 索引越界检查
- 计数器下溢保护

## 7. 扩展性

### 7.1 自定义哈希函数

可以实现自定义哈希函数:
```python
class CustomHashFunction(HashFunction):
    def hash(self, item: Any) -> int:
        # 自定义实现
        pass
```

### 7.2 自定义存储后端

可以实现自定义存储后端:
```python
class RedisBitArray:
    def get(self, index: int) -> bool:
        # 使用 Redis 存储
        pass
```

## 8. 测试策略

### 8.1 单元测试

- 每个类的独立测试
- 边界条件测试
- 错误处理测试

### 8.2 集成测试

- 不同组件的交互测试
- 端到端功能测试

### 8.3 性能测试

- 插入性能基准
- 查询性能基准
- 内存使用分析
