# 分布式缓存设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端 (Client)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    负载均衡 (Load Balancer)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Node 1     │  │   Node 2     │  │   Node 3     │
│  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │
│  │ Cache  │  │  │  │ Cache  │  │  │  │ Cache  │  │
│  └────────┘  │  │  └────────┘  │  │  └────────┘  │
│  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │
│  │ Hash   │  │  │  │ Hash   │  │  │  │ Hash   │  │
│  │ Ring   │  │  │  │ Ring   │  │  │  │ Ring   │  │
│  └────────┘  │  │  └────────┘  │  │  └────────┘  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    存储层 (Storage Layer)                     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
distributed-cache/
├── cmd/                    # 命令行入口
│   ├── server/            # HTTP 服务器
│   └── benchmark/         # 性能测试
├── internal/              # 内部实现
│   ├── cache/            # 缓存核心
│   ├── hash/             # 一致性哈希
│   ├── patterns/         # 缓存模式
│   ├── problem/          # 问题解决方案
│   ├── distributed/      # 分布式特性
│   └── application/      # 实际应用
├── pkg/                   # 公共包
│   └── api/              # API 类型
├── test/                  # 测试
└── docs/                  # 文档
```

## 2. 核心设计

### 2.1 缓存核心

#### 2.1.1 数据结构

```go
// Item 缓存项
type Item struct {
    Key        string
    Value      interface{}
    Expiration int64
    Frequency  int64
    AccessAt   time.Time
    CreateAt   time.Time
}

// Cache 缓存
type Cache struct {
    mu       sync.RWMutex
    items    map[string]*Item
    eviction EvictionPolicy
    capacity int
    stats    CacheStats
}
```

#### 2.1.2 淘汰策略接口

```go
type EvictionPolicy interface {
    Add(key string)
    Remove(key string)
    Access(key string)
    Evict() string
    Len() int
}
```

#### 2.1.3 LRU 实现

```
双向链表 + HashMap

head <-> node1 <-> node2 <-> node3 <-> tail

访问 node2:
head <-> node2 <-> node1 <-> node3 <-> tail

淘汰:
删除 tail.prev (node3)
```

#### 2.1.4 LFU 实现

```
频率桶

freq=1: [key1, key2]
freq=2: [key3]
freq=3: [key4, key5]

访问 key1:
freq=1: [key2]
freq=2: [key3, key1]
freq=3: [key4, key5]

淘汰:
从 minFreq 桶中淘汰
```

#### 2.1.5 FIFO 实现

```
队列

入队: [key1, key2, key3]

淘汰:
出队 key1
[key2, key3]
```

#### 2.1.6 TTL 实现

```
最小堆

        key1 (10s)
       /         \
   key2 (20s)   key3 (30s)

清理:
检查堆顶 key1
过期? 删除 : 等待
```

### 2.2 一致性哈希

#### 2.2.1 哈希环

```
        0
       / \
      /   \
   2^31   2^31+1
      \   /
       \ /
      2^32-1
```

#### 2.2.2 虚拟节点映射

```go
// 物理节点 -> 虚拟节点
node1 -> node1#0, node1#1, ..., node1#149
node2 -> node2#0, node2#1, ..., node2#149

// 哈希计算
hash = SHA256("node1#0")[:4] -> uint32
```

#### 2.2.3 数据定位

```go
func (ch *ConsistentHash) Get(key string) string {
    hash := ch.hashFunc([]byte(key))

    // 二分查找第一个 >= hash 的节点
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })

    // 环形处理
    if idx >= len(ch.ring) {
        idx = 0
    }

    return ch.nodes[ch.ring[idx]]
}
```

#### 2.2.4 数据复制

```go
func (ch *ConsistentHash) GetN(key string, n int) []string {
    hash := ch.hashFunc([]byte(key))
    idx := sort.Search(...)

    result := []string{}
    seen := map[string]bool{}

    // 顺时针收集 N 个不同的物理节点
    for i := 0; len(result) < n; i++ {
        pos := (idx + i) % len(ch.ring)
        node := ch.nodes[ch.ring[pos]]
        if !seen[node] {
            seen[node] = true
            result = append(result, node)
        }
    }

    return result
}
```

### 2.3 缓存模式

#### 2.3.1 Cache-Aside

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  应用    │────▶│  缓存    │────▶│  数据库  │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │   Get(key)     │                │
     │───────────────▶│                │
     │                │                │
     │   miss         │                │
     │◀───────────────│                │
     │                │                │
     │   load data    │                │
     │───────────────────────────────▶│
     │                │                │
     │   data         │                │
     │◀───────────────────────────────│
     │                │                │
     │   set(key,val) │                │
     │───────────────▶│                │
     │                │                │
     │   return       │                │
     │◀───────────────│                │
```

