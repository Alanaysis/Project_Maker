# 外部排序产品文档

## 1. 产品概述

### 1.1 产品定位

外部排序是一个高性能的 Python 库，用于处理无法全部装入内存的大规模数据排序。它提供了完整的外部排序解决方案，包括初始归并段生成、多路归并、置换选择排序等核心算法。

### 1.2 目标用户

- **数据工程师**: 处理大规模数据集的排序需求
- **数据库开发人员**: 实现数据库的外部排序操作
- **科学计算研究人员**: 对大规模科学数据进行排序
- **系统开发人员**: 构建需要排序功能的应用系统

### 1.3 核心价值

1. **处理超大数据集**: 能够排序超过内存容量的数据
2. **高性能**: 使用置换选择排序和缓冲 I/O 优化
3. **易用性**: 简洁的 API，合理的默认配置
4. **灵活性**: 支持自定义数据类型和排序规则

## 2. 功能特性

### 2.1 核心功能

#### 初始归并段生成

**内部排序法**
- 将数据分块，每块在内存中排序
- 生成的归并段长度约为内存容量 M
- 适用于数据完全随机的情况

**置换选择排序**
- 使用最小堆生成更长的归并段
- 平均归并段长度为 2M
- 减少约 50% 的归并趟数
- 当数据部分有序时效果更好

#### 多路归并

**基本归并**
- 基于最小堆的 K 路归并
- 时间复杂度 O(N log K)
- 支持任意数量的归并段

**多趟归并**
- 当归并路数过多时自动分趟
- 每趟最多归并指定数量的文件
- 最小化总 I/O 次数

#### 缓冲 I/O

**读缓冲区**
- 批量读取数据到内存缓冲区
- 减少磁盘读取次数
- 支持预读取

**写缓冲区**
- 批量写入数据到磁盘
- 减少磁盘写入次数
- 自动刷新机制

### 2.2 应用功能

#### 大文件排序

```python
from src.external_sort import LargeFileSorter

sorter = LargeFileSorter(
    memory_limit=100 * 1024 * 1024,  # 100MB 内存
    max_merge_ways=8,
)

total = sorter.sort("large_file.txt", "sorted_file.txt")
print(f"Sorted {total} records")
```

**特性**:
- 自动内存管理
- 进度报告
- 适用于 GB 级文件

#### 日志排序

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

**特性**:
- 支持多种时间格式
- 自定义分隔符
- 字段提取

#### 数据库排序

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

**特性**:
- CSV 文件支持
- 多列排序
- 表头处理

### 2.3 自定义功能

#### 自定义排序键

```python
# 按绝对值排序
sorter = ExternalSorter(
    key_func=lambda x: abs(x) if isinstance(x, (int, float)) else x
)

# 按元组第二个元素排序
sorter = ExternalSorter(
    key_func=lambda x: x[1]
)

# 多键排序
sorter = ExternalSorter(
    key_func=lambda x: (x[0], -x[1])  # 第一个升序，第二个降序
)
```

#### 自定义解析函数

```python
def custom_parse(line: str) -> dict:
    """解析 CSV 行"""
    parts = line.split(',')
    return {
        'name': parts[0],
        'age': int(parts[1]),
        'score': float(parts[2]),
    }

sorter.sort_file(input_file, output_file, parse_func=custom_parse)
```

## 3. 使用指南

### 3.1 快速开始

#### 安装

```bash
cd projects/external-sort
pip install -r requirements.txt
```

#### 基本用法

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

### 3.2 高级用法

#### 自定义内存限制

```python
# 根据可用内存调整
sorter = ExternalSorter(
    memory_limit=500 * 1024 * 1024,  # 500MB
    buffer_size=10 * 1024 * 1024,    # 10MB 缓冲区
)
```

#### 自定义归并策略

```python
# 调整归并路数
sorter = ExternalSorter(
    max_merge_ways=20,  # 更多归并路数，减少趟数
)

# 或减少归并路数，降低堆操作开销
sorter = ExternalSorter(
    max_merge_ways=5,
)
```

#### 使用内部排序法

```python
# 不使用置换选择排序
sorter = ExternalSorter(
    use_replacement_selection=False,
)
```

### 3.3 实际场景

#### 场景 1: 排序大型日志文件

```python
from src.external_sort import LogSorter

# 假设日志格式: "2024-01-01 10:00:00 INFO Message"
sorter = LogSorter(memory_limit=100 * 1024 * 1024)

# 按时间戳排序
sorter.sort_by_timestamp(
    "/var/log/app.log",
    "/var/log/app_sorted.log",
    timestamp_field=0,
    separator=" "
)
```

#### 场景 2: 排序数据库导出文件

