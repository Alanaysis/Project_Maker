# 外部排序系统设计文档

## 1. 系统架构

### 1.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      ExternalSorter                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ RunGenerator│  │ KWayMerger  │  │ IOBuffer            │ │
│  │             │  │             │  │ (Reader/Writer)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  MinHeap    │  │  MinHeap    │  │    File System      │ │
│  │  (Run)      │  │  (Merge)    │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
src/
├── min_heap.py         # 最小堆实现
│   ├── MinHeap         # 通用最小堆
│   └── KWayMergeHeap   # 多路归并专用堆
│
├── io_buffer.py        # I/O 缓冲区
│   ├── IOBuffer        # 缓冲区基类
│   ├── BufferedWriter  # 写缓冲区
│   ├── BufferedReader  # 读缓冲区
│   └── RunBuffer       # 归并段缓冲区
│
├── run_generator.py    # 归并段生成器
│   ├── RunGenerator              # 内部排序法
│   ├── ReplacementSelection      # 置换选择排序
│   └── ReplacementSelectionV2    # 改进版置换选择
│
├── kway_merger.py      # 多路归并器
│   ├── KWayMerger      # K 路归并
│   └── NaturalMerge    # 自然归并
│
└── external_sort.py    # 主排序模块
    ├── ExternalSorter  # 通用外部排序器
    ├── LargeFileSorter # 大文件排序器
    ├── LogSorter       # 日志排序器
    └── DatabaseSorter  # 数据库排序器
```

## 2. 核心模块设计

### 2.1 MinHeap - 最小堆

#### 2.1.1 类设计

```python
class MinHeap:
    """
    最小堆，用于多路归并。

    支持两种模式:
    1. 简单模式: 直接存储可比较的元素
    2. 键值模式: 存储 (key, value) 对，按 key 排序
    """

    def __init__(self, key_func: Optional[Callable] = None):
        self._heap: List = []
        self._key_func = key_func or (lambda x: x)
        self._counter = 0  # 用于稳定排序

    def push(self, item: Any) -> None: ...
    def pop(self) -> Any: ...
    def peek(self) -> Any: ...
    def push_pop(self, item: Any) -> Any: ...
    def replace(self, item: Any) -> Any: ...
```

#### 2.1.2 存储格式

堆中元素存储为三元组: `(key, counter, item)`
- `key`: 排序键
- `counter`: 插入计数器，保证稳定性
- `item`: 实际数据

#### 2.1.3 时间复杂度

| 操作 | 时间复杂度 |
|------|-----------|
| push | O(log n) |
| pop | O(log n) |
| peek | O(1) |
| push_pop | O(log n) |
| replace | O(log n) |

### 2.2 IOBuffer - I/O 缓冲区

#### 2.2.1 类设计

```python
class IOBuffer:
    """I/O 缓冲区基类"""

    def __init__(self, buffer_size: int = 1024 * 1024):
        self._buffer_size = buffer_size
        self._buffer: List[Any] = []
        self._bytes_used = 0

class BufferedWriter(IOBuffer):
    """写缓冲区"""

    def __init__(self, filepath: str, buffer_size: int = 1024 * 1024,
                 append: bool = False):
        ...

    def write(self, item: Any) -> None: ...
    def flush(self) -> None: ...

class BufferedReader(IOBuffer):
    """读缓冲区"""

    def __init__(self, filepath: str, buffer_size: int = 1024 * 1024):
        ...

    def read(self) -> Optional[Any]: ...
    def read_batch(self, count: int) -> List[Any]: ...
```

#### 2.2.2 缓冲策略

**写缓冲区**:
1. 数据写入内存缓冲区
2. 当缓冲区满时，一次性写入磁盘
3. 关闭文件时刷新缓冲区

**读缓冲区**:
1. 从磁盘批量读取数据到缓冲区
2. 后续从缓冲区读取数据
3. 缓冲区空时重新填充

#### 2.2.3 内存管理

```python
def _estimate_size(self, item: Any) -> int:
    """估算元素大小"""
    if isinstance(item, (int, float)):
        return 8
    elif isinstance(item, str):
        return len(item.encode('utf-8')) + 4
    else:
        return 64  # 默认估算
```

### 2.3 RunGenerator - 归并段生成器

#### 2.3.1 内部排序法

```python
class RunGenerator:
    """内部排序法生成归并段"""

    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        """
        算法流程:
        1. 从迭代器读取数据到缓冲区
        2. 当缓冲区满时:
           a. 对缓冲区排序
           b. 写入临时文件
           c. 清空缓冲区
        3. 处理剩余数据
        """
        current_buffer: List[Any] = []
        current_size = 0

        for item in data_iter:
            item_size = self._estimate_size(item)

            if current_size + item_size > self._memory_limit:
                self._write_run(current_buffer, output_dir)
                current_buffer = []
                current_size = 0

            current_buffer.append(item)
            current_size += item_size

        if current_buffer:
            self._write_run(current_buffer, output_dir)
