# DHT - 分布式哈希表 (Distributed Hash Table)

> 实现 Chord DHT 协议，理解分布式存储与一致性哈希

## English

A learning project implementing the Chord Distributed Hash Table (DHT) protocol in Go. Chord is a foundational peer-to-peer protocol that provides a distributed key-value store using consistent hashing and finger table routing.

## 中文

本项目用 Go 实现了 Chord 分布式哈希表（DHT）协议。Chord 是一个基础的 P2P 协议，通过一致性哈希和指纹表路由提供分布式键值存储。

---

## 学习目标 / Learning Objectives

### 中文

- **理解 DHT 原理**：掌握分布式哈希表的核心概念和工作原理
- **掌握一致性哈希**：理解一致性哈希如何解决节点增减时的数据迁移问题
- **学会路由算法**：掌握 Chord 的 O(log N) 查找算法和指纹表机制
- **理解分布式系统基础**：学习节点加入/离开、数据迁移、环维护等分布式系统核心概念

### English

- **Understand DHT Principles**: Master the core concepts and working principles of Distributed Hash Tables
- **Master Consistent Hashing**: Understand how consistent hashing solves data migration during node join/leave
- **Learn Routing Algorithms**: Master Chord's O(log N) lookup algorithm and finger table mechanism
- **Understand Distributed Systems**: Learn node join/leave, data migration, ring maintenance, and other core distributed system concepts

---

## Chord 协议详解 / Chord Protocol Explained

### 核心概念 / Core Concepts

```
                    Chord Ring (ID space [0, 2^m))
                    
                    0 ---- 100 ---- 200 ---- 300 ---- 400 ---- ... ---- 65535
                     \                                    /
                      \                                  /
                       Node-A (ID=150) --succ--> Node-B (ID=350)
                       
                     Keys in (pred, nodeID} are stored here
```

1. **ID 空间 / ID Space**: 所有节点和键通过哈希函数映射到 [0, 2^m) 的环形 ID 空间
2. **后继指针 / Successor Pointer**: 每个节点维护其后继节点（顺时针下一个节点）
3. **前驱指针 / Predecessor Pointer**: 每个节点维护其前驱节点（顺时针上一个节点）
4. **指纹表 / Finger Table**: 每个节点维护 m 个条目，实现 O(log N) 路由
5. **键值存储 / Key-Value Store**: 节点负责存储 ID 在 (前驱, 节点ID] 范围内的键

### Chord 协议流程 / Protocol Flow

```
1. 节点加入 / Node Join:
   新节点 -> 找到后继 -> 初始化指纹表 -> 稳定环 -> 更新前驱

2. 键查找 / Key Lookup:
   起始节点 -> 查找最接近的前驱 -> 转发查询 -> 到达后继 -> 返回结果

3. 节点离开 / Node Leave:
   后继获取键 -> 前驱更新后继 -> 稳定环 -> 移除节点

4. 故障检测 / Failure Detection:
   心跳机制 -> 检测超时 -> 通知后继 -> 修复环
```

### 指纹表 / Finger Table

每个节点 i 维护一个大小为 m 的指纹表：

```
Finger[i] = successor of (i + 2^(i-1)) mod 2^m
```

| 索引 | 覆盖范围 | 说明 |
|------|----------|------|
| 0 | [i+1, i+1] | 直接后继 |
| 1 | [i+1, i+2] | 距离 1-2 |
| 2 | [i+2, i+4] | 距离 2-4 |
| 3 | [i+4, i+8] | 距离 4-8 |
| ... | ... | ... |
| 15 | [i+32768, i+65536] | 环的另一半 |

### 一致性哈希 / Consistent Hashing

```
传统哈希的问题：
  节点数 N -> 哈希模 N -> 节点增减时所有键重新映射

一致性哈希的解决方案：
  节点和键都映射到环上 -> 键由顺时针第一个节点负责
  节点增减只影响相邻节点的数据
```

---

## 项目结构 / Project Structure

```
dht/
├── go.mod                    # Go module definition
├── README.md                 # This file
├── src/                      # Core library
│   ├── chord.go              # Package documentation
│   ├── id.go                 # Node ID generation and ring operations
│   ├── node.go               # Chord node implementation
│   ├── store.go              # Key-value store
│   ├── ring.go               # Chord ring simulation
│   └── simulator.go          # High-level simulator and migration tracking
├── examples/                 # Demo programs
│   ├── 01_basic_ring.go      # Basic ring creation and node joining
│   ├── 02_key_lookup.go      # Key storage and lookup operations
│   ├── 03_node_join_leave.go # Node join/leave with data migration
│   └── 04_key_migration.go   # Detailed key migration demonstration
└── tests/                    # Unit tests
    ├── id_test.go            # ID generation and ring math tests
    ├── node_test.go          # Node operations tests
    ├── store_test.go         # Key-value store tests
    ├── ring_test.go          # Ring simulation tests
    └── simulator_test.go     # Simulator tests
```

---

## 如何运行 / How to Run

### 运行示例 / Run Examples

```bash
cd projects/dht

# 1. 基本环演示
go run examples/01_basic_ring.go

# 2. 键查找演示
go run examples/02_key_lookup.go

# 3. 节点加入/离开演示
go run examples/03_node_join_leave.go

# 4. 键迁移演示
go run examples/04_key_migration.go
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
go test ./tests/...

# 运行特定测试
go test ./tests/ -v

# 运行覆盖率
go test ./tests/... -cover
```

---

## Chord 协议核心接口 / Core API

### 节点 / Node

```go
// 创建节点
node := chord.NewNode(id, address)

// 设置指针
node.SetSuccessor(succID)
node.SetPredecessor(predID)

// 存储键值
node.StoreValue(key, value)

// 查询键
value, found := node.GetValue(key)
```

### 环 / Ring

```go
// 创建环
ring := chord.NewChordRing()

// 添加节点
ring.AddNode(node)

// 查找键
node, hops := ring.Lookup(key)

// 存储/检索
ring.Store(key, value)
value, found := ring.Retrieve(key)
```

### 模拟器 / Simulator

```go
// 创建模拟器
sim := chord.NewRingSimulator()

// 节点加入
sim.JoinNode("10.0.0.1")

// 存储数据
sim.StoreKey("user:1", "Alice")

// 检索数据
value, found := sim.RetrieveKey("user:1")

// 节点离开
sim.LeaveNode("10.0.0.1")

// 查看状态
sim.PrintStatus()
```

---

## 关键算法 / Key Algorithms

### 稳定协议 / Stabilization Protocol

每个节点定期运行稳定协议以确保环的一致性：

1. 询问后继是否有更接近自己的后继
2. 如果有，更新后继指针
3. 修复前驱指针

### 查找算法 / Lookup Algorithm

查找键 k 的后继节点：

1. 从当前节点开始
2. 在指纹表中找到最接近 k 但又不在 k 之前的节点
3. 将查询转发给该节点
4. 重复直到找到 k 的后继

时间复杂度：**O(log N)** 次网络跳数

---

## 参考资源 / References

- **Chord 论文**: "Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications" (Karger et al., 2001)
- **一致性哈希**: "Consistent Hashing and Random Trees" (Karger et al., 1997)
- **分布式系统**: "Designing Data-Intensive Applications" (Martin Kleppmann)

---

## License

MIT
