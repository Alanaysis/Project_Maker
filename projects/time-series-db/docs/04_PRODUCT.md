# 产品文档: 时间序列数据库

## 1. 产品概述

### 1.1 产品定位
轻量级时间序列数据库，专为以下场景优化:
- 系统监控数据存储
- IoT 传感器数据存储
- 应用性能监控 (APM)

### 1.2 目标用户
- DevOps 工程师
- IoT 开发者
- 数据工程师

### 1.3 核心价值
- **简单易用**: 零配置，开箱即用
- **高性能**: 专为时序数据优化
- **轻量级**: 无外部依赖，资源占用低

## 2. 功能特性

### 2.1 数据写入

#### 批量写入
```python
db.write_batch([
    {
        "metric": "cpu_usage",
        "tags": {"host": "server1"},
        "timestamp": 1625097600,
        "value": 45.2
    },
    {
        "metric": "cpu_usage",
        "tags": {"host": "server1"},
        "timestamp": 1625097660,
        "value": 46.8
    }
])
```

#### 时间戳排序
- 自动按时间戳排序
- 支持乱序写入
- 支持重复时间戳 (覆盖)

#### 数据压缩
- 时间戳 Delta 编码
- 值 Gorilla 编码
- 压缩率 > 10:1

### 2.2 数据查询

#### 时间范围查询
```python
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600
)
```

#### 聚合查询
```python
# 平均值
avg = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    aggregation="avg"
)

# 最大值
max_val = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    aggregation="max"
)

# 多聚合
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    aggregation=["avg", "max", "min"]
)
```

#### 降采样
```python
# 每分钟平均值
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    downsample="1m",
    aggregation="avg"
)

# 每小时最大值
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    downsample="1h",
    aggregation="max"
)
```

### 2.3 数据保留

#### TTL 配置
```python
# 全局默认 TTL
db = TimeSeriesDB(default_ttl=86400 * 30)  # 30天

# Metric 级别 TTL
db.set_ttl("cpu_usage", 86400 * 7)  # 7天
db.set_ttl("memory_usage", 86400 * 30)  # 30天
```

#### 自动清理
- 后台定期检查
- 支持手动触发
- 日志记录清理操作

## 3. API 参考

### 3.1 REST API

#### 写入数据
```
POST /write
Content-Type: application/json

Request:
{
    "metric": "cpu_usage",
    "tags": {
        "host": "server1",
        "region": "us-east"
    },
    "points": [
        {"timestamp": 1625097600, "value": 45.2},
        {"timestamp": 1625097660, "value": 46.8}
    ]
}

Response:
{
    "status": "ok",
    "written": 2
}
```

#### 查询数据
```
GET /query
Parameters:
- metric (required): 指标名称
- start (required): 开始时间戳
- end (required): 结束时间戳
- tags (optional): 标签过滤，格式 key=value
- aggregation (optional): 聚合函数 (avg/max/min/sum/count)
- downsample (optional): 降采样间隔 (1s/1m/1h/1d)

Response:
{
    "metric": "cpu_usage",
    "points": [
        {"timestamp": 1625097600, "value": 45.2},
        {"timestamp": 1625097660, "value": 46.8}
    ],
    "count": 2
}
```

#### 批量查询
```
POST /query/batch
Content-Type: application/json

Request:
{
    "queries": [
        {
            "metric": "cpu_usage",
            "start": 1625097600,
            "end": 1625098600,
            "aggregation": "avg"
        },
        {
            "metric": "memory_usage",
            "start": 1625097600,
            "end": 1625098600
        }
    ]
}

Response:
{
    "results": [
        {
            "metric": "cpu_usage",
            "points": [...],
            "aggregation": "avg"
        },
        {
            "metric": "memory_usage",
            "points": [...]
        }
    ]
}
```

#### 健康检查
```
GET /health

Response:
{
    "status": "ok",
    "version": "1.0.0",
    "uptime": 3600,
    "metrics": {
        "write_qps": 1234,
        "query_qps": 567,
        "storage_size": 1073741824,
        "memory_usage": 134217728
    }
}
```

### 3.2 Python API

```python
from src.db import TimeSeriesDB

# 初始化
db = TimeSeriesDB(data_dir="./data")

# 写入
db.write(
    metric="cpu_usage",
    tags={"host": "server1"},
    timestamp=1625097600,
    value=45.2
)

# 批量写入
db.write_batch([...])

# 查询
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600
)

# 聚合查询
avg = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    aggregation="avg"
)

# 降采样
results = db.query(
    metric="cpu_usage",
    start=1625097600,
    end=1625098600,
    downsample="1m",
    aggregation="avg"
)

# 设置 TTL
db.set_ttl("cpu_usage", 86400 * 30)

# 关闭
db.close()
```

## 4. 使用场景

### 4.1 系统监控

#### 场景描述
监控 100 台服务器的 CPU、内存、磁盘、网络指标。

#### 数据模型
```python
# CPU 使用率
db.write(
    metric="cpu_usage",
    tags={"host": "web-server-1", "region": "us-east"},
    timestamp=timestamp,
    value=45.2
)

# 内存使用
db.write(
    metric="memory_usage",
    tags={"host": "web-server-1", "region": "us-east"},
    timestamp=timestamp,
    value=8192
)
```

