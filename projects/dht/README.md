# Chord DHT - 分布式哈希表实现

## 项目概述

这是一个基于 Chord 协议的分布式哈希表(DHT)实现，用于理解分布式存储系统的核心原理。

## 核心特性

- **一致性哈希**: 使用 SHA-1 进行键值映射
- **Chord 路由算法**: O(log N) 复杂度的高效查找
- **键值存储**: 支持 Put/Get/Delete 操作
- **节点管理**: 支持节点动态加入和离开
- **Finger Table**: 加速路由查找的数据结构

## 项目结构

```
dht/
├── internal/           # 核心实现
│   ├── hash.go        # 哈希函数和工具
│   ├── node.go        # Chord 节点实现
│   └── ring.go        # Chord 环管理
├── cmd/dht/           # 命令行入口
│   └── main.go        # 主程序
├── test/              # 测试文件
│   └── chord_test.go  # 单元测试
└── docs/              # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 运行演示

```bash
cd projects/dht
go run cmd/dht/main.go
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

### 一致性哈希

使用 SHA-1 哈希函数将节点和键映射到同一个标识符空间:
- 节点 ID = SHA1(节点地址)
- 键 ID = SHA1(键名)

### Finger Table

每个节点维护一个 finger table，用于加速路由:
- entry[i] 指向节点 (n + 2^i) mod 2^m 的后继
- 支持 O(log N) 的查找复杂度

## API 使用

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

## 学习目标

通过本项目，你将学到:
1. **DHT 原理**: 理解分布式哈希表如何工作
2. **一致性哈希**: 掌握键值到节点的映射机制
3. **路由算法**: 学习 Chord 的 O(log N) 查找算法
4. **分布式系统**: 理解节点加入/离开的处理

## 参考资源

- [Chord论文](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf)
- [分布式系统概念](https://www.distributed-systems.net/)
