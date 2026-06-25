# 设计文档: 时间序列数据库

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          API Layer                              │
│                    (HTTP REST API Server)                       │
├─────────────────────────────────────────────────────────────────┤
│                        Query Layer                              │
│           (QueryExecutor, Aggregator, Downsampler)              │
├─────────────────────────────────────────────────────────────────┤
│                       Storage Engine                            │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│     │ MemTable │  │   WAL    │  │  SSTable │  │ Compactor│    │
│     └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    Retention Manager                            │
│                   (TTL, Auto Cleanup)                           │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 存储引擎设计

### 2.1 内存表 (MemTable)

#### 数据结构
使用跳表 (Skip List) 实现，支持:
- O(log n) 插入
- O(log n) 查找
- 有序遍历

```python
class MemTable:
    def __init__(self, max_size=64*1024*1024):  # 64MB
        self.data = SortedDict()  # {timestamp: value}
        self.size = 0
        self.max_size = max_size

    def put(self, timestamp, value):
        self.data[timestamp] = value
        self.size += self._estimate_size(timestamp, value)

    def get(self, timestamp):
        return self.data.get(timestamp)

    def range_query(self, start, end):
        return [(ts, v) for ts, v in self.data.items()
                if start <= ts <= end]

    def is_full(self):
        return self.size >= self.max_size
```

#### 刷盘策略
1. **大小触发**: MemTable 达到阈值 (默认 64MB)
2. **时间触发**: 定时刷盘 (默认 60 秒)
3. **手动触发**: API 调用

### 2.2 WAL (Write-Ahead Log)

#### 文件格式
```
┌─────────────────────────────────────────────────────────┐
│                    WAL File Format                       │
├─────────────────────────────────────────────────────────┤
│  Header (16 bytes)                                      │
│  ├── Magic Number (4 bytes): 0x57414C00                │
│  ├── Version (4 bytes): 1                              │
│  ├── Created At (8 bytes): timestamp                   │
├─────────────────────────────────────────────────────────┤
│  Entry 1                                                │
│  ├── Length (4 bytes)                                   │
│  ├── CRC32 (4 bytes)                                   │
│  ├── Data (variable)                                   │
├─────────────────────────────────────────────────────────┤
│  Entry 2                                                │
│  ├── Length (4 bytes)                                   │
│  ├── CRC32 (4 bytes)                                   │
│  ├── Data (variable)                                   │
├─────────────────────────────────────────────────────────┤
│  ...                                                    │
└─────────────────────────────────────────────────────────┘
```

#### WAL 操作
```python
class WAL:
    def __init__(self, wal_dir):
        self.wal_dir = wal_dir
        self.current_file = None
        self.current_size = 0
        self.max_file_size = 64 * 1024 * 1024  # 64MB

    def write(self, metric, tags, timestamp, value):
        entry = self._encode_entry(metric, tags, timestamp, value)
        crc = crc32(entry)
        self.current_file.write(pack('I', len(entry)))
        self.current_file.write(pack('I', crc))
        self.current_file.write(entry)
        self.current_file.flush()

    def recover(self):
        """从 WAL 恢复数据到 MemTable"""
        for wal_file in self._list_wal_files():
            for entry in self._read_entries(wal_file):
                yield entry
```

### 2.3 SSTable (Sorted String Table)

#### 文件格式
```
┌─────────────────────────────────────────────────────────┐
│                   SSTable File Format                    │
├─────────────────────────────────────────────────────────┤
│  Data Blocks                                            │
│  ├── Block 1 (compressed)                              │
│  ├── Block 2 (compressed)                              │
│  └── ...                                               │
├─────────────────────────────────────────────────────────┤
│  Index Block                                            │
│  ├── Key 1 -> Block 1 offset                           │
│  ├── Key 2 -> Block 2 offset                           │
│  └── ...                                               │
├─────────────────────────────────────────────────────────┤
│  Bloom Filter (optional)                                │
├─────────────────────────────────────────────────────────┤
│  Footer (32 bytes)                                      │
│  ├── Index Offset (8 bytes)                            │
│  ├── Index Size (8 bytes)                              │
│  ├── Bloom Filter Offset (8 bytes)                     │
│  └── Magic Number (8 bytes)                            │
└─────────────────────────────────────────────────────────┘
```

