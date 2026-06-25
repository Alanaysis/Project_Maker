# 分布式缓存需求文档

## 1. 项目概述

### 1.1 项目目标

构建一个高性能、可扩展的分布式缓存系统，支持多种缓存策略和分布式特性。

### 1.2 核心价值

- **高性能**: 微秒级读写延迟
- **高可用**: 故障自动转移
- **可扩展**: 支持动态扩缩容
- **易使用**: 简洁的 API 接口

## 2. 功能需求

### 2.1 缓存核心功能

#### 2.1.1 基本操作

| 操作 | 描述 | 返回值 |
|------|------|--------|
| GET | 获取缓存值 | value, error |
| SET | 设置缓存值 | error |
| DELETE | 删除缓存值 | error |
| HAS | 检查键是否存在 | bool |
| CLEAR | 清空缓存 | - |

#### 2.1.2 缓存淘汰策略

**LRU (Least Recently Used)**
- 淘汰最久未访问的数据
- 支持自定义容量
- O(1) 时间复杂度

**LFU (Least Frequently Used)**
- 淘汰访问频率最低的数据
- 支持频率衰减
- O(1) 时间复杂度

**FIFO (First In First Out)**
- 淘汰最早进入的数据
- 适用于时效性数据
- O(1) 时间复杂度

**TTL (Time To Live)**
- 基于过期时间淘汰
- 支持全局和单键 TTL
- 自动清理过期数据

#### 2.1.3 缓存统计

- 命中次数 (Hits)
- 未命中次数 (Misses)
- 命中率 (Hit Rate)
- 淘汰次数 (Evictions)
- 当前大小 (Size)
- 容量 (Capacity)

### 2.2 一致性哈希

#### 2.2.1 基本功能

- 节点添加/删除
- 键到节点映射
- 虚拟节点支持

#### 2.2.2 虚拟节点

- 每个物理节点支持 N 个虚拟节点
- 可配置虚拟节点数量
- 提高数据分布均匀性

#### 2.2.3 节点扩缩容

**扩容**:
1. 新节点加入哈希环
2. 自动迁移部分数据
3. 只影响相邻节点的数据

**缩容**:
1. 节点离开哈希环
2. 数据迁移到相邻节点
3. 保证数据不丢失

### 2.3 缓存模式

#### 2.3.1 Cache-Aside

**职责**:
- 应用负责缓存管理
- 缓存未命中时从数据库加载
- 写入时更新数据库并删除缓存

**接口**:
```go
Get(key string) (interface{}, error)
Set(key string, value interface{}, ttl time.Duration) error
Delete(key string) error
```

#### 2.3.2 Read-Through

**职责**:
- 缓存自动加载数据
- 应用只需调用缓存接口
- 缓存层负责与数据库交互

**配置**:
- DataLoader: 数据加载函数
- TTL: 缓存过期时间

#### 2.3.3 Write-Through

**职责**:
- 写入时同步更新缓存和数据库
- 保证数据一致性
- 写延迟较高

**配置**:
- DataWriter: 数据写入函数
- DataLoader: 数据加载函数

#### 2.3.4 Write-Behind

**职责**:
- 写入时只更新缓存
- 异步批量写入数据库
- 写延迟最低

**配置**:
- BatchSize: 批量大小
- FlushInterval: 刷新间隔
- DataWriter: 数据写入函数

### 2.4 缓存问题解决方案

#### 2.4.1 缓存穿透

**问题**: 查询不存在的数据

**解决方案**:

**布隆过滤器**:
- 预先加载所有有效键
- 查询前先检查布隆过滤器
- 不存在的键直接返回

**空值缓存**:
- 缓存不存在的键
- 设置较短的 TTL
- 避免重复查询数据库

#### 2.4.2 缓存击穿

**问题**: 热点键过期，大量请求同时访问

**解决方案**:

**Single Flight**:
- 合并并发请求
- 只有一个请求去数据库加载
- 其他请求等待结果

**互斥锁**:
- Double-check 机制
- 先检查缓存
- 获取锁后再次检查

#### 2.4.3 缓存雪崩

**问题**: 大量缓存同时过期

**解决方案**:

**随机 TTL**:
- 基础 TTL + 随机偏移
- 避免同时过期

**多级缓存**:
- L1: 本地缓存（快速）
- L2: 分布式缓存（大容量）
- 逐级加载

### 2.5 分布式特性

#### 2.5.1 节点发现

**静态配置**:
- 预先配置节点列表
- 适用于小规模集群

**动态发现**:
- 支持注册中心
- 自动发现新节点
- 自动移除故障节点

#### 2.5.2 数据复制

**同步复制**:
- 写入所有副本后返回
- 数据强一致性
- 写延迟高

**异步复制**:
- 写入本地后异步复制
- 最终一致性
- 写延迟低

**Quorum 复制**:
- 写入多数副本后返回
- 可配置一致性级别
- 平衡一致性和性能

#### 2.5.3 故障转移

