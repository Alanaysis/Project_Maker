# 04 - 产品规范: MVCC 并发控制

## 1. 产品概述

MVCC 并发控制引擎是一个教学级别的多版本并发控制系统，用于演示数据库事务隔离的核心机制。

### 目标用户

- 数据库学习者
- 后端开发者
- 分布式系统工程师

### 核心价值

- 理解 MVCC 的工作原理
- 学习快照隔离的实现方式
- 掌握并发控制的实际应用

## 2. 功能规格

### 2.1 核心功能

#### 事务管理

```
操作:
  begin()        开始新事务，返回事务对象
  commit(txn)    提交事务，返回冲突检测结果
  abort(txn)     中止事务，丢弃所有写入

约束:
  - 只有 ACTIVE 状态的事务可以提交或中止
  - 重复提交/中止会抛出 RuntimeError
```

#### 数据操作

```
操作:
  txn_read(txn, key)          读取数据
  txn_write(txn, key, value)  写入数据
  txn_delete(txn, key)        删除数据

行为:
  - 读操作先检查写缓冲，再查找版本链
  - 写操作只缓存到写缓冲
  - 删除操作标记到删除集合
  - 所有修改在提交时才生效
```

#### 冲突检测

```
检测类型:
  1. 写写冲突: 并发事务修改同一 key
  2. 读写冲突: 读取的数据被并发事务修改

返回值:
  ConflictResult {
    has_conflict: bool
    conflict_type: "write_write" | "read_write" | "none"
    conflicting_keys: Set[str]
    message: str
  }

处理策略:
  - 检测到冲突时自动中止事务
  - 支持跳过冲突检测的模式
```

#### 垃圾回收

```
操作:
  run_gc()          执行垃圾回收
  run_gc(max_keys)  限制处理的 key 数量

行为:
  - 计算安全点（最早活跃事务的时间戳）
  - 清理安全点之前的不可见旧版本
  - 每条版本链至少保留一个版本
```

### 2.2 批量操作

```
操作:
  txn_read_batch(txn, keys)         批量读取
  txn_write_batch(txn, kv_dict)     批量写入
```

### 2.3 查询接口

```
操作:
  get_version_chain(key)  获取版本链（调试用）
  get_stats()             获取引擎统计信息
```

## 3. 用户界面

### 3.1 Python API

```python
from mvcc.engine import MVCCEngine

# 创建引擎
engine = MVCCEngine(gc_threshold=10)

# 基本操作
txn = engine.begin()
engine.txn_write(txn, "name", "Alice")
engine.txn_write(txn, "age", 30)
result = engine.commit(txn)

# 读取
txn = engine.begin()
name = engine.txn_read(txn, "name")
engine.commit(txn)

# 冲突检测
result = engine.commit(txn)
if result.has_conflict:
    print(f"冲突: {result.message}")
    print(f"冲突 key: {result.conflicting_keys}")
```

### 3.2 错误信息

| 场景 | 错误信息 |
|------|----------|
| 提交非活跃事务 | "Cannot commit transaction {id}: status is {status}" |
| 中止非活跃事务 | "Cannot abort transaction {id}: status is {status}" |
| 写写冲突 | "Write-write conflict on keys: {keys}" |
| 读写冲突 | "Read-write conflict on keys: {keys}" |

## 4. 性能规格

### 4.1 延迟

| 操作 | 目标延迟 |
|------|----------|
| begin() | < 0.1ms |
| read() | < 0.5ms |
| write() | < 0.1ms |
| commit() (无冲突) | < 1ms |
| commit() (有冲突检测) | < 2ms |

### 4.2 吞吐量

| 场景 | 目标 |
|------|------|
| 读密集型 | > 10000 ops/s |
| 写密集型 | > 5000 ops/s |
| 混合型 | > 8000 ops/s |

### 4.3 内存使用

| 组件 | 内存占用 |
|------|----------|
| 单个版本 | ~100 bytes |
| 版本链 (10 版本) | ~1KB |
| 事务对象 | ~500 bytes |
| 快照 | ~100 bytes |

## 5. 测试规格

### 5.1 单元测试

```
测试文件:
  test_version.py      版本链测试
  test_transaction.py  事务管理测试
  test_snapshot.py     快照隔离测试
  test_storage.py      存储引擎测试
  test_conflict.py     冲突检测测试
  test_gc.py           垃圾回收测试
  test_engine.py       引擎集成测试
```

### 5.2 测试场景

| 场景 | 验证点 |
|------|--------|
| 基本读写 | 数据正确读写 |
| 快照隔离 | 事务看到一致视图 |
| 写写冲突 | 冲突被检测并中止 |
| 读写冲突 | Write Skew 被检测 |
| 中止事务 | 写入被丢弃 |
| 垃圾回收 | 旧版本被清理 |
| 批量操作 | 批量操作正确 |

### 5.3 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| version.py | > 90% |
| transaction.py | > 90% |
| snapshot.py | > 90% |
| storage.py | > 85% |
| conflict.py | > 85% |
| gc.py | > 80% |
| engine.py | > 85% |

## 6. 示例场景

### 6.1 银行转账

```
场景: Alice 向 Bob 转账 100 元

步骤:
  1. 开始事务
  2. 读取 Alice 余额
  3. 读取 Bob 余额
  4. 检查 Alice 余额 >= 100
  5. 写入 Alice 新余额
  6. 写入 Bob 新余额
  7. 提交事务

冲突场景:
  - 两个事务同时从 Alice 转出
  - 写写冲突检测，先提交者获胜
```

### 6.2 库存扣减

```
场景: 扣减商品库存

步骤:
  1. 开始事务
  2. 读取库存数量
  3. 检查库存 > 0
  4. 写入新库存数量
  5. 提交事务

冲突场景:
  - 并发扣减同一商品
  - 写写冲突，后提交者重试
```

## 7. 已知限制

| 限制 | 说明 |
|------|------|
| 内存存储 | 数据不持久化 |
| 单机 | 不支持分布式 |
| Python GIL | 并发受 GIL 限制 |
| 无索引 | 只支持 key 查找 |
| 无事务日志 | 不支持崩溃恢复 |
