# 05 - 开发: LSM Tree 开发记录

## 开发时间线

| 阶段 | 时间 | 内容 |
|------|------|------|
| 研究 | 2h | 调研 LSM Tree 原理和业界实现 |
| 设计 | 1h | 设计数据结构和接口 |
| 实现 | 4h | 编写核心代码 |
| 测试 | 2h | 编写测试用例并修复 bug |
| 文档 | 1h | 编写文档和学习笔记 |
| **总计** | **10h** | |

## 开发过程

### 阶段 1: SkipList 实现

**目标**: 实现 MemTable 的底层数据结构

**关键决策**:
- 选择跳表而非红黑树 (实现简单)
- 使用 `bytes.Compare` 进行 key 比较
- 支持 tombstone 标记 (deleted 字段)

**遇到的问题**:
- 无

**代码量**: ~210 行

### 阶段 2: SSTable 实现

**目标**: 实现磁盘存储格式

**关键决策**:
- 使用稀疏索引 (每 16 个 key)
- 支持 tombstone (deleted 字段 + CRC)
- 使用 `io.SectionReader` 限制读取范围

**遇到的问题**:

1. **CRC 计算的 append 陷阱**
   - 问题: `append(entry.Key, entry.Value...)` 可能修改原始切片
   - 原因: Go 的 `append` 在切片有剩余容量时会复用底层数组
   - 解决: 创建新的切片 `make([]byte, 0, len(key)+len(value)+1)`

2. **SSTable 读取越界**
   - 问题: `bufio.Reader` 会读取超过数据区域
   - 原因: SSTable 文件包含索引和页脚
   - 解决: 使用 `io.NewSectionReader` 限制读取范围

**代码量**: ~450 行

### 阶段 3: WAL 实现

**目标**: 实现预写日志保证持久性

**关键决策**:
- 使用 CRC32 校验数据完整性
- 支持 PUT 和 DELETE 两种操作
- 支持 WAL 重放恢复 MemTable

**遇到的问题**:
- 无

**代码量**: ~200 行

### 阶段 4: Compaction 实现

**目标**: 实现分层合并策略

**关键决策**:
- 使用 Leveled Compaction
- Level 0 支持重叠，Level 1+ 不重叠
- 最高层移除 tombstone

**遇到的问题**:
- 读取 SSTable 时的越界问题 (同 SSTable)

**代码量**: ~320 行

### 阶段 5: Engine 实现

**目标**: 组装所有组件，实现完整的 LSM 引擎

**关键决策**:
- 使用 `sync.RWMutex` 保证并发安全
- 写入时先写 WAL，再写 MemTable
- Flush 后检查是否需要 Compaction

**遇到的问题**:
- 无

**代码量**: ~420 行

## Bug 修复记录

### Bug 1: CRC 校验失败

**现象**: SSTable.Get 在查找不存在的 key 时返回 CRC 错误

**原因**: `readSSTableEntry` 读取超过数据区域，进入索引/页脚区域

**修复**: 使用 `io.SectionReader` 限制读取范围

```go
// 修复前
reader := bufio.NewReader(s.file)

// 修复后
sectionReader := io.NewSectionReader(s.file, 0, int64(s.dataSize))
reader := bufio.NewReader(sectionReader)
```

### Bug 2: append 修改原始数据

**现象**: CRC 校验偶尔失败

**原因**: `append(entry.Key, entry.Value...)` 在切片有剩余容量时会修改原始数据

**修复**: 创建新的切片

```go
// 修复前
data := append(entry.Key, entry.Value...)

// 修复后
data := make([]byte, 0, len(entry.Key)+len(entry.Value)+1)
data = append(data, entry.Key...)
data = append(data, entry.Value...)
```

## 代码质量

### 测试覆盖率

```
总体: 59.9%

SkipList:     100% (核心操作)
MemTable:     100% (核心操作)
SSTable:      55-95% (不同函数)
WAL:          57-100% (不同函数)
Compaction:   0-92% (不同函数)
Engine:       67-100% (不同函数)
```

### 代码风格

- 遵循 Go 标准代码风格
- 使用 `gofmt` 格式化
- 有意义的变量名和函数名
- 充分的注释

### 错误处理

- 所有错误都正确返回
- 使用 `fmt.Errorf` 包装错误
- 关键操作有日志记录

## 学到的经验

### 1. Go 的 append 陷阱

```go
// 危险: 可能修改原始切片
result := append(slice1, slice2...)

// 安全: 创建新的切片
result := make([]byte, 0, len(slice1)+len(slice2))
result = append(result, slice1...)
result = append(result, slice2...)
```

### 2. bufio.Reader 的状态管理

```go
// 问题: bufio.Reader 有内部缓冲区，Seek 后需要重新创建
f.Seek(newOffset, io.SeekStart)
reader.Reset(f) // 不够，旧缓冲区还在

// 解决: 使用 SectionReader
sectionReader := io.NewSectionReader(f, offset, size)
reader := bufio.NewReader(sectionReader)
```

### 3. 测试驱动开发

- 先写测试，再写实现
- 测试边界条件 (空表、大数据量)
- 测试错误路径 (CRC 错误、文件不存在)

## 未来改进

1. **Bloom Filter**: 减少无效的 SSTable 查找
2. **Block Cache**: 缓存热点 SSTable block
3. **并发安全**: 无锁跳表、读写分离
4. **Range Scan**: 支持范围查询
5. **Prefix Compression**: 压缩有序 key
6. **配置化**: 支持运行时调整参数

## 总结

LSM Tree 是一个很好的学习项目，涵盖了:
- 数据结构 (跳表)
- 文件格式设计 (SSTable)
- 持久化机制 (WAL)
- 后台任务 (Compaction)
- 错误处理 (CRC 校验)

通过实现这个项目，深入理解了现代存储引擎的核心原理。
