# 分布式 MapReduce - 开发文档

## 1. 开发环境

### 1.1 环境要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Go | 1.21+ | 编程语言 |
| Git | 2.30+ | 版本控制 |
| Make | 3.81+ | 构建工具 |
| Docker | 24.0+ | 容器化 (可选) |

### 1.2 环境配置

```bash
# 安装 Go
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz

# 配置环境变量
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
source ~/.bashrc

# 验证安装
go version
```

### 1.3 项目初始化

```bash
# 克隆项目
git clone <repository-url>
cd mapreduce

# 初始化 Go 模块
go mod init mapreduce
go mod tidy

# 编译项目
make build
```

---

## 2. 项目结构

```
mapreduce/
├── cmd/                          # 可执行文件入口
│   ├── coordinator/             # Coordinator 主程序
│   │   └── main.go
│   └── worker/                  # Worker 主程序
│       └── main.go
├── internal/                    # 内部实现 (不对外暴露)
│   ├── coordinator/             # Coordinator 核心逻辑
│   │   ├── coordinator.go       # Coordinator 结构体和方法
│   │   ├── scheduler.go         # 任务调度器
│   │   └── fault_detector.go    # 故障检测器
│   ├── worker/                  # Worker 核心逻辑
│   │   ├── worker.go            # Worker 结构体和方法
│   │   ├── map_task.go          # Map 任务执行
│   │   └── reduce_task.go       # Reduce 任务执行
│   ├── mapreduce/               # MapReduce 框架
│   │   ├── types.go             # 公共类型定义
│   │   ├── mapreduce.go         # MapReduce 接口
│   │   └── partitioner.go       # 分区器
│   └── rpc/                     # RPC 定义
│       └── rpc.go               # RPC 消息类型
├── pkg/                         # 公共包 (可对外暴露)
│   └── applications/            # 应用示例
│       ├── wordcount.go         # 词频统计
│       ├── inverted_index.go    # 倒排索引
│       └── log_analysis.go      # 日志分析
├── docs/                        # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── testdata/                    # 测试数据
│   ├── pg-*.txt                 # 文本文件
│   └── expected/                # 期望输出
├── scripts/                     # 脚本
│   ├── build.sh                 # 编译脚本
│   ├── test.sh                  # 测试脚本
│   └── run.sh                   # 运行脚本
├── Makefile                     # 构建配置
├── go.mod                       # Go 模块定义
├── go.sum                       # 依赖校验
└── README.md                    # 项目说明
```

---

## 3. 代码规范

### 3.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 小写单词 | `coordinator`, `worker` |
| 结构体 | PascalCase | `Coordinator`, `TaskInfo` |
| 接口 | PascalCase + er | `Mapper`, `Reducer` |
| 函数 | PascalCase (导出) / camelCase (内部) | `RequestTask`, `assignTask` |
| 常量 | PascalCase | `TaskTimeout`, `MaxRetries` |
| 变量 | camelCase | `taskID`, `workerAddr` |

### 3.2 注释规范

```go
// Coordinator 管理 MapReduce 任务的生命周期。
// 它负责任务分配、状态跟踪和故障处理。
type Coordinator struct {
    mu       sync.Mutex
    files    []string
    nReduce  int
    phase    Phase
    tasks    map[int]*TaskInfo
}

// RequestTask 处理 Worker 的任务请求。
// 根据当前阶段返回 Map 或 Reduce 任务。
func (c *Coordinator) RequestTask(args *RequestTaskArgs, reply *RequestTaskReply) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    // ...
}
```

### 3.3 错误处理

```go
// 好的错误处理
func (w *Worker) doMap(task *RequestTaskReply) error {
    content, err := os.ReadFile(task.Filename)
    if err != nil {
        return fmt.Errorf("read file %s: %w", task.Filename, err)
    }
    // ...
}

// 不好的错误处理
func (w *Worker) doMap(task *RequestTaskReply) error {
    content, _ := os.ReadFile(task.Filename)  // 忽略错误
    // ...
}
```

### 3.4 并发安全

