# 外部排序开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- 操作系统: Linux, macOS, Windows
- 无第三方依赖（仅使用标准库）

### 1.2 环境配置

```bash
# 克隆项目
cd /home/siok/project_copyninja/projects/external-sort

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 目录结构

```
external-sort/
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── min_heap.py         # 最小堆实现
│   ├── io_buffer.py        # I/O 缓冲区管理
│   ├── run_generator.py    # 归并段生成器
│   ├── kway_merger.py      # 多路归并器
│   └── external_sort.py    # 主排序模块
├── tests/                  # 测试代码
│   ├── __init__.py
│   ├── test_min_heap.py
│   ├── test_io_buffer.py
│   ├── test_run_generator.py
│   ├── test_kway_merger.py
│   └── test_external_sort.py
├── examples/               # 示例代码
│   ├── basic_usage.py
│   └── applications.py
├── docs/                   # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
└── requirements.txt
```

## 2. 代码规范

### 2.1 Python 风格指南

遵循 PEP 8 风格指南:

```python
# 命名约定
# - 类名: PascalCase
class ExternalSorter:
    pass

# - 函数名和变量名: snake_case
def sort_file():
    total_records = 0

# - 常量: UPPER_SNAKE_CASE
MAX_MEMORY_LIMIT = 1024 * 1024

# - 私有成员: 前缀下划线
def _internal_method(self):
    self._private_var = 42
```

### 2.2 文档字符串

使用 Google 风格的文档字符串:

```python
def sort_file(self, input_file: str, output_file: str,
              parse_func: Optional[Callable] = None) -> int:
    """
    对文件进行外部排序。

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        parse_func: 行解析函数，None 则按数值解析

    Returns:
        排序后的记录数

    Raises:
        FileNotFoundError: 输入文件不存在
        MemoryError: 内存不足

    Example:
        >>> sorter = ExternalSorter(memory_limit=10*1024*1024)
        >>> total = sorter.sort_file("input.txt", "output.txt")
        >>> print(f"Sorted {total} records")
    """
    pass
```

### 2.3 类型注解

使用类型注解提高代码可读性:

```python
from typing import Any, Callable, Iterator, List, Optional, Tuple

def merge_files(self, input_files: List[str], output_file: str,
                parse_func: Optional[Callable] = None) -> int:
    pass

@property
def stats(self) -> dict:
    pass
```

### 2.4 导入规范

```python
# 标准库导入
import os
import tempfile
from typing import Any, Callable, List, Optional

# 本地导入
from .min_heap import MinHeap
from .io_buffer import BufferedReader, BufferedWriter
```

## 3. 模块开发指南

### 3.1 最小堆模块 (min_heap.py)

**职责**:
- 提供最小堆数据结构
- 支持自定义比较函数
- 保证排序稳定性

**关键实现**:

```python
class MinHeap:
    def __init__(self, key_func: Optional[Callable] = None):
        self._heap: List = []
        self._key_func = key_func or (lambda x: x)
        self._counter = 0  # 用于稳定排序

    def push(self, item: Any) -> None:
        key = self._key_func(item)
        # 使用 (key, counter, item) 保证稳定性
        heapq.heappush(self._heap, (key, self._counter, item))
        self._counter += 1

    def pop(self) -> Any:
        key, _, item = heapq.heappop(self._heap)
        return item
```

**注意事项**:
- 使用计数器保证稳定性
- 支持自定义键提取函数
- 处理空堆情况

### 3.2 I/O 缓冲区模块 (io_buffer.py)

**职责**:
- 提供缓冲的文件读写
- 减少磁盘 I/O 次数
- 管理内存使用

**关键实现**:

```python
class BufferedWriter(IOBuffer):
    def write(self, item: Any) -> None:
        self._buffer.append(item)
        self._bytes_used += self._estimate_size(item)

        if self.is_full:
            self.flush()

    def flush(self) -> None:
        for item in self._buffer:
            line = f"{item}\n"
            self._file.write(line.encode('utf-8'))

        self._flush_count += 1
        self.clear()
