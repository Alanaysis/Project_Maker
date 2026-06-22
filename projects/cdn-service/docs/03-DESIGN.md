# 技术设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      CDN Service                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Server    │  │ Dispatcher  │  │   Origin    │        │
│  │   Module    │  │   Module    │  │   Module    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│                   ┌──────▼──────┐                         │
│                   │    Cache    │                         │
│                   │   Manager   │                         │
│                   └──────┬──────┘                         │
│                          │                                 │
│                   ┌──────▼──────┐                         │
│                   │   Storage   │                         │
│                   │    Layer    │                         │
│                   └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 请求流程

```
Client Request
      │
      ▼
┌─────────────┐
│   Server    │ ── 接收请求，解析HTTP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Dispatcher  │ ── 选择后端节点（如有多节点）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Cache     │ ── 查询缓存
│   Lookup    │
└──────┬──────┘
       │
       ├──── Cache HIT ──── 返回缓存内容
       │
       └──── Cache MISS ────┐
                            ▼
                    ┌─────────────┐
                    │   Origin    │ ── 回源获取
                    │   Fetch     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Cache     │ ── 更新缓存
                    │   Update    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Return    │ ── 返回响应
                    │   Response  │
                    └─────────────┘
```

## 2. 模块设计

### 2.1 Server模块

**职责**：
- 监听HTTP请求
- 解析请求参数
- 调用其他模块处理
- 返回响应

**接口**：
```go
type Server struct {
    addr     string
    cache    *CacheManager
    origin   *OriginFetcher
    dispatcher *Dispatcher
}

func NewServer(addr string, opts ...ServerOption) *Server
func (s *Server) Start() error
func (s *Server) Stop() error
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request)
```

**配置项**：
- `addr`: 监听地址
- `read_timeout`: 读取超时
- `write_timeout`: 写入超时
- `max_header_bytes`: 最大头部大小

### 2.2 Cache模块

#### 2.2.1 LRU缓存

**数据结构**：
```go
type LRUCache struct {
    capacity int
    size     int
    cache    map[string]*list.Element
    list     *list.List
    mutex    sync.RWMutex
}

type entry struct {
    key   string
    value *CacheItem
}
```

**算法**：
1. 访问缓存时，将元素移到链表头部
2. 插入新元素时，如果缓存满，淘汰链表尾部元素
3. 使用哈希表实现O(1)查找

**时间复杂度**：
- Get: O(1)
- Put: O(1)
- Delete: O(1)

#### 2.2.2 CacheManager

**职责**：
- 管理缓存生命周期
- 处理缓存过期
- 提供缓存统计

**接口**：
```go
type CacheManager struct {
    cache      *LRUCache
    maxSize    int64
    currentSize int64
    stats      CacheStats
}

type CacheStats struct {
    Hits      int64
    Misses    int64
    Evictions int64
    Size      int64
}

func (cm *CacheManager) Get(key string) (*CacheItem, bool)
func (cm *CacheManager) Set(key string, item *CacheItem, ttl time.Duration)
func (cm *CacheManager) Delete(key string)
func (cm *CacheManager) Clear()
func (cm *CacheManager) Stats() CacheStats
```

#### 2.2.3 CacheItem

```go
type CacheItem struct {
    Key        string
    Value      []byte
    Headers    http.Header
    StatusCode int
    CreatedAt  time.Time
    ExpiresAt  time.Time
    Size       int64
}
```

### 2.3 Origin模块

**职责**：
- 从源站获取内容
- 处理回源错误
- 支持重试机制

**接口**：
```go
type OriginFetcher struct {
    client  *http.Client
    baseURL string
    timeout time.Duration
    retries int
}

func NewOriginFetcher(baseURL string, opts ...OriginOption) *OriginFetcher
func (of *OriginFetcher) Fetch(path string, headers http.Header) (*http.Response, error)
func (of *OriginFetcher) FetchWithRetry(path string, headers http.Header) (*http.Response, error)
```

**重试策略**：
- 指数退避
- 最大重试次数可配置
- 可配置重试间隔

### 2.4 Dispatcher模块

**职责**：
- 选择后端节点
- 实现负载均衡算法
- 管理节点状态

**接口**：
```go
type Dispatcher struct {
    nodes    []*Node
    strategy Strategy
    mutex    sync.RWMutex
}

type Node struct {
    ID         string
    Address    string
    Weight     int
    Status     NodeStatus
    Connections int
    LastCheck  time.Time
}

type Strategy interface {
    Select(nodes []*Node, r *http.Request) (*Node, error)
}

func NewDispatcher(strategy Strategy) *Dispatcher
func (d *Dispatcher) AddNode(node *Node)
func (d *Dispatcher) RemoveNode(id string)
func (d *Dispatcher) Select(r *http.Request) (*Node, error)
```

**调度算法**：

#### 轮询（Round Robin）
```go
type RoundRobinStrategy struct {
    current int
}

func (s *RoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // 轮询选择下一个节点
}
```

#### 加权轮询（Weighted Round Robin）
```go
type WeightedRoundRobinStrategy struct {
    current int
    weight  int
}

func (s *WeightedRoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // 根据权重选择节点
}
```

#### 最少连接（Least Connections）
```go
type LeastConnectionsStrategy struct{}

func (s *LeastConnectionsStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // 选择连接数最少的节点
}
```

## 3. 数据结构设计

### 3.1 缓存键设计

```
cache_key = method + ":" + host + ":" + path + "?" + query
```

示例：
```
GET:example.com:/index.html
GET:example.com:/api/data?id=123
```

### 3.2 节点状态

