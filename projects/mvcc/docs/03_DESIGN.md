# 03 - 系统设计: MVCC 并发控制

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     MVCCEngine                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              事务接口层                           │    │
│  │  begin() | commit() | abort() | read() | write() │    │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│  ┌───────────┬───────────┼───────────┬──────────────┐    │
│  │           │           │           │              │    │
│  ▼           ▼           ▼           ▼              │    │
│ ┌────┐   ┌──────┐   ┌──────┐   ┌────────┐         │    │
│ │Txn │   │Storage│   │Conflict│  │   GC   │         │    │
│ │Mgr │   │Engine │   │Detector│  │        │         │    │
│ └────┘   └──────┘   └──────┘   └────────┘         │    │
│    │         │           │           │              │    │
│    ▼         ▼           ▼           ▼              │    │
│ ┌────┐   ┌──────┐   ┌──────┐   ┌────────┐         │    │
│ │Txn │   │Version│   │Result│   │Safe    │         │    │
│ │Obj │   │Chain  │   │      │   │Point   │         │    │
│ └────┘   └──────┘   └──────┘   └────────┘         │    │
│              │                                      │    │
│              ▼                                      │    │
│         ┌──────┐                                   │    │
│         │Version│                                   │    │
│         │ Node  │                                   │    │
│         └──────┘                                   │    │
└─────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 Version (版本链)

```
文件: src/mvcc/version.py

职责:
  - Version: 单个数据版本节点
  - VersionChain: 版本链管理

类图:
  Version {
    +data: Dict
    +create_txn_id: int
    +create_ts: int
    +delete_txn_id: int?
    +delete_ts: int?
    +prev: Version?
    +is_deleted: bool
    +mark_deleted(txn_id, ts)
  }

  VersionChain {
    +head: Version?
    +length: int
    +append(version)
    +find_visible(ts, active_txns, read_own, txn_id): Version?
    +find_latest_committed(): Version?
    +gc(min_active_ts, committed_txns): int
  }
```

### 2.2 Transaction (事务)

```
文件: src/mvcc/transaction.py

职责:
  - Transaction: 事务对象
  - TransactionManager: 事务生命周期管理

状态机:
  ┌────────┐   commit()   ┌───────────┐
  │ ACTIVE │──────────────→│ COMMITTED │
  │        │               └───────────┘
  │        │   abort()    ┌────────┐
  │        │──────────────→│ ABORTED│
  └────────┘               └────────┘

TransactionManager {
  +begin(snapshot): Transaction
  +commit(txn, commit_ts)
  +abort(txn)
  +advance_timestamp(): int
  +get_active_txn_ids(): Set[int]
  +get_committed_txns(): Dict[int, Transaction]
}
```

### 2.3 Snapshot (快照)

```
文件: src/mvcc/snapshot.py

职责:
  - 捕获事务开始时的数据库状态
  - 提供版本可见性判断

Snapshot {
  +timestamp: int           // 快照时间戳
  +active_txns: frozenset   // 活跃事务集合（不可变）
  +is_visible(create_txn, create_ts, delete_txn?, delete_ts?): bool
}

可见性判断算法:
  function is_visible(v):
    if v.create_txn in active_txns: return false
    if v.create_ts > timestamp: return false
    if v.delete_txn not in active_txns and v.delete_ts <= timestamp:
      return false
    return true
```

### 2.4 Storage (存储引擎)

```
文件: src/mvcc/storage.py

职责:
  - 管理主存储 (key -> VersionChain)
  - 提供事务感知的读写接口
  - 提交时应用写缓冲

数据流:
  WRITE:  txn.write_buffer[key] = value  (缓存)
  READ:   1. 检查 write_buffer
          2. 查找 version_chain.find_visible()
  COMMIT: 1. 创建新 Version
          2. 追加到 VersionChain
          3. 标记删除

Storage {
  +data: Dict[str, VersionChain]
  +read(key, txn): Any?
  +write(key, value, txn)
  +delete(key, txn): bool
  +apply_commit(txn, commit_ts): int
}
```

### 2.5 ConflictDetector (冲突检测)