#### 数据块格式
```python
class DataBlock:
    def __init__(self):
        self.timestamps = []  # Delta 编码的时间戳
        self.values = []      # Gorilla 编码的值
        self.tags = {}        # 字典编码的标签
```

### 2.4 数据压缩

#### 时间戳压缩 (Delta + Simple8b)
```python
def compress_timestamps(timestamps):
    """压缩时间戳序列"""
    if not timestamps:
        return b''

    # Delta 编码
    deltas = [timestamps[0]]
    for i in range(1, len(timestamps)):
        deltas.append(timestamps[i] - timestamps[i-1])

    # Simple8b 编码
    return simple8b_encode(deltas)
```

#### 值压缩 (Gorilla)
```python
def compress_values(values):
    """压缩浮点数值序列"""
    if not values:
        return b''

    # XOR 编码
    encoded = []
    prev = values[0]
    encoded.append(struct.pack('d', prev))

    for val in values[1:]:
        xor = struct.unpack('Q', struct.pack('d', val))[0] ^ \
              struct.unpack('Q', struct.pack('d', prev))[0]
        encoded.append(gorilla_encode(xor))
        prev = val

    return b''.join(encoded)
```

## 3. 查询层设计

### 3.1 查询执行器

```python
class QueryExecutor:
    def __init__(self, storage_engine):
        self.storage = storage_engine

    def execute(self, query):
        """执行查询"""
        # 1. 从 MemTable 查询
        memtable_results = self.storage.memtable.range_query(
            query.start, query.end
        )

        # 2. 从 SSTable 查询
        sstable_results = self.storage.query_sstables(
            query.metric, query.start, query.end, query.tags
        )

        # 3. 合并结果
        results = self._merge_results(memtable_results, sstable_results)

        # 4. 应用聚合
        if query.aggregation:
            results = self._apply_aggregation(results, query.aggregation)

        # 5. 应用降采样
        if query.downsample:
            results = self._apply_downsample(results, query.downsample,
                                            query.aggregation)

        return results
```

### 3.2 聚合函数

```python
class Aggregator:
    @staticmethod
    def avg(values):
        return sum(values) / len(values) if values else 0

    @staticmethod
    def max(values):
        return max(values) if values else 0

    @staticmethod
    def min(values):
        return min(values) if values else 0

    @staticmethod
    def sum(values):
        return sum(values)

    @staticmethod
    def count(values):
        return len(values)

    @staticmethod
    def first(values):
        return values[0] if values else 0

    @staticmethod
    def last(values):
        return values[-1] if values else 0

    @staticmethod
    def stddev(values):
        if not values:
            return 0
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return variance ** 0.5
```

### 3.3 降采样

```python
class Downsampler:
    @staticmethod
    def downsample(points, interval, aggregation, fill=None):
        """降采样数据点"""
        if not points:
            return []

        buckets = {}
        for ts, value in points:
            bucket_key = (ts // interval) * interval
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(value)

        results = []
        for ts in sorted(buckets.keys()):
            values = buckets[ts]
            agg_func = getattr(Aggregator, aggregation)
            result_value = agg_func(values)
            results.append((ts, result_value))

        # 处理填充
        if fill is not None:
            results = _fill_gaps(results, interval, fill)

        return results
```

## 4. 数据保留设计

### 4.1 TTL 管理器

