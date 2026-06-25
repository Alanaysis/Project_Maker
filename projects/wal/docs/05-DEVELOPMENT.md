# 05-DEVELOPMENT.md - 开发指南

## 开发环境

### 系统要求

- Go 1.21+
- Git
- IDE（推荐 VS Code 或 GoLand）

### 环境配置

```bash
# 安装 Go
# macOS
brew install go

# Linux
sudo apt-get install golang-go

# 验证安装
go version

# 配置 GOPATH
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
```

## 项目结构

```
wal/
├── cmd/
│   └── wal-server/
│       └── main.go          # WAL 服务器入口
├── internal/
│   ├── wal/
│   │   ├── wal.go           # WAL 核心实现
│   │   ├── entry.go         # 日志记录定义
│   │   ├── recovery.go      # 崩溃恢复
│   │   ├── checkpoint.go    # 检查点管理
│   │   └── retention.go     # 日志清理和保留策略
│   └── storage/
│       └── storage.go       # 存储层实现
├── test/
│   ├── wal_test.go          # WAL 单元测试
│   ├── recovery_test.go     # 恢复测试
│   ├── checkpoint_test.go   # 检查点测试
│   └── retention_test.go    # 日志清理测试
└── examples/
    ├── usage.go             # 基础使用示例
    ├── event_sourcing.go    # 事件溯源示例
    └── audit_log.go         # 审计日志示例
```

## 开发流程

### 1. 功能开发

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发功能
# ...

# 运行测试
go test ./...

# 提交代码
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature
```

### 2. 代码规范

#### 命名规范

```go
// 包名：小写单词
package wal

// 接口名：-er 结尾
type Reader interface {
    Read() ([]byte, error)
}

// 结构体名：大写开头
type WALWriter struct {
    // ...
}

// 函数名：大写开头（导出）或小写开头（内部）
func NewWALWriter() *WALWriter {
    // ...
}

// 常量：全大写下划线分隔
const (
    MaxBufferSize = 1024
    DefaultSyncMode = SyncImmediate
)
```

#### 注释规范

```go
// WALWriter 负责将日志记录写入 WAL 文件。
// 它支持同步和异步写入模式，并提供批量写入功能。
type WALWriter struct {
    // file 是 WAL 文件的句柄
    file *os.File
    
    // currentLSN 是当前的 LSN 计数器
    currentLSN uint64
}

// Write 将单条日志记录写入 WAL 文件。
// 它会自动分配 LSN 并保证写入的原子性。
func (w *WALWriter) Write(entry *LogEntry) error {
    // ...
}
```

### 3. 错误处理

```go
// 定义错误类型
var (
    ErrWALNotInitialized = errors.New("WAL not initialized")
    ErrChecksumMismatch  = errors.New("checksum mismatch")
)

// 错误处理示例
func (w *WALWriter) Write(entry *LogEntry) error {
    if w.file == nil {
        return ErrWALNotInitialized
    }
    
    data, err := entry.Serialize()
    if err != nil {
        return fmt.Errorf("failed to serialize entry: %w", err)
    }
    
    // ...
}
```

### 4. 并发安全

```go
type WALWriter struct {
    mu   sync.Mutex
    file *os.File
}

func (w *WALWriter) Write(entry *LogEntry) error {
    w.mu.Lock()
    defer w.mu.Unlock()
    
    // 临界区代码
    // ...
}
```

## 调试技巧

### 1. 日志调试

```go
import "log"

func (w *WALWriter) Write(entry *LogEntry) error {
    log.Printf("Writing entry: LSN=%d, TxID=%d, Op=%v", 
        entry.LSN, entry.TxID, entry.OpType)
    
    // ...
    
    log.Printf("Entry written successfully")
    return nil
}
```

### 2. 使用 Delve 调试

```bash
# 安装 Delve
go install github.com/go-delve/delve/cmd/dlv@latest

# 调试测试
dlv test ./test/ -- -test.run TestWALWriter

# 调试程序
dlv debug cmd/wal-server/main.go
```

### 3. 性能分析

```go
import "runtime/pprof"

