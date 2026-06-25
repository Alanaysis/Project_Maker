# 分布式缓存产品文档

## 1. 产品概述

### 1.1 产品定位

分布式缓存系统是一个高性能、可扩展的内存缓存解决方案，适用于需要快速数据访问的应用场景。

### 1.2 目标用户

- 后端开发工程师
- 架构师
- 运维工程师

### 1.3 使用场景

- **Web 应用加速**: 缓存数据库查询结果
- **API 网关**: 限流和缓存
- **会话管理**: 存储用户会话
- **热点数据**: 缓存高频访问数据

## 2. 快速开始

### 2.1 安装

```bash
# 克隆项目
git clone <repo-url>
cd distributed-cache

# 安装依赖
go mod tidy
```

### 2.2 启动服务器

```bash
# 默认端口 8080
go run cmd/server/main.go

# 自定义端口
go run cmd/server/main.go 9090
```

### 2.3 基本使用

#### 设置缓存

```bash
curl -X POST http://localhost:8080/cache/set \
  -H "Content-Type: application/json" \
  -d '{
    "key": "user:1",
    "value": {"name": "Alice", "age": 30},
    "ttl": 3600
  }'
```

#### 获取缓存

```bash
curl http://localhost:8080/cache/get?key=user:1
```

#### 删除缓存

```bash
curl -X DELETE http://localhost:8080/cache/delete?key=user:1
```

## 3. 功能详解

### 3.1 缓存淘汰策略

#### LRU (默认)

最久未使用的数据最先被淘汰。

```bash
# 使用 LRU 策略
go run cmd/server/main.go
```

**适用场景**: 访问模式具有时间局部性

#### LFU

访问频率最低的数据最先被淘汰。

**适用场景**: 访问模式具有频率特征

#### FIFO

最早进入缓存的数据最先被淘汰。

**适用场景**: 数据具有时效性

#### TTL

基于过期时间淘汰。

**适用场景**: 数据具有明确的生命周期

### 3.2 热点数据缓存

自动检测和缓存热点数据。

#### 设置热点数据

```bash
curl -X POST http://localhost:8080/hot/set \
  -H "Content-Type: application/json" \
  -d '{
    "key": "popular-product",
    "value": {"id": 1, "name": "iPhone"}
  }'
```

#### 获取热点数据

```bash
curl http://localhost:8080/hot/get?key=popular-product
```

#### 查看热点键

```bash
curl http://localhost:8080/hot/keys
```

**特性**:
- 自动检测访问频率高的键
- 热点数据自动延长 TTL
- 可配置热点阈值

### 3.3 会话管理

存储和管理用户会话。

#### 创建会话

```bash
curl -X POST http://localhost:8080/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "data": {
      "role": "admin",
      "permissions": ["read", "write"]
    }
  }'
```

响应:
```json
{
  "ID": "abc123...",
  "UserID": "user123",
  "Data": {"role": "admin", "permissions": ["read", "write"]},
  "CreatedAt": "2024-01-01T00:00:00Z",
  "ExpiresAt": "2024-01-01T00:30:00Z"
}
```

#### 获取会话

```bash
curl http://localhost:8080/session/get?id=abc123...
```

#### 更新会话

```bash
curl -X POST http://localhost:8080/session/update \
  -H "Content-Type: application/json" \
  -d '{
    "id": "abc123...",
    "data": {"last_login": "2024-01-01T12:00:00Z"}
  }'
```

#### 删除会话

```bash
curl -X DELETE http://localhost:8080/session/delete?id=abc123...
```

**特性**:
- 自动生成会话 ID
- 支持自定义 TTL
- 自动清理过期会话
- 支持按用户查询会话

### 3.4 限流器

保护后端服务免受过载。

#### 检查限流

```bash
curl http://localhost:8080/ratelimit/check?key=client1
```

响应:
```json
{
  "Allowed": true,
  "Remaining": 95,
  "ResetAt": "2024-01-01T00:01:00Z",
  "RetryAfter": 0
}
```

**限流算法**:

#### 固定窗口
- 固定时间窗口（如每分钟）
- 窗口内计数
- 简单但有边界问题

#### 滑动窗口
- 平滑的限流效果
- 使用加权计数
- 更精确

#### 令牌桶
- 恒定速率生成令牌
- 允许突发流量
- 灵活

#### 漏桶
- 恒定速率处理请求
- 平滑流量
- 严格

### 3.5 集群管理

#### 查看节点信息

```bash
curl http://localhost:8080/cluster/info
```

响应:
```json
{
  "node_id": "node-8080",
  "address": "localhost:8080",
  "state": 0
}
```

#### 查看缓存统计

```bash
curl http://localhost:8080/cluster/stats
```

响应:
```json
{
  "hits": 1000,
  "misses": 100,
  "hit_rate": 0.91,
  "size": 500,
  "capacity": 10000,
  "evictions": 10
}
```

#### 健康检查

```bash
curl http://localhost:8080/health
```

响应:
```json
{
  "status": "healthy"
}
```

## 4. 集群部署

### 4.1 启动集群

```bash
# 终端 1: 启动节点 1
go run cmd/server/main.go 8080

# 终端 2: 启动节点 2
go run cmd/server/main.go 8081

# 终端 3: 启动节点 3
go run cmd/server/main.go 8082
```

### 4.2 数据分布

使用一致性哈希，数据均匀分布在各节点：

