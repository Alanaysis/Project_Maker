# 02 - 设计文档: Chord DHT

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Application Layer                   │
│                    (Put / Get / Delete)                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      Ring Manager                        │
│              (Node Join / Leave / Routing)                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      Chord Node                          │
│          (Finger Table / Successor / Predecessor)        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Hash Function                         │
│                   (SHA-1 / Ring Math)                    │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Hash 函数模块 (`hash.go`)

**职责**:
- 提供一致性哈希函数
- 处理环上的数学运算

**关键函数**:
- `DefaultHash(key)`: SHA-1 哈希
- `Between(key, start, end)`: 判断是否在区间内
- `PowerOfTwo(exp)`: 计算 2^exp

### 2. Node 模块 (`node.go`)

**职责**:
- 表示 Chord 环上的节点
- 维护 finger table
- 处理键值存储

**数据结构**:
```go
type Node struct {
    ID          *big.Int        // 节点标识符
    Addr        string          // 网络地址
    FingerTable []FingerEntry   // Finger 表
    Predecessor *NodeID         // 前驱节点
    Successor   *NodeID         // 后继节点
    storage     map[string]string // 键值存储
}
```

**核心方法**:
- `FindSuccessor(id)`: 查找后继
- `Join(existing)`: 加入环
- `Stabilize()`: 稳定化协议
- `Notify(nodeID)`: 通知前驱

### 3. Ring 模块 (`ring.go`)

**职责**:
- 管理整个 Chord 环
- 协调节点间的交互
- 提供键值操作接口

**数据结构**:
```go
type Ring struct {
    nodes     map[string]*Node  // 节点映射
    sortedIDs []*big.Int        // 排序后的 ID
    hashFunc  HashFunc          // 哈希函数
}
```

**核心方法**:
- `AddNode(addr)`: 添加节点
- `RemoveNode(addr)`: 移除节点
- `Put(key, value)`: 存储键值
- `Get(key)`: 获取值
- `FindNode(key)`: 查找负责节点

## 设计决策

### 1. 使用 big.Int 作为 ID

**原因**:
- SHA-1 产生 160 位哈希
- Go 的 big.Int 支持任意精度
- 方便进行大数运算

### 2. 本地模拟 vs 网络实现

**当前实现**:
- 所有节点在同一进程中
- 通过 map 直接访问节点
- 简化网络通信

**生产实现**:
- 使用 gRPC/HTTP 进行节点通信
- 需要处理网络延迟和故障

### 3. Finger Table 大小

**选择**: M = 160 (SHA-1 输出长度)

**权衡**:
- 更大的 M = 更精确的路由
- 更大的 M = 更多的内存开销

## 数据流

### Put 操作

```
1. 计算 keyID = hash(key)
2. 找到负责节点 = FindNode(keyID)
3. 在节点上存储键值
```

### Get 操作

```
1. 计算 keyID = hash(key)
2. 找到负责节点 = FindNode(keyID)
3. 从节点读取值
```

### 节点加入

```
1. 新节点计算自己的 ID
2. 找到后继节点
3. 更新 finger table
4. 接管后继的部分键
```

## 错误处理

### 节点故障

1. **检测**: 通过心跳或超时
2. **恢复**: 使用 successor list
3. **修复**: 更新 finger table

### 键丢失

1. **预防**: 复制到多个节点
2. **检测**: 后台一致性检查
3. **恢复**: 从副本恢复

## 未来扩展

1. **网络层**: 实现真实的节点通信
2. **持久化**: 将数据持久化到磁盘
3. **复制**: 实现数据副本
4. **负载均衡**: 优化键分布