```python
class TTLManager:
    def __init__(self, storage_engine, check_interval=3600):
        self.storage = storage_engine
        self.ttl_configs = {}  # {metric: ttl_seconds}
        self.default_ttl = None
        self.check_interval = check_interval

    def set_ttl(self, metric, ttl):
        self.ttl_configs[metric] = ttl

    def get_ttl(self, metric):
        return self.ttl_configs.get(metric, self.default_ttl)

    def cleanup(self):
        """清理过期数据"""
        current_time = time.time()
        for metric, ttl in self.ttl_configs.items():
            cutoff_time = current_time - ttl
            self.storage.delete_before(metric, cutoff_time)
```

### 4.2 分区策略

```
data/
├── 2024/
│   ├── 01/
│   │   ├── cpu_usage/
│   │   │   ├── 000001.sst
│   │   │   └── 000002.sst
│   │   └── memory_usage/
│   │       └── 000001.sst
│   └── 02/
│       └── ...
└── 2025/
    └── ...
```

## 5. 文件组织

### 5.1 目录结构
```
data_dir/
├── wal/
│   ├── 000001.wal
│   ├── 000002.wal
│   └── ...
├── sst/
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── cpu_usage/
│   │   │   │   ├── 000001.sst
│   │   │   │   └── MANIFEST
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── meta/
│   ├── metrics.json      # Metric 元数据
│   └── tags.json         # 标签字典
└── tmp/                  # 临时文件
```

### 5.2 MANIFEST 文件
```json
{
    "version": 1,
    "sstables": [
        {
            "file": "000001.sst",
            "min_timestamp": 1625097600,
            "max_timestamp": 1625098600,
            "size": 1048576,
            "created_at": 1625098700
        }
    ]
}
```

## 6. 并发控制

### 6.1 读写锁
```python
class StorageEngine:
    def __init__(self):
        self.memtable = MemTable()
        self.immutable_memtable = None
        self.write_lock = threading.Lock()
        self.read_lock = threading.RLock()

    def write(self, metric, tags, timestamp, value):
        with self.write_lock:
            self.wal.write(metric, tags, timestamp, value)
            self.memtable.put(metric, tags, timestamp, value)
            if self.memtable.is_full():
                self._flush_memtable()

    def query(self, metric, start, end):
        with self.read_lock:
            results = []
            if self.immutable_memtable:
                results.extend(self.immutable_memtable.range_query(start, end))
            results.extend(self.memtable.range_query(start, end))
            results.extend(self._query_sstables(metric, start, end))
            return sorted(results, key=lambda x: x[0])
```

### 6.2 异步刷盘
```python
class AsyncFlusher(threading.Thread):
    def __init__(self, storage_engine):
        super().__init__(daemon=True)
        self.storage = storage_engine
        self.flush_queue = queue.Queue()

    def run(self):
        while True:
            memtable = self.flush_queue.get()
            self.storage.write_sstable(memtable)
            self.flush_queue.task_done()
```

## 7. 配置参数

```python
DEFAULT_CONFIG = {
    # 存储配置
    "data_dir": "./data",
    "memtable_max_size": 64 * 1024 * 1024,  # 64MB
    "flush_interval": 60,  # 秒
    "sstable_max_size": 256 * 1024 * 1024,  # 256MB

    # WAL 配置
    "wal_max_file_size": 64 * 1024 * 1024,  # 64MB
    "wal_sync": True,

    # 压缩配置
    "compression": "lz4",  # lz4, zstd, none
    "block_size": 4096,

    # 查询配置
    "max_query_points": 1000000,
    "query_timeout": 30,  # 秒

    # 保留配置
    "default_ttl": None,  # 不过期
    "cleanup_interval": 3600,  # 1小时
}
```

## 8. 错误处理

### 8.1 错误类型
```python
class TSDBError(Exception):
    pass

class WriteError(TSDBError):
    pass

class QueryError(TSDBError):
    pass

class StorageError(TSDBError):
    pass

class CorruptionError(StorageError):
    pass
```

### 8.2 错误恢复
1. **WAL 损坏**: 跳过损坏条目，记录日志
2. **SSTable 损坏**: 标记为损坏，从备份恢复
3. **内存不足**: 强制刷盘，释放内存
