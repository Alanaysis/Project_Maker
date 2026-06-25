# 02 - 设计文档: 分布式哈希表 DHT

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  P2P File   │  │ Distributed │  │   Future    │      │
│  │   Sharing   │  │   Storage   │  │  Apps       │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
├─────────┴────────────────┴────────────────┴─────────────┤
│                    Protocol Layer                         │
│  ┌─────────────────────┐  ┌─────────────────────┐       │
│  │    Chord Protocol   │  │  Kademlia Protocol  │       │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │       │
│  │  │  Ring Manager │  │  │  │ Routing Table │  │       │
│  │  └───────────────┘  │  │  └───────────────┘  │       │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │       │
│  │  │ Finger Table  │  │  │  │   K-Buckets   │  │       │
│  │  └───────────────┘  │  │  └───────────────┘  │       │
│  └─────────────────────┘  └─────────────────────┘       │
├─────────────────────────────────────────────────────────┤
│                    Network Layer                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              HTTP Server/Client                  │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │    │
│  │  │  PING   │ │  STORE  │ │ FIND_*  │           │    │
│  │  └─────────┘ └─────────┘ └─────────┘           │    │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    Discovery Layer                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Bootstrap  │  Bucket Refresh  │  Ping Check   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 模块设计

#### 1. 哈希模块 (hash.go)

**职责**: 提供哈希函数和标识符操作

**接口**:
```go
type HashFunc func(key string) *big.Int

func DefaultHash(key string) *big.Int
func Between(key, start, end *big.Int) bool
func BetweenRightInclusive(key, start, end *big.Int) bool
func PowerOfTwo(exp int) *big.Int
func FormatID(id *big.Int) string
```

#### 2. Chord 节点模块 (node.go)

**职责**: 实现 Chord 节点核心功能

**数据结构**:
```go
type Node struct {
    ID          *big.Int
    Addr        string
    FingerTable []FingerEntry
    Predecessor *NodeID
    Successor   *NodeID
    storage     map[string]string
    successorList []*NodeID
}
```

**核心方法**:
- `FindSuccessor(id)`: 查找后继节点
- `Join(existing)`: 加入环
- `Stabilize()`: 稳定化协议
- `Notify(nodeID)`: 通知前驱
- `FixFingers()`: 修复指表

#### 3. Chord 环模块 (ring.go)

**职责**: 管理整个 Chord 环

**数据结构**:
```go
type Ring struct {
    nodes     map[string]*Node
    sortedIDs []*big.Int
    hashFunc  HashFunc
}
```

**核心方法**:
- `AddNode(addr)`: 添加节点
- `RemoveNode(addr)`: 移除节点
- `Put(key, value)`: 存储键值
- `Get(key)`: 获取值
- `Delete(key)`: 删除键

#### 4. Kademlia 模块 (kademlia.go)

**职责**: 实现 Kademlia 协议

**数据结构**:
```go
type Contact struct {
    ID       *big.Int
    Addr     string
    LastSeen time.Time
}

type KBucket struct {
    contacts []*Contact
}

type RoutingTable struct {
    localID   *big.Int
    buckets   [160]*KBucket
}

type KademliaNode struct {
    ID       *big.Int
    Addr     string
    RT       *RoutingTable
    storage  map[string]string
}
```

**核心函数**:
```go
func XOR(a, b *big.Int) *big.Int
func XORDistance(a, b *big.Int) *big.Int
func BucketIndex(localID, remoteID *big.Int) int
func (kn *KademliaNode) FindNode(target *big.Int) []*Contact
func (kn *KademliaNode) FindValue(key string) (string, []*Contact, bool)
```

#### 5. 网络模块 (network.go)

**职责**: 提供 HTTP 网络通信

**消息类型**:
```go
type MessageType string

const (
    MsgPing        MessageType = "PING"
    MsgPong        MessageType = "PONG"
    MsgStore       MessageType = "STORE"
    MsgFindNode    MessageType = "FIND_NODE"
    MsgFindValue   MessageType = "FIND_VALUE"
)
```

