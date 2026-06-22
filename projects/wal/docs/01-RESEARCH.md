# 01-RESEARCH.md - WAL 技术研究

## 什么是 WAL？

WAL（Write-Ahead Logging，预写日志）是一种在数据修改之前先写入日志的技术。它的核心思想是：
1. 在修改实际数据之前，先将修改操作记录到日志中
2. 只有当日志写入成功后，才认为操作完成
3. 在系统崩溃后，可以通过重放日志来恢复数据

## WAL 的应用场景

### 1. 数据库系统
- PostgreSQL：使用 WAL 实现事务的原子性和持久性
- MySQL：InnoDB 存储引擎的 redo log
- SQLite：WAL 模式

### 2. 文件系统
- ext4：日志模式
- NTFS：事务日志

### 3. 分布式系统
- Raft 共识算法：日志复制
- Kafka：消息存储

## WAL 的核心原理

### ACID 特性保证

WAL 主要保证以下 ACID 特性：

1. **原子性（Atomicity）**
   - 事务要么全部完成，要么全部回滚
   - 通过日志记录可以回滚未完成的事务

2. **一致性（Consistency）**
   - 数据库从一个一致性状态转换到另一个一致性状态
   - 日志记录保证了数据的一致性

3. **隔离性（Isolation）**
   - 并发事务之间互不干扰
   - WAL 可以与锁机制结合实现隔离

4. **持久性（Durability）**
   - 已提交的事务不会丢失
   - 日志先于数据写入磁盘

### 写入流程

```
1. 开始事务
2. 写入日志记录（包括操作类型、数据、时间戳等）
3. 日志刷盘（fsync）
4. 修改内存中的数据
5. 定期将内存数据写入磁盘（检查点）
6. 提交事务
```

### 恢复流程

```
1. 读取最后一个检查点
2. 从检查点开始读取日志
3. 重放所有已提交的事务
4. 回滚未完成的事务
```

## 日志格式

### 基本日志记录格式

```
┌─────────────────────────────────────────────────────────────┐
│ Log Entry                                                    │
├─────────────────────────────────────────────────────────────┤
│ LSN (Log Sequence Number) - 8 bytes                        │
│ Transaction ID - 8 bytes                                    │
│ Operation Type - 1 byte (PUT/DELETE/CHECKPOINT)            │
│ Key Length - 4 bytes                                        │
│ Key - variable length                                       │
│ Value Length - 4 bytes                                      │
│ Value - variable length                                     │
│ CRC32 - 4 bytes (用于校验)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 检查点记录格式

```
┌─────────────────────────────────────────────────────────────┐
│ Checkpoint Record                                           │
├─────────────────────────────────────────────────────────────┤
│ Checkpoint LSN - 8 bytes                                   │
│ Timestamp - 8 bytes                                         │
│ Active Transactions Count - 4 bytes                         │
│ Active Transactions List - variable length                  │
│ Dirty Pages Count - 4 bytes                                 │
│ Dirty Pages List - variable length                          │
└─────────────────────────────────────────────────────────────┘
```

## 关键技术点

### 1. LSN（日志序列号）
- 每条日志记录的唯一标识
- 单调递增
- 用于恢复时确定重放位置

### 2. 日志刷盘
- `fsync()` 系统调用确保日志写入磁盘
- 批量刷盘可以提高性能
- 组提交（Group Commit）优化

### 3. 检查点机制
- 减少恢复时间
- 标记数据的一致性点
- 可以清理旧的日志文件

### 4. 日志清理
- 检查点之前的日志可以安全删除
- 归档日志用于备份和复制

## 性能优化

### 1. 顺序写入
- WAL 日志是顺序写入的
- 顺序写比随机写快很多

### 2. 批量操作
- 多个操作合并写入
- 减少 I/O 次数

### 3. 并发控制
- 使用锁或无锁数据结构
- 批量写入时需要考虑并发安全

### 4. 内存映射
- 使用 mmap 加速日志读取
- 注意内存使用和同步

## 参考资源

1. **Database Internals** - Alex Petrov
   - 第 5 章：Storage Engines
   - 详细介绍了 B-Tree 和 LSM-Tree 中的 WAL 实现

2. **Designing Data-Intensive Applications** - Martin Kleppmann
   - 第 3 章：Storage and Retrieval
   - 介绍了日志结构存储和 WAL 的基本原理

3. **PostgreSQL Documentation**
   - [WAL Configuration](https://www.postgresql.org/docs/current/wal-configuration.html)
   - [WAL Internals](https://www.postgresql.org/docs/current/wal-internals.html)

4. **InnoDB Storage Engine**
   - [Redo Log](https://dev.mysql.com/doc/refman/8.0/en/innodb-redo-log.html)

5. **Raft Consensus Algorithm**
   - [The Raft Paper](https://raft.github.io/raft.pdf)
   - 日志复制部分
