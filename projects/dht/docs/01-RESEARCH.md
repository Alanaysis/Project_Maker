# 01 - 研究报告: Chord DHT

## 背景知识

### 什么是 DHT?

分布式哈希表(Distributed Hash Table, DHT)是一种分布式存储系统，提供:
- **去中心化**: 没有中心协调节点
- **可扩展性**: 节点数量可动态增减
- **容错性**: 节点故障不影响整体服务

### Chord 协议

Chord 是最经典的 DHT 协议之一，由 MIT 于 2001 年提出。

**核心特性**:
- 基于一致性哈希
- O(log N) 查找复杂度
- 支持节点动态加入/离开

## 关键概念

### 1. 标识符空间

Chord 使用 m 位标识符空间 (通常 m=160，使用 SHA-1):
- 节点 ID = hash(节点地址)
- 键 ID = hash(键名)
- 所有 ID 排列成一个环 (0 到 2^m - 1)

### 2. 后继节点

对于任意 ID，其后继节点是环上顺时针方向第一个节点:
```
successor(id) = min{n ∈ ring | n ≥ id}
```

### 3. Finger Table

每个节点 n 维护 m 个 finger 表项:
```
finger[i] = successor((n + 2^i) mod 2^m)
```

作用:
- 加速路由查找
- 实现 O(log N) 复杂度

### 4. 路由算法

查找 key 的后继节点:
1. 从当前节点开始
2. 在 finger table 中找到最大的不超过 key 的节点
3. 转发到该节点
4. 重复直到找到后继

## 算法分析

### 查找复杂度

- **平均跳数**: O(log N)
- **最坏情况**: O(N) - 当 finger table 未优化时

### 节点加入

新节点 n 加入时:
1. 找到 n 的后继节点
2. 更新相关节点的 finger table
3. 接管后继节点的部分键

### 节点离开

节点 n 离开时:
1. 将键转移给后继
2. 更新相关节点的 finger table

## 研究结论

1. Chord 是一个简洁而强大的 DHT 协议
2. 适用于 P2P 系统和分布式存储
3. finger table 是实现高效路由的关键

## 参考文献

1. Stoica, I., et al. "Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications." ACM SIGCOMM 2001.
2. Dabek, F., et al. "Building Peer-to-Peer Systems With Chord, a Distributed Lookup Service." HOTOS 2001.
