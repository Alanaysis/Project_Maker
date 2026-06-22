# 开发手册

## 1. 环境搭建

### 1.1 系统要求

| 要求 | 版本 | 说明 |
|------|------|------|
| 操作系统 | Linux/macOS | 推荐Linux |
| Go | 1.21+ | 编译和运行 |
| Git | 2.0+ | 版本控制 |
| 内存 | 1GB+ | 编译和运行 |
| 磁盘 | 100MB+ | 项目文件 |

### 1.2 安装Go

#### Linux
```bash
# 下载Go
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# 解压
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 添加到PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# 验证
go version
```

#### macOS
```bash
# 使用Homebrew
brew install go

# 验证
go version
```

### 1.3 配置Go环境

```bash
# 设置GOPATH
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# 设置Go代理（中国用户）
go env -w GOPROXY=https://goproxy.cn,direct
```

### 1.4 获取项目

```bash
# 克隆项目
git clone <repository-url>
cd projects/cdn-service

# 初始化模块
go mod init cdn-service

# 下载依赖
go mod tidy
```

## 2. 项目结构详解

```
cdn-service/
├── cmd/
│   └── cdn-server/          # 主程序入口
│       └── main.go          # 程序入口点
├── pkg/                     # 核心包
│   ├── cache/               # 缓存模块
│   │   ├── lru.go           # LRU缓存实现
│   │   ├── manager.go       # 缓存管理器
│   │   └── cache_test.go    # 缓存测试
│   ├── dispatcher/          # 调度模块
│   │   ├── scheduler.go     # 智能调度
│   │   └── scheduler_test.go # 调度测试
│   ├── origin/              # 回源模块
│   │   ├── fetcher.go       # 回源获取
│   │   └── fetcher_test.go  # 回源测试
│   └── server/              # HTTP服务器
│       ├── handler.go       # 请求处理
│       └── handler_test.go  # 处理测试
├── docs/                    # 文档
├── examples/                # 使用示例
├── tests/                   # 集成测试
├── go.mod                   # Go模块文件
├── go.sum                   # 依赖校验
└── Makefile                 # 构建脚本
```

## 3. 核心模块解析

### 3.1 LRU缓存模块

#### 文件位置
`pkg/cache/lru.go`

#### 核心数据结构

```go
type LRUCache struct {
    capacity int           // 缓存容量
    size     int           // 当前大小
    cache    map[string]*list.Element  // 哈希表
    list     *list.List    // 双向链表
    mutex    sync.RWMutex  // 读写锁
}

type entry struct {
    key   string
    value *CacheItem
}
```

#### 核心算法

**Get操作**：
1. 从哈希表查找元素
2. 如果找到，移到链表头部
3. 返回元素

**Put操作**：
1. 如果元素已存在，更新值，移到链表头部
2. 如果缓存满，删除链表尾部元素
3. 插入新元素到链表头部

**时间复杂度**：
- Get: O(1)
- Put: O(1)
- Delete: O(1)

#### 关键代码

```go
func (c *LRUCache) Get(key string) (*CacheItem, bool) {
    c.mutex.RLock()
    defer c.mutex.RUnlock()

    if elem, ok := c.cache[key]; ok {
        c.list.MoveToFront(elem)
        return elem.Value.(*entry).value, true
    }
    return nil, false
}

func (c *LRUCache) Put(key string, item *CacheItem) {
    c.mutex.Lock()
    defer c.mutex.Unlock()

    if elem, ok := c.cache[key]; ok {
        c.list.MoveToFront(elem)
        elem.Value.(*entry).value = item
        return
    }

    if c.list.Len() >= c.capacity {
        c.removeOldest()
    }

    elem := c.list.PushFront(&entry{key, item})
    c.cache[key] = elem
}
```

### 3.2 缓存管理器

#### 文件位置
`pkg/cache/manager.go`

#### 核心职责

1. 管理缓存生命周期
2. 处理缓存过期
3. 提供缓存统计
4. 控制缓存大小

#### 关键接口

```go
type CacheManager struct {
    cache       *LRUCache
    maxSize     int64
    currentSize int64
    stats       CacheStats
    defaultTTL  time.Duration
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
func (cm *CacheManager) Stats() CacheStats
```

#### 过期处理

```go
func (cm *CacheManager) cleanup() {
    ticker := time.NewTicker(cm.cleanupInterval)
    defer ticker.Stop()

    for range ticker.C {
        cm.mutex.Lock()
        // 遍历缓存，删除过期项
        cm.mutex.Unlock()
    }
}
```

