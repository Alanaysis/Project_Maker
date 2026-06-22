# 学习笔记: Chord DHT

## 核心概念理解

### 1. 什么是 DHT?

分布式哈希表(DHT)是一种去中心化的存储系统，它将键值对分布存储在多个节点上。

**关键特性**:
- **去中心化**: 没有中心协调节点
- **可扩展性**: 节点数量可动态变化
- **容错性**: 单个节点故障不影响整体

### 2. 一致性哈希

**传统哈希的问题**:
```
节点数变化时，几乎所有键都需要重新映射
```

**一致性哈希的优势**:
```
节点数变化时，只有 K/N 个键需要重新映射
(K=键总数, N=节点数)
```

**实现方式**:
- 将节点和键映射到同一个环上
- 键存储在顺时针方向的第一个节点

### 3. Chord 协议

**核心思想**:
- 使用 finger table 加速查找
- 实现 O(log N) 的查找复杂度

**关键数据结构**:
```go
finger[i] = successor((n + 2^i) mod 2^m)
```

**查找算法**:
1. 从当前节点开始
2. 找到不超过目标的最大 finger
3. 跳转到该 finger
4. 重复直到找到后继

## 实现细节

### 1. 大数处理

**问题**: SHA-1 产生 160 位哈希

**解决方案**: 使用 `math/big.Int`

```go
hash := sha1.New()
hash.Write([]byte(key))
hashBytes := hash.Sum(nil)
id := new(big.Int).SetBytes(hashBytes)
```

### 2. 环上运算

**判断区间**:
```go
func Between(key, start, end *big.Int) bool {
    if start < end {
        return start < key && key < end
    }
    // 环绕情况
    return key > start || key < end
}
```

### 3. Finger Table 维护

**初始化**:
```go
for i := 0; i < M; i++ {
    start = (node.ID + 2^i) mod 2^M
}
```

**更新**: 定期运行 stabilize 和 fix_fingers

### 4. 并发控制

**读写锁**:
```go
type Node struct {
    mu sync.RWMutex
    // ...
}

// 读操作
func (n *Node) Get(key string) string {
    n.mu.RLock()
    defer n.mu.RUnlock()
    return n.storage[key]
}

// 写操作
func (n *Node) Store(key, value string) {
    n.mu.Lock()
    defer n.mu.Unlock()
    n.storage[key] = value
}
```

## 算法分析

### 查找复杂度

**理论**: O(log N)

**推导**:
- 每次跳转至少将距离减半
- 总共需要 log N 次跳转

### 空间复杂度

**每个节点**: O(M) - Finger Table
**整体**: O(N * M)

### 节点加入

**步骤**:
1. 新节点找到后继
2. 更新 finger table
3. 接管部分键

**复杂度**: O(log^2 N)

### 节点离开

**步骤**:
1. 转移键给后继
2. 更新相关节点

**复杂度**: O(log N)

## 实际应用

### 1. P2P 文件共享

- BitTorrent 使用 DHT 进行节点发现
- 去中心化追踪器

### 2. 分布式存储

- Amazon DynamoDB 使用一致性哈希
- Cassandra 使用类似 DHT 的架构

### 3. 区块链

- Ethereum 使用 Kademlia DHT
- 用于节点发现和内容寻址

## 学习心得

### 理解难点

1. **环形拓扑**: 理解环上的运算需要特别注意环绕情况
2. **Finger Table**: 初次接触时难以理解其加速原理
3. **并发控制**: 分布式系统中的并发问题复杂

### 关键领悟

1. **一致性哈希的价值**: 解决了传统哈希的扩展性问题
2. **Finger Table 的精妙**: 通过空间换时间，实现高效查找
3. **分布式系统的挑战**: 网络分区、节点故障等问题

### 实践建议

1. **先理解理论**: 在实现前深入理解 Chord 论文
2. **逐步实现**: 从哈希函数开始，逐步构建完整系统
3. **多写测试**: 测试是验证分布式系统正确性的关键

## 扩展阅读

### 推荐资源

1. **论文**: Stoica et al. "Chord: A Scalable Peer-to-peer Lookup Service"
2. **书籍**: "Distributed Systems" by Maarten van Steen
3. **课程**: MIT 6.824 Distributed Systems

### 相关技术

1. **Kademlia**: 另一种 DHT 协议
2. **Pastry**: 基于前缀路由的 DHT
3. **CAN**: 基于多维空间的 DHT

## 总结

通过实现 Chord DHT，我深入理解了:
1. 分布式哈希表的原理
2. 一致性哈希的重要性
3. Chord 路由算法的精妙
4. 分布式系统设计的挑战

这个项目是理解分布式存储系统的绝佳起点。