```python
from src.external_sort import DatabaseSorter

# CSV 文件: name,age,salary,department
sorter = DatabaseSorter()

# 按薪资降序排序
sorter.sort_by_columns(
    "employees.csv",
    "employees_sorted.csv",
    sort_columns=[2],      # 薪资列
    separator=",",
    reverse_flags=[True],  # 降序
    header=True,
)
```

#### 场景 3: 排序科学计算数据

```python
from src.external_sort import ExternalSorter

# 假设数据是浮点数，每行一个
sorter = ExternalSorter(
    memory_limit=200 * 1024 * 1024,
    key_func=lambda x: float(x),
)

total = sorter.sort_file("measurements.txt", "measurements_sorted.txt")
print(f"Sorted {total} measurements")
```

## 4. API 参考

### 4.1 ExternalSorter

```python
class ExternalSorter:
    """外部排序器"""

    def __init__(self,
                 memory_limit: int = 1024 * 1024,
                 max_merge_ways: int = 10,
                 buffer_size: int = 512 * 1024,
                 key_func: Optional[Callable] = None,
                 use_replacement_selection: bool = True,
                 temp_dir: Optional[str] = None):
        """
        初始化参数:
        - memory_limit: 内存限制（字节），默认 1MB
        - max_merge_ways: 最大归并路数，默认 10
        - buffer_size: I/O 缓冲区大小，默认 512KB
        - key_func: 排序键提取函数
        - use_replacement_selection: 是否使用置换选择排序
        - temp_dir: 临时文件目录
        """
        pass

    def sort_file(self, input_file: str, output_file: str,
                  parse_func: Optional[Callable] = None) -> int:
        """
        对文件进行外部排序。

        参数:
        - input_file: 输入文件路径
        - output_file: 输出文件路径
        - parse_func: 行解析函数

        返回:
        - 排序后的记录数
        """
        pass

    def sort_iterator(self, data_iter: Iterator[Any],
                      output_file: str) -> int:
        """
        从迭代器读取数据进行排序。

        参数:
        - data_iter: 数据迭代器
        - output_file: 输出文件路径

        返回:
        - 排序后的记录数
        """
        pass

    def sort_data(self, data: List[Any]) -> List[Any]:
        """
        对内存中的数据进行排序。

        参数:
        - data: 输入数据列表

        返回:
        - 排序后的数据列表
        """
        pass

    @property
    def stats(self) -> dict:
        """
        排序统计信息。

        返回字典包含:
        - total_records: 总记录数
        - total_runs: 归并段数
        - merge_passes: 归并趟数
        - run_generation_time: 归并段生成时间
        - merge_time: 归并时间
        - total_time: 总时间
        """
        pass
```

### 4.2 LargeFileSorter

```python
class LargeFileSorter:
    """大文件排序器"""

    def __init__(self,
                 memory_limit: int = 100 * 1024 * 1024,
                 max_merge_ways: int = 8,
                 chunk_size: int = 10 * 1024 * 1024):
        """
        初始化参数:
        - memory_limit: 总内存限制，默认 100MB
        - max_merge_ways: 最大归并路数，默认 8
        - chunk_size: 每个分块大小，默认 10MB
        """
        pass

    def sort(self, input_file: str, output_file: str,
             key_func: Optional[Callable] = None,
             parse_func: Optional[Callable] = None) -> int:
        """
        对大文件进行排序。

        返回: 排序后的记录数
        """
        pass
```

### 4.3 LogSorter

```python
class LogSorter:
    """日志排序器"""

    def __init__(self,
                 memory_limit: int = 50 * 1024 * 1024,
                 timestamp_format: str = "%Y-%m-%d %H:%M:%S"):
        """
        初始化参数:
        - memory_limit: 内存限制
        - timestamp_format: 时间戳格式
        """
        pass

    def sort_by_timestamp(self, input_file: str, output_file: str,
                          timestamp_field: int = 0,
                          separator: str = " ") -> int:
        """
        按时间戳排序日志文件。

        参数:
        - timestamp_field: 时间戳字段索引
        - separator: 字段分隔符

        返回: 排序后的记录数
        """
        pass

    def sort_by_field(self, input_file: str, output_file: str,
                      field_index: int = 0,
                      separator: str = ",",
                      reverse: bool = False) -> int:
        """
        按指定字段排序。

        参数:
        - field_index: 字段索引
        - separator: 字段分隔符
        - reverse: 是否降序

        返回: 排序后的记录数
        """
        pass
```

### 4.4 DatabaseSorter

