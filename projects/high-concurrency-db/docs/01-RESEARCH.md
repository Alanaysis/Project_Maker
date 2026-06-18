# 市场调研报告

## 1. 调研背景

在学习数据库内核开发时，了解现有开源数据库项目的架构和设计决策至关重要。本报告分析了主流嵌入式数据库和存储引擎，为 MiniDB 的设计提供参考。

## 2. 同类型项目分析

### 2.1 SQLite

**项目地址**: https://github.com/nicoritschel/SQLite

**核心特点**:
- 无服务器、零配置、事务性 SQL 数据库引擎
- 全球部署最广泛的数据库（Android、iOS、浏览器、Python 标准库）
- 单文件存储，B-Tree 索引
- 读写锁粒度：数据库级别

**架构分析**:
```
SQL Input → Tokenizer → Parser → Code Generator → Virtual Machine → B-Tree → Pager → OS Interface
```

**学习价值**:
- 代码简洁（约 15 万行 C 代码）
- 虚拟机执行模型清晰
- B-Tree 实现是经典参考

**局限性**:
- 写并发性能差（数据库级锁）
- 不支持网络访问
- 类型系统弱（动态类型）

---

### 2.2 LevelDB

**项目地址**: https://github.com/google/leveldb

**核心特点**:
- Google 开发的高性能 KV 存储引擎
- LSM-Tree 架构（Log-Structured Merge-Tree）
- 支持前向和反向迭代
- 原子批量写入

**架构分析**:
```
Write → WAL → MemTable → (Flush) → SSTable (Level 0) → (Compaction) → SSTable (Level N)
Read → MemTable → Immutable MemTable → SSTable Level 0 → ... → SSTable Level N
```

**技术特点**:
| 特性 | 实现 |
|------|------|
| 内存表 | SkipList |
| 磁盘格式 | SSTable (Sorted String Table) |
| 压缩 | Snappy |
| 缓存 | LRU Cache |
| 布隆过滤器 | 支持 |

**学习价值**:
- LSM-Tree 设计思想（写优化）
- SkipList 数据结构
- Compaction 策略

---

### 2.3 RocksDB

**项目地址**: https://github.com/facebook/rocksdb

**核心特点**:
- Facebook 基于 LevelDB 改进
- 针对 SSD 优化
- 更好的并发性能
- Column Family 支持

**与 LevelDB 对比**:
| 特性 | LevelDB | RocksDB |
|------|---------|---------|
| 并发 Compaction | 不支持 | 支持 |
| Column Family | 不支持 | 支持 |
| 布隆过滤器 | 简单 | 多种类型 |
| 压缩算法 | Snappy | LZ4, Zstd, Snappy |
| 事务 | 基础 | 完整 ACID |
| 内存表 | SkipList | SkipList + HashSkipList |

**学习价值**:
- 工业级存储引擎设计
- 优化技巧丰富
- 社区活跃

---

### 2.4 CMU BusTub

**项目地址**: https://github.com/cmu-db/bustub

**核心特点**:
- CMU 15-445 数据库课程教学项目
- 关系型数据库内核
- 支持 SQL（简化版）
- Buffer Pool + B+ Tree + Query Executor

**架构**:
```
SQL → Binder → Planner → Optimizer → Executor → Buffer Pool Manager → Disk Manager
```

**核心组件**:
- **Buffer Pool Manager**: LRU-K 替换策略
- **B+ Tree Index**: 支持并发的 B+ 树
- **Executor**: Volcano 模型
- **Optimizer**: 基于规则 + 基于代价

**学习价值**:
- 代码量适中，适合学习
- 教学文档完善
- 涵盖数据库核心概念

---

### 2.5 MiniOB (OceanBase 训练营)

**项目地址**: https://github.com/oceanbase/miniob

**核心特点**:
- OceanBase 团队开发的教学项目
- 面向数据库内核入门
- 支持基本 SQL 操作
- 代码结构清晰

**学习价值**:
- 中文文档丰富
- 配套训练营
- 企业级设计思路

---

## 3. 技术变体和演进路径

### 3.1 存储引擎架构演进

```
堆文件 (Heap File)
    ↓
哈希索引 (Hash Index)
    ↓
B-Tree / B+ Tree          ← 传统关系数据库 (MySQL InnoDB, PostgreSQL)
    ↓
LSM-Tree                   ← 现代 KV 存储 (LevelDB, RocksDB)
    ↓
BW-Tree                    ← 内存优化 (SQL Server Hekaton)
    ↓
Learned Index               ← 未来方向 (MIT)
```

### 3.2 索引结构对比

| 索引类型 | 读性能 | 写性能 | 范围查询 | 适用场景 |
|----------|--------|--------|----------|----------|
| B+ Tree | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | OLTP, 通用 |
| Hash | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | 等值查询 |
| LSM-Tree | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 写密集 |
| SkipList | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 内存数据库 |
| R-Tree | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 空间数据 |

### 3.3 并发控制演进

```
2PL (Two-Phase Locking)
    ↓
MVCC (Multi-Version Concurrency Control)
    ↓
OCC (Optimistic Concurrency Control)
    ↓
混合方案 (MVCC + OCC)
```

**各方案对比**:
| 方案 | 读写冲突 | 实现复杂度 | 适用场景 |
|------|----------|------------|----------|
| 2PL | 阻塞 | 低 | 传统数据库 |
| MVCC | 不阻塞读 | 中 | 现代数据库 |
| OCC | 验证阶段冲突 | 高 | 低冲突场景 |

---

## 4. 技术选型建议

### 4.1 存储架构选择

**MiniDB 选择: B+ Tree**

理由:
1. 教学价值高，B+ Tree 是数据库核心数据结构
2. 支持范围查询，适用于 SQL 场景
3. 实现相对简单，适合从零构建
4. 与传统关系数据库一致

**为什么不选 LSM-Tree?**
- LSM-Tree 更适合 KV 场景
- Compaction 逻辑复杂
- 读放大问题需要额外优化

### 4.2 并发控制选择

**MiniDB 选择: 读写锁 + 简化 MVCC**

理由:
1. 读写锁是并发控制的基础
2. 简化 MVCC 帮助理解核心思想
3. 避免过度复杂的锁管理

---

## 5. 发力方向分析

| 项目 | 发力方向 | 核心优势 |
|------|----------|----------|
| SQLite | 简单可靠 | 零配置，广泛部署 |
| LevelDB | 写性能 | LSM-Tree，简单 API |
| RocksDB | 极致性能 | SSD 优化，高度可调 |
| BusTub | 教学 | 清晰架构，配套课程 |
| MiniOB | 入门 | 中文生态，企业支持 |

---

## 6. 总结

通过调研，我们得出以下结论:

1. **B+ Tree 是关系数据库索引的标准选择**，适合 MiniDB 的定位
2. **Volcano/Iterator 模型**是查询执行的经典范式
3. **Buffer Pool**是存储引擎的核心组件
4. **并发控制**是数据库最难的部分之一
5. **教学项目**应注重代码清晰性而非极致性能

MiniDB 的设计将参考 BusTub 和 MiniOB 的架构，同时简化复杂度，专注于核心概念的学习。
