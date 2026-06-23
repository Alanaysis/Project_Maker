# 03 - 实现: LSM Tree 核心实现

## 实现顺序

1. SkipList → 2. MemTable → 3. WAL → 4. SSTable → 5. Compaction → 6. Engine

## 1. SkipList 实现

### 核心数据结构

```go
type SkipListNode struct {
    key     []byte
    value   []byte
    deleted bool
    next    []*SkipListNode  // 多级指针
}

type SkipList struct {
    head  *SkipListNode
    level int               // 当前最高层级
    size  int               // 节点数量
    bytes int               // 内存占用
}
```

### 插入操作

```go
func (s *SkipList) Insert(key, value []byte) {
    update := make([]*SkipListNode, maxLevel)
    current := s.head

    // 从高到低找插入位置
    for i := s.level; i >= 0; i-- {
        for current.next[i] != nil && bytes.Compare(current.next[i].key, key) < 0 {
            current = current.next[i]
        }
        update[i] = current
    }

    // 如果 key 存在，更新 value
    current = current.next[0]
    if current != nil && bytes.Equal(current.key, key) {
        current.value = value
        return
    }

    // 生成随机层级
    newLevel := randomLevel()
    if newLevel > s.level {
        for i := s.level + 1; i <= newLevel; i++ {
            update[i] = s.head
        }
        s.level = newLevel
    }

    // 创建新节点并插入
    newNode := &SkipListNode{key: key, value: value, next: make([]*SkipListNode, newLevel+1)}
    for i := 0; i <= newLevel; i++ {
        newNode.next[i] = update[i].next[i]
        update[i].next[i] = newNode
    }
}
```

### 查找操作

```go
func (s *SkipList) Get(key []byte) ([]byte, bool) {
    current := s.head

    // 从高到低查找
    for i := s.level; i >= 0; i-- {
        for current.next[i] != nil && bytes.Compare(current.next[i].key, key) < 0 {
            current = current.next[i]
        }
    }

    current = current.next[0]
    if current != nil && bytes.Equal(current.key, key) && !current.deleted {
        return current.value, true
    }
    return nil, false
}
```

## 2. SSTable 实现

### 写入流程

```go
func (b *SSTableBuilder) Build(filePath string, level int) (*SSTable, error) {
    // 1. 排序 entries
    sort.Slice(b.entries, func(i, j int) bool {
        return bytes.Compare(b.entries[i].Key, b.entries[j].Key) < 0
    })

    // 2. 写入数据区
    for i, entry := range b.entries {
        // 写入 [key_len][key][val_len][value][deleted][crc32]
        writeEntry(writer, entry)

        // 每 16 个 key 记录索引
        if i % indexInterval == 0 {
            indexEntries = append(indexEntries, &indexEntry{key: entry.Key, offset: dataOffset})
        }
    }

    // 3. 写入索引区
    for _, ie := range indexEntries {
        writeIndexEntry(writer, ie)
    }

    // 4. 写入页脚
    writeFooter(writer, indexBlockOffset, entryCount, indexCount, level)
}
```

### 读取流程

```go
func (s *SSTable) Get(key []byte) ([]byte, bool, error) {
    // 1. 用稀疏索引找起始位置
    startOffset := uint64(0)
    for i := len(s.index) - 1; i >= 0; i-- {
        if bytes.Compare(s.index[i].key, key) <= 0 {
            startOffset = s.index[i].offset
            break
        }
    }

    // 2. 从起始位置顺序扫描
    sectionReader := io.NewSectionReader(s.file, int64(startOffset), int64(s.dataSize-startOffset))
    reader := bufio.NewReader(sectionReader)

    for {
        rec, err := readSSTableEntry(reader)
        if err == io.EOF {
            break
        }
        if bytes.Equal(rec.Key, key) {
            return rec.Value, !rec.Deleted, nil
        }
        if bytes.Compare(rec.Key, key) > 0 {
            break // 已经过了目标 key
        }
    }
    return nil, false, nil
}
```