### 3.3 回源模块

#### 文件位置
`pkg/origin/fetcher.go`

#### 核心职责

1. 从源站获取内容
2. 处理回源错误
3. 支持重试机制

#### 关键接口

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

#### 重试策略

```go
func (of *OriginFetcher) FetchWithRetry(path string, headers http.Header) (*http.Response, error) {
    var lastErr error

    for i := 0; i <= of.retries; i++ {
        resp, err := of.Fetch(path, headers)
        if err == nil {
            return resp, nil
        }

        lastErr = err

        if i < of.retries {
            // 指数退避
            delay := time.Duration(1<<uint(i)) * 100 * time.Millisecond
            time.Sleep(delay)
        }
    }

    return nil, lastErr
}
```

### 3.4 调度模块

#### 文件位置
`pkg/dispatcher/scheduler.go`

#### 核心职责

1. 选择后端节点
2. 实现负载均衡算法
3. 管理节点状态

#### 调度算法

**轮询（Round Robin）**：
```go
type RoundRobinStrategy struct {
    current int
}

func (s *RoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    if len(nodes) == 0 {
        return nil, ErrNoAvailableNode
    }

    node := nodes[s.current%len(nodes)]
    s.current++
    return node, nil
}
```

**加权轮询（Weighted Round Robin）**：
```go
type WeightedRoundRobinStrategy struct {
    current int
    weight  int
}

func (s *WeightedRoundRobinStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // 根据权重选择节点
}
```

**最少连接（Least Connections）**：
```go
type LeastConnectionsStrategy struct{}

func (s *LeastConnectionsStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // 选择连接数最少的节点
}
```

### 3.5 HTTP服务器模块

#### 文件位置
`pkg/server/handler.go`

#### 核心职责

1. 监听HTTP请求
2. 解析请求参数
3. 调用其他模块处理
4. 返回响应

#### 请求处理流程

```go
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
    // 1. 生成缓存键
    cacheKey := generateCacheKey(r)

    // 2. 查询缓存
    if item, ok := s.cache.Get(cacheKey); ok {
        // 缓存命中，直接返回
        s.writeResponse(w, item)
        return
    }

    // 3. 缓存未命中，回源获取
    resp, err := s.origin.Fetch(r.URL.Path, r.Header)
    if err != nil {
        http.Error(w, "Origin fetch failed", http.StatusBadGateway)
        return
    }

    // 4. 读取响应内容
    body, err := io.ReadAll(resp.Body)
    if err != nil {
        http.Error(w, "Read response failed", http.StatusInternalServerError)
        return
    }

    // 5. 更新缓存
    item := &CacheItem{
        Key:        cacheKey,
        Value:      body,
        Headers:    resp.Header,
        StatusCode: resp.StatusCode,
        CreatedAt:  time.Now(),
        ExpiresAt:  time.Now().Add(s.defaultTTL),
    }
    s.cache.Set(cacheKey, item, s.defaultTTL)

    // 6. 返回响应
    s.writeResponse(w, item)
}
```

## 4. 开发流程

### 4.1 开发步骤

1. **理解需求**：阅读需求文档
2. **设计接口**：定义模块接口
3. **实现功能**：编写代码
4. **编写测试**：单元测试和集成测试
5. **代码审查**：检查代码质量
6. **性能测试**：验证性能指标

### 4.2 代码规范

#### 命名规范

```go
// 包名：小写单词
package cache

// 结构体：大写开头，驼峰命名
type CacheManager struct {}

// 函数：大写开头（导出）或小写开头（内部）
func (cm *CacheManager) Get(key string) (*CacheItem, bool) {}
func generateCacheKey(r *http.Request) string {}

// 常量：大写，下划线分隔
const MAX_CACHE_SIZE = 1024

// 变量：小写，驼峰命名
var defaultTTL = time.Hour
```

#### 注释规范

```go
// Get retrieves an item from the cache.
// It returns the item and true if found, nil and false otherwise.
// The item is moved to the front of the LRU list.
func (c *LRUCache) Get(key string) (*CacheItem, bool) {
    // ...
}
```

### 4.3 测试规范

#### 单元测试