- 每个物理节点对应 150 个虚拟节点
- 数据根据键的哈希值分配到对应节点
- 节点扩缩容时只迁移少量数据

### 4.3 数据复制

支持多种复制策略：

#### 同步复制
- 写入所有副本后返回
- 数据强一致性
- 写延迟较高

#### 异步复制
- 写入本地后异步复制
- 最终一致性
- 写延迟低

#### Quorum 复制
- 写入多数副本后返回
- 可配置一致性级别
- 平衡一致性和性能

### 4.4 故障转移

自动检测和处理节点故障：

1. **健康检查**: 每 5 秒检查一次
2. **故障阈值**: 连续 3 次失败标记为故障
3. **自动恢复**: 每 30 秒尝试恢复，最多重试 5 次
4. **数据恢复**: 故障节点恢复后自动同步数据

## 5. 配置说明

### 5.1 缓存配置

```go
type CacheConfig struct {
    Capacity     int           // 缓存容量，默认 10000
    EvictionType string        // 淘汰策略: lru, lfu, fifo, ttl
    DefaultTTL   time.Duration // 默认 TTL，默认 10 分钟
    CleanupTick  time.Duration // 清理间隔，默认 1 分钟
}
```

### 5.2 会话配置

```go
type SessionConfig struct {
    DefaultTTL      time.Duration // 默认 TTL，默认 30 分钟
    MaxTTL          time.Duration // 最大 TTL，默认 24 小时
    CleanupInterval time.Duration // 清理间隔，默认 5 分钟
}
```

### 5.3 限流配置

```go
type RateLimiterConfig struct {
    RequestsPerWindow int           // 窗口内最大请求数，默认 100
    WindowSize        time.Duration // 窗口大小，默认 1 分钟
    BurstSize         int           // 突发大小，默认 10
}
```

### 5.4 故障转移配置

```go
type FailoverConfig struct {
    HealthCheckInterval time.Duration // 健康检查间隔，默认 5 秒
    FailureThreshold    int           // 故障阈值，默认 3
    RecoveryInterval    time.Duration // 恢复检查间隔，默认 30 秒
    MaxRetries          int           // 最大重试次数，默认 5
}
```

## 6. 性能指标

### 6.1 延迟

| 操作 | P50 | P99 |
|------|-----|-----|
| GET | 0.1ms | 1ms |
| SET | 0.2ms | 2ms |
| DELETE | 0.1ms | 1ms |

### 6.2 吞吐量

| 并发数 | 吞吐量 |
|--------|--------|
| 1 | 10K ops/sec |
| 10 | 80K ops/sec |
| 100 | 500K ops/sec |

### 6.3 命中率

- 预热后: > 95%
- 稳态: > 90%
- 冷启动: 逐渐提升

### 6.4 内存使用

- 基础开销: ~10MB
- 每个缓存项: ~100 bytes
- 10K 项: ~1MB

## 7. 最佳实践

### 7.1 键命名规范

```
# 推荐格式
{type}:{id}:{field}

# 示例
user:123:profile
product:456:details
session:abc123
```

### 7.2 TTL 设置

```
# 短期数据 (频繁变化)
TTL: 1-5 分钟

# 中期数据 (偶尔变化)
TTL: 10-30 分钟

# 长期数据 (很少变化)
TTL: 1-24 小时

# 会话数据
TTL: 30 分钟 - 24 小时
```

### 7.3 缓存策略选择

```
# 读多写少
使用 Cache-Aside 或 Read-Through

# 写密集型
使用 Write-Behind

# 强一致性要求
使用 Write-Through

# 热点数据
使用热点缓存功能
```

### 7.4 容量规划

```
# 计算公式
所需内存 = 每项大小 × 项数 × (1 + 冗余系数)

# 示例
100 bytes × 100,000 × 1.2 = 12MB
```

## 8. 故障排查

### 8.1 命中率低

**可能原因**:
- 缓存容量不足
- TTL 设置过短
- 访问模式不匹配

**解决方案**:
- 增加缓存容量
- 调整 TTL
- 更换淘汰策略

### 8.2 延迟高

**可能原因**:
- 缓存雪崩
- 网络问题
- 内存不足

**解决方案**:
- 使用随机 TTL
- 检查网络
- 增加内存

### 8.3 节点故障

**可能原因**:
- 网络分区
- 资源耗尽
- 程序崩溃

**解决方案**:
- 检查网络连接
- 监控资源使用
- 查看日志

## 9. 常见问题

### Q: 如何选择淘汰策略？

A: 根据访问模式选择：
- 时间局部性强: LRU
- 频率特征明显: LFU
- 数据有时效性: FIFO
- 需要精确过期: TTL

### Q: 如何保证数据一致性？

A: 使用 Write-Through 模式，或在 Cache-Aside 模式下先更新数据库再删除缓存。

### Q: 如何处理缓存穿透？

A: 使用布隆过滤器或缓存空值。

### Q: 如何处理缓存雪崩？

A: 使用随机 TTL 或多级缓存。

### Q: 如何扩展集群？

A: 添加新节点，一致性哈希会自动重新分配数据。

## 10. 更新日志

### v1.0.0 (2024-01-01)

- 初始发布
- 支持 LRU/LFU/FIFO/TTL 淘汰策略
- 支持一致性哈希
- 支持缓存模式 (Cache-Aside, Read-Through, Write-Through, Write-Behind)
- 支持热点缓存、会话管理、限流器
- 支持集群部署和故障转移
