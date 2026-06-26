# Distributed Cache System / 分布式缓存系统

> A learning project implementing a distributed cache system with consistent hashing, multiple eviction policies, and cluster support.
> 实现高并发分布式缓存系统的学习项目，包含一致性哈希、多种淘汰策略和集群支持。

---

## English

### Overview

This project implements a distributed cache system from scratch to help understand:

- **Caching fundamentals**: How caches work, hit/miss ratios, and the core cache loop
- **Consistent hashing**: How to distribute keys across multiple nodes with minimal rebalancing
- **Eviction policies**: LRU, LFU, and TTL strategies for managing cache memory
- **Cluster management**: Adding/removing nodes, graceful degradation, and statistics

### Architecture

```
                    +-------------------+
                    |   Client Code     |
                    +-------------------+
                           |
              +------------+------------+
              |                         |
     +--------v--------+      +--------v--------+
     |  Single Node    |      |  Multi-Node     |
     |  Cache (LRU)    |      |  Cluster        |
     +-----------------+      +-----------------+
              |                         |
     +--------v--------+      +--------v--------+
     |  Cache Ring     |      | Consistent      |
     |  (Virtual Nodes)|      | Hashing Ring    |
     +-----------------+      +-----------------+
```

### Cache Flow

```
Request → Cache Lookup → [Hit] Return → [Miss] Fetch from source → Cache result → Return
```

### Core Components

| Component | Description |
|-----------|-------------|
| `cache.Node` | Single cache node with configurable eviction policy |
| `cache.Cluster` | Multi-node cluster with consistent hashing |
| `cache.HashRing` | Consistent hashing ring with virtual nodes |
| `cache.Stats` | Performance statistics (hit/miss ratio, etc.) |

### Eviction Policies

| Policy | Description | Best For |
|--------|-------------|----------|
| **LRU** (Least Recently Used) | Evicts the item accessed longest ago | Workloads with temporal locality |
| **LFU** (Least Frequently Used) | Evicts the least frequently accessed item | Workloads with skewed access patterns |
| **TTL** (Time To Live) | Items expire after a set duration | Time-sensitive data (sessions, tokens) |

### Consistent Hashing

Traditional hashing (`hash(key) % nodes`) causes massive cache thrashing when nodes change. Consistent hashing solves this:

1. Both nodes and keys are hashed onto a circular ring (0 to 2^32-1)
2. A key maps to the first node found clockwise on the ring
3. When a node is added/removed, only ~1/N of keys need remapping

**Virtual nodes** ensure even distribution: each real node maps to many points on the ring.

```
Ring: [0]---------------------------------[2^32-1]
      node1-v1    node2-v42    node3-v99
      \           /  \           /
       \         /    \         /
      key-a /        key-b /
```

### Learning Objectives

- [x] Understand cache principles and the core cache loop
- [x] Master consistent hashing with virtual nodes
- [x] Learn cache eviction strategies (LRU, LFU, TTL)
- [x] Practice multi-node cluster management
- [x] Implement cache statistics and hot key detection
- [x] Support cache warming for bootstrapping

---

## 中文

### 概述

本项目从零实现一个分布式缓存系统，帮助理解：

- **缓存基础**: 缓存的工作原理、命中率、核心缓存循环
- **一致性哈希**: 如何在多个节点间分配键值，最小化重新平衡
- **淘汰策略**: LRU、LFU 和 TTL 三种缓存内存管理策略
- **集群管理**: 节点增删、优雅降级和统计监控

### 缓存原理

缓存通过将频繁访问的数据存储在快速存储（内存）中，减少对慢速存储（数据库、网络、磁盘）的访问。

```
请求 → 缓存查找 → [命中]返回 → [未命中]回源 → 缓存 → 返回
```

### 缓存淘汰策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **LRU** (最近最少使用) | 淘汰最久未访问的项 | 具有时间局部性的工作负载 |
| **LFU** (最不经常使用) | 淘汰访问频率最低的项 | 访问模式偏斜的工作负载 |
| **TTL** (存活时间) | 项在设定时间后过期 | 时效性数据（会话、令牌） |

### 一致性哈希

传统哈希（`hash(key) % nodes`）在节点变化时会导致大量缓存失效。一致性哈希解决了这个问题：

1. 将节点和键都哈希到一个环形空间（0 到 2^32-1）
2. 键映射到环上顺时针方向的第一个节点
3. 节点增删时，只有约 1/N 的键需要重新映射

**虚拟节点**确保均匀分布：每个真实节点映射到环上的多个点。

---

## Quick Start / 快速开始

### Prerequisites / 前置条件

- Go 1.22+
- No external dependencies required

### Run Examples / 运行示例

```bash
cd projects/distributed-cache

# Run all demos
go run examples/main.go

# Run cluster demo
go run examples/cluster.go

# Run consistent hashing visualization
go run examples/hashring.go

# Run benchmarks
go run examples/benchmark.go
```

### Run Tests / 运行测试

```bash
# Run all tests
go test ./tests/...

# Run with coverage
go test -cover ./tests/...

# Run benchmarks
go test -bench=. ./tests/...
```

### Project Structure / 项目结构

```
distributed-cache/
├── go.mod                  # Go module definition
├── README.md               # This file
├── src/                    # Core package
│   ├── cache.go            # In-memory cache with LRU/LFU/TTL
│   ├── hashring.go         # Consistent hashing with virtual nodes
│   └── cluster.go          # Multi-node cache cluster
├── examples/               # Demo programs
│   ├── main.go             # Single node cache demos
│   ├── cluster.go          # Multi-node cluster demo
│   ├── hashring.go         # Consistent hashing visualization
│   └── benchmark.go        # Performance benchmarks
└── tests/                  # Unit tests
    ├── cache_test.go       # Cache node tests
    ├── hashring_test.go    # Consistent hashing tests
    └── cluster_test.go     # Cluster tests
```

---

## Key Concepts / 核心概念

### 1. Cache Hit Ratio / 命中率

```
Hit Ratio = Hits / (Hits + Misses) * 100%
```

A good cache should have > 80% hit ratio. Low hit ratio means:
- Cache is too small
- Data access pattern doesn't benefit from caching
- Eviction policy is suboptimal for the workload

### 2. Cache Warming / 缓存预热

Before a cache is fully populated, it suffers from "cold start" — every request is a miss. Cache warming pre-populates the cache with known important data.

### 3. Hot Key Detection / 热键检测

Some keys are accessed far more frequently than others. Identifying hot keys helps:
- Give them dedicated cache space
- Replicate them across multiple nodes
- Apply different eviction policies

### 4. Consistent Hashing Benefits / 一致性哈希优势

| Aspect | Traditional Hash | Consistent Hashing |
|--------|-----------------|-------------------|
| Node added | ~100% keys remapped | ~1/N keys remapped |
| Node removed | ~100% keys remapped | ~1/N keys remapped |
| Distribution | Uneven | Even (with vnodes) |
| Cache thrashing | Severe | Minimal |

---

## License / 许可证

MIT
