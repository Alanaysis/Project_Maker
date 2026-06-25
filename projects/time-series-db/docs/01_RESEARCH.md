# 研究文档: 时间序列数据库

## 1. 背景

时间序列数据 (Time Series Data) 是按时间顺序排列的数据点序列，广泛应用于:
- 系统监控 (CPU、内存、网络)
- IoT 传感器数据
- 金融交易数据
- 应用性能监控 (APM)

## 2. 现有解决方案分析

### 2.1 专业时序数据库

| 数据库 | 语言 | 特点 | 适用场景 |
|--------|------|------|----------|
| InfluxDB | Go | 高性能、SQL-like 查询 | 通用时序数据 |
| TimescaleDB | C | PostgreSQL 扩展、SQL 支持 | 需要 SQL 的场景 |
| Prometheus | Go | 拉取模型、内置可视化 | 监控告警 |
| QuestDB | Java/C++ | 超高写入性能 | 高吞吐场景 |

### 2.2 通用数据库方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| Redis + 时间戳 | 极快读写 | 内存限制、无持久化 |
| PostgreSQL | SQL 支持、成熟 | 时序性能一般 |
| MongoDB | 灵活 schema | 聚合性能一般 |
| ClickHouse | 列式存储、高压缩 | 部署复杂 |

## 3. 核心技术研究

### 3.1 存储结构

#### LSM-Tree (Log-Structured Merge-Tree)
```
内存表 (MemTable) → 不可变内存表 (Immutable MemTable) → SSTable
```

**优点**:
- 写入性能高 (顺序写)
- 支持高效压缩
- 适合写多读少场景

**实现要点**:
- MemTable: 使用跳表或红黑树
- SSTable: 有序字符串表，支持布隆过滤器
- Compaction: 合并多个 SSTable

#### TSM (Time-Structured Merge Tree)
InfluxDB 使用的变体，针对时序数据优化:
- 按时间分片
- 列式存储值
- 时间索引加速查询

### 3.2 数据压缩

#### 时间戳压缩
- Delta 编码: 存储差值而非绝对值
- Delta-of-delta: 进一步压缩规律性时间戳
- Simple8b: 位打包编码

#### 值压缩
- Gorilla 编码: Facebook 提出的浮点数压缩
- Run-Length Encoding (RLE): 适合重复值
- Dictionary Encoding: 适合低基数标签

### 3.3 查询优化

#### 时间分区
```
数据按时间分区存储
├── 2024-01/
│   ├── cpu_usage.001
│   └── cpu_usage.002
├── 2024-02/
│   └── cpu_usage.001
└── ...
```

#### 索引策略
- 时间索引: B+ 树或跳表
- 标签索引: 倒排索引
- 复合索引: (metric, tags, time)

### 3.4 写入优化

#### 批量写入
```python
# 差: 逐条写入
for point in points:
    db.write(point)

# 好: 批量写入
db.write_batch(points)
```

#### WAL (Write-Ahead Log)
1. 先写 WAL (顺序写，快)
2. 再写 MemTable (内存)
3. MemTable 满后刷盘
4. WAL 可清理

## 4. 数据模型设计

### 4.1 点模型 (Point Model)
```json
{
    "metric": "cpu_usage",
    "tags": {
        "host": "server1",
        "region": "us-east"
    },
    "timestamp": 1625097600,
    "value": 45.2
}
```

### 4.2 多值模型 (Multi-Value Model)
```json
{
    "metric": "system_metrics",
    "tags": {"host": "server1"},
    "timestamp": 1625097600,
    "fields": {
        "cpu": 45.2,
        "memory": 8192,
        "disk_io": 1024
    }
}
```

### 4.3 本项目选择
采用单值模型，原因:
- 简单直观
- 灵活性高
- 便于压缩

## 5. 关键算法

### 5.1 降采样算法
```python
def downsample(points, interval, aggregation):
    """将数据点降采样到指定间隔"""
    buckets = {}
    for point in points:
        bucket_key = (point.timestamp // interval) * interval
        if bucket_key not in buckets:
            buckets[bucket_key] = []
        buckets[bucket_key].append(point.value)

    results = []
    for timestamp, values in sorted(buckets.items()):
        if aggregation == "avg":
            value = sum(values) / len(values)
        elif aggregation == "max":
            value = max(values)
        # ...
        results.append({"timestamp": timestamp, "value": value})
    return results
```

### 5.2 TTL 过期算法
```python
def cleanup_expired(data_dir, current_time):
    """清理过期数据"""
    for partition in list_partitions(data_dir):
        if partition.end_time < current_time - retention_period:
            delete_partition(partition)
```

## 6. 性能基准

### 6.1 写入性能目标
- 单点写入: > 10,000 points/sec
- 批量写入: > 100,000 points/sec
- 批量大小: 1000-5000 points

### 6.2 查询性能目标
- 时间范围查询: < 10ms (1M points)
- 聚合查询: < 50ms (1M points)
- 降采样查询: < 100ms (10M points)

## 7. 技术选型

### 7.1 编程语言: Python
**选择理由**:
- 开发效率高
- 丰富的数据处理库
- 易于测试和调试
- 适合原型开发

**优化手段**:
- 使用 mmap 提升 I/O 性能
- 使用 struct 进行二进制序列化
- 使用 lz4/zstd 进行压缩

### 7.2 依赖库
- `uvloop`: 高性能事件循环
- `lz4`: 快速压缩
- `msgpack`: 高效序列化
- `aiohttp`: 异步 HTTP 服务

## 8. 参考资料

1. InfluxDB Storage Engine: https://docs.influxdata.com/influxdb/v2/storage-engine/
2. Facebook Gorilla Paper: http://www.vldb.org/pvldb/vol8/p1816-teller.pdf
3. LSM-Tree Paper: https://www.cs.umb.edu/~poneil/lsmtree.pdf
4. Time Series Compression Algorithms: https://www.timescale.com/blog/time-series-compression-algorithms-explained/
