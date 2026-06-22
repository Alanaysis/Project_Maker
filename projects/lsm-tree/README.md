# LSM Tree - 日志结构合并树存储引擎

## 项目概述

这是一个 LSM Tree (Log-Structured Merge Tree) 存储引擎的 Go 实现，用于理解现代数据库存储引擎的核心原理。LSM Tree 是 LevelDB、RocksDB、Cassandra 等流行存储系统的基础数据结构。

## 核心特性

- **MemTable**: 基于跳表的内存写缓冲区
- **SSTable**: 有序字符串表的磁盘存储格式
- **WAL**: 预写日志保证数据持久性
- **Compaction**: 分层合并策略，回收空间并优化读取

## 项目结构

```
lsm-tree/
├── internal/           # 核心实现
│   ├── skiplist.go    # 跳表数据结构
│   ├── memtable.go    # MemTable 内存表
│   ├── sstable.go     # SSTable 磁盘存储
│   ├── wal.go         # 预写日志
│   ├── compaction.go  # 合并压缩策略
│   └── engine.go      # LSM 引擎主入口
├── cmd/lsm-tree/      # 命令行入口
│   └── main.go        # 演示程序
├── test/              # 测试文件
│   ├── skiplist_test.go
│   ├── memtable_test.go
│   ├── sstable_test.go
│   ├── wal_test.go
│   ├── compaction_test.go
│   └── engine_test.go
└── docs/              # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 运行演示

```bash
cd projects/lsm-tree
go run cmd/lsm-tree/main.go
```

### 运行测试

```bash
cd projects/lsm-tree
go test ./test/ -v
```

### 查看覆盖率

```bash
cd projects/lsm-tree
go test ./test/ -coverpkg=./internal/ -coverprofile=coverage.out
go tool cover -func=coverage.out
```

## 核心概念

### LSM Tree 写入路径

```
写入请求 → WAL (持久化) → MemTable (内存) → [达到阈值] → Flush → SSTable (磁盘)
```

### LSM Tree 读取路径

```
读取请求 → MemTable → SSTable L0 → SSTable L1 → ... → 返回结果
```

### Compaction 合并

```
Level 0 SSTables (可能重叠)
    ↓ 合并
Level 1 SSTables (不重叠)
    ↓ 合并
Level 2 SSTables (不重叠，更大)
    ...
```

## API 使用

```go
// 创建引擎
engine, _ := lsm.NewLSMEngine("/tmp/mydata", 4096)
defer engine.Close()

// 写入数据
engine.Put([]byte("name"), []byte("Alice"))

// 读取数据
value, _ := engine.Get([]byte("name"))
fmt.Println(string(value)) // "Alice"

// 更新数据
engine.Put([]byte("name"), []byte("Bob"))

// 删除数据
engine.Delete([]byte("name"))
```

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| MemTable 结构 | 跳表 | O(log N) 操作，支持有序遍历 |
| SSTable 格式 | 稀疏索引 | 平衡索引大小和查找效率 |
| Compaction 策略 | 分层合并 | 减少写放大，控制空间 |
| WAL 格式 | CRC32 校验 | 保证数据完整性 |

## 学习目标

通过本项目，你将学到:
1. **LSM Tree 原理**: 理解写优化存储引擎的核心思想
2. **MemTable/SSTable**: 掌握内存和磁盘存储组件
3. **WAL 机制**: 学会预写日志保证数据持久性
4. **Compaction 策略**: 理解空间回收和读写平衡

## 参考资源

- [LevelDB 文档](https://github.com/google/leveldb)
- [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki)
- [LSM Tree 论文](http://www.cs.umb.edu/~poneil/lsmtree.pdf)

---

[返回主目录](../../README.md)
