# 分布式缓存系统

一个用 Go 实现的高性能分布式缓存系统，支持多种缓存淘汰策略、一致性哈希、多种缓存模式和分布式特性。

## 特性

### 缓存淘汰策略
- **LRU** (Least Recently Used) - 最近最少使用
- **LFU** (Least Frequently Used) - 最不经常使用
- **FIFO** (First In First Out) - 先进先出
- **TTL** (Time To Live) - 基于过期时间

### 一致性哈希
- 虚拟节点支持
- 节点动态扩缩容
- 数据均匀分布

### 缓存模式
- **Cache-Aside** - 应用管理缓存
- **Read-Through** - 缓存自动加载
- **Write-Through** - 同步写入
- **Write-Behind** - 异步写入

### 缓存问题解决方案
- **缓存穿透** - 布隆过滤器 + 空值缓存
- **缓存击穿** - Single Flight + 互斥锁
- **缓存雪崩** - 随机 TTL + 多级缓存

### 分布式特性
- 节点发现与管理
- 数据复制（同步/异步/Quorum）
- 故障转移与恢复

### 实际应用
- 热点数据缓存
- 会话存储
- 限流器（固定窗口/滑动窗口/令牌桶）

## 项目结构

```
distributed-cache/
├── cmd/
│   ├── server/          # HTTP 服务器
│   ├── client/          # 客户端示例
│   └── benchmark/       # 性能测试
├── internal/
│   ├── cache/           # 缓存核心实现
│   │   ├── cache.go     # 缓存主逻辑
│   │   ├── eviction.go  # 淘汰策略
│   │   └── item.go      # 缓存项
│   ├── hash/            # 一致性哈希
│   │   └── consistent.go
│   ├── patterns/        # 缓存模式
│   │   └── patterns.go
│   ├── problem/         # 缓存问题解决方案
│   │   └── solutions.go
│   ├── distributed/     # 分布式特性
│   │   ├── node.go      # 节点管理
│   │   ├── replication.go # 数据复制
│   │   └── failover.go  # 故障转移
│   └── application/     # 实际应用
│       ├── hotcache.go  # 热点缓存
│       ├── session.go   # 会话存储
│       └── ratelimiter.go # 限流器
├── pkg/
│   └── api/             # API 类型定义
├── test/                # 测试文件
└── docs/                # 文档
```

## 快速开始

### 前置要求

- Go 1.21+

### 安装

```bash
cd distributed-cache
go mod tidy
```

### 运行服务器

```bash
go run cmd/server/main.go [port]
```

默认端口为 8080。

### API 接口

#### 缓存操作

```bash
# 设置缓存
curl -X POST http://localhost:8080/cache/set \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "hello", "ttl": 60}'

# 获取缓存
curl http://localhost:8080/cache/get?key=test

# 删除缓存
curl -X DELETE http://localhost:8080/cache/delete?key=test
```

#### 热点缓存

```bash
# 设置热点数据
curl -X POST http://localhost:8080/hot/set \
  -H "Content-Type: application/json" \
  -d '{"key": "hot-data", "value": "popular"}'

# 获取热点数据
curl http://localhost:8080/hot/get?key=hot-data

# 查看热点键
curl http://localhost:8080/hot/keys
```

#### 会话管理

```bash
# 创建会话
curl -X POST http://localhost:8080/session/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "data": {"role": "admin"}}'

# 获取会话
curl http://localhost:8080/session/get?id=<session-id>

# 更新会话
curl -X POST http://localhost:8080/session/update \
  -H "Content-Type: application/json" \
  -d '{"id": "<session-id>", "data": {"last_login": "2024-01-01"}}'

# 删除会话
curl -X DELETE http://localhost:8080/session/delete?id=<session-id>
```

#### 限流器

```bash
# 检查限流
curl http://localhost:8080/ratelimit/check?key=user1
```

#### 集群信息

```bash
# 节点信息
curl http://localhost:8080/cluster/info

# 缓存统计
curl http://localhost:8080/cluster/stats

# 健康检查
curl http://localhost:8080/health
```

## 运行测试

```bash
# 运行所有测试
go test ./... -v

# 运行特定测试
go test ./test/ -v -run TestCache
go test ./internal/hash/ -v -run TestConsistentHash
```

## 性能测试

```bash
go run cmd/benchmark/main.go
```

## 设计原理

### 缓存淘汰策略

#### LRU (Least Recently Used)
- 使用双向链表 + HashMap 实现
- O(1) 时间复杂度的访问和删除
- 适用于访问模式有时间局部性的场景

#### LFU (Least Frequently Used)
- 使用频率桶实现
- 自动提升频繁访问的键
- 适用于访问模式有频率特征的场景

#### FIFO (First In First Out)
- 使用队列实现
- 最简单的淘汰策略
- 适用于数据有时效性的场景

#### TTL (Time To Live)
- 使用最小堆实现
- 自动过期清理
- 适用于需要精确过期控制的场景

### 一致性哈希

- 使用 SHA256 哈希函数
- 每个物理节点映射 150 个虚拟节点
- 节点扩缩容时只需迁移少量数据
- 支持数据复制（N 副本）

### 缓存模式

#### Cache-Aside
```
应用 -> 检查缓存 -> 命中? 返回 : 加载数据 -> 存入缓存 -> 返回
```

#### Read-Through
```
应用 -> 缓存 -> 命中? 返回 : 自动加载 -> 存入缓存 -> 返回
```

#### Write-Through
```
应用 -> 写入存储 -> 写入缓存 -> 返回
```

#### Write-Behind
```
应用 -> 写入缓存 -> 返回
                -> 异步写入存储
```

### 缓存问题解决方案

#### 缓存穿透
- **布隆过滤器**: 预先判断键是否存在
- **空值缓存**: 缓存不存在的键，设置较短 TTL

#### 缓存击穿
- **Single Flight**: 合并并发请求，只加载一次
- **互斥锁**: 使用 double-check 机制

#### 缓存雪崩
- **随机 TTL**: 避免同时过期
- **多级缓存**: L1 (快速) + L2 (大容量)

### 分布式特性

#### 数据复制
- **同步复制**: 写入所有副本后返回
- **异步复制**: 写入本地后异步复制
- **Quorum 复制**: 写入多数副本后返回

#### 故障转移
- 健康检查（每 5 秒）
- 故障阈值（连续 3 次失败）
- 自动恢复（最多重试 5 次）

## 学习要点

1. **缓存淘汰策略**: 理解不同策略的适用场景
2. **一致性哈希**: 掌握分布式数据分片原理
3. **缓存模式**: 学习缓存与存储的协作方式
4. **缓存问题**: 了解常见问题及解决方案
5. **分布式特性**: 理解数据复制和故障转移机制
6. **实际应用**: 学习缓存的实际应用场景

## 参考资料

- [Redis 设计与实现](https://redisbook.com/)
- [分布式系统：概念与设计](https://www.distributed-systems.net/)
- [一致性哈希算法](https://en.wikipedia.org/wiki/Consistent_hashing)
- [缓存模式](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)

## 许可证

MIT License