```go
type NodeStatus int

const (
    NodeStatusHealthy   NodeStatus = iota
    NodeStatusUnhealthy
    NodeStatusUnknown
)
```

### 3.3 配置结构

```go
type Config struct {
    Server   ServerConfig   `yaml:"server"`
    Cache    CacheConfig    `yaml:"cache"`
    Origin   OriginConfig   `yaml:"origin"`
    Dispatch DispatchConfig `yaml:"dispatch"`
}

type ServerConfig struct {
    Addr           string        `yaml:"addr"`
    ReadTimeout    time.Duration `yaml:"read_timeout"`
    WriteTimeout   time.Duration `yaml:"write_timeout"`
    MaxHeaderBytes int           `yaml:"max_header_bytes"`
}

type CacheConfig struct {
    MaxSize         int64         `yaml:"max_size"`
    DefaultTTL      time.Duration `yaml:"default_ttl"`
    CleanupInterval time.Duration `yaml:"cleanup_interval"`
}

type OriginConfig struct {
    URL        string        `yaml:"url"`
    Timeout    time.Duration `yaml:"timeout"`
    Retries    int           `yaml:"retries"`
    RetryDelay time.Duration `yaml:"retry_delay"`
}

type DispatchConfig struct {
    Algorithm         string        `yaml:"algorithm"`
    HealthCheckInterval time.Duration `yaml:"health_check_interval"`
}
```

## 4. 并发设计

### 4.1 缓存并发

使用`sync.RWMutex`保护缓存访问：
- 读操作使用读锁
- 写操作使用写锁
- 批量操作使用写锁

```go
func (c *LRUCache) Get(key string) (*CacheItem, bool) {
    c.mutex.RLock()
    defer c.mutex.RUnlock()
    // ...
}

func (c *LRUCache) Put(key string, item *CacheItem) {
    c.mutex.Lock()
    defer c.mutex.Unlock()
    // ...
}
```

### 4.2 节点并发

使用`sync.RWMutex`保护节点列表：
- 读操作（选择节点）使用读锁
- 写操作（添加/删除节点）使用写锁

### 4.3 连接并发

使用goroutine处理每个请求：
```go
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
    go s.processRequest(w, r)
}
```

## 5. 错误处理

### 5.1 错误类型

```go
var (
    ErrCacheMiss      = errors.New("cache miss")
    ErrCacheExpired   = errors.New("cache expired")
    ErrOriginTimeout  = errors.New("origin timeout")
    ErrOriginFailed   = errors.New("origin fetch failed")
    ErrNodeUnavailable = errors.New("no available node")
)
```

### 5.2 错误处理策略

| 错误类型 | 处理方式 |
|----------|----------|
| 缓存未命中 | 回源获取 |
| 缓存过期 | 回源获取，更新缓存 |
| 回源超时 | 返回错误，或返回过期缓存 |
| 回源失败 | 重试，或返回错误 |
| 节点不可用 | 选择其他节点 |

## 6. 性能优化

### 6.1 缓存优化

1. **内存池**：复用内存，减少GC压力
2. **压缩**：对大对象进行压缩
3. **分片**：按路径分片，减少锁竞争

### 6.2 网络优化

1. **连接池**：复用HTTP连接
2. **Keep-Alive**：保持长连接
3. **压缩**：支持gzip压缩

### 6.3 并发优化

1. **无锁数据结构**：使用sync.Map等
2. **批量操作**：减少锁的获取次数
3. **异步处理**：非关键路径异步执行

## 7. 监控设计

### 7.1 指标收集

```go
type Metrics struct {
    RequestsTotal    int64
    CacheHits        int64
    CacheMisses      int64
    OriginRequests   int64
    OriginErrors     int64
    ResponseTime     time.Duration
    ActiveConnections int64
}
```

### 7.2 日志设计

```go
type AccessLog struct {
    Timestamp    time.Time
    ClientIP     string
    Method       string
    Path         string
    StatusCode   int
    ResponseTime time.Duration
    CacheStatus  string  // HIT, MISS, EXPIRED
}
```

## 8. 扩展性设计

### 8.1 插件接口

```go
type Plugin interface {
    Name() string
    Init(config map[string]interface{}) error
    OnRequest(r *http.Request) error
    OnResponse(w http.ResponseWriter, r *http.Request) error
}
```

### 8.2 中间件支持

```go
type Middleware func(http.Handler) http.Handler

func Chain(middlewares ...Middleware) Middleware {
    // 组合多个中间件
}
```

## 9. 安全设计

### 9.1 缓存投毒防护

- 验证缓存键的合法性
- 限制缓存大小
- 定期清理过期缓存

### 9.2 访问控制

- IP白名单
- 路径白名单
- 速率限制

## 10. 测试策略

### 10.1 单元测试

- 缓存模块测试
- 调度算法测试
- 回源模块测试

### 10.2 集成测试

- 端到端请求测试
- 缓存命中测试
- 故障恢复测试

### 10.3 性能测试

- 并发测试
- 压力测试
- 内存泄漏测试

## 11. 部署设计

### 11.1 单机部署

```
┌─────────────────┐
│   CDN Server    │
│   (单实例)      │
└─────────────────┘
```

### 11.2 集群部署

```
┌─────────────┐
│ Load Balancer│
└──────┬──────┘
       │
       ├─────────┬─────────┐
       │         │         │
┌──────▼───┐ ┌───▼────┐ ┌─▼──────┐
│ CDN Node │ │CDN Node│ │CDN Node│
└──────────┘ └────────┘ └────────┘
```

## 12. 总结

本设计文档详细描述了CDN服务的架构、模块、数据结构和接口。通过模块化设计，保证了代码的可维护性和可扩展性。通过并发设计，保证了系统的高性能。