**网络节点**:
```go
type NetworkNode struct {
    node       *KademliaNode
    httpServer *http.Server
    peers      map[string]*ContactInfo
}
```

**核心方法**:
- `Start()`: 启动 HTTP 服务器
- `Ping(addr)`: 发送 PING
- `RemoteStore(addr, key, value)`: 远程存储
- `RemoteFindNode(addr, targetID)`: 远程查找节点
- `RemoteFindValue(addr, key)`: 远程查找值

#### 6. 发现模块 (discovery.go)

**职责**: 节点发现和路由表维护

**配置**:
```go
type DiscoveryConfig struct {
    BootstrapAddrs  []string
    RefreshInterval time.Duration
    PingInterval    time.Duration
}
```

**核心功能**:
- `Bootstrap()`: 连接引导节点
- `refreshBuckets()`: 刷新 K-桶
- `pingContacts()`: 检测节点存活

#### 7. P2P 模块 (p2p.go)

**职责**: P2P 文件共享

**数据结构**:
```go
type FileInfo struct {
    Hash     string
    Name     string
    Size     int64
    Uploader string
}
```

**核心方法**:
- `ShareFile(path)`: 共享文件
- `DownloadFile(hash)`: 下载文件
- `SearchFiles(query)`: 搜索文件

#### 8. 存储模块 (storage.go)

**职责**: 分布式键值存储

**数据结构**:
```go
type StorageItem struct {
    Key       string
    Value     string
    CreatedAt time.Time
    TTL       int64
    Replicas  int
}
```

**核心方法**:
- `Put(key, value, ttl)`: 存储
- `Get(key)`: 获取
- `Delete(key)`: 删除
- `Cleanup()`: 清理过期数据

## 数据流

### 1. 存储数据流

```
Client -> PUT(key, value) -> NetworkNode
  -> KademliaStore(key, value)
    -> FindNode(hash(key)) [找到 K 个最近节点]
    -> RemoteStore(addr, key, value) [并发存储到 K 个节点]
```

### 2. 查找数据流

```
Client -> GET(key) -> NetworkNode
  -> KademliaIterativeFindValue(key)
    -> FindValue(key) [本地查找]
    -> RemoteFindValue(addr, key) [迭代查找]
    -> 返回值或最近节点
```

### 3. 节点加入流程

```
NewNode -> Bootstrap(bootstrapAddr)
  -> Ping(bootstrapAddr) [建立连接]
  -> RemoteFindNode(bootstrapAddr, selfID) [发现节点]
  -> AddContact() [更新路由表]
  -> refreshBuckets() [刷新 K-桶]
```

## 容错设计

### 1. 数据复制

- 每个键值对存储到 K=3 个节点
- 写入时并发存储，部分失败不影响整体
- 读取时从任意副本获取

### 2. 节点故障检测

- 定期 PING 检测节点存活
- 超时未响应的节点从路由表移除
- K-桶中的节点自动降级

### 3. 路由表维护

- 定期刷新 K-桶
- 随机 ID 查找保持路由表活性
- 新节点自动加入路由表

## 性能优化

### 1. 并发查询

- Alpha=3 的并发查询
- 异步网络请求
- 并发数据存储

### 2. 缓存机制

- 本地缓存已查找的值
- K-桶缓存最近节点
- 文件元数据缓存

### 3. 连接池

- HTTP 客户端复用
- 连接超时控制
- 错误重试机制

## 设计决策

### 1. 使用 big.Int 作为 ID

**原因**:
- SHA-1 产生 160 位哈希
- Go 的 big.Int 支持任意精度
- 方便进行大数运算

### 2. HTTP 作为网络层

**原因**:
- 简单易实现
- 跨语言兼容
- 调试方便

**权衡**:
- 性能不如 gRPC
- 但对于学习目的足够

### 3. K=20 作为桶大小

**原因**:
- Kademlia 论文推荐值
- 平衡路由表大小和容错性
- 足够应对节点故障

## 扩展性

### 1. 水平扩展

- 节点动态加入/离开
- 自动负载均衡
- 无单点故障

### 2. 功能扩展

- 支持多种哈希函数
- 可配置的复制因子
- 可插拔的网络层