```go
// 使用互斥锁保护共享状态
type Coordinator struct {
    mu    sync.Mutex
    tasks map[int]*TaskInfo
}

func (c *Coordinator) getTask(id int) *TaskInfo {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.tasks[id]
}

// 使用 channel 进行 goroutine 通信
func (c *Coordinator) startTaskQueue() {
    c.taskQueue = make(chan int, 100)
    go func() {
        for taskID := range c.taskQueue {
            c.processTask(taskID)
        }
    }()
}
```

---

## 4. 核心实现

### 4.1 Coordinator 实现

```go
// internal/coordinator/coordinator.go

package coordinator

import (
    "sync"
    "time"
)

// Phase 表示 MapReduce 的执行阶段
type Phase int

const (
    MapPhase    Phase = iota
    ReducePhase
    AllDone
)

// TaskStatus 表示任务状态
type TaskStatus int

const (
    TaskIdle     TaskStatus = iota
    TaskInProgress
    TaskCompleted
    TaskFailed
)

// TaskInfo 存储任务信息
type TaskInfo struct {
    ID         int
    Status     TaskStatus
    WorkerID   string
    StartTime  time.Time
    RetryCount int
    Filename   string
}

// Coordinator 管理 MapReduce 任务
type Coordinator struct {
    mu        sync.Mutex
    files     []string
    nReduce   int
    phase     Phase
    tasks     map[int]*TaskInfo
    taskQueue chan int
    done      chan struct{}
}

// New 创建新的 Coordinator
func New(files []string, nReduce int) *Coordinator {
    c := &Coordinator{
        files:     files,
        nReduce:   nReduce,
        phase:     MapPhase,
        tasks:     make(map[int]*TaskInfo),
        taskQueue: make(chan int, len(files)),
        done:      make(chan struct{}),
    }
    
    // 初始化 Map 任务
    for i, file := range files {
        c.tasks[i] = &TaskInfo{
            ID:       i,
            Status:   TaskIdle,
            Filename: file,
        }
        c.taskQueue <- i
    }
    
    // 启动超时检测
    go c.timeoutChecker()
    
    return c
}
```

### 4.2 Worker 实现

```go
// internal/worker/worker.go

package worker

import (
    "net/rpc"
    "os"
    "fmt"
)

// MapFunc Map 函数类型
type MapFunc func(filename string, contents string) []KeyValue

// ReduceFunc Reduce 函数类型
type ReduceFunc func(key string, values []string) string

// Worker 执行 MapReduce 任务
type Worker struct {
    id         string
    coordinator *rpc.Client
    mapFunc    MapFunc
    reduceFunc ReduceFunc
}

// New 创建新的 Worker
func New(coordinatorAddr string, mapFunc MapFunc, reduceFunc ReduceFunc) (*Worker, error) {
    client, err := rpc.Dial("tcp", coordinatorAddr)
    if err != nil {
        return nil, fmt.Errorf("dial coordinator: %w", err)
    }
    
    return &Worker{
        id:         generateWorkerID(),
        coordinator: client,
        mapFunc:    mapFunc,
        reduceFunc: reduceFunc,
    }, nil
}

// Run 启动 Worker 主循环
func (w *Worker) Run() {
    for {
        // 请求任务
        reply, err := w.requestTask()
        if err != nil {
            time.Sleep(time.Second)
            continue
        }
        
        switch reply.TaskType {
        case MapTask:
            w.doMap(reply)
        case ReduceTask:
            w.doReduce(reply)
        case WaitTask:
            time.Sleep(time.Second)
            continue
        case ExitTask:
            return
        }
        
        // 报告完成
        w.reportTask(reply.TaskID, reply.TaskType, true)
    }
}
```

### 4.3 Map 任务执行

