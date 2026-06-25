# 学习笔记: 分布式哈希表 DHT (Chord & Kademlia)

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

### 4. Kademlia 协议

**核心思想**:
- 使用 XOR 距离度量
- 使用 K-桶路由表
- 实现 O(log N) 的查找复杂度

**XOR 距离**:
```go
distance(a, b) = a XOR b
```

**性质**:
- 对称性: d(a,b) = d(b,a)
- 自反性: d(a,a) = 0
- 三角不等式: d(a,c) = d(a,b) XOR d(b,c)

**K-桶**:
- 每个节点维护 160 个 K-桶
- 桶 i 存储距离在 [2^i, 2^(i+1)) 范围内的节点
- 每个桶最多 K=20 个节点

**查找操作**:
- **FIND_NODE**: 查找距离目标最近的 K 个节点
- **FIND_VALUE**: 查找键对应的值，或返回最近节点

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

### 2. XOR 距离计算

```go
func XOR(a, b *big.Int) *big.Int {
    return new(big.Int).Xor(a, b)
}

func BucketIndex(localID, remoteID *big.Int) int {
    dist := XOR(localID, remoteID)
    leading := LeadingZeros(dist)
    return IDLength - 1 - leading
}
```

### 3. K-桶实现

```go
type KBucket struct {
    contacts []*Contact
}

func (kb *KBucket) AddContact(contact *Contact) bool {
    // 检查是否已存在
    for i, c := range kb.contacts {
        if c.ID.Cmp(contact.ID) == 0 {
            // 移到末尾（最近使用）
            kb.contacts = append(kb.contacts[:i], kb.contacts[i+1:]...)
            kb.contacts = append(kb.contacts, contact)
            return true
        }
    }

    // 如果桶满，移除最旧的
    if len(kb.contacts) >= K {
        kb.contacts = kb.contacts[1:]
    }

    kb.contacts = append(kb.contacts, contact)
    return true
}
```

### 4. 网络层实现

```go
type NetworkNode struct {
    node       *KademliaNode
    httpServer *http.Server
}

func (nn *NetworkNode) Start() error {
    mux := http.NewServeMux()
    mux.HandleFunc("/ping", nn.handlePing)
    mux.HandleFunc("/store", nn.handleStore)
    mux.HandleFunc("/find_node", nn.handleFindNode)
    mux.HandleFunc("/find_value", nn.handleFindValue)

    nn.httpServer = &http.Server{
        Addr:    nn.node.Addr,
        Handler: mux,
    }

    go nn.httpServer.ListenAndServe()
    return nil
}
```

### 5. 迭代查找

```go
func (nn *NetworkNode) KademliaIterativeFindNode(targetID *big.Int) []*Contact {
    closest := nn.node.FindNode(targetID)
    queried := make(map[string]bool)

    for i := 0; i < Alpha; i++ {
        var newClosest []*Contact
        for _, c := range closest {
            if queried[c.Addr] {
                continue
            }
            queried[c.Addr] = true

            contacts, err := nn.RemoteFindNode(c.Addr, targetID)
            if err != nil {
                continue
            }

            newClosest = append(newClosest, contacts...)
        }

        // 合并并排序
        closest = append(closest, newClosest...)
        sort.Slice(closest, func(i, j int) bool {
            distI := XOR(closest[i].ID, targetID)
            distJ := XOR(closest[j].ID, targetID)
            return distI.Cmp(distJ) < 0
        })

        if len(closest) > K {
            closest = closest[:K]
        }
    }

    return closest
}
```

## 算法分析

### 查找复杂度

**理论**: O(log N)

**推导**:
- 每次跳转至少将距离减半
- 总共需要 log N 次跳转

### 空间复杂度

**每个节点**: O(M) - Finger Table / K-桶
**整体**: O(N * M)

### 节点加入

**Chord 步骤**:
1. 新节点找到后继
2. 更新 finger table
3. 接管部分键

**Kademlia 步骤**:
1. 连接 Bootstrap 节点
2. FIND_NODE 查找自己
3. 填充路由表

### 节点离开

**Chord 步骤**:
1. 转移键给后继
2. 更新相关节点

**Kademlia**:
- K-桶自动维护
- 定期刷新保持活性

## 协议对比

| 特性 | Chord | Kademlia |
|------|-------|----------|
| 距离度量 | 环上距离 | XOR 距离 |
| 路由表 | Finger Table | K-桶 |
| 查找复杂度 | O(log N) | O(log N) |
| 容错性 | 后继列表 | K-桶冗余 |
| 应用场景 | 分布式存储 | P2P 网络 |

## 实际应用

### 1. P2P 文件共享

- BitTorrent 使用 DHT 进行节点发现
- 去中心化追踪器
- Kademlia 是 BitTorrent DHT 的基础

### 2. 分布式存储

- Amazon DynamoDB 使用一致性哈希
- Cassandra 使用类似 DHT 的架构

### 3. 区块链

- Ethereum 使用 Kademlia DHT (discv5)
- 用于节点发现和内容寻址

### 4. IPFS

- 使用 Kademlia DHT 进行内容路由
- 支持内容寻址和去中心化存储

## 学习心得

### 理解难点

1. **环形拓扑**: 理解环上的运算需要特别注意环绕情况
2. **Finger Table**: 初次接触时难以理解其加速原理
3. **XOR 距离**: 理解 XOR 的数学性质需要时间
4. **并发控制**: 分布式系统中的并发问题复杂

### 关键领悟

1. **一致性哈希的价值**: 解决了传统哈希的扩展性问题
2. **Finger Table 的精妙**: 通过空间换时间，实现高效查找
3. **XOR 距离的优雅**: 简单的位运算实现了高效的路由
4. **分布式系统的挑战**: 网络分区、节点故障等问题

### 实践建议

1. **先理解理论**: 在实现前深入理解论文
2. **逐步实现**: 从哈希函数开始，逐步构建完整系统
3. **多写测试**: 测试是验证分布式系统正确性的关键
4. **阅读源码**: 学习 BitTorrent、Ethereum 等实际实现

## 扩展阅读

### 推荐资源

1. **Chord 论文**: Stoica et al. "Chord: A Scalable Peer-to-peer Lookup Service"
2. **Kademlia 论文**: Maymounkov & Mazières "Kademlia: A Peer-to-peer Information System Based on the XOR Metric"
3. **书籍**: "Distributed Systems" by Maarten van Steen
4. **课程**: MIT 6.824 Distributed Systems

### 相关技术

1. **Pastry**: 基于前缀路由的 DHT
2. **CAN**: 基于多维空间的 DHT
3. **Tapestry**: 基于 Plaxton 路由的 DHT

## 总结

通过实现 Chord 和 Kademlia DHT，我深入理解了:
1. 分布式哈希表的原理
2. 一致性哈希的重要性
3. Chord 和 Kademlia 路由算法的精妙
4. 分布式系统设计的挑战
5. P2P 网络的实际应用

这个项目是理解分布式存储系统的绝佳起点。
