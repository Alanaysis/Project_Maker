# WAL 日志学习笔记

## 项目概述

本项目实现了 WAL（Write-Ahead Logging，预写日志）系统，用于保证数据的一致性和持久性。

**技术栈**：Go

**学习目标**：
- 理解 WAL 原理
- 掌握日志写入
- 学会崩溃恢复

## 核心概念

### 什么是 WAL？

WAL 的核心思想是：**在修改数据之前，先将修改操作记录到日志中**。

```
传统方式：
1. 修改数据
2. 如果崩溃，数据可能不一致

WAL 方式：
1. 写入日志
2. 刷盘（fsync）
3. 修改数据
4. 如果崩溃，可以通过日志恢复
```

### 为什么需要 WAL？

1. **原子性**：事务要么全部完成，要么全部回滚
2. **持久性**：已提交的事务不会丢失
3. **一致性**：数据始终保持一致状态

### WAL 的应用场景

- **数据库**：PostgreSQL、MySQL、SQLite
- **文件系统**：ext4、NTFS
- **分布式系统**：Raft、Kafka

## 核心循环

```
操作 → 日志写入 → 数据写入 → 检查点
```

详细流程：

```
1. 应用发起操作（如 PUT key value）
2. WAL 记录该操作
3. 日志刷盘（fsync）
4. 修改内存中的数据
5. 定期创建检查点
6. 检查点之前的日志可以清理
```

## 实现细节

### 日志格式

```
┌─────────────────────────────────────────┐
│ Log Entry                               │
├─────────────────────────────────────────┤
│ LSN (8 bytes)      - 日志序列号        │
│ TxID (8 bytes)     - 事务 ID           │
│ OpType (1 byte)    - 操作类型          │
│ Key (variable)     - 键                │
│ Value (variable)   - 值                │
│ Timestamp (8 bytes) - 时间戳          │
│ CRC32 (4 bytes)    - 校验和            │
└─────────────────────────────────────────┘
```

### LSN（日志序列号）

- 每条日志的唯一标识
- 单调递增
- 用于恢复时确定重放位置

### 校验和

使用 CRC32 算法保证数据完整性：

```go
checksum := crc32.ChecksumIEEE(data)
```

### 崩溃恢复流程

```
1. 加载最后一个检查点
2. 从检查点位置开始读取日志
3. 识别已提交的事务
4. 重放已提交事务的操作
5. 回滚未完成的事务
```

### 检查点机制

```
检查点的作用：
1. 标记数据的一致性点
2. 减少恢复时间
3. 允许清理旧日志

检查点创建流程：
1. 暂停新的写入
2. 刷盘所有脏页
3. 写入检查点记录
4. 清理旧日志
5. 恢复写入
```

## 关键技术点

### 1. 顺序写入

WAL 日志是顺序写入的，顺序写比随机写快很多：

```
顺序写：100-200 MB/s
随机写：0.1-1 MB/s（HDD）
```

### 2. fsync 刷盘

确保日志真正写入磁盘：

```go
file.Sync() // 调用 fsync
```

### 3. 批量写入

多个操作合并写入，减少 I/O 次数：

```go
func WriteBatch(entries []*LogEntry) error {
    // 批量序列化
    // 一次性写入
    // 一次性刷盘
}
```

### 4. 并发控制

使用锁保证并发安全：

```go
type WALWriter struct {
    mu sync.Mutex
}

func (w *WALWriter) Write(entry *LogEntry) error {
    w.mu.Lock()
    defer w.mu.Unlock()
    // ...
}
```

## 学习收获

### 1. 数据一致性

WAL 保证了数据的一致性，即使在系统崩溃的情况下也能恢复。

### 2. 性能优化

- 顺序写入比随机写快
- 批量操作减少 I/O 次数
- 缓冲区管理提高性能

### 3. 错误处理

- 校验和保证数据完整性
- 崩溃恢复机制保证数据不丢失
- 错误重试机制提高可靠性

### 4. 系统设计

- 模块化设计便于维护
- 接口设计便于扩展
- 测试策略保证质量

## 实际应用

### 1. 数据库事务

```sql
BEGIN;
INSERT INTO users (name) VALUES ('Alice');
INSERT INTO users (name) VALUES ('Bob');
COMMIT;
```

WAL 记录：
1. BEGIN - 开始事务
2. INSERT users (name) VALUES ('Alice')
3. INSERT users (name) VALUES ('Bob')
4. COMMIT - 提交事务

### 2. 分布式复制

```
Leader: 写入 WAL → 复制到 Follower → 提交
Follower: 接收 WAL → 写入本地 → 确认
```

### 3. 消息队列

```
Producer: 发送消息 → 写入 WAL → 返回确认
Consumer: 读取消息 → 更新偏移量 → 写入 WAL
```

## 进一步学习

### 1. 相关论文

- **ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking**
  - 现代 WAL 实现的基础

- **The Log-Structured Merge-Tree (LSM-Tree)**
  - 日志结构存储的理论基础

### 2. 开源项目

- **PostgreSQL**：完整的 WAL 实现
- **SQLite**：WAL 模式实现
- **etcd**：Raft 日志实现

### 3. 相关技术

- **LSM-Tree**：日志结构合并树
- **B-Tree**：平衡树结构
- **Raft**：共识算法

## 常见问题

### Q1: WAL 和 Redo Log 的区别？

A: WAL 是通用概念，Redo Log 是 MySQL InnoDB 中的具体实现。

### Q2: 为什么需要 fsync？

A: 操作系统会缓冲写入，fsync 确保数据真正写入磁盘。

### Q3: 检查点频率如何选择？

A: 频繁检查点减少恢复时间但增加开销，需要根据场景平衡。

### Q4: 如何处理日志文件过大？

A: 定期创建检查点，清理检查点之前的日志。

## 总结

通过本项目，我深入理解了：

1. **WAL 原理**：预写日志保证数据一致性
2. **日志写入**：顺序写入、批量操作、fsync 刷盘
3. **崩溃恢复**：检查点 + 日志重放
4. **性能优化**：顺序写、批量操作、缓冲区管理

WAL 是数据库和分布式系统中的核心技术，掌握它对于理解现代存储系统非常重要。
