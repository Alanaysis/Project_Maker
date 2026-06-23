# 02 - 设计: LSM Tree 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     LSM Engine                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    写入路径                          ││
│  │   Put/Delete → WAL → MemTable → [Flush] → SSTable  ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │                    读取路径                          ││
│  │   Get → MemTable → SSTable L0 → L1 → ... → Result  ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │                    Compaction                        ││
│  │   Level 0 → Level 1 → Level 2 → ... → 删除旧文件   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## 组件设计

### 1. MemTable 设计

```
MemTable (内存)
├── SkipList (有序数据)
│   ├── Head Node
│   │   └── next[0..maxLevel]
│   ├── Node(key1, value1)
│   │   └── next[0..level]
│   ├── Node(key2, value2)
│   │   └── next[0..level]
│   └── ...
├── Size: 当前大小
└── Limit: 触发 Flush 的阈值
```

接口设计:
```go
type MemTable interface {
    Put(key, value []byte)      // 写入
    Get(key []byte) ([]byte, bool) // 读取
    Delete(key []byte) bool     // 删除 (墓碑)
    Entries() []*Entry          // 所有 entries (用于 Flush)
    ShouldFlush() bool          // 是否需要 Flush
}
```

### 2. SSTable 设计

```
SSTable 文件格式:
┌──────────────────────────────────────┐
│           Data Section               │
│  Entry 0: [key_len][key][val_len]   │
│           [value][deleted][crc32]    │
│  Entry 1: ...                        │
│  ...                                 │
│  Entry N: ...                        │
├──────────────────────────────────────┤
│           Index Section              │
│  Index 0: [key_len][key][offset]    │
│  Index 1: ...                        │
│  (每 16 个 key 一个索引)             │
├──────────────────────────────────────┤
│           Footer (32 bytes)          │
│  [index_offset: 8]                   │
│  [entry_count: 8]                    │
│  [index_count: 8]                    │
│  [level: 8]                          │
└──────────────────────────────────────┘
```

接口设计:
```go
type SSTable interface {
    Get(key []byte) ([]byte, bool, error) // 查找 key
    NewIterator() (*SSTableIterator, error) // 迭代器
    Close() error                           // 关闭文件
    FilePath() string                       // 文件路径
    EntryCount() uint64                     // entry 数量
    Level() int                             // 所在层级
}
```

### 3. WAL 设计

```
WAL 文件格式:
Record 1: [type:1][key_len:4][key][val_len:4][value][crc32:4]
Record 2: ...
Record N: ...
```

接口设计:
```go
type WAL interface {
    WritePut(key, value []byte) error    // 写入 PUT 记录
    WriteDelete(key []byte) error        // 写入 DELETE 记录
    Sync() error                         // 刷盘
    Close() error                        // 关闭
}

func WALReplay(filePath string, memTable *MemTable) error // 重放 WAL
```

### 4. Compaction 设计

```
Compaction 策略:
1. Level 0: 收集所有 SSTables (可能重叠)
2. Level 1+: 选择重叠的 SSTables
3. 归并排序所有 entries
4. 写入新的 SSTable (Level + 1)
5. 删除旧文件

触发条件:
- Level 0: 超过 4 个文件
- Level N: 超过 10^N 个文件
```

## 数据流设计

### 写入流程

```
1. Put(key, value)
   │
   ├─→ 2. WAL.WritePut(key, value)
   │       └─→ 写入磁盘
   │
   └─→ 3. MemTable.Put(key, value)
           │
           └─→ 4. if MemTable.ShouldFlush()
                   │
                   └─→ 5. flushMemTable()
                           │
                           ├─→ 6. Build SSTable from entries
                           │
                           └─→ 7. Reset MemTable + WAL
```

### 读取流程

```
1. Get(key)
   │
   ├─→ 2. MemTable.Get(key)
   │       ├─→ 命中: 返回 value
   │       └─→ 未命中: 继续
   │
   └─→ 3. for level in [0, maxLevel]:
           │
           └─→ 4. for table in SSTables[level] (newest first):
                   │
                   └─→ 5. SSTable.Get(key)
                           ├─→ 命中: 返回 value
                           └─→ 未命中: 继续
```

### Compaction 流程

```
1. compactLevel(level)
   │
   ├─→ 2. 选择 level 层的所有 SSTables
   │
   ├─→ 3. 找出 level+1 层重叠的 SSTables
   │
   ├─→ 4. 归并排序所有 entries
   │       └─→ 处理重复 key (last writer wins)
   │
   ├─→ 5. 过滤 tombstones (最高层)
   │
   └─→ 6. 写入新 SSTable (level+1)
           └─→ 删除旧文件
```

## 关键设计决策

### 1. 跳表 vs 红黑树

选择跳表:
- 实现简单 (约 150 行)
- 并发友好 (锁粒度细)
- 有序遍历自然

### 2. 稀疏索引密度

选择每 16 个 key:
- 索引大小: key_count / 16 * (avg_key_size + 8)
- 查找范围: 最多扫描 16 个 entries
- 平衡点: 索引小，查找快

### 3. MemTable 大小

默认 4KB (可配置):
- 太小: 频繁 Flush，写放大高
- 太大: 占用内存多，恢复慢
- 权衡: 根据写入量调整

### 4. Compaction 触发

Level 0: 4 个文件
- 太少: 频繁合并
- 太多: 读性能差
- 权衡: 根据读写比例调整

## 错误处理策略

| 场景 | 处理 |
|------|------|
| WAL 写入失败 | 返回错误，不写 MemTable |
| SSTable 构建失败 | 返回错误，保留 MemTable |
| CRC 校验失败 | 返回错误，记录日志 |
| Compaction 失败 | 返回错误，保留旧文件 |
| 文件不存在 | 返回 nil (key 不存在) |

## 并发安全

当前实现: 单线程，使用 sync.RWMutex

```go
type LSMEngine struct {
    mu sync.RWMutex
    // ...
}

func (e *LSMEngine) Put(key, value []byte) error {
    e.mu.Lock()
    defer e.mu.Unlock()
    // ...
}

func (e *LSMEngine) Get(key []byte) ([]byte, error) {
    e.mu.RLock()
    defer e.mu.RUnlock()
    // ...
}
```

未来优化: 无锁跳表、读写分离
