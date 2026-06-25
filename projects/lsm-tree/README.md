# LSM Tree - 日志结构合并树存储引擎

## 项目概述

这是一个 LSM Tree (Log-Structured Merge Tree) 存储引擎的 Go 实现，用于理解现代数据库存储引擎的核心原理。LSM Tree 是 LevelDB、RocksDB、Cassandra 等流行存储系统的基础数据结构。

## 核心特性

- **MemTable**: 基于跳表的内存写缓冲区
- **SSTable**: 有序字符串表的磁盘存储格式，包含稀疏索引和布隆过滤器
- **WAL**: 预写日志保证数据持久性
- **Bloom Filter**: 概率数据结构，快速判断键是否不存在，减少无效磁盘 I/O
- **Compaction**: 支持两种合并策略
  - **Leveled Compaction**: 分层合并，减少读放大
  - **Size-Tiered Compaction**: 按大小分组合并，减少写放大

## 项目结构

```
lsm-tree/
├── internal/           # 核心实现
│   ├── skiplist.go    # 跳表数据结构
│   ├── memtable.go    # MemTable 内存表
│   ├── sstable.go     # SSTable 磁盘存储（含布隆过滤器）
│   ├── bloom.go       # 布隆过滤器实现
│   ├── wal.go         # 预写日志
│   ├── compaction.go  # 合并压缩策略（Leveled + Size-Tiered）
│   └── engine.go      # LSM 引擎主入口
├── cmd/lsm-tree/      # 命令行入口
│   └── main.go        # 演示程序
├── test/              # 测试文件
│   ├── skiplist_test.go
│   ├── sstable_test.go
│   ├── bloom_test.go
│   ├── wal_test.go
│   ├── compaction_test.go
│   ├── sizetiered_test.go
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
读取请求 → MemTable → [Bloom Filter 检查] → SSTable L0 → SSTable L1 → ... → 返回结果
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

// 读取数据（自动使用布隆过滤器加速）
value, _ := engine.Get([]byte("name"))
fmt.Println(string(value)) // "Alice"

// 更新数据
engine.Put([]byte("name"), []byte("Bob"))

// 删除数据
engine.Delete([]byte("name"))

// 使用布隆过滤器
bloom := lsm.OptimalBloomFilter(1000, 0.01) // 1000个元素，1%假阳性率
bloom.Add([]byte("key1"))
bloom.Contains([]byte("key1")) // true
bloom.Contains([]byte("key2")) // false（确定不存在）

// 使用 Size-Tiered Compaction
nextID := 0
st := lsm.NewSizeTieredCompactionStrategy("/tmp/data", &nextID)
if st.ShouldCompact(sstables) {
    compacted, _ := st.Compact(sstables)
}
```

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| MemTable 结构 | 跳表 | O(log N) 操作，支持有序遍历 |
| SSTable 格式 | 稀疏索引 + 布隆过滤器 | 平衡索引大小和查找效率，快速过滤不存在的键 |
| Bloom Filter | 双哈希技术 | 更好的分布性，减少假阳性率 |
| Compaction 策略 | Leveled + Size-Tiered | Leveled 减少读放大，Size-Tiered 减少写放大 |
| WAL 格式 | CRC32 校验 | 保证数据完整性 |

## 学习目标

通过本项目，你将学到:
1. **LSM Tree 原理**: 理解写优化存储引擎的核心思想
2. **MemTable/SSTable**: 掌握内存和磁盘存储组件
3. **WAL 机制**: 学会预写日志保证数据持久性
4. **Bloom Filter**: 理解概率数据结构在存储引擎中的应用
5. **Compaction 策略**: 理解 Leveled 和 Size-Tiered 两种合并策略的权衡

## 参考资源

- [LevelDB 文档](https://github.com/google/leveldb)
- [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki)
- [LSM Tree 论文](http://www.cs.umb.edu/~poneil/lsmtree.pdf)

---

[返回主目录](../../README.md)