```go
func TestLRUCache_Get(t *testing.T) {
    cache := NewLRUCache(10)

    // 测试缓存未命中
    item, ok := cache.Get("key1")
    if ok {
        t.Error("Expected cache miss")
    }

    // 测试缓存命中
    cache.Put("key1", &CacheItem{Value: []byte("value1")})
    item, ok = cache.Get("key1")
    if !ok {
        t.Error("Expected cache hit")
    }
    if string(item.Value) != "value1" {
        t.Error("Value mismatch")
    }
}
```

#### 基准测试

```go
func BenchmarkLRUCache_Get(b *testing.B) {
    cache := NewLRUCache(1000)
    for i := 0; i < 1000; i++ {
        cache.Put(fmt.Sprintf("key%d", i), &CacheItem{})
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        cache.Get(fmt.Sprintf("key%d", i%1000))
    }
}
```

## 5. 构建和运行

### 5.1 使用Makefile

```makefile
# Makefile

.PHONY: build run test clean

# 构建
build:
	go build -o bin/cdn-server cmd/cdn-server/main.go

# 运行
run: build
	./bin/cdn-server -port 8080 -origin http://localhost:9090

# 测试
test:
	go test -v ./...

# 清理
clean:
	rm -rf bin/

# 格式化代码
fmt:
	go fmt ./...

# 静态检查
vet:
	go vet ./...

# 生成文档
docs:
	godoc -http=:6060
```

### 5.2 手动构建

```bash
# 构建
go build -o bin/cdn-server cmd/cdn-server/main.go

# 运行
./bin/cdn-server -port 8080 -origin http://localhost:9090

# 测试
go test -v ./...

# 格式化
go fmt ./...

# 静态检查
go vet ./...
```

### 5.3 命令行参数

```bash
./bin/cdn-server [options]

Options:
  -port int
        监听端口 (default 8080)
  -origin string
        源站地址 (default "http://localhost:9090")
  -cache-size int
        缓存大小(MB) (default 100)
  -cache-ttl duration
        缓存TTL (default 1h)
  -log-level string
        日志级别 (default "info")
```

## 6. 调试技巧

### 6.1 日志调试

```go
import "log"

func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
    log.Printf("Received request: %s %s", r.Method, r.URL.Path)

    // ...

    log.Printf("Cache hit for key: %s", cacheKey)
}
```

### 6.2 性能分析

```go
import "runtime/pprof"

// CPU分析
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// 内存分析
f, _ := os.Create("mem.prof")
pprof.WriteHeapProfile(f)
```

### 6.3 使用Delve调试器

```bash
# 安装Delve
go install github.com/go-delve/delve/cmd/dlv@latest

# 启动调试
dlv debug cmd/cdn-server/main.go

# 设置断点
(dlv) break main.main
(dlv) break pkg/cache/lru.go:50

# 运行
(dlv) continue

# 查看变量
(dlv) print cacheKey
(dlv) print item
```

## 7. 常见问题

### 7.1 编译错误

**问题**：`cannot find package`
**解决**：运行 `go mod tidy`

**问题**：`undefined: xxx`
**解决**：检查导入路径和包名

### 7.2 运行错误

**问题**：`bind: address already in use`
**解决**：更换端口或停止占用端口的程序

**问题**：`connection refused`
**解决**：检查源站是否运行

### 7.3 性能问题

**问题**：缓存命中率低
**解决**：调整缓存大小和TTL

**问题**：响应时间长
**解决**：检查网络和源站性能

## 8. 最佳实践

### 8.1 代码组织

- 一个文件只做一件事
- 相关功能放在同一个包
- 避免循环依赖

### 8.2 错误处理

- 不要忽略错误
- 提供有意义的错误信息
- 使用错误包装

### 8.3 并发安全

- 使用适当的锁
- 避免锁的粒度过大
- 注意死锁

### 8.4 性能优化

- 减少内存分配
- 使用对象池
- 避免不必要的拷贝

## 9. 扩展开发

### 9.1 添加新的缓存策略

```go
// 实现Strategy接口
type LFUStrategy struct {
    // ...
}

func (s *LFUStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // LFU实现
}
```

### 9.2 添加新的调度算法

```go
// 实现Strategy接口
type IPHashStrategy struct {
    // ...
}

func (s *IPHashStrategy) Select(nodes []*Node, r *http.Request) (*Node, error) {
    // IP哈希实现
}
```

### 9.3 添加中间件

```go
// 日志中间件
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
    })
}
```

## 10. 总结

本开发手册详细介绍了CDN服务的开发环境、代码结构、核心模块和开发流程。通过遵循本手册，开发者可以快速上手项目开发，并理解CDN的核心原理。