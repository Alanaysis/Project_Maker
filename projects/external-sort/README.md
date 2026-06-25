# 外部排序 (External Sort)

大规模数据排序库，适用于无法全部装入内存的数据排序场景。

## 项目概述

外部排序是一种用于处理超大数据集的排序算法，当数据量超过可用内存时，需要将数据分块处理并合并。本项目实现了完整的外部排序库，包含初始归并段生成、多路归并、置换选择排序等核心算法。

### 核心特性

- **初始归并段生成**: 内部排序法和置换选择排序
- **多路归并**: 基于最小堆的高效归并
- **置换选择排序**: 生成更长的初始归并段（平均长度 2M）
- **缓冲 I/O**: 减少磁盘 I/O 次数
- **多趟归并**: 支持超多路归并
- **实际应用**: 大文件排序、日志排序、数据库排序

## 目录结构

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
│   ├── test_min_heap.py
│   ├── test_io_buffer.py
│   ├── test_run_generator.py
│   ├── test_kway_merger.py
│   └── test_external_sort.py
├── examples/               # 示例代码
│   ├── basic_usage.py      # 基本用法
│   └── applications.py     # 实际应用
├── docs/                   # 文档
│   ├── 01_RESEARCH.md      # 研究文档
│   ├── 02_REQUIREMENTS.md  # 需求文档
│   ├── 03_DESIGN.md        # 设计文档
│   ├── 04_PRODUCT.md       # 产品文档
│   └── 05_DEVELOPMENT.md   # 开发文档
└── requirements.txt        # 依赖
```

## 快速开始

### 安装

```bash
cd projects/external-sort
pip install -r requirements.txt
```

### 基本用法

```python
from src.external_sort import ExternalSorter

# 创建排序器
sorter = ExternalSorter(
    memory_limit=10 * 1024 * 1024,  # 10MB 内存限制
    max_merge_ways=10,               # 最大归并路数
    use_replacement_selection=True,  # 使用置换选择排序
)

# 对文件排序
total = sorter.sort_file("input.txt", "output.txt")

# 查看统计信息
stats = sorter.stats
print(f"总记录数: {stats['total_records']}")
print(f"归并段数: {stats['total_runs']}")
print(f"总时间: {stats['total_time']:.2f}s")
```

### 大文件排序

```python
from src.external_sort import LargeFileSorter

sorter = LargeFileSorter(
    memory_limit=100 * 1024 * 1024,  # 100MB 内存
    max_merge_ways=8,
)

total = sorter.sort("large_file.txt", "sorted_file.txt")
```

### 日志排序

```python
from src.external_sort import LogSorter

sorter = LogSorter()

# 按时间戳排序
sorter.sort_by_timestamp(
    "app.log", "sorted.log",
    timestamp_field=0,
    separator=" "
)

# 按字段排序
sorter.sort_by_field(
    "data.csv", "sorted.csv",
    field_index=1,
    separator=","
)
```

### 数据库排序

```python
from src.external_sort import DatabaseSorter

sorter = DatabaseSorter()

# 单列排序
sorter.sort_by_columns(
    "employees.csv", "sorted.csv",
    sort_columns=[3],  # 按薪资排序
    separator=",",
    header=True,
)

# 多列排序
sorter.sort_by_columns(
    "scores.csv", "sorted.csv",
    sort_columns=[1, 2, 3],  # 按数学、英语、科学排序
    separator=",",
    header=True,
)
```

## 算法详解

### 1. 初始归并段生成

#### 内部排序法
- 将数据分块，每块大小不超过内存限制
- 对每块在内存中排序
- 将排序后的块写入临时文件

#### 置换选择排序
- 使用最小堆维护当前可用内存中的元素
- 输出堆顶元素（当前最小值）
- 从输入读取新元素:
  - 如果新元素 >= 已输出的最大值，加入当前归并段
  - 否则，标记为下一个归并段
- 平均归并段长度为 2M（M 为内存容量）

### 2. 多路归并

- 使用最小堆管理 K 个归并段
- 每次从堆中弹出最小元素
- 从对应的归并段读取下一个元素
- 时间复杂度: O(N log K)

### 3. 缓冲 I/O

- 读缓冲区: 批量读取数据，减少 I/O 次数
- 写缓冲区: 批量写入数据，减少 I/O 次数
- 自动刷新机制

## 性能特点

| 特性 | 说明 |
|------|------|
| 时间复杂度 | O(N log N) |
| 空间复杂度 | O(M) - M 为内存限制 |
| I/O 复杂度 | O(N log_{M/B}(N/M)) |
| 归并段长度 | 内部排序: M，置换选择: ~2M |

## 应用场景

1. **大文件排序**: 超过内存容量的数据文件排序
2. **日志排序**: 按时间戳或字段排序日志文件
3. **数据库排序**: 外部排序操作
4. **数据处理**: ETL 流程中的排序步骤
5. **科学计算**: 大规模数据集排序

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_external_sort.py

# 运行示例
python examples/basic_usage.py
python examples/applications.py
```

## 技术栈

- Python 3.8+
- 标准库: heapq, os, tempfile

## 学习资源

- [外部排序算法详解](docs/01_RESEARCH.md)
- [需求分析](docs/02_REQUIREMENTS.md)
- [系统设计](docs/03_DESIGN.md)
- [产品说明](docs/04_PRODUCT.md)
- [开发文档](docs/05_DEVELOPMENT.md)

## 许可证

MIT License
