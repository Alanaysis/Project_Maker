# 时间序列数据库 (Time Series Database)

一个轻量级的时间序列数据库，专为监控数据和 IoT 数据存储设计。

## 特性

- **高性能写入**: 批量写入、时间戳排序、数据压缩
- **灵活查询**: 时间范围查询、聚合查询 (avg/max/min/sum/count)、降采样
- **可靠存储**: 内存表 + WAL + 持久化
- **数据保留**: TTL 过期、自动清理

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│                    (HTTP REST API)                          │
├─────────────────────────────────────────────────────────────┤
│                      Query Layer                            │
│              (Executor, Aggregation, Downsampling)          │
├─────────────────────────────────────────────────────────────┤
│                     Storage Engine                          │
│           (MemTable, WAL, Persistent Storage)               │
├─────────────────────────────────────────────────────────────┤
│                   Retention Manager                         │
│                   (TTL, Auto Cleanup)                       │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
time-series-db/
├── src/
│   ├── engine/          # 存储引擎
│   │   ├── memtable.py  # 内存表
│   │   ├── wal.py       # Write-Ahead Log
│   │   └── storage.py   # 持久化存储
│   ├── query/           # 查询层
│   │   ├── executor.py  # 查询执行器
│   │   ├── aggregation.py
│   │   └── downsampling.py
│   ├── retention/       # 数据保留
│   │   └── ttl.py
│   ├── api/             # API 层
│   │   └── server.py
│   └── db.py            # 主入口
├── tests/
├── examples/
└── docs/
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python -m src.api.server
```

### API 使用

#### 写入数据

```bash
curl -X POST http://localhost:8080/write \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "cpu_usage",
    "tags": {"host": "server1", "region": "us-east"},
    "points": [
      {"timestamp": 1625097600, "value": 45.2},
      {"timestamp": 1625097660, "value": 46.8}
    ]
  }'
```

#### 查询数据

```bash
# 时间范围查询
curl "http://localhost:8080/query?metric=cpu_usage&start=1625097600&end=1625097700"

# 聚合查询
curl "http://localhost:8080/query?metric=cpu_usage&start=1625097600&end=1625097700&agg=avg"

# 降采样
curl "http://localhost:8080/query?metric=cpu_usage&start=1625097600&end=1625098600&downsample=60"
```

## 应用场景

### 监控数据存储

```python
from src.db import TimeSeriesDB

db = TimeSeriesDB(data_dir="./monitoring_data")

# 写入监控数据
db.write(
    metric="cpu_usage",
    tags={"host": "web-server-1"},
    points=[
        {"timestamp": 1625097600, "value": 45.2},
        {"timestamp": 1625097660, "value": 46.8}
    ]
)

# 查询并聚合
result = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    aggregation="avg",
    downsample=60  # 每60秒一个点
)
```

### IoT 数据存储

```python
from src.db import TimeSeriesDB

db = TimeSeriesDB(data_dir="./iot_data", default_ttl=86400*30)  # 30天保留

# 写入传感器数据
db.write(
    metric="temperature",
    tags={"device": "sensor-001", "location": "warehouse-A"},
    points=[
        {"timestamp": 1625097600, "value": 23.5},
        {"timestamp": 1625097660, "value": 23.6}
    ]
)
```

## 文档

- [研究文档](docs/01_RESEARCH.md)
- [需求文档](docs/02_REQUIREMENTS.md)
- [设计文档](docs/03_DESIGN.md)
- [产品文档](docs/04_PRODUCT.md)
- [开发文档](docs/05_DEVELOPMENT.md)

## 性能指标

| 操作 | 性能 |
|------|------|
| 批量写入 | 100,000 points/sec |
| 时间范围查询 | < 10ms (1M points) |
| 聚合查询 | < 50ms (1M points) |
| 降采样查询 | < 100ms (10M points) |

## 技术栈

- Python 3.10+
- 内存映射文件 (mmap)
- 二进制序列化
- 压缩算法: LZ4 / Zstandard

## 许可证

MIT License
