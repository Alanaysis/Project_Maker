# 05 - 开发笔记: MVCC 并发控制

## 1. 开发环境

```
语言: Python 3.10+
依赖: pytest (测试框架)
工具: git, pytest, mypy (可选)
```

## 2. 项目结构

```
projects/mvcc/
├── README.md                   # 项目文档
├── LEARNING_NOTES.md           # 学习笔记
├── requirements.txt            # 依赖
├── docs/
│   ├── 01_RESEARCH.md          # 技术调研
│   ├── 02_REQUIREMENTS.md      # 需求分析
│   ├── 03_DESIGN.md            # 系统设计
│   ├── 04_PRODUCT.md           # 产品规范
│   └── 05_DEVELOPMENT.md       # 开发笔记（本文件）
├── src/
│   ├── __init__.py
│   └── mvcc/
│       ├── __init__.py         # 包导出
│       ├── version.py          # 版本链
│       ├── transaction.py      # 事务管理
│       ├── snapshot.py         # 快照隔离
│       ├── storage.py          # 存储引擎
│       ├── conflict.py         # 冲突检测
│       ├── gc.py               # 垃圾回收
│       └── engine.py           # 主引擎
├── tests/
│   ├── __init__.py
│   ├── test_version.py
│   ├── test_transaction.py
│   ├── test_snapshot.py
│   ├── test_storage.py
│   ├── test_conflict.py
│   ├── test_gc.py
│   └── test_engine.py
└── examples/
    ├── basic_usage.py          # 基本使用示例
    └── concurrent_access.py    # 并发访问示例
```

## 3. 实现细节

### 3.1 版本链实现

版本链采用单链表结构，新版本插入链头:

```
插入新版本: O(1)
  new_version.prev = chain.head
  chain.head = new_version

查找可见版本: O(n)
  遍历版本链，找到第一个满足可见性条件的版本

垃圾回收: O(n)
  遍历版本链，删除满足清理条件的旧版本
```

### 3.2 快照实现

快照使用 frozenset 存储活跃事务集合:

```python
class Snapshot:
    __slots__ = ("timestamp", "active_txns")

    def __init__(self, timestamp, active_txns):
        self.timestamp = timestamp
        self.active_txns = frozenset(active_txns)  # 不可变
```

使用 frozenset 的原因:
- 不可变性保证快照不会被修改
- 可以作为字典键
- 支持高效的集合操作

### 3.3 写缓冲设计

写缓冲是事务私有的:

```python
class Transaction:
    write_buffer: Dict[str, Any]    # key -> value
    delete_set: Set[str]            # 要删除的 key
```

提交时批量应用:

```python
def apply_commit(txn, commit_ts):
    for key, value in txn.write_buffer.items():
        version = Version(data={"value": value}, ...)
        chain.append(version)

    for key in txn.delete_set:
        chain.head.mark_deleted(txn.txn_id, commit_ts)
```

### 3.4 冲突检测时机

冲突检测在提交时进行（乐观并发控制）:

```
写入阶段: 只记录到写缓冲，不检测冲突
提交阶段:
  1. 检查写写冲突
  2. 检查读写冲突
  3. 无冲突则应用写缓冲
  4. 有冲突则中止事务
```

## 4. 开发过程中遇到的问题

### 4.1 版本可见性判断

问题: 如何正确判断一个版本对快照是否可见?

解决方案: 三层判断
1. 创建事务是否在活跃集合中
2. 创建时间是否 <= 快照时间
3. 删除操作是否在快照之前

### 4.2 写写冲突检测

问题: 如何避免误检自己的写入为冲突?

解决方案: 跳过自己创建的版本

```python
while latest and latest.create_txn_id == txn.txn_id:
    latest = latest.prev
```

### 4.3 读写冲突中的自依赖

问题: 事务读取自己写入的 key 不应该产生冲突

解决方案: 在检查读写冲突时排除自己写入的 key

```python
for key in txn.read_set:
    if key in txn.write_buffer:
        continue  # 自依赖，跳过
```

### 4.4 GC 安全点计算

问题: 如何确定可以安全清理的版本?

解决方案: 取所有活跃事务中最早的开始时间戳

```python
safe_point = min(txn.start_ts for txn in active_txns)
```

## 5. 测试策略

### 5.1 测试层次

```
单元测试: 测试单个类/方法
  - Version, VersionChain
  - Transaction, TransactionManager
  - Snapshot
  - Storage
  - ConflictDetector
  - GarbageCollector

集成测试: 测试多个组件协作
  - MVCCEngine (完整的读写提交流程)
```

### 5.2 关键测试场景

```
1. 基本读写: 验证数据正确读写
2. 快照隔离: 验证事务看到一致视图
3. 写写冲突: 验证冲突检测
4. 读写冲突: 验证 Write Skew 检测
5. 中止丢弃: 验证中止后数据不泄露
6. 垃圾回收: 验证旧版本被清理
7. 并发访问: 验证线程安全
```

## 6. 构建和运行

### 6.1 安装依赖

```bash
cd projects/mvcc
pip install -r requirements.txt
```

### 6.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_version.py -v

# 运行并显示覆盖率
pytest tests/ -v --cov=src/mvcc
```

### 6.3 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 并发访问示例
python examples/concurrent_access.py
```

## 7. 学习收获

### 7.1 MVCC 核心概念

- 版本链是 MVCC 的数据基础
- 快照是 MVCC 的隔离机制
- 冲突检测是 MVCC 的并发控制手段
- 垃圾回收是 MVCC 的空间管理策略

### 7.2 快照隔离

- 快照在事务开始时创建
- 所有读操作基于快照进行
- 写入先缓存，提交时检测冲突
- 实现了读写不互斥

### 7.3 冲突类型

- 写写冲突: 两个事务修改同一数据
- 读写冲突 (Write Skew): 读取的数据被并发修改
- 两种冲突都需要在提交时检测

## 8. 改进方向

| 方向 | 说明 |
|------|------|
| 持久化 | 支持数据落盘 |
| 索引 | 支持范围查询 |
| 分布式 | 支持多节点协调 |
| 事务日志 | 支持崩溃恢复 |
| 隔离级别 | 支持更多隔离级别 |
| 性能优化 | 减少锁竞争 |

## 9. 参考实现

- PostgreSQL MVCC
- MySQL InnoDB MVCC
- Hekaton (SQL Server)
- TicToc (2015)
- FOEDUS (2014)