func main() {
    // CPU 分析
    f, _ := os.Create("cpu.prof")
    pprof.StartCPUProfile(f)
    defer pprof.StopCPUProfile()
    
    // 运行程序
    // ...
    
    // 内存分析
    f, _ = os.Create("mem.prof")
    pprof.WriteHeapProfile(f)
}
```

```bash
# 分析 CPU
go tool pprof cpu.prof

# 分析内存
go tool pprof mem.prof
```

## 测试策略

### 1. 单元测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/wal/

# 运行特定测试
go test -run TestWALWriter ./test/

# 详细输出
go test -v ./...
```

### 2. 集成测试

```bash
# 运行集成测试
go test -tags=integration ./...

# 运行端到端测试
go test -tags=e2e ./...
```

### 3. 测试覆盖率

```bash
# 生成覆盖率报告
go test -coverprofile=coverage.out ./...

# 查看覆盖率
go tool cover -html=coverage.out

# 查看总覆盖率
go test -cover ./...
```

## 构建和部署

### 1. 本地构建

```bash
# 构建
go build -o wal-server cmd/wal-server/main.go

# 运行
./wal-server
```

### 2. 交叉编译

```bash
# Linux
GOOS=linux GOARCH=amd64 go build -o wal-server-linux cmd/wal-server/main.go

# macOS
GOOS=darwin GOARCH=amd64 go build -o wal-server-mac cmd/wal-server/main.go

# Windows
GOOS=windows GOARCH=amd64 go build -o wal-server.exe cmd/wal-server/main.go
```

### 3. Docker 构建

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o wal-server cmd/wal-server/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/wal-server .
CMD ["./wal-server"]
```

```bash
# 构建镜像
docker build -t wal-server .

# 运行容器
docker run -p 8080:8080 wal-server
```

## 性能优化

### 1. 批量写入

```go
// 使用批量写入提高性能
func (w *WALWriter) WriteBatch(entries []*LogEntry) error {
    w.mu.Lock()
    defer w.mu.Unlock()
    
    // 批量序列化
    var batch []byte
    for _, entry := range entries {
        data, err := entry.Serialize()
        if err != nil {
            return err
        }
        batch = append(batch, data...)
    }
    
    // 一次性写入
    return w.writeBatch(batch)
}
```

### 2. 缓冲区池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 4096)
    },
}

func getBuffer() []byte {
    return bufferPool.Get().([]byte)
}

func putBuffer(buf []byte) {
    bufferPool.Put(buf)
}
```

### 3. 异步刷盘

```go
type WALWriter struct {
    syncMode SyncMode
    flushCh  chan struct{}
}

func (w *WALWriter) asyncFlush() {
    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            w.file.Sync()
        case <-w.flushCh:
            return
        }
    }
}
```

## 常见问题

### 1. 文件锁冲突

**问题**：多个进程同时访问 WAL 文件

**解决**：使用文件锁或单进程模式

```go
func lockFile(f *os.File) error {
    return syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB)
}
```

### 2. 磁盘空间不足

**问题**：日志文件过大导致磁盘空间不足

**解决**：定期创建检查点并清理旧日志

```go
func (cm *CheckpointManager) cleanOldLogs(checkpointLSN uint64) error {
    // 删除检查点之前的日志文件
    // ...
}
```

### 3. 性能瓶颈

**问题**：频繁的小写入导致性能下降

**解决**：使用批量写入和缓冲区

```go
// 批量写入
writer.WriteBatch(entries)

// 使用缓冲区
writer.SetBufferSize(4096)
```

## 最佳实践

1. **错误处理**：始终检查错误并妥善处理
2. **并发安全**：使用锁保护共享资源
3. **资源管理**：及时关闭文件和释放资源
4. **测试覆盖**：编写全面的单元测试和集成测试
5. **性能监控**：使用 pprof 进行性能分析
6. **日志记录**：添加适当的日志便于调试
7. **文档完善**：编写清晰的代码注释和文档
