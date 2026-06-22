# 01 - 研究: LSM Tree 技术调研

## 什么是 LSM Tree?

LSM Tree (Log-Structured Merge Tree) 是一种基于日志结构的存储引擎设计，由 Patrick O'Neil 等人在 1996 年提出。它是 LevelDB、RocksDB、Cassandra、HBase 等现代存储系统的核心数据结构。

## 核心思想

### 传统 B+ 树的问题

传统关系数据库使用 B+ 树作为存储结构:
- 每次写入需要找到正确的页并修改
- 随机 IO 性能差，尤其是 HDD
- 写放大严重 (一次写入可能触发多次页分裂)

### LSM Tree 的解决方案

LSM Tree 将随机写转为顺序写:

```
传统 B+ 树:  随机写 → 查找页 → 修改 → 写回
LSM Tree:    顺序写 → 内存表 → 批量刷盘 → 后台合并
```

关键优势:
1. **写入快**: 先写内存，顺序刷盘
2. **吞吐高**: 批量写入减少 IO 次数
3. **压缩好**: 合并时可以压缩数据

## 业界实现对比

| 系统 | MemTable | SSTable | Compaction | 特点 |
|------|----------|---------|------------|------|
| LevelDB | 跳表 | Block-based | 分层合并 | 简单高效 |
| RocksDB | 跳表 | Block/Index/Filter | 分层/通用 | 高度可配置 |
| Cassandra | 跳表 | 顺序写 | 分层/时间窗口 | 分布式 |
| HBase | 跳表 | HFile | 分层合并 | HDFS 集成 |

## 关键数据结构

### 1. 跳表 (Skip List)

跳表是 MemTable 的首选实现:

```
优点:
- O(log N) 平均查找/插入/删除
- 实现简单，代码量少
- 天然支持有序遍历
- 并发友好 (锁粒度细)

缺点:
- 空间开销 (多级指针)
- 不是严格平衡 (概率性的)
```

### 2. SSTable (Sorted String Table)

SSTable 是磁盘上的有序存储格式:

```
特点:
- 数据按 key 排序
- 支持稀疏索引加速查找
- 不可变 (immutable)，写入后不修改
- 支持前缀压缩减少空间
```

### 3. WAL (Write-Ahead Log)

WAL 保证数据持久性:

```
作用:
- 崩溃恢复: 重放 WAL 恢复 MemTable
- 顺序写: 所有写入先到 WAL
- 批量刷盘: MemTable 满了再刷
```

## Compaction 策略

### Size-Tiered Compaction

```
SSTable 大小相近，按大小分层
优点: 写放大低
缺点: 空间放大高，读性能差
```

### Leveled Compaction

```
每层 SSTable 大小递增，key 范围不重叠
优点: 空间放大低，读性能好
缺点: 写放大高
```

### 本项目选择: Leveled Compaction

原因:
1. 更好的读性能
2. 空间可控
3. 实现相对简单

## 性能指标

### 写入性能

| 操作 | 耗时 | 说明 |
|------|------|------|
| MemTable 写入 | ~100ns | 纯内存 |
| WAL 写入 | ~1us | 顺序磁盘 IO |
| Flush | ~10ms | 批量顺序写 |

### 读取性能

| 场景 | 耗时 | 说明 |
|------|------|------|
| MemTable 命中 | ~100ns | 最好情况 |
| L0 SSTable | ~1ms | 需要查多个文件 |
| L1+ SSTable | ~100us | 稀疏索引加速 |

## 参考资料

1. [The Log-Structured Merge-Tree (LSM-Tree)](http://www.cs.umb.edu/~poneil/lsmtree.pdf)
2. [LevelDB 实现文档](https://github.com/google/leveldb/blob/master/doc/impl.md)
3. [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki)
4. [Designing Data-Intensive Applications - Chapter 3](https://dataintensive.net/)
