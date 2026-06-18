# MiniDB - 高并发数据库查询引擎

> 一个从零实现的支持高并发查询的轻量级数据库引擎

## 项目简介

MiniDB 是一个用于学习数据库内核原理的教学项目，实现了从 SQL 解析到存储引擎的完整查询链路。通过本项目，你可以深入理解 B+ 树索引、查询优化、并发控制等数据库核心技术。

## 学习目标

1. **B+ 树索引原理** ⭐⭐⭐
   - 理解 B+ 树的插入、删除、分裂、合并操作
   - 掌握范围查询的高效实现
   - 了解磁盘友好的数据结构设计

2. **查询优化和执行计划** ⭐⭐
   - 实现基于规则的查询优化（RBO）
   - 理解算子模型（Iterator Model）
   - 学习代价模型的基本思想

3. **并发控制和事务管理** ⭐⭐⭐
   - 实现读写锁（Read-Write Lock）
   - 理解 MVCC 的基本思想
   - 掌握死锁检测和预防

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C++17 | 主语言 | ⭐⭐ |
| CMake | 构建系统 | ⭐ |
| Google Test | 单元测试 | ⭐ |

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    SQL Interface                         │
│         (SQL Parser → AST → Logical Plan)               │
├─────────────────────────────────────────────────────────┤
│                    Query Optimizer                       │
│      (Rule-based Optimization → Physical Plan)          │
├─────────────────────────────────────────────────────────┤
│                   Execution Engine                       │
│         (Volcano Iterator Model → Result Set)           │
├─────────────────────────────────────────────────────────┤
│                  Storage Engine                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│   │ B+ Tree  │  │  Buffer  │  │  Concurrency     │     │
│   │  Index   │  │  Pool    │  │  Manager         │     │
│   └──────────┘  └──────────┘  └──────────────────┘     │
│              ┌──────────────────┐                       │
│              │   Disk Manager   │                       │
│              └──────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
high-concurrency-db/
├── CMakeLists.txt
├── README.md
├── LEARNING_NOTES.md
├── include/
│   ├── core/           # 核心类型定义
│   ├── sql/            # SQL 解析器
│   ├── storage/        # 存储引擎
│   ├── concurrency/    # 并发控制
│   └── cache/          # 缓存管理
├── src/
│   ├── core/           # 核心实现
│   ├── sql/            # SQL 解析实现
│   ├── storage/        # 存储引擎实现
│   ├── concurrency/    # 并发控制实现
│   └── cache/          # 缓存实现
├── tests/              # 单元测试
├── examples/           # 使用示例
├── docs/               # 项目文档
└── build/              # 构建目录
```

## 快速开始

### 编译

```bash
cd projects/high-concurrency-db
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 运行测试

```bash
cd build
./minidb_tests
```

### 运行示例

```bash
cd build
./minidb_example
```

## 核心功能

### 1. SQL 支持

- `CREATE TABLE table_name (col1 type1, col2 type2, ...)`
- `INSERT INTO table_name VALUES (val1, val2, ...)`
- `SELECT col1, col2 FROM table_name WHERE condition`
- `UPDATE table_name SET col1 = val1 WHERE condition`
- `DELETE FROM table_name WHERE condition`

### 2. 数据类型

- `INT` - 32 位整数
- `FLOAT` - 浮点数
- `VARCHAR(n)` - 变长字符串

### 3. 查询优化

- 谓词下推（Predicate Pushdown）
- 常量折叠（Constant Folding）
- 投影消除（Projection Elimination）

### 4. 并发控制

- 表级读写锁
- 事务隔离级别：READ COMMITTED
- 死锁检测

## 重点难点 ⭐

### 难点 1：B+ 树的节点分裂与合并
B+ 树的插入可能导致节点分裂，删除可能导致节点合并。需要仔细处理各种边界情况。

### 难点 2：查询优化器的设计
如何选择合适的执行计划是一个复杂的问题。本项目实现了基于规则的优化，但实际数据库会使用基于代价的优化（CBO）。

### 难点 3：并发控制的正确性
并发 bug 难以复现和调试。需要仔细设计锁的粒度和顺序，避免死锁和数据竞争。

## 值得思考 💡

1. **为什么用 B+ 树而不是 B 树？**
   - B+ 树的数据只存储在叶子节点，内部节点可以存储更多 key，树更矮，IO 更少

2. **为什么数据库不用哈希索引？**
   - 哈希索引不支持范围查询，而范围查询在实际业务中非常常见

3. **为什么需要 WAL（Write-Ahead Logging）？**
   - 为了保证事务的原子性和持久性，需要在修改数据之前先记录日志

4. **MVCC 如何实现快照隔离？**
   - 通过版本链和读视图（Read View）实现

## 参考资源

### 书籍
- 《Database Internals》- Alex Petrov
- 《Architecture of a Database System》- Joseph M. Hellerstein
- 《Database System Concepts》- Abraham Silberschatz

### 开源项目
- [SQLite](https://github.com/nicoritschel/SQLite) - 最流行的嵌入式数据库
- [LevelDB](https://github.com/google/leveldb) - Google 的 KV 存储引擎
- [RocksDB](https://github.com/facebook/rocksdb) - Facebook 的 KV 存储引擎
- [CMU 15-445](https://github.com/cmu-db/bustub) - CMU 数据库课程项目
- [MiniOB](https://github.com/oceanbase/miniob) - OceanBase 训练营项目

### 在线资源
- [CMU 15-445 视频课程](https://15445.courses.cs.cmu.edu/)
- [SQLite 架构文档](https://www.sqlite.org/arch.html)
- [B+ Tree 可视化](https://www.cs.usfca.edu/~galles/visualization/BPlusTree.html)

## 许可证

MIT License
