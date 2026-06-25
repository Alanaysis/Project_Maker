# 分布式缓存开发文档

## 1. 开发环境

### 1.1 环境要求

- Go 1.21+
- Git
- IDE (推荐 VS Code + Go 插件)

### 1.2 环境配置

```bash
# 安装 Go
# https://golang.org/dl/

# 配置 GOPATH
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# 验证安装
go version
```

### 1.3 获取代码

```bash
git clone <repo-url>
cd distributed-cache
go mod tidy
```

## 2. 项目结构

```
distributed-cache/
├── cmd/                    # 命令行入口
│   ├── server/            # HTTP 服务器
│   │   └── main.go
│   └── benchmark/         # 性能测试
│       └── main.go
├── internal/              # 内部实现
│   ├── cache/            # 缓存核心
│   │   ├── cache.go      # 缓存主逻辑
│   │   ├── eviction.go   # 淘汰策略
│   │   └── item.go       # 缓存项
│   ├── hash/             # 一致性哈希
│   │   ├── consistent.go
│   │   └── consistent_test.go
│   ├── patterns/         # 缓存模式
│   │   └── patterns.go
│   ├── problem/          # 问题解决方案
│   │   └── solutions.go
│   ├── distributed/      # 分布式特性
│   │   ├── node.go
│   │   ├── replication.go
│   │   └── failover.go
│   └── application/      # 实际应用
│       ├── hotcache.go
│       ├── session.go
│       └── ratelimiter.go
├── pkg/                   # 公共包
│   └── api/              # API 类型
│       └── types.go
├── test/                  # 测试
│   └── cache_test.go
├── docs/                  # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── go.mod                 # Go 模块文件
└── README.md              # 项目说明
```

## 3. 编码规范

### 3.1 命名规范

```go
// 包名: 小写单词，无下划线
package cache

// 接口名: 动词或形容词 + er
type EvictionPolicy interface {
    Add(key string)
    Remove(key string)
}

// 结构体名: 大写开头，驼峰命名
type ConsistentHash struct {
    // ...
}

// 函数名: 大写开头，驼峰命名
func NewConsistentHash() *ConsistentHash {
    // ...
}

// 变量名: 小写开头，驼峰命名
var nodeCount int

// 常量名: 全大写，下划线分隔
const MAX_RETRIES = 5
```

### 3.2 注释规范

```go
// Package cache provides in-memory caching with various eviction policies.
package cache

// Cache represents an in-memory cache with configurable eviction strategy.
//
// Example:
//
//	c := cache.NewCache(cache.CacheConfig{
//	    Capacity:     1000,
//	    EvictionType: "lru",
//	})
//	c.Set("key", "value", time.Minute)
type Cache struct {
    // items stores the cached items
    items map[string]*Item

    // eviction is the eviction policy
    eviction EvictionPolicy
}

// Get retrieves an item from the cache.
// It returns the value and a boolean indicating if the key was found.
func (c *Cache) Get(key string) (interface{}, bool) {
    // ...
}
```

### 3.3 错误处理

```go
// 定义错误类型
var (
    ErrKeyNotFound = errors.New("key not found")
    ErrCacheFull   = errors.New("cache is full")
)

// 返回错误
func (c *Cache) Get(key string) (interface{}, error) {
    item, exists := c.items[key]
    if !exists {
        return nil, ErrKeyNotFound
    }
    return item.Value, nil
}

// 检查错误
val, err := cache.Get("key")
if err != nil {
    if errors.Is(err, ErrKeyNotFound) {
        // 处理键不存在
    }
    return err
}
```

### 3.4 并发安全

```go
type Cache struct {
    mu    sync.RWMutex
    items map[string]*Item
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

## 4. 核心模块开发

### 4.1 缓存核心

#### 4.1.1 Item 结构

```go
// internal/cache/item.go

type Item struct {
    Key        string
    Value      interface{}
    Expiration int64
    Frequency  int64
    AccessAt   time.Time
    CreateAt   time.Time
}

func (item *Item) IsExpired() bool {
    if item.Expiration == 0 {
        return false
    }
    return time.Now().UnixNano() > item.Expiration
}
```

#### 4.1.2 淘汰策略

```go
// internal/cache/eviction.go

type EvictionPolicy interface {
    Add(key string)
    Remove(key string)
    Access(key string)
    Evict() string
    Len() int
}

// LRU 实现
type LRUPolicy struct {
    mu    sync.Mutex
    items map[string]*lruItem
    head  *lruItem
    tail  *lruItem
}

func (l *LRUPolicy) Add(key string) {
    l.mu.Lock()
    defer l.mu.Unlock()
    // ...
}
```

#### 4.1.3 Cache 结构

```go
// internal/cache/cache.go

type Cache struct {
    mu       sync.RWMutex
    items    map[string]*Item
    eviction EvictionPolicy
    capacity int
    stats    CacheStats
}