#### 查询示例
```python
# 查询最近 1 小时的平均 CPU
avg_cpu = db.query(
    metric="cpu_usage",
    start=now - 3600,
    end=now,
    tags={"host": "web-server-1"},
    aggregation="avg"
)

# 查询所有服务器的 CPU 最大值
max_cpu = db.query(
    metric="cpu_usage",
    start=now - 3600,
    end=now,
    aggregation="max"
)

# 按小时降采样
hourly_avg = db.query(
    metric="cpu_usage",
    start=now - 86400,
    end=now,
    downsample="1h",
    aggregation="avg"
)
```

### 4.2 IoT 传感器

#### 场景描述
1000 个温度传感器，每分钟采集一次，保留 90 天。

#### 数据模型
```python
db.write(
    metric="temperature",
    tags={
        "device": "sensor-001",
        "location": "warehouse-A",
        "floor": "1"
    },
    timestamp=timestamp,
    value=23.5
)
```

#### 查询示例
```python
# 查询某个仓库的温度
temps = db.query(
    metric="temperature",
    start=now - 3600,
    end=now,
    tags={"location": "warehouse-A"}
)

# 查询温度异常 (超过阈值)
def check_temperature_alert(threshold=30):
    results = db.query(
        metric="temperature",
        start=now - 300,
        end=now
    )
    alerts = [r for r in results if r["value"] > threshold]
    return alerts
```

### 4.3 应用性能监控

#### 场景描述
监控 Web 应用的请求延迟、错误率、吞吐量。

#### 数据模型
```python
# 请求延迟
db.write(
    metric="request_latency",
    tags={
        "service": "api-gateway",
        "endpoint": "/api/users",
        "method": "GET"
    },
    timestamp=timestamp,
    value=125.5  # 毫秒
)

# 错误率
db.write(
    metric="error_rate",
    tags={"service": "api-gateway"},
    timestamp=timestamp,
    value=0.02  # 2%
)
```

#### 查询示例
```python
# P99 延迟
p99_latency = db.query(
    metric="request_latency",
    start=now - 3600,
    end=now,
    tags={"service": "api-gateway"},
    aggregation="p99"  # 自定义聚合
)

# 错误率趋势
error_trend = db.query(
    metric="error_rate",
    start=now - 86400,
    end=now,
    downsample="1h",
    aggregation="avg"
)
```

## 5. 配置说明

### 5.1 配置文件
```yaml
# config.yaml
storage:
  data_dir: "./data"
  memtable_max_size: 67108864  # 64MB
  flush_interval: 60
  compression: "lz4"

wal:
  enabled: true
  max_file_size: 67108864
  sync: true

query:
  max_points: 1000000
  timeout: 30

retention:
  default_ttl: null
  cleanup_interval: 3600

server:
  host: "0.0.0.0"
  port: 8080
  workers: 4
```

### 5.2 环境变量
```bash
TSDB_DATA_DIR=./data
TSDB_HOST=0.0.0.0
TSDB_PORT=8080
TSDB_LOG_LEVEL=INFO
```

## 6. 监控指标

### 6.1 性能指标
| 指标 | 说明 | 单位 |
|------|------|------|
| write_qps | 写入 QPS | points/sec |
| query_qps | 查询 QPS | queries/sec |
| write_latency | 写入延迟 | ms |
| query_latency | 查询延迟 | ms |

### 6.2 存储指标
| 指标 | 说明 | 单位 |
|------|------|------|
| storage_size | 存储大小 | bytes |
| memtable_size | 内存表大小 | bytes |
| sstable_count | SSTable 数量 | 个 |
| compression_ratio | 压缩率 | - |

### 6.3 系统指标
| 指标 | 说明 | 单位 |
|------|------|------|
| memory_usage | 内存使用 | bytes |
| cpu_usage | CPU 使用 | % |
| disk_io | 磁盘 I/O | bytes/sec |

## 7. 故障处理

### 7.1 常见问题

#### 写入失败
**症状**: 返回写入错误
**原因**: 磁盘空间不足、权限问题
**处理**: 检查磁盘空间、检查文件权限

#### 查询超时
**症状**: 查询超时
**原因**: 数据量过大、索引损坏
**处理**: 缩小查询范围、重建索引

#### 数据丢失
**症状**: 查询结果不完整
**原因**: WAL 未同步、进程崩溃
**处理**: 从 WAL 恢复、检查数据完整性

### 7.2 数据恢复

#### 从 WAL 恢复
```bash
python -m src.tools.recover_wal --data-dir ./data
```

#### 重建索引
```bash
python -m src.tools.rebuild_index --data-dir ./data
```

## 8. 最佳实践

### 8.1 数据模型设计
- 使用有意义的 metric 名称
- 合理使用 tags，避免高基数
- 保持 tag 值的一致性

### 8.2 查询优化
- 缩小时间范围
- 使用降采样减少数据量
- 使用标签过滤减少扫描范围

### 8.3 存储优化
- 合理设置 TTL
- 定期清理过期数据
- 监控存储使用量
