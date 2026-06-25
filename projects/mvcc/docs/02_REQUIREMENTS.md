# 02 - 需求分析: MVCC 并发控制

## 1. 项目目标

实现一个教学级别的 MVCC 并发控制引擎，用于:
- 理解 MVCC 的核心原理
- 学习快照隔离的实现方式
- 掌握冲突检测和垃圾回收机制
- 体验并发事务的实际效果

## 2. 功能需求

### 2.1 版本链管理 (Version Chain)

| ID | 需求 | 优先级 |
|----|------|--------|
| V1 | 支持创建数据版本，包含数据内容、创建事务 ID、创建时间戳 | P0 |
| V2 | 支持版本链单链表结构，新版本插入链头 O(1) | P0 |
| V3 | 支持按快照查找可见版本 | P0 |
| V4 | 支持标记删除版本 | P0 |
| V5 | 支持版本链的垃圾回收 | P1 |

### 2.2 快照隔离 (Snapshot Isolation)

| ID | 需求 | 优先级 |
|----|------|--------|
| S1 | 事务开始时创建快照，包含时间戳和活跃事务集合 | P0 |
| S2 | 快照不可变，创建后不改变 | P0 |
| S3 | 支持基于快照的版本可见性判断 | P0 |
| S4 | 写入先缓存到写缓冲，不立即修改主存储 | P0 |
| S5 | 事务可以读取自己未提交的写入 | P0 |

### 2.3 事务管理 (Transaction Management)

| ID | 需求 | 优先级 |
|----|------|--------|
| T1 | 支持事务状态机: ACTIVE -> COMMITTED / ABORTED | P0 |
| T2 | 全局唯一事务 ID 分配 | P0 |
| T3 | 全局时间戳管理 | P0 |
| T4 | 活跃事务集合维护 | P0 |
| T5 | 读集合记录 | P0 |
| T6 | 写缓冲管理 | P0 |
| T7 | 删除集合管理 | P1 |

### 2.4 冲突检测 (Conflict Detection)

| ID | 需求 | 优先级 |
|----|------|--------|
| C1 | 写写冲突检测: 并发事务修改同一 key | P0 |
| C2 | 读写冲突检测: 读取的数据被并发事务修改 | P0 |
| C3 | First-Writer-Wins 策略: 先提交者获胜 | P0 |
| C4 | 冲突时自动中止事务 | P0 |
| C5 | 支持跳过冲突检测的提交模式 | P1 |

### 2.5 垃圾回收 (Garbage Collection)

| ID | 需求 | 优先级 |
|----|------|--------|
| G1 | 安全点计算: 最早活跃事务的时间戳 | P0 |
| G2 | 清理安全点之前的不可见旧版本 | P0 |
| G3 | 每条版本链至少保留一个版本 | P0 |
| G4 | 支持阈值触发 GC | P1 |
| G5 | 支持手动触发 GC | P1 |
| G6 | GC 统计信息 | P2 |

### 2.6 存储引擎 (Storage Engine)

| ID | 需求 | 优先级 |
|----|------|--------|
| E1 | 键值存储接口 (key-value) | P0 |
| E2 | 事务感知的读操作 (写缓冲 + 版本链) | P0 |
| E3 | 事务感知的写操作 (写缓冲) | P0 |
| E4 | 事务感知的删除操作 | P0 |
| E5 | 提交时批量应用写缓冲 | P0 |
| E6 | 批量读写接口 | P2 |

## 3. 非功能需求

### 3.1 性能要求

| 指标 | 目标 |
|------|------|
| 读操作延迟 | < 1ms (内存操作) |
| 写操作延迟 | < 1ms (写缓冲) |
| 提交延迟 | < 5ms (含冲突检测) |
| 支持并发事务数 | > 100 |

### 3.2 正确性要求

| 指标 | 说明 |
|------|------|
| 快照隔离 | 事务看到一致的数据视图 |
| 冲突检测 | 不漏检写写和读写冲突 |
| 数据完整性 | 中止的事务不影响其他事务 |

### 3.3 代码质量

| 指标 | 说明 |
|------|------|
| 测试覆盖率 | > 80% |
| 文档完整性 | 所有公共 API 有文档 |
| 类型注解 | 所有函数有类型注解 |

## 4. 接口设计

### 4.1 核心 API

```python
engine = MVCCEngine()

# 事务操作
txn = engine.begin()
engine.txn_write(txn, key, value)
engine.txn_read(txn, key)
engine.txn_delete(txn, key)
result = engine.commit(txn)
engine.abort(txn)

# 批量操作
engine.txn_write_batch(txn, {k1: v1, k2: v2})
engine.txn_read_batch(txn, [k1, k2])

# 垃圾回收
engine.run_gc()

# 统计信息
stats = engine.get_stats()
```

### 4.2 冲突检测结果

```python
@dataclass
class ConflictResult:
    has_conflict: bool
    conflict_type: str      # "write_write", "read_write", "none"
    conflicting_keys: Set[str]
    message: str
```

## 5. 数据模型

### 5.1 版本

```
Version {
    data: Dict[str, Any]    // 版本数据
    create_txn_id: int      // 创建事务 ID
    create_ts: int          // 创建时间戳
    delete_txn_id: int?     // 删除事务 ID
    delete_ts: int?         // 删除时间戳
    prev: Version?          // 前一个版本
}
```

### 5.2 快照

```
Snapshot {
    timestamp: int          // 快照时间戳
    active_txns: Set[int]   // 活跃事务 ID 集合
}
```

### 5.3 事务

```
Transaction {
    txn_id: int             // 事务 ID
    start_ts: int           // 开始时间戳
    status: TxnStatus       // 事务状态
    snapshot: Snapshot       // 快照
    read_set: Set[str]      // 读集合
    write_buffer: Dict      // 写缓冲
    delete_set: Set[str]    // 删除集合
}
```

## 6. 约束和限制

- 键值类型: key 为 string，value 为任意类型
- 存储方式: 内存存储（不持久化）
- 隔离级别: Snapshot Isolation (SI)
- 事务大小: 建议 < 1000 个操作
- 并发度: 受 Python GIL 限制