#### 2.3.2 Read-Through

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  应用    │────▶│  缓存    │────▶│  数据库  │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │   Get(key)     │                │
     │───────────────▶│                │
     │                │                │
     │                │   load data    │
     │                │───────────────▶│
     │                │                │
     │                │   data         │
     │                │◀───────────────│
     │                │                │
     │   return       │                │
     │◀───────────────│                │
```

#### 2.3.3 Write-Through

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  应用    │────▶│  缓存    │────▶│  数据库  │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │ Set(key,val)   │                │
     │───────────────▶│                │
     │                │                │
     │                │  write data    │
     │                │───────────────▶│
     │                │                │
     │                │   success      │
     │                │◀───────────────│
     │                │                │
     │   return       │                │
     │◀───────────────│                │
```

#### 2.3.4 Write-Behind

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  应用    │────▶│  缓存    │     │  数据库  │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │ Set(key,val)   │                │
     │───────────────▶│                │
     │                │                │
     │   return       │                │
     │◀───────────────│                │
     │                │                │
     │                │  async write   │
     │                │───────────────▶│
```

### 2.4 缓存问题解决方案

#### 2.4.1 布隆过滤器

```
位数组: [0, 1, 0, 1, 1, 0, 0, 1, 0, 1]

添加 "key1":
hash1("key1") = 1 -> set bit[1]
hash2("key1") = 4 -> set bit[4]
hash3("key1") = 7 -> set bit[7]

查询 "key1":
bit[1] = 1 ✓
bit[4] = 1 ✓
bit[7] = 1 ✓
-> 可能存在

查询 "key2":
bit[?] = 0
-> 一定不存在
```

#### 2.4.2 Single Flight

```
并发请求同一 key:

Request1 ──┐
Request2 ──┼──▶ Single Flight ──▶ 只有一个请求去加载
Request3 ──┘

加载完成后，所有请求都得到结果
```

#### 2.4.3 随机 TTL

```
原始 TTL: 60s
随机偏移: ±10s

key1 TTL: 55s
key2 TTL: 63s
key3 TTL: 58s
key4 TTL: 67s

效果: 过期时间分散，避免同时过期
```

### 2.5 分布式特性

#### 2.5.1 数据复制

```
同步复制:

Client ──▶ Node1 (Leader)
              │
              ├──▶ Node2 (Replica1)
              │
              └──▶ Node3 (Replica2)
              │
              ▼
           All ACK
              │
              ▼
         Return to Client
```

```
异步复制:

Client ──▶ Node1 (Leader)
              │
              ├──▶ Return to Client
              │
              ├──▶ Node2 (Replica1) async
              │
              └──▶ Node3 (Replica2) async
```

```
Quorum 复制:

Client ──▶ Node1 (Leader)
              │
              ├──▶ Node2 (Replica1)
              │
              └──▶ Node3 (Replica2)
              │
              ▼
         2/3 ACK (Quorum)
              │
              ▼
         Return to Client
```

#### 2.5.2 故障检测

```
健康检查循环:

Node1 ──Ping──▶ Node2
         │
         ├── Success: 更新 LastSeen
         │
         └── Failure: consecutiveFailures++
                      │
                      └── consecutiveFailures >= threshold
                          │
                          └── 标记为 Down
```

#### 2.5.3 故障恢复

```
恢复流程:

Node2 Down
    │
    ├── 标记为 Failed
    │
    ├── 开始恢复尝试
    │   │
    │   ├── 尝试 Ping
    │   │   │
    │   │   ├── Success: 恢复
    │   │   │
    │   │   └── Failure: retryCount++
    │   │
    │   └── retryCount >= maxRetries?
    │       │
    │       └── 放弃恢复
    │
    └── 恢复成功
        │
        ├── 标记为 Running
        │
        └── 重新加入集群
```

## 3. 数据结构设计

### 3.1 缓存项

```go
type Item struct {
    Key        string      // 缓存键
    Value      interface{} // 缓存值
    Expiration int64       // 过期时间 (UnixNano)
    Frequency  int64       // 访问频率
    AccessAt   time.Time   // 最后访问时间
    CreateAt   time.Time   // 创建时间
}
```

### 3.2 哈希环

```go
type ConsistentHash struct {
    ring    []uint32          // 排序的哈希环
    nodes   map[uint32]string // 哈希 -> 节点映射
    nodeSet map[string]bool   // 节点集合
    replicas int              // 虚拟节点数
}
```

### 3.3 会话

```go
type Session struct {
    ID         string
    UserID     string
    Data       map[string]interface{}
    CreatedAt  time.Time
    ExpiresAt  time.Time
    LastAccess time.Time
}
```

### 3.4 限流器

```go
type RequestCounter struct {
    Count       int
    WindowStart time.Time
}