func NewCache(config CacheConfig) *Cache {
    c := &Cache{
        items:    make(map[string]*Item),
        eviction: newEviction(config.EvictionType),
        capacity: config.Capacity,
    }
    go c.cleanup()
    return c
}
```

### 4.2 一致性哈希

```go
// internal/hash/consistent.go

type ConsistentHash struct {
    mu       sync.RWMutex
    ring     []uint32
    nodes    map[uint32]string
    replicas int
}

func (ch *ConsistentHash) Add(node string) {
    ch.mu.Lock()
    defer ch.mu.Unlock()

    for i := 0; i < ch.replicas; i++ {
        key := fmt.Sprintf("%s#%d", node, i)
        hash := ch.hashFunc([]byte(key))
        ch.ring = append(ch.ring, hash)
        ch.nodes[hash] = node
    }

    sort.Slice(ch.ring, func(i, j int) bool {
        return ch.ring[i] < ch.ring[j]
    })
}

func (ch *ConsistentHash) Get(key string) (string, bool) {
    ch.mu.RLock()
    defer ch.mu.RUnlock()

    if len(ch.ring) == 0 {
        return "", false
    }

    hash := ch.hashFunc([]byte(key))
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })

    if idx >= len(ch.ring) {
        idx = 0
    }

    return ch.nodes[ch.ring[idx]], true
}
```

### 4.3 缓存模式

```go
// internal/patterns/patterns.go

type CacheAside struct {
    cache  *cache.Cache
    loader DataLoader
    writer DataWriter
}

func (ca *CacheAside) Get(key string) (interface{}, error) {
    // 尝试从缓存获取
    if val, ok := ca.cache.Get(key); ok {
        return val, nil
    }

    // 从数据库加载
    val, err := ca.loader(key)
    if err != nil {
        return nil, err
    }

    // 存入缓存
    ca.cache.Set(key, val, 0)
    return val, nil
}
```

### 4.4 缓存问题解决方案

```go
// internal/problem/solutions.go

// 布隆过滤器
type BloomFilter struct {
    bits    []bool
    size    uint
    hashNum uint
}

func (bf *BloomFilter) Add(key string) {
    for i := uint(0); i < bf.hashNum; i++ {
        idx := bf.hash(key, i) % bf.size
        bf.bits[idx] = true
    }
}

// Single Flight
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

### 4.5 分布式特性

```go
// internal/distributed/node.go

type Node struct {
    ID       string
    Address  string
    cache    *cache.Cache
    peers    map[string]*PeerNode
    hashRing *hash.ConsistentHash
}

func (n *Node) Get(key string) (interface{}, error) {
    // 确定哪个节点拥有这个键
    owner, ok := n.hashRing.Get(key)
    if !ok {
        return nil, fmt.Errorf("no node available")
    }

    // 如果是本地节点，从本地缓存获取
    if owner == n.ID {
        return n.cache.Get(key)
    }

    // 否则转发到拥有者节点
    peer, exists := n.peers[owner]
    if !exists {
        return nil, fmt.Errorf("peer not found")
    }

    return peer.Client.Get(key)
}
```

## 5. 测试开发

### 5.1 单元测试

```go
// test/cache_test.go

func TestCache_BasicOperations(t *testing.T) {
    c := cache.NewCache(cache.CacheConfig{
        Capacity:     100,
        EvictionType: "lru",
        DefaultTTL:   time.Minute,
    })

    // 测试 Set
    c.Set("key1", "value1", 0)

    // 测试 Get
    val, ok := c.Get("key1")
    if !ok || val != "value1" {
        t.Errorf("Expected value1, got %v", val)
    }

    // 测试 Delete
    c.Delete("key1")
    if c.Has("key1") {
        t.Error("Expected key1 to be deleted")
    }
}
```

### 5.2 表驱动测试

```go
func TestCache_EvictionPolicies(t *testing.T) {
    tests := []struct {
        name     string
        policy   string
        capacity int
        keys     []string
        expected []string // 应该存在的键
    }{
        {
            name:     "LRU",
            policy:   "lru",
            capacity: 3,
            keys:     []string{"a", "b", "c", "d"},
            expected: []string{"b", "c", "d"},
        },
        {
            name:     "LFU",
            policy:   "lfu",
            capacity: 3,
            keys:     []string{"a", "b", "c", "d"},
            expected: []string{"b", "c", "d"},
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            c := cache.NewCache(cache.CacheConfig{
                Capacity:     tt.capacity,
                EvictionType: tt.policy,
                DefaultTTL:   time.Minute,
            })

            for _, key := range tt.keys {
                c.Set(key, "value", 0)
            }

            for _, key := range tt.expected {
                if !c.Has(key) {
                    t.Errorf("Expected %s to exist", key)
                }
            }
        })
    }
}
```

### 5.3 并发测试

```go
func TestCache_ConcurrentAccess(t *testing.T) {
    c := cache.NewCache(cache.CacheConfig{
        Capacity:     1000,
        EvictionType: "lru",
        DefaultTTL:   time.Minute,
    })

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            for j := 0; j < 100; j++ {
                key := fmt.Sprintf("key-%d-%d", i, j)
                c.Set(key, "value", time.Minute)
                c.Get(key)
                c.Delete(key)
            }
        }(i)
    }
    wg.Wait()
}
```