**健康检查**:
- 定期心跳检测
- 可配置检查间隔
- 多次失败确认

**故障处理**:
- 标记节点为故障
- 路由到健康节点
- 触发数据恢复

**节点恢复**:
- 自动检测恢复
- 重新加入集群
- 数据同步

### 2.6 实际应用

#### 2.6.1 热点数据缓存

**功能**:
- 热点检测：访问计数
- 动态 TTL：热点数据延长过期时间
- 热点列表：返回当前热点键

**配置**:
- Threshold: 热点阈值
- HotTTL: 热点数据 TTL
- ColdTTL: 冷数据 TTL

#### 2.6.2 会话存储

**功能**:
- 会话创建/获取/更新/删除
- 会话过期管理
- 用户会话查询

**配置**:
- DefaultTTL: 默认过期时间
- MaxTTL: 最大过期时间
- CleanupInterval: 清理间隔

#### 2.6.3 限流器

**算法**:

**固定窗口**:
- 固定时间窗口
- 窗口内计数
- 简单但有边界问题

**滑动窗口**:
- 平滑的限流效果
- 使用加权计数
- 更精确

**令牌桶**:
- 恒定速率生成令牌
- 允许突发流量
- 灵活

**漏桶**:
- 恒定速率处理请求
- 平滑流量
- 严格

**接口**:
```go
Allow(key string) RateLimitResult
```

**返回**:
- Allowed: 是否允许
- Remaining: 剩余配额
- ResetAt: 重置时间
- RetryAfter: 重试等待时间

## 3. 非功能需求

### 3.1 性能需求

| 指标 | 目标值 |
|------|--------|
| 读延迟 | < 1ms |
| 写延迟 | < 5ms |
| 吞吐量 | > 100K ops/sec |
| 命中率 | > 90% |

### 3.2 可用性需求

| 指标 | 目标值 |
|------|--------|
| 可用性 | 99.9% |
| 故障恢复时间 | < 30s |
| 数据丢失 | 0 (同步复制) |

### 3.3 扩展性需求

| 指标 | 目标值 |
|------|--------|
| 节点数量 | 支持 100+ 节点 |
| 数据容量 | 支持 TB 级 |
| 并发连接 | 支持 10K+ |

### 3.4 安全需求

- 访问控制
- 数据加密
- 审计日志

## 4. 接口需求

### 4.1 HTTP API

#### 缓存操作

```
GET  /cache/get?key={key}
POST /cache/set
DELETE /cache/delete?key={key}
```

#### 热点缓存

```
GET  /hot/get?key={key}
POST /hot/set
GET  /hot/keys
```

#### 会话管理

```
POST /session/create
GET  /session/get?id={id}
POST /session/update
DELETE /session/delete?id={id}
```

#### 限流器

```
GET  /ratelimit/check?key={key}
```

#### 集群管理

```
GET  /cluster/info
GET  /cluster/stats
GET  /health
```

### 4.2 响应格式

```json
{
  "success": true,
  "value": "...",
  "error": "",
  "stats": {
    "hits": 100,
    "misses": 10,
    "hit_rate": 0.91,
    "size": 1000,
    "capacity": 10000,
    "evictions": 5
  }
}
```

## 5. 配置需求

### 5.1 缓存配置

```go
type CacheConfig struct {
    Capacity     int           // 缓存容量
    EvictionType string        // 淘汰策略: lru, lfu, fifo, ttl
    DefaultTTL   time.Duration // 默认 TTL
    CleanupTick  time.Duration // 清理间隔
}
```

### 5.2 复制配置

```go
type ReplicationConfig struct {
    Replicas int               // 副本数
    Strategy ReplicationStrategy // 复制策略
}
```

### 5.3 故障转移配置

```go
type FailoverConfig struct {
    HealthCheckInterval time.Duration // 健康检查间隔
    FailureThreshold    int           // 故障阈值
    RecoveryInterval    time.Duration // 恢复检查间隔
    MaxRetries          int           // 最大重试次数
}
```

## 6. 测试需求

### 6.1 单元测试

- 缓存基本操作
- 淘汰策略
- 一致性哈希
- 缓存模式
- 缓存问题解决方案

### 6.2 集成测试

- 节点间通信
- 数据复制
- 故障转移

### 6.3 性能测试

- 单机性能
- 集群性能
- 扩展性测试

### 6.4 压力测试

- 高并发测试
- 大数据量测试
- 长时间稳定性测试

## 7. 部署需求

### 7.1 环境要求

- Go 1.21+
- Linux/macOS
- 内存: 4GB+
- CPU: 2核+

### 7.2 部署方式

**单机部署**:
```bash
go run cmd/server/main.go 8080
```

**集群部署**:
```bash
go run cmd/server/main.go 8080  # Node 1
go run cmd/server/main.go 8081  # Node 2
go run cmd/server/main.go 8082  # Node 3
```

### 7.3 监控需求

- 命中率监控
- 延迟监控
- 内存使用监控
- 节点状态监控
