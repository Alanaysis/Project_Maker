# 03-IMPLEMENTATION.md - 实现细节

## 实现阶段

### 阶段 1：基础框架
1. 创建项目结构
2. 定义数据模型
3. 实现基本的文件 I/O

### 阶段 2：日志写入
1. 实现日志记录序列化
2. 实现日志文件写入
3. 添加校验和验证

### 阶段 3：日志读取
1. 实现日志记录反序列化
2. 实现顺序读取
3. 实现随机读取（按 LSN）

### 阶段 4：事务管理
1. 实现事务开始/提交/回滚
2. 实现事务状态跟踪
3. 实现并发控制

### 阶段 5：检查点机制
1. 实现检查点创建
2. 实现脏页跟踪
3. 实现日志清理

### 阶段 6：崩溃恢复
1. 实现检查点加载
2. 实现日志重放
3. 实现未完成事务回滚

## 核心实现

### 1. 日志记录序列化

```go
func (e *LogEntry) Serialize() ([]byte, error) {
    buf := new(bytes.Buffer)
    
    // 写入 LSN
    if err := binary.Write(buf, binary.LittleEndian, e.LSN); err != nil {
        return nil, err
    }
    
    // 写入事务 ID
    if err := binary.Write(buf, binary.LittleEndian, e.TxID); err != nil {
        return nil, err
    }
    
    // 写入操作类型
    if err := binary.Write(buf, binary.LittleEndian, uint8(e.OpType)); err != nil {
        return nil, err
    }
    
    // 写入键长度和键
    keyBytes := []byte(e.Key)
    if err := binary.Write(buf, binary.LittleEndian, uint32(len(keyBytes))); err != nil {
        return nil, err
    }
    if _, err := buf.Write(keyBytes); err != nil {
        return nil, err
    }
    
    // 写入值长度和值
    if err := binary.Write(buf, binary.LittleEndian, uint32(len(e.Value))); err != nil {
        return nil, err
    }
    if _, err := buf.Write(e.Value); err != nil {
        return nil, err
    }
    
    // 写入时间戳
    if err := binary.Write(buf, binary.LittleEndian, e.Timestamp); err != nil {
        return nil, err
    }
    
    // 计算并写入校验和
    data := buf.Bytes()
    checksum := crc32.ChecksumIEEE(data)
    if err := binary.Write(buf, binary.LittleEndian, checksum); err != nil {
        return nil, err
    }
    
    return buf.Bytes(), nil
}
```

### 2. 日志记录反序列化

```go
func DeserializeLogEntry(data []byte) (*LogEntry, error) {
    if len(data) < 4 {
        return nil, ErrCorruptedLog
    }
    
    buf := bytes.NewReader(data)
    entry := &LogEntry{}
    
    // 读取 LSN
    if err := binary.Read(buf, binary.LittleEndian, &entry.LSN); err != nil {
        return nil, err
    }
    
    // 读取事务 ID
    if err := binary.Read(buf, binary.LittleEndian, &entry.TxID); err != nil {
        return nil, err
    }
    
    // 读取操作类型
    var opType uint8
    if err := binary.Read(buf, binary.LittleEndian, &opType); err != nil {
        return nil, err
    }
    entry.OpType = OperationType(opType)
    
    // 读取键
    var keyLen uint32
    if err := binary.Read(buf, binary.LittleEndian, &keyLen); err != nil {
        return nil, err
    }
    key := make([]byte, keyLen)
    if _, err := buf.Read(key); err != nil {
        return nil, err
    }
    entry.Key = string(key)
    
    // 读取值
    var valueLen uint32
    if err := binary.Read(buf, binary.LittleEndian, &valueLen); err != nil {
        return nil, err
    }
    value := make([]byte, valueLen)
    if _, err := buf.Read(value); err != nil {
        return nil, err
    }
    entry.Value = value
    
    // 读取时间戳
    if err := binary.Read(buf, binary.LittleEndian, &entry.Timestamp); err != nil {
        return nil, err
    }
    
    // 读取并验证校验和
    var checksum uint32
    if err := binary.Read(buf, binary.LittleEndian, &checksum); err != nil {
        return nil, err
    }
    
    // 计算校验和
    dataWithoutChecksum := data[:len(data)-4]
    expectedChecksum := crc32.ChecksumIEEE(dataWithoutChecksum)
    if checksum != expectedChecksum {
        return nil, ErrChecksumMismatch
    }
    
    return entry, nil
}
```

