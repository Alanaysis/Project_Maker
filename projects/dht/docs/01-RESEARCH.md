# 01 - 研究报告: Chord & Kademlia DHT

## 背景知识

### 什么是 DHT?

分布式哈希表(Distributed Hash Table, DHT)是一种分布式存储系统，提供:
- **去中心化**: 没有中心协调节点
- **可扩展性**: 节点数量可动态增减
- **容错性**: 节点故障不影响整体服务
- **高效查找**: O(log N) 的查找复杂度

### Chord 协议

Chord 是最经典的 DHT 协议之一，由 MIT 于 2001 年提出。

**核心特性**:
- 基于一致性哈希
- O(log N) 查找复杂度
- 支持节点动态加入/离开

### Kademlia 协议

Kademlia 是另一种流行的 DHT 协议，由 Petar Maymounkov 和 David Mazières 于 2002 年提出。

**核心特性**:
- 基于 XOR 距离度量
- K-桶路由表结构
- 高度容错和自组织
- 广泛应用于 BitTorrent、Ethereum 等

## 关键概念

### 1. 标识符空间

两种协议都使用 m 位标识符空间 (通常 m=160，使用 SHA-1):
- 节点 ID = hash(节点地址)
- 键 ID = hash(键名)
- 所有 ID 排列成一个环 (0 到 2^m - 1)

### 2. Chord 核心概念

#### 后继节点

对于任意 ID，其后继节点是环上顺时针方向第一个节点:
```
successor(id) = min{n ∈ ring | n ≥ id}
```

#### Finger Table

每个节点 n 维护 m 个 finger 表项:
```
finger[i] = successor((n + 2^i) mod 2^m)
```

作用:
- 加速路由查找
- 实现 O(log N) 复杂度

#### 路由算法

查找 key 的后继节点:
1. 从当前节点开始
2. 在 finger table 中找到最大的不超过 key 的节点
3. 转发到该节点
4. 重复直到找到后继

### 3. Kademlia 核心概念

#### XOR 距离

Kademlia 使用 XOR 运算计算节点间距离:
```
distance(a, b) = a XOR b
```

性质:
- 对称性: d(a,b) = d(b,a)
- 自反性: d(a,a) = 0
- 三角不等式: d(a,c) = d(a,b) XOR d(b,c)

#### K-桶

每个节点维护 160 个 K-桶，按距离分组:
- 桶 i 存储距离在 [2^i, 2^(i+1)) 范围内的节点
- 每个桶最多 K=20 个节点
- 最近的节点更新更频繁

#### 查找操作

- **FIND_NODE**: 查找距离目标最近的 K 个节点
- **FIND_VALUE**: 查找键对应的值，或返回最近节点

#### 迭代查找

1. 从本地路由表获取 α=3 个最近节点
2. 向这些节点发送 FIND_NODE/FIND_VALUE
3. 将返回的节点加入候选集
4. 重复直到找到目标或没有更近的节点

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

### Kademlia 容错性

- 每个 K-桶维护多个节点
- 节点故障时自动降级到下一个节点
- 定期刷新路由表

## 协议对比

| 特性 | Chord | Kademlia |
|------|-------|----------|
| 距离度量 | 环上距离 | XOR 距离 |
| 路由表 | Finger Table | K-桶 |
| 查找复杂度 | O(log N) | O(log N) |
| 容错性 | 后继列表 | K-桶冗余 |
| 应用场景 | 分布式存储 | P2P 网络 |

## 研究结论

1. Chord 和 Kademlia 都是优秀的 DHT 协议
2. Chord 更适合分布式存储场景
3. Kademlia 更适合 P2P 网络场景
4. 两种协议都实现了 O(log N) 的查找复杂度
5. 实际应用中需要考虑网络延迟和节点故障

## 参考文献

1. Stoica, I., et al. "Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications." ACM SIGCOMM 2001.
2. Maymounkov, P. and Mazières, D. "Kademlia: A Peer-to-peer Information System Based on the XOR Metric." IPTPS 2002.
3. Dabek, F., et al. "Building Peer-to-Peer Systems With Chord, a Distributed Lookup Service." HOTOS 2001.
