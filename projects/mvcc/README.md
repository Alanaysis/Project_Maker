# MVCC 并发控制引擎

> 多版本并发控制 (Multi-Version Concurrency Control) 的 Python 实现

## 项目简介

本项目实现了一个教学级别的 MVCC 并发控制引擎，完整演示了数据库事务隔离的核心机制。MVCC 是 PostgreSQL、MySQL InnoDB 等主流数据库使用的核心并发控制技术。

### 核心特性

- **版本链**: 每条数据维护完整的历史版本链
- **快照隔离**: 事务看到开始时的一致性数据视图
- **写缓冲**: 写入先缓存，提交时批量应用
- **冲突检测**: 自动检测写写冲突和读写冲突 (Write Skew)
- **垃圾回收**: 自动清理不可见的旧版本

## 快速开始

### 环境要求

- Python 3.10+
- pytest (测试)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from mvcc.engine import MVCCEngine

# 创建引擎
engine = MVCCEngine()

# 写入数据
txn = engine.begin()
engine.txn_write(txn, "account_a", 1000)
engine.txn_write(txn, "account_b", 2000)
result = engine.commit(txn)
print(result.message)  # "Transaction committed successfully."

# 读取数据
txn = engine.begin()
balance = engine.txn_read(txn, "account_a")
print(f"Account A: {balance}")  # Account A: 1000
engine.commit(txn)
```

### 并发冲突检测

```python
engine = MVCCEngine()

# 写入初始数据
txn = engine.begin()
engine.txn_write(txn, "key", 100)
engine.commit(txn)

# 两个并发事务修改同一个 key
txn1 = engine.begin()
txn2 = engine.begin()

engine.txn_write(txn1, "key", 200)
engine.txn_write(txn2, "key", 300)

# txn1 先提交 -> 成功
engine.commit(txn1)

# txn2 后提交 -> 写写冲突，自动中止
result = engine.commit(txn2)
print(result.has_conflict)     # True
print(result.conflict_type)    # "write_write"
```

### 快照隔离

```python
engine = MVCCEngine()

# 写入初始数据
txn = engine.begin()
engine.txn_write(txn, "data", 100)
engine.commit(txn)

# 事务 A 开始（快照时刻 data=100）
txn_a = engine.begin()
print(engine.txn_read(txn_a, "data"))  # 100

# 事务 B 修改 data 并提交
txn_b = engine.begin()
engine.txn_write(txn_b, "data", 200)
engine.commit(txn_b)

# 事务 A 仍然看到旧值（快照隔离）
print(engine.txn_read(txn_a, "data"))  # 100
engine.commit(txn_a)
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_version.py -v
pytest tests/test_engine.py -v
```

## 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 并发访问模拟
python examples/concurrent_access.py
```

## 项目结构

```
mvcc/
├── src/mvcc/
│   ├── version.py       # 版本链管理
│   ├── transaction.py   # 事务管理器
│   ├── snapshot.py      # 快照隔离
│   ├── storage.py       # 存储引擎
│   ├── conflict.py      # 冲突检测
│   ├── gc.py            # 垃圾回收
│   └── engine.py        # 主引擎接口
├── tests/               # 单元测试和集成测试
├── examples/            # 使用示例
└── docs/                # 设计文档
```

## 技术文档

| 文档 | 说明 |
|------|------|
| [技术调研](docs/01_RESEARCH.md) | MVCC 原理和相关论文 |
| [需求分析](docs/02_REQUIREMENTS.md) | 功能和非功能需求 |
| [系统设计](docs/03_DESIGN.md) | 架构和模块设计 |
| [产品规范](docs/04_PRODUCT.md) | 接口和性能规格 |
| [开发笔记](docs/05_DEVELOPMENT.md) | 实现细节和问题记录 |

## MVCC 核心概念

```
┌─────────────────────────────────────────────────────┐
│                    MVCC 架构                         │
│                                                      │
│  事务 A (读)              事务 B (写)                │
│  ┌──────────────┐        ┌──────────────┐           │
│  │ 快照 ts=5     │        │ 写缓冲        │           │
│  │ active={2,3} │        │ {k1: v1}     │           │
│  └──────────────┘        └──────────────┘           │
│         │                       │                    │
│         ▼                       ▼                    │
│  ┌──────────────┐        ┌──────────────┐           │
│  │ 版本链查找    │        │ 提交时检测    │           │
│  │ find_visible │        │ 冲突          │           │
│  └──────────────┘        └──────────────┘           │
│         │                       │                    │
│         ▼                       ▼                    │
│  返回 ts<=5 且          无冲突: 应用写缓冲            │
│  不在 active 中         有冲突: 中止事务              │
│  的最新版本                                            │
└─────────────────────────────────────────────────────┘
```

## 技术栈

- **语言**: Python 3.10+
- **测试**: pytest
- **并发**: threading

## 难度等级

中级 (3/5)

## 学习收获

1. 理解 MVCC 多版本并发控制的核心原理
2. 掌握快照隔离的实现方式
3. 学习冲突检测（写写冲突、读写冲突）策略
4. 理解垃圾回收和安全点的概念
5. 了解主流数据库（PostgreSQL、MySQL）的并发控制机制

---

[返回主目录](../../README.md)
