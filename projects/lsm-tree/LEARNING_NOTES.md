# LSM Tree 学习笔记

## 核心概念理解

### 什么是 LSM Tree?

LSM Tree (Log-Structured Merge Tree) 是一种写优化的存储引擎设计。它的核心思想是:
- **写入时**: 先写内存 (MemTable)，再异步刷到磁盘 (SSTable)
- **读取时**: 从最新到最老依次查找
- **定期合并**: 将多个小 SSTable 合并成更大的 SSTable

### 为什么需要 LSM Tree?

传统 B+ 树的写入需要随机 IO，性能差。LSM Tree 将随机写转为顺序写:
- 写 MemTable 是纯内存操作，非常快
- Flush 到磁盘是顺序写，比随机写快 10-100 倍
- 代价是读取需要查多个文件，通过 Compaction 优化

## 数据结构详解

### 跳表 (Skip List)

```
Level 3: HEAD ─────────────────────────────────────→ 9 → NIL
Level 2: HEAD ────────────→ 3 ──────→ 7 ──→ 9 → NIL
Level 1: HEAD ──→ 1 ──→ 3 ──→ 5 ──→ 7 ──→ 9 → NIL
Level 0: HEAD → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → NIL
```

关键特性:
- 概率平衡，不需要旋转操作
- 平均 O(log N) 查找
- 实现简单，适合并发

### SSTable 格式

```
┌─────────────────────────┐
│     Data Blocks         │  ← 排序的 KV 对
│  [key_len][key][val_len]│
│  [value][deleted][crc32]│
├─────────────────────────┤
│     Index Block         │  ← 稀疏索引 (每 16 个 key)
│  [key_len][key][offset] │
├─────────────────────────┤
│     Footer              │  ← 元数据
│  [index_offset][count]  │
│  [index_count][level]   │
└─────────────────────────┘
```

### WAL 格式

```
Record: [type:1][key_len:4][key][val_len:4][value][crc32:4]
```

- type: PUT(1) 或 DELETE(2)
- CRC32 保证数据完整性

## 实现中的关键问题

### 1. CRC 计算的 append 陷阱

```go
// 错误: append 可能修改原始切片
data := append(entry.Key, entry.Value...)
data = append(data, deletedByte)

// 正确: 创建新的切片
data := make([]byte, 0, len(entry.Key)+len(entry.Value)+1)
data = append(data, entry.Key...)
data = append(data, entry.Value...)
data = append(data, deletedByte)
```

原因: Go 的 `append` 在切片有剩余容量时会复用底层数组，导致原始数据被修改。

### 2. SSTable 读取越界问题

```go
// 错误: bufio.Reader 会读取超过数据区域
reader := bufio.NewReader(s.file)

// 正确: 使用 SectionReader 限制读取范围
sectionReader := io.NewSectionReader(s.file, 0, int64(s.dataSize))
reader := bufio.NewReader(sectionReader)
```

原因: SSTable 文件包含索引和页脚，直接读取会读到非数据区域。

### 3. MemTable 大小控制

```go
// 检查是否需要 Flush
func (m *MemTable) ShouldFlush() bool {
    return m.Bytes() >= m.sizeLimit
}
```

## Compaction 策略

### 分层合并 (Leveled Compaction)

```
Level 0: SSTable_0, SSTable_1, SSTable_2 (可能重叠)
    ↓ 触发条件: 超过 4 个文件
Level 1: SSTable_0 (不重叠)
    ↓ 触发条件: 超过 10 个文件
Level 2: SSTable_0, SSTable_1 (不重叠)
    ...
```

合并过程:
1. 选择要合并的 SSTables
2. 找出重叠的下一层 SSTables
3. 归并排序所有 entries
4. 写入新的 SSTable
5. 删除旧文件

### Tombstone 处理

```go
// 删除操作写入墓碑标记
entry := &Entry{Key: key, Value: nil, Deleted: true}

// 在最高层合并时移除墓碑
if entry.Deleted && level >= maxLevel-1 {
    continue // 不写入新文件
}
```

## 测试策略

### 单元测试层次

1. **SkipList 测试**: 基础数据结构正确性
2. **MemTable 测试**: 内存表的 CRUD 操作
3. **WAL 测试**: 持久化和恢复
4. **SSTable 测试**: 磁盘存储和读取
5. **Compaction 测试**: 合并逻辑
6. **Engine 测试**: 端到端功能

### 关键测试场景

- 基本 CRUD 操作
- 大数据量压测
- 崩溃恢复 (WAL Replay)
- 持久化验证 (关闭后重新打开)
- 混合操作 (Put + Delete + Update)

## 性能考虑

### 写入性能

- MemTable 写入: O(log N)，纯内存
- WAL 写入: 顺序 IO，很快
- Flush 触发: 达到阈值时异步刷盘

### 读取性能

- 最好情况: MemTable 命中，O(log N)
- 最坏情况: 遍历所有 SSTable，O(N * log M)
- 优化: Bloom Filter (未实现)、稀疏索引

### 空间放大

- 无 Compaction: 空间无限增长
- 有 Compaction: 控制在 1.1x 左右
- 代价: 写放大 (多次写入同一 key)

## 进一步学习方向

1. **Bloom Filter**: 减少无效的 SSTable 查找
2. **Prefix Compression**: 压缩有序 key 的公共前缀
3. **Block Cache**: 缓存热点 SSTable block
4. **并发控制**: 读写并发安全
5. **Range Scan**: 支持范围查询的迭代器