```

#### 2.3.2 置换选择排序

```python
class ReplacementSelectionV2:
    """改进版置换选择排序"""

    def generate_from_iterator(self, data_iter: Iterator[Any],
                               output_dir: Optional[str] = None) -> List[str]:
        """
        算法流程:
        1. 初始化: 读取 M 个元素到最小堆
        2. 输出堆顶元素，记为 last_output
        3. 从输入读取下一个元素:
           - 如果 new_item >= last_output:
             加入堆（当前归并段）
           - 否则:
             暂存到 next_run_buffer
        4. 当堆为空时:
           a. 写入当前归并段
           b. 将暂存元素放入堆
           c. 开始新归并段
        """
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

### 2.4 KWayMerger - 多路归并器

#### 2.4.1 基本归并

```python
class KWayMerger:
    """K 路归并器"""

    def merge_files(self, input_files: List[str], output_file: str,
                    parse_func: Optional[Callable] = None) -> int:
        """
        算法流程:
        1. 打开所有输入文件
        2. 读取每个文件的第一个元素到堆
        3. 重复以下步骤直到堆为空:
           a. 弹出堆顶元素
           b. 写入输出文件
           c. 从对应文件读取下一个元素
           d. 如果有下一个元素，加入堆
        4. 关闭所有文件
        """
        # 初始化堆
        for i, filepath in enumerate(input_files):
            reader = BufferedReader(filepath)
            line = reader.read()
            if line:
                value = parse_func(line)
                heap.push((value, i))

        # 归并
        while heap:
            value, reader_idx = heap.pop()
            writer.write(value)

            line = readers[reader_idx].read()
            if line:
                next_value = parse_func(line)
                heap.push((next_value, reader_idx))
```

#### 2.4.2 多趟归并

```python
def multi_pass_merge(self, input_files: List[str], output_file: str,
                     max_merge_ways: int = 10,
                     temp_dir: Optional[str] = None) -> int:
    """
    算法流程:
    1. 如果归并段数 <= max_merge_ways:
       直接归并
    2. 否则:
       a. 将归并段分成若干组，每组最多 max_merge_ways 个
       b. 对每组进行归并，生成中间结果
       c. 对中间结果递归进行多趟归并
    """
    if len(input_files) <= max_merge_ways:
        return self.merge_files(input_files, output_file)

    current_files = input_files
    while len(current_files) > max_merge_ways:
        next_files = []
        for i in range(0, len(current_files), max_merge_ways):
            batch = current_files[i:i + max_merge_ways]
            temp_output = f"pass_{pass_num}_batch_{i}.txt"
            self.merge_files(batch, temp_output)
            next_files.append(temp_output)
        current_files = next_files

    return self.merge_files(current_files, output_file)
```

## 3. 数据流设计

### 3.1 排序流程

```
输入文件
    │
    ▼
┌─────────────────┐
│  RunGenerator   │
│  (生成归并段)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  run_0000.txt   │
│  run_0001.txt   │
│  run_0002.txt   │
│  ...            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  KWayMerger     │
│  (多路归并)      │
└────────┬────────┘
         │
         ▼
输出文件
```

### 3.2 内存使用

```
┌─────────────────────────────────────────┐
│              内存布局                    │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │        堆内存 (O(K))            │    │
│  │  - K 个归并段的当前元素         │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │     读缓冲区 (O(B × K))        │    │
│  │  - 每个归并段一个缓冲区         │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │     写缓冲区 (O(B))            │    │
│  │  - 输出文件的一个缓冲区         │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 4. 接口设计

### 4.1 核心接口

```python
class ExternalSorter:
    """外部排序器主接口"""

    def __init__(self,
                 memory_limit: int = 1024 * 1024,
                 max_merge_ways: int = 10,
                 buffer_size: int = 512 * 1024,
                 key_func: Optional[Callable] = None,
                 use_replacement_selection: bool = True,
                 temp_dir: Optional[str] = None):
        """
        初始化参数:
        - memory_limit: 内存限制（字节）
        - max_merge_ways: 最大归并路数
        - buffer_size: I/O 缓冲区大小
        - key_func: 排序键提取函数
        - use_replacement_selection: 是否使用置换选择排序
        - temp_dir: 临时文件目录
        """
        pass

    def sort_file(self, input_file: str, output_file: str,
                  parse_func: Optional[Callable] = None) -> int:
        """
        对文件进行外部排序。

        返回: 排序后的记录数
        """
        pass

    @property
    def stats(self) -> dict:
        """
        排序统计信息。

        返回: 包含统计信息的字典
        - total_records: 总记录数
        - total_runs: 归并段数
        - merge_passes: 归并趟数
        - run_generation_time: 归并段生成时间
        - merge_time: 归并时间
        - total_time: 总时间
        """
        pass