type TokenBucket struct {
    Tokens     float64
    LastRefill time.Time
}
```

## 4. 接口设计

### 4.1 缓存接口

```go
type Cache interface {
    Get(key string) (interface{}, bool)
    Set(key string, value interface{}, ttl time.Duration)
    Delete(key string) bool
    Has(key string) bool
    Len() int
    Clear()
    Stats() CacheStats
}
```

### 4.2 缓存模式接口

```go
type CachePattern interface {
    Get(key string) (interface{}, error)
    Set(key string, value interface{}, ttl time.Duration) error
    Delete(key string) error
}
```

### 4.3 限流器接口

```go
type RateLimiter interface {
    Allow(key string) RateLimitResult
}
```

## 5. 并发设计

### 5.1 锁策略

```go
type Cache struct {
    mu sync.RWMutex // 读写锁
}

// 读操作使用读锁
func (c *Cache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    // ...
}

// 写操作使用写锁
func (c *Cache) Set(key string, value interface{}, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    // ...
}
```

### 5.2 无锁优化

```go
// 使用 atomic 操作
type HotKeyStats struct {
    AccessCount int64
}

func (h *HotKeyStats) Increment() {
    atomic.AddInt64(&h.AccessCount, 1)
}
```

### 5.3 并发控制

```go
// Single Flight 防止缓存击穿
type singleFlight struct {
    done chan struct{}
    val  interface{}
    err  error
}

func (ca *CacheAside) Get(key string) (interface{}, error) {
    ca.mu.Lock()
    if flight, ok := ca.flybacks[key]; ok {
        ca.mu.Unlock()
        <-flight.done
        return flight.val, flight.err
    }
    // ...
}
```

## 6. 性能设计

### 6.1 内存优化

```go
// 使用 sync.Pool 复用对象
var itemPool = sync.Pool{
    New: func() interface{} {
        return &Item{}
    },
}

func getItem() *Item {
    return itemPool.Get().(*Item)
}

func putItem(item *Item) {
    itemPool.Put(item)
}
```

### 6.2 批量操作

```go
// Write-Behind 批量写入
type WriteBehind struct {
    writeCh   chan writeRequest
    batchSize int
}

func (wb *WriteBehind) flushLoop() {
    batch := make([]writeRequest, 0, wb.batchSize)
    for req := range wb.writeCh {
        batch = append(batch, req)
        if len(batch) >= wb.batchSize {
            wb.flush(batch)
            batch = batch[:0]
        }
    }
}
```

### 6.3 异步处理

```go
// 异步复制
func (rm *ReplicationManager) replicateAsync(key string, value interface{}, ttl time.Duration, operation string, targets []string) error {
    task := ReplicationTask{
        Key:       key,
        Value:     value,
        TTL:       ttl,
        Operation: operation,
        Targets:   targets,
    }

    select {
    case rm.replicationQ <- task:
        return nil
    default:
        return fmt.Errorf("queue full")
    }
}
```

## 7. 容错设计

### 7.1 错误处理

```go
// 统一错误处理
type CacheError struct {
    Code    int
    Message string
}

func (e *CacheError) Error() string {
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
```

### 7.2 重试机制

```go
// 指数退避重试
func retry(fn func() error, maxRetries int) error {
    for i := 0; i < maxRetries; i++ {
        if err := fn(); err == nil {
            return nil
        }
        time.Sleep(time.Duration(math.Pow(2, float64(i))) * time.Second)
    }
    return fmt.Errorf("max retries exceeded")
}
```

### 7.3 熔断机制

```go
// 简单熔断器
type CircuitBreaker struct {
    failures    int
    threshold   int
    state       string // "closed", "open", "half-open"
    lastFailure time.Time
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    if cb.state == "open" {
        if time.Since(cb.lastFailure) > 30*time.Second {
            cb.state = "half-open"
        } else {
            return fmt.Errorf("circuit breaker open")
        }
    }

    err := fn()
    if err != nil {
        cb.failures++
        if cb.failures >= cb.threshold {
            cb.state = "open"
            cb.lastFailure = time.Now()
        }
        return err
    }

    cb.failures = 0
    cb.state = "closed"
    return nil
}
```

## 8. 监控设计

### 8.1 指标收集

```go
type CacheStats struct {
    Hits       int64
    Misses     int64
    HitRate    float64
    Size       int
    Capacity   int
    Evictions  int64
}
```

### 8.2 日志设计

```go
// 结构化日志
type LogEntry struct {
    Timestamp time.Time
    Level     string
    Message   string
    Fields    map[string]interface{}
}
```

### 8.3 告警设计

```go
// 告警规则
type AlertRule struct {
    Name      string
    Condition func(stats CacheStats) bool
    Action    func()
}
```