```

**注意事项**:
- 正确估算元素大小
- 处理文件关闭时的刷新
- 支持上下文管理器

### 3.3 归并段生成器模块 (run_generator.py)

**职责**:
- 生成初始归并段
- 支持内部排序法和置换选择排序
- 管理临时文件

**关键实现**:

```python
class ReplacementSelectionV2:
    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        heap = MinHeap(key_func=self._key_func)
        next_run_buffer: List[Any] = []

        # 填充初始堆
        for _ in range(max_elements):
            item = next(data_iter_obj)
            heap.push(item)

        while heap or next_run_buffer:
            if not heap and next_run_buffer:
                self._write_run(current_run, output_dir)
                for item in next_run_buffer:
                    heap.push(item)
                next_run_buffer.clear()

            item = heap.pop()
            current_run.append(item)
            last_output = item

            new_item = next(data_iter_obj)
            if self._key_func(new_item) >= self._key_func(last_output):
                heap.push(new_item)
            else:
                next_run_buffer.append(new_item)
```

**注意事项**:
- 正确实现置换选择算法
- 处理输入数据结束的情况
- 生成的归并段必须有序

### 3.4 多路归并器模块 (kway_merger.py)

**职责**:
- 合并多个有序文件
- 支持多趟归并
- 管理文件句柄

**关键实现**:

```python
class KWayMerger:
    def merge_files(self, input_files: List[str], output_file: str,
                    parse_func: Optional[Callable] = None) -> int:
        heap = []

        # 初始化堆
        for i, filepath in enumerate(input_files):
            reader = BufferedReader(filepath)
            line = reader.read()
            if line:
                value = parse_func(line)
                heapq.heappush(heap, (value, i))

        # 归并
        while heap:
            value, reader_idx = heapq.heappop(heap)
            writer.write(value)

            line = readers[reader_idx].read()
            if line:
                next_value = parse_func(line)
                heapq.heappush(heap, (next_value, reader_idx))
```

**注意事项**:
- 正确管理文件句柄
- 处理文件结束情况
- 支持多趟归并

### 3.5 主排序模块 (external_sort.py)

**职责**:
- 组合各个模块
- 提供统一接口
- 管理排序流程

**关键实现**:

```python
class ExternalSorter:
    def sort_file(self, input_file: str, output_file: str,
                  parse_func: Optional[Callable] = None) -> int:
        # 阶段 1: 生成初始归并段
        run_files = self._generate_runs(input_file, temp_dir, parse_func)

        # 阶段 2: 多路归并
        total_records = self._merge_runs(run_files, output_file, parse_func)

        return total_records
```

**注意事项**:
- 正确组合各个模块
- 处理错误情况
- 清理临时文件

## 4. 测试指南

### 4.1 测试策略

**单元测试**:
- 测试每个模块的独立功能
- 覆盖正常和边界情况
- 测试错误处理

**集成测试**:
- 测试模块间的协作
- 测试完整排序流程
- 测试实际应用场景

**性能测试**:
- 测试排序速度
- 测试内存使用
- 测试 I/O 效率

### 4.2 编写测试

```python
import unittest
import tempfile
import os