## 3. WAL 实现

### 写入记录

```go
func (w *WAL) writeRecord(rec WALRecord) error {
    // 1. 写入类型
    w.writer.WriteByte(byte(rec.Type))

    // 2. 写入 key
    binary.Write(w.writer, binary.LittleEndian, uint32(len(rec.Key)))
    w.writer.Write(rec.Key)

    // 3. 写入 value
    binary.Write(w.writer, binary.LittleEndian, uint32(len(rec.Value)))
    w.writer.Write(rec.Value)

    // 4. 计算并写入 CRC32
    data := make([]byte, 0, len(rec.Key)+len(rec.Value)+1)
    data = append(data, rec.Key...)
    data = append(data, rec.Value...)
    checksum := crc32.ChecksumIEEE(data)
    binary.Write(w.writer, binary.LittleEndian, checksum)

    return w.writer.Flush()
}
```

### 重放 WAL

```go
func WALReplay(filePath string, memTable *MemTable) error {
    f, _ := os.Open(filePath)
    reader := bufio.NewReader(f)

    for {
        rec, err := readRecord(reader)
        if err == io.EOF {
            break
        }

        switch rec.Type {
        case WALPut:
            memTable.Put(rec.Key, rec.Value)
        case WALDelete:
            memTable.Delete(rec.Key)
        }
    }
    return nil
}
```

## 4. Engine 实现

### 写入操作

```go
func (e *LSMEngine) Put(key, value []byte) error {
    e.mu.Lock()
    defer e.mu.Unlock()

    // 1. 写 WAL
    if err := e.wal.WritePut(key, value); err != nil {
        return err
    }

    // 2. 写 MemTable
    e.memTable.Put(key, value)

    // 3. 检查是否需要 Flush
    if e.memTable.ShouldFlush() {
        return e.flushMemTable()
    }
    return nil
}
```

### Flush 操作

```go
func (e *LSMEngine) flushMemTable() error {
    entries := e.memTable.Entries()

    // 1. 构建 SSTable
    builder := NewSSTableBuilder()
    for _, entry := range entries {
        builder.Add(entry.Key, entry.Value, entry.Deleted)
    }
    table, _ := builder.Build(filePath, 0)

    // 2. 添加到 L0
    e.sstables[0] = append(e.sstables[0], table)

    // 3. 重置 MemTable 和 WAL
    e.memTable = NewMemTable(e.memTable.sizeLimit)
    e.wal.Close()
    RemoveWAL(e.wal.Path())
    e.wal, _ = NewWAL(newWalPath)

    // 4. 检查是否需要 Compaction
    if len(e.sstables[0]) >= level0MaxTables {
        e.compactLevel(0)
    }
    return nil
}
```

## 关键技术点

### 1. CRC32 校验

```go
// 计算 CRC 时避免 append 陷阱
data := make([]byte, 0, len(key)+len(value)+1)
data = append(data, key...)
data = append(data, value...)
data = append(data, deletedByte)
checksum := crc32.ChecksumIEEE(data)
```

### 2. SectionReader 限制读取

```go
// 防止读取超过数据区域
sectionReader := io.NewSectionReader(s.file, 0, int64(s.dataSize))
reader := bufio.NewReader(sectionReader)
```

### 3. Tombstone 处理

```go
// 删除操作
entry := &Entry{Key: key, Value: nil, Deleted: true}

// 读取时检查
if entry.Deleted {
    return nil, nil // key 已删除
}

// 最高层 Compaction 时移除 tombstone
if entry.Deleted && level >= maxLevel-1 {
    continue
}
```

## 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| skiplist.go | ~210 | 跳表数据结构 |
| memtable.go | ~65 | MemTable 封装 |
| sstable.go | ~450 | SSTable 读写 |
| wal.go | ~200 | WAL 实现 |
| compaction.go | ~320 | Compaction 策略 |
| engine.go | ~420 | LSM 引擎 |
| **总计** | **~1665** | |
