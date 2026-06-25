# 布隆过滤器开发指南

## 1. 开发环境

### 1.1 系统要求

- Python 3.8+
- pip 或 conda

### 1.2 依赖安装

```bash
# 安装开发依赖
pip install pytest pytest-cov

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 1.3 项目结构

```
bloom-filter/
├── src/
│   └── bloom_filter/
│       ├── __init__.py
│       ├── bit_array.py
│       ├── hash_functions.py
│       ├── bloom_filter.py
│       ├── counting_bloom_filter.py
│       ├── scalable_bloom_filter.py
│       ├── analysis.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_bloom_filter.py
│   ├── test_counting_bloom_filter.py
│   ├── test_scalable_bloom_filter.py
│   └── test_analysis.py
├── examples/
│   ├── basic_usage.py
│   ├── applications.py
│   └── performance.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── README.md
└── requirements.txt
```

## 2. 开发流程

### 2.1 克隆项目

```bash
git clone <repository-url>
cd bloom-filter
```

### 2.2 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_bloom_filter.py

# 运行特定测试类
pytest tests/test_bloom_filter.py::TestBloomFilter

# 运行特定测试方法
pytest tests/test_bloom_filter.py::TestBloomFilter::test_add_and_contains

# 生成覆盖率报告
pytest --cov=bloom_filter --cov-report=html
```

### 2.5 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 实际应用示例
python examples/applications.py

# 性能分析示例
python examples/performance.py
```

## 3. 代码规范

### 3.1 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 行长度限制为 88 字符
- 使用类型注解

### 3.2 命名规范

- 类名: PascalCase
- 函数名: snake_case
- 变量名: snake_case
- 常量名: UPPER_SNAKE_CASE
- 私有成员: _前缀

### 3.3 文档规范

- 每个模块都有模块级文档字符串
- 每个类都有类级文档字符串
- 每个公共方法都有方法级文档字符串
- 使用 Google 风格的文档字符串

### 3.4 示例

```python
"""
模块文档字符串

描述模块的功能和用途。
"""

from typing import Any, List


class ExampleClass:
    """
    类文档字符串

    描述类的功能和用途。

    Attributes:
        attribute1: 属性1的描述
        attribute2: 属性2的描述

    Examples:
        >>> example = ExampleClass()
        >>> example.method()
    """

    def __init__(self, param1: int, param2: str = "default"):
        """
        初始化方法

        Args:
            param1: 参数1的描述
            param2: 参数2的描述

        Raises:
            ValueError: 参数无效时
        """
        self._param1 = param1
        self._param2 = param2

    def method(self, arg: Any) -> bool:
        """
        方法文档字符串

        Args:
            arg: 参数描述

        Returns:
            返回值描述

        Raises:
            ValueError: 参数无效时

        Examples:
            >>> example = ExampleClass(1)
            >>> example.method("test")
            True
        """
        return True
```

## 4. 测试规范

### 4.1 测试文件命名

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

### 4.2 测试组织

```python
class TestBloomFilter:
    """标准布隆过滤器测试"""

    def test_create(self):
        """测试创建"""
        pass

    def test_add(self):
        """测试添加"""
        pass

    def test_contains(self):
        """测试查询"""
        pass
```

### 4.3 测试夹具

```python
@pytest.fixture
def bloom_filter():
    """创建布隆过滤器夹具"""
    return BloomFilter(expected_items=1000, false_positive_rate=0.01)


def test_with_fixture(bloom_filter):
    """使用夹具的测试"""
    bloom_filter.add("hello")
    assert "hello" in bloom_filter
```

### 4.4 参数化测试

```python
@pytest.mark.parametrize("n,p", [
    (1000, 0.01),
    (10000, 0.001),
    (100000, 0.0001),
])
def test_optimal_parameters(n, p):
    """参数化测试最优参数"""
    bf = BloomFilter(expected_items=n, false_positive_rate=p)
    assert bf.size > 0
    assert bf.hash_count > 0
```

## 5. 性能优化

### 5.1 位数组优化

- 使用 Python 整数数组而非 list[bool]
- 每个整数存储 64 位
- 使用位操作进行高效访问

### 5.2 哈希函数优化

- 使用双重哈希技术
- 只需计算两个哈希值
- 避免重复计算

### 5.3 批量操作

```python
def add_many(self, items: Iterator[Any]) -> int:
    """批量添加元素"""
    count = 0
    for item in items:
        self.add(item)
        count += 1
    return count
