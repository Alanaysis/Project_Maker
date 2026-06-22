# 03 - 实现指南

## 实现概述

本项目采用本地模拟的方式实现 Chord DHT，所有节点在同一进程中运行。

## 核心实现

### 1. 哈希函数实现

```go
// SHA-1 哈希函数
func DefaultHash(key string) *big.Int {
    hash := sha1.New()
    hash.Write([]byte(key))
    hashBytes := hash.Sum(nil)
    return new(big.Int).SetBytes(hashBytes)
}
```

**实现要点**:
- 使用 SHA-1 产生 160 位哈希
- 转换为 big.Int 用于大数运算

### 2. 环上数学运算

```go
// 判断 key 是否在 (start, end) 区间内
func Between(key, start, end *big.Int) bool {
    if start.Cmp(end) < 0 {
        return key.Cmp(start) > 0 && key.Cmp(end) < 0
    }
    if start.Cmp(end) > 0 {
        return key.Cmp(start) > 0 || key.Cmp(end) < 0
    }
    return key.Cmp(start) != 0
}
```

**关键点**:
- 处理环的环绕情况
- start > end 表示跨越 0 点

### 3. 节点实现

#### Finger Table 初始化

```go
for i := 0; i < M; i++ {
    start := new(big.Int).Add(node.ID, PowerOfTwo(i))
    start.Mod(start, PowerOfTwo(M))
    node.FingerTable[i] = FingerEntry{Start: start}
}
```

#### 查找后继

```go
func (n *Node) FindSuccessor(id *big.Int) *NodeID {
    if BetweenRightInclusive(id, n.ID, n.Successor.ID) {
        return n.Successor
    }
    return n.closestPrecedingFinger(id)
}
```

#### 最近前驱节点

```go
func (n *Node) closestPrecedingFinger(id *big.Int) *NodeID {
    for i := M - 1; i >= 0; i-- {
        finger := n.FingerTable[i].Node
        if finger != nil && Between(finger.ID, n.ID, id) {
            return finger
        }
    }
    return n.Successor
}
```

### 4. Ring 管理实现

#### 添加节点

```go
func (r *Ring) AddNode(addr string) (*Node, error) {
    node := NewNode(addr, r.hashFunc)
    r.nodes[addr] = node
    r.sortedIDs = append(r.sortedIDs, node.ID)
    sort.Slice(r.sortedIDs, ...)
    r.updateFingerTables()
    return node, nil
}
```

#### 查找负责节点

```go
func (r *Ring) findNodeByID(id *big.Int) *Node {
    for _, nodeID := range r.sortedIDs {
        if nodeID.Cmp(id) >= 0 {
            return r.nodes[r.findAddrByID(nodeID)]
        }
    }
    return r.nodes[r.findAddrByID(r.sortedIDs[0])]  // 环绕
}
```

## 并发处理

### 读写锁使用

```go
type Node struct {
    mu sync.RWMutex
    // ...
}

func (n *Node) Get(key string) (string, bool) {
    n.mu.RLock()
    defer n.mu.RUnlock()
    return n.storage[key]
}
```

**原则**:
- 读操作使用 RLock
- 写操作使用 Lock
- 延迟释放锁

## 测试策略

### 单元测试

1. **哈希函数测试**: 验证一致性和分布
2. **环运算测试**: 测试 Between 函数
3. **节点测试**: 测试查找和存储
4. **集成测试**: 测试多节点场景

### 测试用例

```go
func TestBetween(t *testing.T) {
    // 正常情况
    // 环绕情况
    // 边界情况
}

func TestRingPutGet(t *testing.T) {
    // 创建环
    // 添加节点
    // 存储键值
    // 验证读取
}
```

## 性能优化

### 当前实现

- 使用 map 存储键值，O(1) 查找
- 使用排序数组维护节点 ID，O(N) 查找

### 优化方向

1. 使用二分查找优化节点查找
2. 使用更高效的哈希函数
3. 实现 finger table 缓存

## 已知限制

1. **本地模拟**: 没有真实网络通信
2. **单点故障**: 没有数据复制
3. **静态配置**: 没有动态配置支持

## 下一步

1. 添加网络层实现
2. 实现数据复制
3. 添加监控和日志