```go
// internal/worker/map_task.go

package worker

import (
    "encoding/json"
    "fmt"
    "os"
    "sort"
)

// KeyValue 键值对
type KeyValue struct {
    Key   string
    Value string
}

// doMap 执行 Map 任务
func (w *Worker) doMap(task *RequestTaskReply) error {
    // 1. 读取输入文件
    content, err := os.ReadFile(task.Filename)
    if err != nil {
        return fmt.Errorf("read file: %w", err)
    }
    
    // 2. 执行 Map 函数
    kvs := w.mapFunc(task.Filename, string(content))
    
    // 3. 按 hash 分区
    buckets := make([][]KeyValue, task.NReduce)
    for _, kv := range kvs {
        bucket := ihash(kv.Key) % task.NReduce
        buckets[bucket] = append(buckets[bucket], kv)
    }
    
    // 4. 写入中间文件
    for i, bucket := range buckets {
        if len(bucket) == 0 {
            continue
        }
        
        // 排序
        sort.Slice(bucket, func(i, j int) bool {
            return bucket[i].Key < bucket[j].Key
        })
        
        // 写入临时文件
        tmpFile := fmt.Sprintf("tmp/mr-%d-%d.tmp", task.TaskID, i)
        finalFile := fmt.Sprintf("tmp/mr-%d-%d", task.TaskID, i)
        
        if err := writeKeyValueFile(tmpFile, bucket); err != nil {
            return err
        }
        
        // 原子重命名
        if err := os.Rename(tmpFile, finalFile); err != nil {
            return err
        }
    }
    
    return nil
}

// ihash 计算 key 的 hash 值
func ihash(key string) int {
    h := fnv.New32a()
    h.Write([]byte(key))
    return int(h.Sum32() & 0x7fffffff)
}
```

### 4.4 Reduce 任务执行

```go
// internal/worker/reduce_task.go

package worker

import (
    "fmt"
    "os"
    "sort"
    "strconv"
)

// doReduce 执行 Reduce 任务
func (w *Worker) doReduce(task *RequestTaskReply) error {
    // 1. 读取所有中间文件
    var allKVs []KeyValue
    for i := 0; i < task.NMap; i++ {
        filename := fmt.Sprintf("tmp/mr-%d-%d", i, task.TaskID)
        kvs, err := readKeyValueFile(filename)
        if err != nil {
            if os.IsNotExist(err) {
                continue
            }
            return err
        }
        allKVs = append(allKVs, kvs...)
    }
    
    // 2. 按 key 排序
    sort.Slice(allKVs, func(i, j int) bool {
        return allKVs[i].Key < allKVs[j].Key
    })
    
    // 3. 分组并执行 Reduce
    outputFile := fmt.Sprintf("tmp/mr-out-%d.tmp", task.TaskID)
    finalFile := fmt.Sprintf("mr-out-%d", task.TaskID)
    
    f, err := os.Create(outputFile)
    if err != nil {
        return err
    }
    defer f.Close()
    
    i := 0
    for i < len(allKVs) {
        j := i + 1
        for j < len(allKVs) && allKVs[j].Key == allKVs[i].Key {
            j++
        }
        
        // 收集 values
        values := []string{}
        for k := i; k < j; k++ {
            values = append(values, allKVs[k].Value)
        }
        
        // 执行 Reduce
        output := w.reduceFunc(allKVs[i].Key, values)
        
        // 写入结果
        fmt.Fprintf(f, "%v %v\n", allKVs[i].Key, output)
        
        i = j
    }
    
    // 4. 原子重命名
    return os.Rename(outputFile, finalFile)
}
```

---

## 5. 测试指南

### 5.1 单元测试

```bash
# 运行所有单元测试
go test ./...

# 运行特定包的测试
go test ./internal/coordinator/
go test ./internal/worker/

# 运行带 race 检测的测试
go test -race ./...

# 查看测试覆盖率
go test -cover ./...
```

### 5.2 集成测试

```bash
# 运行集成测试
go test -tags=integration ./test/

# 运行完整的 MapReduce 流程测试
go test -run TestMapReduceFlow ./test/
```

### 5.3 性能测试

```bash
# 运行基准测试
go test -bench=. ./...

# 生成 CPU profile
go test -bench=. -cpuprofile=cpu.prof ./internal/worker/

# 分析 profile
go tool pprof cpu.prof
```

### 5.4 测试用例示例