```

## 6. 扩展开发

### 6.1 添加新的布隆过滤器变体

1. 创建新的类文件
2. 继承或组合现有类
3. 实现特定功能
4. 添加测试
5. 更新文档

### 6.2 示例: 添加持久化支持

```python
import pickle

class PersistentBloomFilter(BloomFilter):
    """支持持久化的布隆过滤器"""

    def save(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str) -> "PersistentBloomFilter":
        """从文件加载"""
        with open(filepath, "rb") as f:
            return pickle.load(f)
```

### 6.3 示例: 添加 Redis 支持

```python
import redis

class RedisBloomFilter:
    """基于 Redis 的布隆过滤器"""

    def __init__(self, redis_client: redis.Redis, key: str,
                 expected_items: int, false_positive_rate: float):
        self._redis = redis_client
        self._key = key
        self._size = BloomFilter._optimal_size(expected_items, false_positive_rate)
        self._hash_count = BloomFilter._optimal_hash_count(self._size, expected_items)

    def add(self, item: Any) -> None:
        """添加元素"""
        indices = self._get_indices(item)
        pipe = self._redis.pipeline()
        for index in indices:
            pipe.setbit(self._key, index, 1)
        pipe.execute()

    def __contains__(self, item: Any) -> bool:
        """查询元素"""
        indices = self._get_indices(item)
        pipe = self._redis.pipeline()
        for index in indices:
            pipe.getbit(self._key, index)
        results = pipe.execute()
        return all(results)
```

## 7. 发布流程

### 7.1 版本管理

使用语义化版本:
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修复

### 7.2 发布检查清单

1. [ ] 所有测试通过
2. [ ] 代码覆盖率 > 95%
3. [ ] 文档已更新
4. [ ] 版本号已更新
5. [ ] CHANGELOG 已更新

### 7.3 发布命令

```bash
# 更新版本号
# 在 __init__.py 中更新 __version__

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=bloom_filter --cov-report=html

# 提交更改
git add .
git commit -m "Release version X.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## 8. 常见问题

### 8.1 如何选择合适的参数?

使用 `optimal_size()` 和 `optimal_hash_count()` 函数:
```python
from bloom_filter import optimal_size, optimal_hash_count

n = 10000  # 预期元素数量
p = 0.01   # 期望误判率

m = optimal_size(n, p)
k = optimal_hash_count(m, n)
```

### 8.2 如何测试误判率?

```python
from bloom_filter import BloomFilter

bf = BloomFilter(expected_items=10000, false_positive_rate=0.01)
for i in range(10000):
    bf.add(f"item_{i}")

# 测量实际误判率
test_size = 100000
false_positives = sum(1 for i in range(test_size) if f"test_{i}" in bf)
actual_fpr = false_positives / test_size
print(f"Actual FPR: {actual_fpr:.6f}")
```

### 8.3 如何优化内存使用?

1. 使用更大的误判率 (如 0.1 而非 0.01)
2. 使用标准布隆过滤器而非计数布隆过滤器
3. 使用可扩展布隆过滤器而非预分配大数组

### 8.4 如何处理大数据量?

1. 使用可扩展布隆过滤器
2. 使用 Redis 布隆过滤器
3. 分片处理

## 9. 贡献指南

### 9.1 提交代码

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request

### 9.2 代码审查

- 代码风格符合规范
- 测试覆盖率 > 95%
- 文档已更新
- 性能测试通过

### 9.3 问题报告

使用 GitHub Issues 报告问题:
- 描述问题现象
- 提供复现步骤
- 提供环境信息
- 提供错误日志

## 10. 学习资源

### 10.1 布隆过滤器

- [Wikipedia: Bloom filter](https://en.wikipedia.org/wiki/Bloom_filter)
- [Bloom Filters by Example](https://llimllib.github.io/bloomfilter-tutorial/)

### 10.2 哈希函数

- [MurmurHash3](https://github.com/aappleby/smhasher)
- [CityHash](https://github.com/google/cityhash)

### 10.3 Python

- [Python Documentation](https://docs.python.org/3/)
- [PEP 8](https://peps.python.org/pep-0008/)