```

### 4.2 应用接口

```python
class LargeFileSorter:
    """大文件排序器"""

    def sort(self, input_file: str, output_file: str,
             key_func: Optional[Callable] = None,
             parse_func: Optional[Callable] = None) -> int:
        pass

class LogSorter:
    """日志排序器"""

    def sort_by_timestamp(self, input_file: str, output_file: str,
                          timestamp_field: int = 0,
                          separator: str = " ") -> int:
        pass

    def sort_by_field(self, input_file: str, output_file: str,
                      field_index: int = 0,
                      separator: str = ",",
                      reverse: bool = False) -> int:
        pass

class DatabaseSorter:
    """数据库排序器"""

    def sort_by_columns(self, input_file: str, output_file: str,
                        sort_columns: List[int],
                        separator: str = ",",
                        reverse_flags: Optional[List[bool]] = None,
                        header: bool = True) -> int:
        pass
```

## 5. 错误处理设计

### 5.1 异常类型

```python
class ExternalSortError(Exception):
    """外部排序基础异常"""
    pass

class FileNotFoundError(ExternalSortError):
    """文件不存在"""
    pass

class DiskSpaceError(ExternalSortError):
    """磁盘空间不足"""
    pass

class MemoryError(ExternalSortError):
    """内存不足"""
    pass

class DataFormatError(ExternalSortError):
    """数据格式错误"""
    pass
```

### 5.2 错误处理策略

```python
def sort_file(self, input_file: str, output_file: str, ...) -> int:
    try:
        # 执行排序
        ...
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file}")
    except OSError as e:
        if "No space left" in str(e):
            raise DiskSpaceError("Disk space insufficient")
        raise
    except MemoryError:
        raise MemoryError("Memory insufficient, try increasing memory_limit")
    finally:
        # 清理临时文件
        self._cleanup_temp(temp_dir)
```

## 6. 性能优化设计

### 6.1 I/O 优化

**批量读写**:
- 使用缓冲区批量读写数据
- 减少系统调用次数
- 提高磁盘利用率

**顺序访问**:
- 尽量使用顺序读写
- 避免随机访问
- 利用磁盘预读机制

### 6.2 内存优化

**流式处理**:
- 不一次性加载所有数据
- 使用迭代器逐条处理
- 内存使用稳定

**缓冲区管理**:
- 合理设置缓冲区大小
- 及时释放不需要的内存
- 避免内存碎片

### 6.3 算法优化

**置换选择排序**:
- 生成更长的归并段
- 减少归并趟数
- 提高整体效率

**多路归并平衡**:
- 平衡归并路数和堆操作开销
- 选择最优的归并路数
- 减少总 I/O 次数

## 7. 可扩展性设计

### 7.1 数据类型扩展

```python
class CustomType:
    """自定义数据类型示例"""

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __lt__(self, other):
        return self.key < other.key

# 使用自定义类型
sorter = ExternalSorter(key_func=lambda x: x.key)
```

### 7.2 解析函数扩展

```python
def custom_parse(line: str) -> Any:
    """自定义解析函数"""
    parts = line.split(',')
    return {
        'name': parts[0],
        'age': int(parts[1]),
        'score': float(parts[2]),
    }

sorter.sort_file(input_file, output_file, parse_func=custom_parse)
```

### 7.3 输出格式扩展

```python
def custom_format(item: Any) -> str:
    """自定义格式化函数"""
    return f"{item['name']},{item['age']},{item['score']}"

# 可以通过覆盖 _write_run 方法实现
```

## 8. 测试设计

### 8.1 单元测试

```
tests/
├── test_min_heap.py         # 最小堆测试
├── test_io_buffer.py        # I/O 缓冲区测试
├── test_run_generator.py    # 归并段生成器测试
├── test_kway_merger.py      # 多路归并器测试
└── test_external_sort.py    # 主排序模块测试
```

### 8.2 测试策略

**功能测试**:
- 基本排序功能
- 自定义排序规则
- 边界情况

**性能测试**:
- 大数据集排序
- 内存使用监控
- I/O 次数统计

**压力测试**:
- 超大数据集
- 极小内存限制
- 并发访问

## 9. 部署设计

### 9.1 目录结构

```
external-sort/
├── src/           # 源代码
├── tests/         # 测试代码
├── examples/      # 示例代码
├── docs/          # 文档
└── requirements.txt
```

### 9.2 依赖管理

```txt
# requirements.txt
# 无第三方依赖，仅使用标准库
```

### 9.3 安装方式

```bash
# 直接使用
cd projects/external-sort
python -c "from src import ExternalSorter"

# 或添加到 Python 路径
export PYTHONPATH=$PYTHONPATH:/path/to/external-sort
```
