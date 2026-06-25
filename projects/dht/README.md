# 分布式哈希表 DHT - Chord & Kademlia 实现

## 项目概述

这是一个完整的分布式哈希表(DHT)实现，包含 **Chord** 和 **Kademlia** 两种经典协议。项目支持 P2P 文件共享和分布式存储等实际应用场景。

## 核心特性

### Chord 协议
- **一致性哈希**: 使用 SHA-1 进行键值映射
- **Finger Table**: O(log N) 复杂度的高效查找
- **节点管理**: 支持节点动态加入和离开
- **数据转移**: 节点离开时自动转移数据

### Kademlia 协议
- **XOR 距离**: 基于 XOR 运算的距离度量
- **K-桶**: 每个桶最多存放 K=20 个节点
- **FIND_NODE**: 查找距离目标最近的 K 个节点
- **FIND_VALUE**: 查找键对应的值，或返回最近节点
- **迭代查找**: Alpha=3 的并发查询

### 数据操作
- **PUT**: 存储键值对，支持 TTL 过期
- **GET**: 获取键值对，支持分布式查找
- **DELETE**: 删除键值对

### 节点发现
- **引导节点**: 通过 Bootstrap 节点加入网络
- **周期刷新**: 定期刷新 K-桶保持路由表活性
- **Ping 检测**: 定期检测节点存活状态

### 实际应用
- **P2P 文件共享**: 基于 DHT 的去中心化文件共享
- **分布式存储**: 带复制和 TTL 的分布式键值存储

## 项目结构

```
dht/
├── internal/                    # 核心实现
│   ├── hash.go                 # 哈希函数和工具
│   ├── node.go                 # Chord 节点实现
│   ├── ring.go                 # Chord 环管理
│   ├── kademlia.go             # Kademlia 协议实现
│   ├── network.go              # 网络层 (HTTP)
│   ├── discovery.go            # 节点发现和引导
│   ├── p2p.go                  # P2P 文件共享
│   └── storage.go              # 分布式存储
├── cmd/
│   ├── dht-server/             # DHT 服务器
│   │   └── main.go
│   ├── dht-client/             # P2P 文件共享客户端
│   │   └── main.go
│   └── dht-storage/            # 分布式存储演示
│       └── main.go
├── test/                       # 测试文件
│   ├── chord_test.go           # Chord 测试
│   ├── kademlia_test.go        # Kademlia 测试
│   ├── network_test.go         # 网络层测试
│   └── storage_test.go         # 存储层测试
└── docs/                       # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 运行 DHT 服务器

```bash
cd projects/dht
go run cmd/dht-server/main.go -addr localhost:8000
```

### 运行分布式存储演示

```bash
# 启动服务器
go run cmd/dht-server/main.go -addr localhost:8000

# 在另一个终端运行存储演示
go run cmd/dht-storage/main.go -server localhost:8000 -action demo
```

### 运行 P2P 文件共享

```bash
# 启动服务器
go run cmd/dht-server/main.go -addr localhost:8000

# 共享文件
go run cmd/dht-client/main.go -server localhost:8000 -action share -file ./myfile.txt

# 列出共享文件
go run cmd/dht-client/main.go -server localhost:8000 -action list
```

### 运行测试

```bash
cd projects/dht
go test ./test/ -v
```

## 核心概念

### Chord 协议

Chord 是一种分布式哈希表协议，提供以下功能:
- **键值存储**: 将键映射到环上的节点
- **高效查找**: O(log N) 跳数查找
- **动态拓扑**: 支持节点加入/离开

### Kademlia 协议

Kademlia 是另一种流行的 DHT 协议，特点包括:
- **XOR 距离**: 使用 XOR 运算计算节点间距离
- **K-桶**: 每个距离范围维护最多 K 个节点
- **迭代查找**: 通过多轮查询找到最近节点

### XOR 距离

Kademlia 使用 XOR 运算计算距离:
```
distance(a, b) = a XOR b
```

性质:
- 对称性: d(a,b) = d(b,a)
- 自反性: d(a,a) = 0
- 三角不等式: d(a,c) = d(a,b) XOR d(b,c)

### K-桶

每个节点维护 160 个 K-桶，按距离分组:
- 桶 i 存储距离在 [2^i, 2^(i+1)) 范围内的节点
- 每个桶最多 K=20 个节点
- 最近的节点更新更频繁

## API 使用

### Chord Ring

```go
// 创建环
ring := internal.NewRing(nil)

// 添加节点
ring.AddNode("node1:8000")
ring.AddNode("node2:8001")

// 存储键值
ring.Put("mykey", "myvalue")

// 获取值
value, err := ring.Get("mykey")

// 删除键
ring.Delete("mykey")
```

### Kademlia Node

```go
// 创建节点
node := internal.NewKademliaNode("node1:8000", nil)

// 引导连接
node.Bootstrap("bootstrap:8000", bootstrapID)

// 查找节点
contacts := node.FindNode(targetID)

// 查找值
value, contacts, found := node.FindValue("mykey")
```

### 分布式存储

```go
// 创建存储
storage := internal.NewDistributedStorage(node, 3)

// 存储 (带 TTL)
storage.Put("key", "value", 3600) // 1小时过期

// 获取
value, err := storage.Get("key")

// 删除
storage.Delete("key")
```

### P2P 文件共享

```go
// 创建 P2P 网络
p2p, _ := internal.NewP2PNetwork(node, "./shared_files")

// 共享文件
info, _ := p2p.ShareFile("./myfile.txt")

// 下载文件
path, _ := p2p.DownloadFile(info.Hash)

// 搜索文件
results := p2p.SearchFiles("query")
```

## 学习目标

通过本项目，你将学到:
1. **DHT 原理**: 理解分布式哈希表如何工作
2. **一致性哈希**: 掌握键值到节点的映射机制
3. **Chord 协议**: 学习 O(log N) 的查找算法
4. **Kademlia 协议**: 理解 XOR 距离和 K-桶机制
5. **分布式系统**: 理解节点加入/离开的处理
6. **P2P 网络**: 学习去中心化文件共享
7. **分布式存储**: 掌握带复制的键值存储

## 参考资源

- [Chord 论文](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf)
- [Kademlia 论文](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)
- [分布式系统概念](https://www.distributed-systems.net/)

---

[返回 BLOCKCHAIN 模块](../BLOCKCHAIN_README.md) | [返回主目录](../../README.md)