### 5.4 基准测试

```go
func BenchmarkCache_Get(b *testing.B) {
    c := cache.NewCache(cache.CacheConfig{
        Capacity:     10000,
        EvictionType: "lru",
        DefaultTTL:   time.Minute,
    })

    for i := 0; i < 10000; i++ {
        c.Set(fmt.Sprintf("key-%d", i), "value", time.Minute)
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        c.Get(fmt.Sprintf("key-%d", i%10000))
    }
}

func BenchmarkCache_Set(b *testing.B) {
    c := cache.NewCache(cache.CacheConfig{
        Capacity:     10000,
        EvictionType: "lru",
        DefaultTTL:   time.Minute,
    })

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        c.Set(fmt.Sprintf("key-%d", i), "value", time.Minute)
    }
}
```

### 5.5 运行测试

```bash
# 运行所有测试
go test ./... -v

# 运行特定测试
go test ./test/ -v -run TestCache

# 运行基准测试
go test ./... -bench=.

# 生成覆盖率报告
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 6. 构建和部署

### 6.1 构建

```bash
# 构建可执行文件
go build -o bin/server ./cmd/server/

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o bin/server-linux ./cmd/server/
GOOS=darwin GOARCH=amd64 go build -o bin/server-macos ./cmd/server/
GOOS=windows GOARCH=amd64 go build -o bin/server.exe ./cmd/server/
```

### 6.2 运行

```bash
# 直接运行
go run cmd/server/main.go 8080

# 运行构建后的文件
./bin/server 8080
```

### 6.3 Docker 部署

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o server ./cmd/server/

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server", "8080"]
```

```bash
# 构建镜像
docker build -t distributed-cache .

# 运行容器
docker run -p 8080:8080 distributed-cache
```

### 6.4 Docker Compose

```yaml
# docker-compose.yml
version: '3'
services:
  cache1:
    build: .
    ports:
      - "8080:8080"
    command: ["./server", "8080"]

  cache2:
    build: .
    ports:
      - "8081:8081"
    command: ["./server", "8081"]

  cache3:
    build: .
    ports:
      - "8082:8082"
    command: ["./server", "8082"]
```

```bash
docker-compose up -d
```

## 7. 调试技巧

### 7.1 日志

```go
import "log"

// 使用标准日志
log.Printf("Cache hit: key=%s", key)
log.Printf("Cache miss: key=%s", key)
log.Printf("Eviction: key=%s", key)

// 结构化日志
type LogEntry struct {
    Level   string
    Message string
    Key     string
    Value   interface{}
}
```

### 7.2 性能分析

```go
import "runtime/pprof"

// CPU 分析
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// 内存分析
f, _ := os.Create("mem.prof")
pprof.WriteHeapProfile(f)
```

```bash
# 分析 CPU
go tool pprof cpu.prof

# 分析内存
go tool pprof mem.prof
```

### 7.3 调试命令

```bash
# 查看 goroutine
go tool pprof http://localhost:6060/debug/pprof/goroutine

# 查看内存分配
go tool pprof http://localhost:6060/debug/pprof/heap

# 查看锁竞争
go tool pprof http://localhost:6060/debug/pprof/mutex
```

## 8. 贡献指南

### 8.1 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例:
```
feat(cache): add LFU eviction policy

- Implement LFU eviction using frequency buckets
- Add unit tests for LFU policy
- Update documentation

Closes #123
```

### 8.2 代码审查

1. 代码符合编码规范
2. 有足够的测试覆盖
3. 文档已更新
4. 通过 CI 检查

### 8.3 发布流程

1. 创建发布分支
2. 更新版本号
3. 更新 CHANGELOG
4. 创建 PR
5. 合并后打 Tag
6. 构建和发布

## 9. 常见问题

### Q: 如何添加新的淘汰策略？

A: 实现 `EvictionPolicy` 接口，然后在 `newEviction` 函数中注册。

### Q: 如何添加新的缓存模式？

A: 实现 `CachePattern` 接口。

### Q: 如何扩展分布式特性？

A: 在 `internal/distributed` 包中添加新功能。

### Q: 如何优化性能？

A: 使用基准测试找出瓶颈，然后针对性优化。

## 10. 学习资源

### Go 语言
- [Go 官方文档](https://golang.org/doc/)
- [Go 语言圣经](https://gopl.io/)
- [Go 并发编程](https://github.com/ardanlabs/gotraining)

### 分布式系统
- [分布式系统：概念与设计](https://www.distributed-systems.net/)
- [数据密集型应用系统设计](https://dataintensive.net/)
- [MIT 6.824](https://pdos.csail.mit.edu/6.824/)

### 缓存
- [Redis 设计与实现](https://redisbook.com/)
- [Memcached 文档](https://memcached.org/)
- [Groupcache](https://github.com/golang/groupcache)
