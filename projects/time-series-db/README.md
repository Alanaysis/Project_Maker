# 🕐 Time Series Database / 时间序列数据库

> A learning implementation of time series data storage and querying with compression algorithms.
> 实现时序数据存储和查询的学习项目。

---

## 📖 Overview / 项目概述

**English**: This project implements a simplified time series database from scratch to help understand the core concepts behind systems like InfluxDB, TimescaleDB, and Prometheus. It covers data models, indexing, compression algorithms, and aggregation queries.

**中文**: 本项目从零实现了一个简化的时序数据库，帮助理解 InfluxDB、TimescaleDB 和 Prometheus 等系统的核心概念。涵盖数据模型、索引、压缩算法和聚合查询。

### Core Data Flow / 核心数据流

```
Data Write → Time Index → Compressed Storage → Aggregation Query
数据写入 → 时间索引 → 压缩存储 → 聚合查询
```

---

## 🎯 Learning Objectives / 学习目标

### English
1. **Understand Time Series Data Characteristics** - Learn how time series data differs from relational data
2. **Master Compression Algorithms** - Implement and compare delta encoding, delta-of-delta, and RLE
3. **Learn Aggregation Queries** - Implement downsampling with avg/min/max/sum operations
4. **Build a Time Index** - Implement efficient range queries using binary search
5. **Tag-Based Filtering** - Implement metadata-based series discovery

### 中文
1. **理解时序数据特点** - 学习时序数据与关系型数据的区别
2. **掌握压缩算法** - 实现并对比 delta 编码、delta-of-delta 和 RLE
3. **学会聚合查询** - 实现 avg/min/max/sum 下采样操作
4. **构建时间索引** - 使用二分查找实现高效的范围查询
5. **基于标签的过滤** - 实现基于元数据的系列发现

---

## 🏗️ Architecture / 架构

```
time-series-db/
├── src/                    # Core package
│   ├── tsdb.go             # Main types: Storage, Series, Point, compression
│   ├── series.go           # Series management operations
│   ├── mock_data.go        # Mock data generators for testing
│   └── tsdb_test.go        # Unit tests
├── examples/               # Demo programs
│   ├── 01_basic_query.go        # Basic write and query operations
│   ├── 02_compression_demo.go   # Compression ratio demonstration
│   ├── 03_aggregation_demo.go   # Aggregation queries (downsampling)
│   └── 04_range_filter_demo.go  # Time range queries with filtering
├── tests/                  # Additional test files
├── README.md               # This file
└── go.mod                  # Go module definition
```

---

## 🚀 How to Run / 如何运行

### Prerequisites / 前置条件
- Go 1.22+ required
- Go 1.22+ 必需

### Run Examples / 运行示例

```bash
cd projects/time-series-db

# Example 1: Basic write and query
go run examples/01_basic_query.go

# Example 2: Compression ratio demonstration
go run examples/02_compression_demo.go

# Example 3: Aggregation queries (downsampling)
go run examples/03_aggregation_demo.go

# Example 4: Time range queries with filtering
go run examples/04_range_filter_demo.go
```

### Run Tests / 运行测试

```bash
# Run all tests
go test ./src/...

# Run with verbose output
go test -v ./src/...

# Run with coverage
go test -cover ./src/...
```

---

## 📊 Compression Algorithms / 压缩算法

### 1. Delta Encoding / Delta 编码

**Purpose**: Compress timestamps by storing differences between consecutive values.
**用途**: 通过存储连续值之间的差值来压缩时间戳。

For time series data, consecutive timestamps are usually close together. Instead of storing
full 64-bit timestamps, we store the difference (delta), which often fits in fewer bytes
when further compressed.

时序数据中，连续时间戳通常很接近。我们存储差值（delta）而不是完整的 64 位时间戳，
这样在进一步压缩时通常能节省空间。

```
Original:  [1000, 1010, 1020, 1035]
Deltas:     [1000,   10,   10,   15]
```

### 2. Delta-of-Delta Encoding / Delta-of-Delta 编码

**Purpose**: Further compress timestamps with regular intervals.
**用途**: 进一步压缩具有固定间隔的时间戳。

When data points arrive at regular intervals (e.g., every 10 seconds), the deltas
themselves are constant. Taking the delta of deltas produces mostly zeros.

当数据点以固定间隔到达时（例如每 10 秒），差值本身是常数。对差值再取差值会产生大量零。

```
Original:  [1000, 1010, 1020, 1030, 1040]
Deltas:     [1000,   10,   10,   10,   10]
D-of-D:     [1000,   10,    0,    0,    0]  ← Mostly zeros!
```

### 3. Run-Length Encoding (RLE) / 游程编码

**Purpose**: Compress repeated values (useful for constant sensor readings).
**用途**: 压缩重复的值（对恒定传感器读数有用）。

RLE replaces consecutive identical values with (value, count) pairs.

RLE 用 (值, 计数) 对替换连续的相同值。

```
Original:  [1.0, 1.0, 1.0, 2.5, 2.5, 3.0]
RLE:       [1.0, 3, 2.5, 2, 3.0, 1]
```

---

## 📚 Key Concepts / 关键概念

### Time Series Data Model / 时序数据模型

```go
type Point struct {
    Timestamp int64              // Unix nanosecond timestamp
    Value     float64             // Numeric value
    Tags      map[string]string   // Key-value labels
}

type Series struct {
    ID     string      // Unique identifier
    Points []Point     // Sorted by timestamp
}
```

### Time Index / 时间索引

The time index uses binary search to find data points within a time range in O(log n) time.
时间索引使用二分查找在 O(log n) 时间内找到时间范围内的数据点。

```go
// Find points between 10:00 and 11:00
start, end := index.FindRange(startTs, endTs)
```

### Downsampling / 下采样

Downsampling groups data points into fixed-width time buckets and computes an aggregate
per bucket. This reduces data volume while preserving trends.

下采样将数据点分组到固定宽度的时间桶中，并计算每个桶的聚合值。这在保留趋势的同时减少数据量。

```go
// Average every 5 minutes
result, _ := storage.Downsample("cpu.usage", tsdb.AggAvg, 5*time.Minute, start, end)
```

---

## 📈 Performance Characteristics / 性能特征

| Operation / 操作 | Complexity / 复杂度 | Notes / 说明 |
|-----------------|---------------------|-------------|
| Write (append) | O(n log n) | Sorting points by timestamp |
| Range query | O(log n + k) | Binary search + linear scan |
| Tag filter | O(n × m) | n=series, m=points per series |
| Downsample | O(n) | Single pass through points |
| Delta encode | O(n) | Linear scan |
| RLE encode | O(n) | Linear scan |

---

## 🔧 How It Works / 工作原理

### Data Write Flow / 数据写入流程

```
1. Create series with CreateSeries(id, name)
2. Build Point objects with timestamp, value, tags
3. WritePoints() appends and sorts data
4. Time index is rebuilt for O(log n) lookups
5. DataBlock is created with delta/RLE compression
```

### Query Flow / 查询流程

```
1. QueryRange() uses TimeIndex.FindRange() for O(log n) start/end
2. Scan points in range [start, end]
3. Apply tag filters if needed
4. For aggregation: group into time buckets
5. Compute aggregate (avg/min/max/sum) per bucket
```

---

## 📝 Notes / 说明

- This is a **learning implementation**, not a production-ready database.
- Data is stored **in-memory** with optional file persistence.
- Compression is applied at the **block level** (per write batch).
- For production use, consider InfluxDB, TimescaleDB, or VictoriaMetrics.

---

## 📄 License / 许可证

MIT License