```
文件: src/mvcc/conflict.py

职责:
  - 写写冲突检测
  - 读写冲突检测

检测算法:
  check_write_write(txn):
    for key in txn.write_buffer:
      chain = storage[key]
      latest = chain.find_latest_committed()
      if latest and latest.create_txn != txn.id
         and latest.create_ts > txn.start_ts:
        return CONFLICT

  check_read_write(txn):
    for key in txn.read_set - txn.write_buffer:
      chain = storage[key]
      latest = chain.find_latest_committed()
      if latest and latest.create_txn != txn.id
         and latest.create_ts > txn.start_ts:
        return CONFLICT
```

### 2.6 GarbageCollector (垃圾回收)

```
文件: src/mvcc/gc.py

职责:
  - 计算安全点
  - 清理旧版本

GC 算法:
  safe_point = min(txn.start_ts for txn in active_txns)

  for each version_chain:
    current = chain.head
    while current.next:
      if current.create_ts < safe_point
         and current.is_deleted
         and current.delete_txn in committed_txns:
        remove current from chain
      current = current.next
```

## 3. 数据流

### 3.1 事务写入流程

```
Application          Engine              Storage           VersionChain
    │                   │                   │                   │
    │── write(k,v) ───→│                   │                   │
    │                   │── buffer(k,v) ──→│                   │
    │                   │  (写缓冲)        │                   │
    │←──────────────────│                   │                   │
    │                   │                   │                   │
    │── commit() ──────→│                   │                   │
    │                   │── 检测冲突 ──────→│                   │
    │                   │                   │                   │
    │                   │── apply ─────────→│── new Version ───→│
    │                   │                   │  (追加到链头)      │
    │←── result ────────│                   │                   │
```

### 3.2 事务读取流程

```
Application          Engine              Storage           VersionChain
    │                   │                   │                   │
    │── read(k) ──────→│                   │                   │
    │                   │── check buffer ──→│                   │
    │                   │                   │                   │
    │                   │  (缓冲无数据)      │                   │
    │                   │── find_visible ──────────────────────→│
    │                   │                   │                   │
    │                   │←── version.data ─────────────────────│
    │←── value ─────────│                   │                   │
```

### 3.3 垃圾回收流程

```
GC Timer             GC                  Storage           VersionChain
    │                   │                   │                   │
    │── trigger ───────→│                   │                   │
    │                   │── compute_safe ──→│                   │
    │                   │←── safe_point ───│                   │
    │                   │                   │                   │
    │                   │── for each chain ────────────────────→│
    │                   │                   │                   │
    │                   │   ←── gc(safe_point, committed) ──────│
    │                   │                   │                   │
    │←── stats ─────────│                   │                   │
```

## 4. 关键算法

### 4.1 版本可见性判断

```python
def find_visible(chain, snapshot_ts, active_txns, read_own, txn_id):
    current = chain.head
    while current:
        # 读取自己的写入
        if read_own and current.create_txn_id == txn_id:
            return current

        # 创建事务已提交且时间 <= 快照
        if current.create_txn_id not in active_txns \
           and current.create_ts <= snapshot_ts:
            if not current.is_deleted:
                return current
            # 检查删除是否在快照之后
            if current.delete_txn_id in active_txns \
               or current.delete_ts > snapshot_ts:
                return current

        current = current.prev
    return None
```

### 4.2 写写冲突检测

```python
def check_ww_conflict(txn, storage, committed_txns):
    for key in txn.write_buffer:
        chain = storage.get(key)
        if not chain or not chain.head:
            continue

        latest = chain.head
        while latest and latest.create_txn_id == txn.txn_id:
            latest = latest.prev

        if latest:
            other = committed_txns.get(latest.create_txn_id)
            if other and other.commit_ts > txn.start_ts:
                return CONFLICT

    return NO_CONFLICT
```

## 5. 线程安全设计

```
┌──────────────────────────────────────────────┐
│           线程安全策略                         │
│                                               │
│  1. 写缓冲是事务私有的（无竞争）               │
│  2. 版本链追加是原子的（链头替换）             │
│  3. 冲突检测在提交时串行化                     │
│  4. GC 可以异步执行（不影响读写）              │
│                                               │
│  注意: Python GIL 提供了额外的线程安全保证     │
└──────────────────────────────────────────────┘
```

## 6. 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 事务不在活跃状态时提交/中止 | 抛出 RuntimeError |
| 写写冲突 | 返回 ConflictResult，自动中止 |
| 读写冲突 | 返回 ConflictResult，自动中止 |
| 读取不存在的 key | 返回 None |
| 删除不存在的 key | 返回 False |