class TestExternalSorter(unittest.TestCase):
    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_sort_file_basic(self):
        """测试基本文件排序"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        # 创建测试数据
        with open(input_file, 'w') as f:
            for v in [5, 3, 8, 1, 9, 2, 7, 4, 6]:
                f.write(f"{v}\n")

        # 执行排序
        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_file(input_file, output_file)

        # 验证结果
        self.assertEqual(total, 9)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_sort_large_dataset(self):
        """测试大数据集排序"""
        import random

        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = [random.randint(1, 100000) for _ in range(10000)]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=10000)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 10000)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))
```

### 4.3 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_external_sort.py

# 运行特定测试类
python -m pytest tests/test_external_sort.py::TestExternalSorter

# 运行特定测试方法
python -m pytest tests/test_external_sort.py::TestExternalSorter::test_sort_file_basic

# 显示详细输出
python -m pytest tests/ -v

# 显示覆盖率
python -m pytest tests/ --cov=src
```

### 4.4 测试数据生成

```python
def generate_test_data(num_records: int, data_type: str = "int") -> List[Any]:
    """生成测试数据"""
    import random

    if data_type == "int":
        return [random.randint(1, 1000000) for _ in range(num_records)]
    elif data_type == "float":
        return [random.random() * 1000 for _ in range(num_records)]
    elif data_type == "string":
        return [f"string_{i:08d}" for i in range(num_records)]
    else:
        raise ValueError(f"Unknown data type: {data_type}")
```

## 5. 构建和发布

### 5.1 项目结构

```
external-sort/
├── src/           # 源代码
├── tests/         # 测试
├── examples/      # 示例
├── docs/          # 文档
├── README.md      # 项目说明
├── requirements.txt
└── setup.py       # 打包配置（可选）
```

### 5.2 打包配置

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="external-sort",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    description="External sorting library for large datasets",
    author="AI Analysis",
    license="MIT",
)
```

### 5.3 发布流程

```bash
# 1. 运行测试
python -m pytest tests/

# 2. 构建包
python setup.py sdist bdist_wheel

# 3. 上传到 PyPI（可选）
twine upload dist/*
```

## 6. 调试指南

### 6.1 常见问题

#### 问题 1: 排序结果不正确

**调试步骤**:
1. 检查输入数据是否正确
2. 检查解析函数是否正确
3. 检查排序键函数是否正确
4. 检查归并段是否有序

```python
# 调试归并段
for i, run_file in enumerate(run_files):
    with open(run_file, 'r') as f:
        values = [int(line.strip()) for line in f if line.strip()]
    assert values == sorted(values), f"Run {i} is not sorted"
```

#### 问题 2: 内存使用过多

**调试步骤**:
1. 检查内存限制设置
2. 检查缓冲区大小设置
3. 监控内存使用

```python
import psutil

process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

#### 问题 3: 临时文件未清理

**调试步骤**:
1. 检查临时目录
2. 检查错误处理
3. 手动清理

```python
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)
```

### 6.2 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def sort_file(self, input_file: str, output_file: str, ...) -> int:
    logger.info(f"Starting sort: {input_file} -> {output_file}")
    logger.debug(f"Memory limit: {self._memory_limit}")

    # ...

    logger.info(f"Sort completed: {total} records in {stats['total_time']:.2f}s")
```

### 6.3 性能分析

```python
import cProfile
import pstats

# 分析排序性能
cProfile.run('sorter.sort_file(input_file, output_file)', 'sort_stats')

# 显示统计信息
stats = pstats.Stats('sort_stats')
stats.sort_stats('cumulative')
stats.print_stats()
```

## 7. 贡献指南

### 7.1 开发流程

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 运行测试
5. 提交代码
6. 创建 Pull Request

### 7.2 代码审查

**审查要点**:
- 代码风格是否符合规范
- 是否有完整的文档
- 是否有充分的测试
- 是否有性能问题

### 7.3 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

**示例**:
```
feat(run-generator): add replacement selection sort

Implement replacement selection sort for generating longer initial runs.
Average run length is now 2M instead of M.

Closes #123
```

## 8. 版本管理

### 8.1 版本号

使用语义化版本号: `MAJOR.MINOR.PATCH`

- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能添加
- PATCH: 向后兼容的问题修复

### 8.2 变更日志

```markdown
# Changelog

## [1.0.0] - 2024-01-01

### Added
- 基本外部排序功能
- 内部排序法和置换选择排序
- 多路归并
- 缓冲 I/O
- 大文件排序、日志排序、数据库排序

### Changed
- 无

### Deprecated
- 无

### Removed
- 无

### Fixed
- 无

### Security
- 无
```

## 9. 已知问题

### 9.1 限制

1. **单线程**: 当前实现是单线程的，不支持并行排序
2. **内存估算**: 元素大小估算是近似的，可能不准确
3. **临时文件**: 临时文件需要手动清理（程序异常退出时）

### 9.2 计划改进

1. **并行排序**: 支持多线程并行排序
2. **内存优化**: 更精确的内存管理
3. **压缩支持**: 支持数据压缩
4. **分布式排序**: 支持分布式环境

## 10. 参考资料

### 10.1 算法参考

- Knuth, D. E. (1998). The Art of Computer Programming, Volume 3.
- External Merge Sort - Wikipedia

### 10.2 Python 参考

- Python heapq 模块
- Python tempfile 模块
- PEP 8 - Style Guide for Python Code

### 10.3 工具参考

- pytest - 测试框架
- mypy - 类型检查
- black - 代码格式化