### 3. WAL 写入实现

```go
type WALWriter struct {
    mu          sync.Mutex
    file        *os.File
    currentLSN  uint64
    buffer      []byte
    bufferSize  int
    syncMode    SyncMode
}

func (w *WALWriter) Write(entry *LogEntry) error {
    w.mu.Lock()
    defer w.mu.Unlock()
    
    // 分配 LSN
    w.currentLSN++
    entry.LSN = w.currentLSN
    
    // 序列化
    data, err := entry.Serialize()
    if err != nil {
        return err
    }
    
    // 写入长度前缀
    lengthBytes := make([]byte, 4)
    binary.LittleEndian.PutUint32(lengthBytes, uint32(len(data)))
    
    // 写入文件
    if _, err := w.file.Write(lengthBytes); err != nil {
        return err
    }
    if _, err := w.file.Write(data); err != nil {
        return err
    }
    
    // 刷盘
    if w.syncMode == SyncImmediate {
        if err := w.file.Sync(); err != nil {
            return err
        }
    }
    
    return nil
}
```

### 4. WAL 读取实现

```go
type WALReader struct {
    file   *os.File
    offset int64
}

func (r *WALReader) ReadNext() (*LogEntry, error) {
    // 读取长度
    lengthBytes := make([]byte, 4)
    if _, err := r.file.ReadAt(lengthBytes, r.offset); err != nil {
        return nil, err
    }
    
    length := binary.LittleEndian.Uint32(lengthBytes)
    r.offset += 4
    
    // 读取数据
    data := make([]byte, length)
    if _, err := r.file.ReadAt(data, r.offset); err != nil {
        return nil, err
    }
    r.offset += int64(length)
    
    // 反序列化
    return DeserializeLogEntry(data)
}

func (r *WALReader) ReadAll() ([]*LogEntry, error) {
    var entries []*LogEntry
    
    for {
        entry, err := r.ReadNext()
        if err == io.EOF {
            break
        }
        if err != nil {
            return entries, err
        }
        entries = append(entries, entry)
    }
    
    return entries, nil
}
```

### 5. 崩溃恢复实现

```go
type RecoveryManager struct {
    walPath     string
    storage     Storage
    lastCheckpoint *Checkpoint
}

func (rm *RecoveryManager) Recover() error {
    // 1. 加载最后一个检查点
    checkpoint, err := rm.loadLastCheckpoint()
    if err != nil {
        return err
    }
    rm.lastCheckpoint = checkpoint
    
    // 2. 从检查点位置开始读取日志
    reader, err := NewWALReader(rm.walPath)
    if err != nil {
        return err
    }
    
    // 3. 跳转到检查点位置
    if checkpoint != nil {
        reader.SeekToLSN(checkpoint.LSN)
    }
    
    // 4. 读取所有日志记录
    entries, err := reader.ReadAll()
    if err != nil {
        return err
    }
    
    // 5. 分类处理
    committedTxns := make(map[uint64]bool)
    for _, entry := range entries {
        if entry.OpType == OpCheckpoint {
            continue
        }
        
        if entry.OpType == OpCommit {
            committedTxns[entry.TxID] = true
            continue
        }
        
        // 只重放已提交事务的操作
        if committedTxns[entry.TxID] {
            if err := rm.applyEntry(entry); err != nil {
                return err
            }
        }
    }
    
    return nil
}

func (rm *RecoveryManager) applyEntry(entry *LogEntry) error {
    switch entry.OpType {
    case OpPut:
        return rm.storage.Put(entry.Key, entry.Value)
    case OpDelete:
        return rm.storage.Delete(entry.Key)
    default:
        return nil
    }
}
```