```python
class DatabaseSorter:
    """数据库排序器"""

    def __init__(self,
                 memory_limit: int = 64 * 1024 * 1024,
                 max_merge_ways: int = 10):
        """
        初始化参数:
        - memory_limit: 内存限制
        - max_merge_ways: 最大归并路数
        """
        pass

    def sort_by_columns(self, input_file: str, output_file: str,
                        sort_columns: List[int],
                        separator: str = ",",
                        reverse_flags: Optional[List[bool]] = None,
                        header: bool = True) -> int:
        """
        按多个列排序。

        参数:
        - sort_columns: 排序列索引列表
        - separator: 字段分隔符
        - reverse_flags: 每列是否降序的标志列表
        - header: 是否有表头

        返回: 排序后的记录数
        """
        pass
```

## 5. 性能指南

### 5.1 内存配置

**推荐配置**:
- 小文件（< 100MB）: 10-50MB 内存
- 中等文件（100MB - 1GB）: 50-200MB 内存
- 大文件（> 1GB）: 200MB - 1GB 内存

**内存与性能关系**:
- 更多内存 → 更少归并段 → 更少归并趟数 → 更快
- 但内存过多可能导致系统交换，反而变慢

### 5.2 归并路数配置

**推荐配置**:
- 机械硬盘: 4-8 路
- SSD: 8-16 路
- 内存充足: 16-32 路

**权衡**:
- 更多归并路数 → 更少趟数 → 更少 I/O
- 但更多归并路数 → 更大堆操作开销

### 5.3 缓冲区配置

**推荐配置**:
- 读缓冲区: 1-10MB
- 写缓冲区: 1-10MB

**优化建议**:
- 缓冲区太小: I/O 次数多
- 缓冲区太大: 内存浪费，可能影响归并路数

### 5.4 置换选择排序

**何时使用**:
- 数据部分有序时效果最好
- 随机数据也能获得约 2M 的归并段长度

**何时不使用**:
- 数据量很小（< 内存容量）
- 数据完全逆序（最坏情况）

## 6. 故障排除

### 6.1 常见问题

#### 问题 1: 排序速度慢

**可能原因**:
- 内存限制太小
- 归并路数不合适
- 使用机械硬盘

**解决方案**:
```python
# 增加内存限制
sorter = ExternalSorter(memory_limit=500 * 1024 * 1024)

# 调整归并路数
sorter = ExternalSorter(max_merge_ways=16)

# 使用 SSD
# 将数据放在 SSD 上
```

#### 问题 2: 内存不足

**可能原因**:
- 内存限制设置过大
- 系统可用内存不足

**解决方案**:
```python
# 减小内存限制
sorter = ExternalSorter(memory_limit=10 * 1024 * 1024)

# 减小缓冲区
sorter = ExternalSorter(buffer_size=100 * 1024)
```

#### 问题 3: 临时文件未清理

**可能原因**:
- 程序异常退出
- 磁盘空间不足

**解决方案**:
```python
# 手动清理临时目录
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)
```

### 6.2 错误信息

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| Input file not found | 输入文件不存在 | 检查文件路径 |
| Disk space insufficient | 磁盘空间不足 | 清理磁盘空间 |
| Memory insufficient | 内存不足 | 减小内存限制 |
| Invalid data format | 数据格式错误 | 检查数据格式 |

## 7. 最佳实践

### 7.1 选择合适的参数

```python
# 根据数据量选择内存限制
if data_size < 100 * 1024 * 1024:  # < 100MB
    memory_limit = 10 * 1024 * 1024
elif data_size < 1024 * 1024 * 1024:  # < 1GB
    memory_limit = 100 * 1024 * 1024
else:  # > 1GB
    memory_limit = 500 * 1024 * 1024
```

### 7.2 使用统计信息

```python
sorter.sort_file(input_file, output_file)
stats = sorter.stats

# 分析性能瓶颈
if stats['run_generation_time'] > stats['merge_time']:
    print("瓶颈在归并段生成，考虑增加内存")
else:
    print("瓶颈在归并，考虑调整归并路数")
```

### 7.3 错误处理

```python
try:
    sorter.sort_file(input_file, output_file)
except FileNotFoundError:
    print(f"文件不存在: {input_file}")
except MemoryError:
    print("内存不足，请减小内存限制")
except Exception as e:
    print(f"排序失败: {e}")
```

### 7.4 资源清理

```python
# 使用上下文管理器（如果支持）
with ExternalSorter() as sorter:
    sorter.sort_file(input_file, output_file)
# 临时文件自动清理

# 或手动清理
sorter = ExternalSorter(temp_dir="/tmp/my_sort")
try:
    sorter.sort_file(input_file, output_file)
finally:
    shutil.rmtree("/tmp/my_sort", ignore_errors=True)
```

## 8. 版本历史

### v1.0.0 (2024-01-01)

- 初始版本
- 基本外部排序功能
- 内部排序法和置换选择排序
- 多路归并
- 缓冲 I/O
- 大文件排序、日志排序、数据库排序