```go
// internal/coordinator/coordinator_test.go

package coordinator

import (
    "testing"
    "time"
)

func TestCoordinatorRequestTask(t *testing.T) {
    files := []string{"file1.txt", "file2.txt", "file3.txt"}
    c := New(files, 2)
    
    // 请求 Map 任务
    args := &RequestTaskArgs{WorkerID: "worker-1"}
    reply := &RequestTaskReply{}
    
    err := c.RequestTask(args, reply)
    if err != nil {
        t.Fatalf("RequestTask failed: %v", err)
    }
    
    if reply.TaskType != MapTask {
        t.Errorf("expected MapTask, got %v", reply.TaskType)
    }
    
    if reply.Filename == "" {
        t.Error("expected filename, got empty")
    }
}

func TestCoordinatorReportTask(t *testing.T) {
    files := []string{"file1.txt"}
    c := New(files, 1)
    
    // 请求任务
    args := &RequestTaskArgs{WorkerID: "worker-1"}
    reply := &RequestTaskReply{}
    c.RequestTask(args, reply)
    
    // 报告完成
    reportArgs := &ReportTaskArgs{
        WorkerID: "worker-1",
        TaskID:   reply.TaskID,
        TaskType: MapTask,
        Success:  true,
    }
    reportReply := &ReportTaskReply{}
    
    err := c.ReportTask(reportArgs, reportReply)
    if err != nil {
        t.Fatalf("ReportTask failed: %v", err)
    }
    
    if !reportReply.OK {
        t.Error("expected OK=true")
    }
}
```

---

## 6. 构建与部署

### 6.1 Makefile

```makefile
.PHONY: build test clean run

# 编译
build:
	go build -o bin/coordinator ./cmd/coordinator
	go build -o bin/worker ./cmd/worker

# 测试
test:
	go test -race ./...

# 清理
clean:
	rm -rf bin/ tmp/ mr-out-*

# 运行
run: build
	./bin/coordinator testdata/pg-*.txt &
	sleep 1
	./bin/worker pkg/applications/wc.so

# Docker 构建
docker:
	docker build -t mapreduce .
```

### 6.2 Docker 支持

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o /coordinator ./cmd/coordinator
RUN CGO_ENABLED=0 go build -o /worker ./cmd/worker

FROM alpine:3.18

RUN apk --no-cache add ca-certificates
COPY --from=builder /coordinator /usr/local/bin/
COPY --from=builder /worker /usr/local/bin/

ENTRYPOINT ["coordinator"]
```

### 6.3 部署脚本

```bash
#!/bin/bash
# scripts/run.sh

# 启动 Coordinator
echo "Starting Coordinator..."
./bin/coordinator -port 8888 testdata/pg-*.txt &
COORDINATOR_PID=$!

# 等待 Coordinator 就绪
sleep 2

# 启动 Workers
echo "Starting Workers..."
for i in {1..4}; do
    ./bin/worker -coordinator localhost:8888 pkg/applications/wc.so &
done

# 等待完成
wait $COORDINATOR_PID
echo "MapReduce completed!"
```

---

## 7. 调试指南

### 7.1 日志配置

```go
// 使用 structured logging
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelDebug,
}))

logger.Info("task started",
    "task_id", taskID,
    "worker_id", workerID,
    "type", "map",
)
```

### 7.2 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Worker 连接失败 | Coordinator 未启动 | 先启动 Coordinator |
| 任务卡住 | Worker 崩溃 | 检查 Worker 进程 |
| 结果不正确 | Map/Reduce 函数错误 | 添加调试日志 |
| 内存溢出 | 数据量过大 | 增加分片数 |

### 7.3 调试技巧

```bash
# 启用 race 检测
go run -race cmd/coordinator/main.go

# 查看 goroutine 泄漏
go run cmd/worker/main.go 2>&1 | grep "goroutine"

# 使用 delve 调试
dlv debug cmd/coordinator/main.go -- testdata/pg-*.txt
```

---

## 8. 贡献指南

### 8.1 开发流程

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/my-feature`
3. 提交更改: `git commit -m "feat: add my feature"`
4. 推送分支: `git push origin feature/my-feature`
5. 创建 Pull Request

### 8.2 Commit 规范

```
<type>(<scope>): <subject>

类型:
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建/工具

示例:
feat(coordinator): add task retry mechanism
fix(worker): handle empty file gracefully
docs(readme): update usage examples
```

### 8.3 代码审查

- [ ] 代码通过 `go vet` 检查
- [ ] 测试通过 `go test -race`
- [ ] 新功能有测试覆盖
- [ ] 文档已更新

---

## 9. 版本历史

### v1.0.0 (2024-01-15)

- 初始发布
- 实现基本 MapReduce 框架
- 支持 WordCount、InvertedIndex、LogAnalysis 示例
- 实现 Worker 故障检测和任务重试