### 6. 检查点实现

```go
type CheckpointManager struct {
    walPath     string
    storage     Storage
    interval    time.Duration
    dirtyPages  map[uint64]bool
}

func (cm *CheckpointManager) CreateCheckpoint() error {
    cm.mu.Lock()
    defer cm.mu.Unlock()
    
    // 1. 暂停新的写入
    cm.walWriter.PauseWrites()
    defer cm.walWriter.ResumeWrites()
    
    // 2. 刷盘所有脏页
    if err := cm.flushDirtyPages(); err != nil {
        return err
    }
    
    // 3. 创建检查点记录
    checkpoint := &Checkpoint{
        LSN:       cm.walWriter.CurrentLSN(),
        Timestamp: time.Now().UnixNano(),
    }
    
    // 4. 写入检查点日志
    if err := cm.writeCheckpointLog(checkpoint); err != nil {
        return err
    }
    
    // 5. 清理旧日志
    if err := cm.cleanOldLogs(checkpoint.LSN); err != nil {
        return err
    }
    
    return nil
}
```

## 关键技术实现

### 1. 校验和计算

使用 CRC32 算法：

```go
func calculateChecksum(data []byte) uint32 {
    return crc32.ChecksumIEEE(data)
}
```

### 2. 文件锁

使用文件锁保证并发安全：

```go
func lockFile(f *os.File) error {
    return syscall.Flock(int(f.Fd()), syscall.LOCK_EX)
}

func unlockFile(f *os.File) error {
    return syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
}
```

### 3. 内存映射

使用 mmap 加速读取：

```go
func mmapFile(f *os.File) ([]byte, error) {
    stat, err := f.Stat()
    if err != nil {
        return nil, err
    }
    
    return syscall.Mmap(
        int(f.Fd()),
        0,
        int(stat.Size()),
        syscall.PROT_READ,
        syscall.MAP_SHARED,
    )
}
```

## 性能优化

### 1. 批量写入

```go
func (w *WALWriter) WriteBatch(entries []*LogEntry) error {
    w.mu.Lock()
    defer w.mu.Unlock()
    
    // 批量序列化
    var batch []byte
    for _, entry := range entries {
        w.currentLSN++
        entry.LSN = w.currentLSN
        
        data, err := entry.Serialize()
        if err != nil {
            return err
        }
        
        lengthBytes := make([]byte, 4)
        binary.LittleEndian.PutUint32(lengthBytes, uint32(len(data)))
        
        batch = append(batch, lengthBytes...)
        batch = append(batch, data...)
    }
    
    // 一次性写入
    if _, err := w.file.Write(batch); err != nil {
        return err
    }
    
    // 一次性刷盘
    if w.syncMode == SyncImmediate {
        return w.file.Sync()
    }
    
    return nil
}
```

### 2. 缓冲区管理

```go
type BufferPool struct {
    pool sync.Pool
}

func NewBufferPool() *BufferPool {
    return &BufferPool{
        pool: sync.Pool{
            New: func() interface{} {
                return make([]byte, 4096)
            },
        },
    }
}

func (p *BufferPool) Get() []byte {
    return p.pool.Get().([]byte)
}

func (p *BufferPool) Put(buf []byte) {
    p.pool.Put(buf)
}
```

## 文件管理

### 日志文件命名

```
wal.000001.log
wal.000002.log
wal.000003.log
...
```

### 文件轮转

当日志文件达到阈值（如 64MB）时创建新文件：

```go
func (w *WALWriter) rotateIfNeeded() error {
    stat, err := w.file.Stat()
    if err != nil {
        return err
    }
    
    if stat.Size() > w.maxFileSize {
        return w.rotate()
    }
    
    return nil
}
```
