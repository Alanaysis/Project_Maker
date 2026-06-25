# 分布式 MapReduce - 系统设计

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户应用层                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  WordCount  │  │ InvertedIdx │  │ LogAnalysis │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MapReduce 框架层                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Map Engine  │  │Shuffle Sort│  │Reduce Engine│                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        调度与管理层                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Coordinator                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│  │
│  │  │TaskQueue │  │Scheduler │  │FaultDetec│  │ StateMgr ││  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker N │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         存储层                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Input Files │  │Temp Files  │  │Output Files │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 组件 | 职责 | 通信方式 |
|------|------|----------|
| Coordinator | 任务调度、状态管理、故障检测 | RPC Server |
| Worker | 执行 Map/Reduce 任务 | RPC Client |
| Map Engine | 执行 Map 函数、输出中间文件 | 本地调用 |
| Reduce Engine | 执行 Reduce 函数、输出最终结果 | 本地调用 |

---

## 2. 核心模块设计

### 2.1 Coordinator 模块

#### 2.1.1 数据结构

```go
type Coordinator struct {
    mu           sync.Mutex        // 互斥锁
    files        []string          // 输入文件列表
    nReduce      int               // Reduce 任务数
    phase        Phase             // 当前阶段
    tasks        map[int]*TaskInfo // 任务信息
    taskQueue    chan int           // 任务队列
    workers      map[string]*WorkerInfo // Worker 信息
}

type TaskInfo struct {
    ID         int
    Status     TaskStatus
    WorkerID   string
    StartTime  time.Time
    RetryCount int
    Filename   string
}

type WorkerInfo struct {
    ID         string
    LastBeat   time.Time
    TaskCount  int
    Status     WorkerStatus
}
```

#### 2.1.2 状态机

```
Coordinator 状态转换:

  Init ──→ MapPhase ──→ ReducePhase ──→ AllDone
                     │
                     └──→ Failed (Worker 全部失败)
```

#### 2.1.3 核心算法

```go
// 任务分配算法
func (c *Coordinator) RequestTask(args *RequestTaskArgs, reply *RequestTaskReply) error {
    c.mu.Lock()
    defer c.mu.Unlock()

    switch c.phase {
    case MapPhase:
        return c.assignMapTask(args, reply)
    case ReducePhase:
        return c.assignReduceTask(args, reply)
    case AllDone:
        reply.TaskType = ExitTask
        return nil
    }
    return nil
}

// 任务分配策略
func (c *Coordinator) assignMapTask(args *RequestTaskArgs, reply *RequestTaskReply) error {
    // 1. 从队列获取空闲任务
    taskID, ok := <-c.taskQueue
    if !ok {
        // 队列为空，等待或进入下一阶段
        reply.TaskType = WaitTask
        return nil
    }

    // 2. 更新任务状态
    task := c.tasks[taskID]
    task.Status = TaskInProgress
    task.WorkerID = args.WorkerID
    task.StartTime = time.Now()

    // 3. 返回任务信息
    reply.TaskType = MapTask
    reply.TaskID = taskID
    reply.Filename = task.Filename
    reply.NReduce = c.nReduce
    return nil
}
```

### 2.2 Worker 模块

#### 2.2.1 数据结构

```go
type Worker struct {
    id        string
    coordinator *rpc.Client
    mapFunc   MapFunc
    reduceFunc ReduceFunc
}

type MapFunc func(filename string, contents string) []KeyValue
type ReduceFunc func(key string, values []string) string
```

#### 2.2.2 工作流程

```
Worker 主循环:

1. 向 Coordinator 请求任务
   ↓
2. 根据任务类型执行:
   ├─ MapTask → 执行 Map 函数
   │   ├─ 读取输入文件
   │   ├─ 调用用户 Map 函数
   │   ├─ 按 key hash 分区
   │   └─ 写入中间文件 mr-X-Y
   │
   ├─ ReduceTask → 执行 Reduce 函数
   │   ├─ 读取所有 mr-*-Y 文件
   │   ├─ 按 key 分组排序
   │   ├─ 调用用户 Reduce 函数
   │   └─ 写入输出文件 mr-out-Y
   │
   ├─ WaitTask → 等待后重试
   │
   └─ ExitTask → 退出
   ↓
3. 报告任务结果
   ↓
4. 回到步骤 1
```

#### 2.2.3 核心实现

```go
func (w *Worker) Run() {
    for {
        // 1. 请求任务
        reply := w.requestTask()
        
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
        
        // 2. 报告完成
        w.reportTask(reply.TaskID, reply.TaskType, true)
    }
}

func (w *Worker) doMap(task *RequestTaskReply) error {
    // 1. 读取输入文件
    content, err := os.ReadFile(task.Filename)
    if err != nil {
        return err
    }
    
    // 2. 执行 Map 函数
    kvs := w.mapFunc(task.Filename, string(content))
    
    // 3. 按 hash 分区并写入文件
    buckets := make([][]KeyValue, task.NReduce)
    for _, kv := range kvs {
        bucket := ihash(kv.Key) % task.NReduce
        buckets[bucket] = append(buckets[bucket], kv)
    }
    
    // 4. 写入中间文件
    for i, bucket := range buckets {
        filename := fmt.Sprintf("tmp/mr-%d-%d", task.TaskID, i)
        w.writeIntermediate(filename, bucket)
    }
    
    return nil
}
```

### 2.3 Shuffle & Sort 模块

#### 2.3.1 设计目标

- 将 Map 输出按 key 分组
- 保证相同 key 的数据发送到同一个 Reduce
- 对 values 进行排序

#### 2.3.2 实现策略

```
方案一: Map 端分区 (本项目采用)
  Map 输出 → Hash(key) % nReduce → 写入对应文件
  Reduce 读取 → 合并排序 → 分组

方案二: Reduce 端排序
  Map 输出 → 写入单个文件
  Reduce 读取 → 全局排序 → 分组
```

#### 2.3.3 Hash 函数

```go
func ihash(key string) int {
    h := fnv.New32a()
    h.Write([]byte(key))
    return int(h.Sum32() & 0x7fffffff)
}
```

---

## 3. 通信设计

### 3.1 RPC 协议

```go
// 任务请求
type RequestTaskArgs struct {
    WorkerID string
}

type RequestTaskReply struct {
    TaskType   TaskType
    TaskID     int
    Filename   string
    NReduce    int
    AllMapDone bool
}

// 任务报告
type ReportTaskArgs struct {
    WorkerID string
    TaskID   int
    TaskType TaskType
    Success  bool
}

type ReportTaskReply struct {
    OK bool
}
```

### 3.2 通信流程

```
Worker                    Coordinator
   │                          │
   │──── RequestTask ────────→│
   │                          │ (分配任务)
   │←──── TaskInfo ──────────│
   │                          │
   │ (执行任务)                │
   │                          │
   │──── ReportTask ─────────→│
   │                          │ (更新状态)
   │←──── Ack ───────────────│
   │                          │
```

### 3.3 超时机制

```go
// 心跳超时: 10 秒
const HeartbeatTimeout = 10 * time.Second

// 任务超时: 60 秒
const TaskTimeout = 60 * time.Second

// 超时检测协程
func (c *Coordinator) timeoutChecker() {
    ticker := time.NewTicker(time.Second)
    for range ticker.C {
        c.mu.Lock()
        for _, task := range c.tasks {
            if task.Status == TaskInProgress {
                if time.Since(task.StartTime) > TaskTimeout {
                    // 任务超时，重新调度
                    task.Status = TaskIdle
                    c.taskQueue <- task.ID
                }
            }
        }
        c.mu.Unlock()
    }
}
```

---

## 4. 数据流设计

### 4.1 输入数据流

```
输入文件:
  file1.txt → [Split] → Chunk 1, Chunk 2, Chunk 3
  file2.txt → [Split] → Chunk 4, Chunk 5

分片策略:
  - 默认每个文件作为一个分片
  - 可配置分片大小 (如 64MB)
```

### 4.2 中间数据流

```
Map 任务 0:
  输入: file1.txt
  输出: mr-0-0, mr-0-1, mr-0-2, ..., mr-0-(nReduce-1)

Map 任务 1:
  输入: file2.txt
  输出: mr-1-0, mr-1-1, mr-1-2, ..., mr-1-(nReduce-1)

文件命名: mr-<mapID>-<reduceID>
```

### 4.3 输出数据流

```
Reduce 任务 0:
  输入: mr-0-0, mr-1-0, mr-2-0, ...
  输出: mr-out-0

Reduce 任务 1:
  输入: mr-0-1, mr-1-1, mr-2-1, ...
  输出: mr-out-1
```

---

## 5. 容错设计

### 5.1 Worker 故障处理

```
故障检测:
  1. Worker 定期发送心跳 (每秒)
  2. Coordinator 检测心跳超时 (10秒)
  3. 标记 Worker 为离线

故障恢复:
  1. 重新分配该 Worker 的任务
  2. 重置任务状态为 Idle
  3. 加入任务队列等待重新执行
```

### 5.2 任务超时处理

```
超时检测:
  1. 记录任务开始时间
  2. 定期检查任务执行时间
  3. 超过阈值 (60秒) 标记为超时

重试策略:
  1. 最大重试次数: 3
  2. 重试时分配给其他 Worker
  3. 超过最大次数标记为失败
```

### 5.3 幂等性保证

```
问题: Worker 可能执行任务但报告失败
解决: 
  1. Map 输出使用临时文件
  2. 任务完成后原子重命名
  3. 覆盖写入保证幂等性

实现:
  tmp/mr-0-0 → mr-0-0 (原子操作)
```

---

## 6. 性能优化设计

### 6.1 数据本地性

```go
// 优先分配到数据所在节点
func (c *Coordinator) scheduleWithLocality(workerID string) int {
    // 1. 查找该 Worker 本地的数据
    localTasks := c.getLocalTasks(workerID)
    if len(localTasks) > 0 {
        return localTasks[0]
    }
    
    // 2. 退化为任意空闲任务
    return c.getAnyIdleTask()
}
```

### 6.2 Combiner 优化

```go
// Map 端预聚合
func (w *Worker) doMapWithCombiner(task *RequestTaskReply) error {
    kvs := w.mapFunc(task.Filename, content)
    
    // 本地聚合
    combined := make(map[string][]string)
    for _, kv := range kvs {
        combined[kv.Key] = append(combined[kv.Key], kv.Value)
    }
    
    // 执行 Combiner (如果定义)
    if w.combiner != nil {
        for key, values := range combined {
            combined[key] = []string{w.combiner(key, values)}
        }
    }
    
    // 写入文件
    w.writeIntermediate(filename, combined)
    return nil
}
```

### 6.3 并发优化

```go
// 并发读取中间文件
func (w *Worker) doReduce(task *RequestTaskReply) error {
    var wg sync.WaitGroup
    ch := make(chan KeyValue, 1000)
    
    // 并发读取所有 Map 输出
    for i := 0; i < nMap; i++ {
        wg.Add(1)
        go func(mapID int) {
            defer wg.Done()
            kvs := w.readIntermediate(fmt.Sprintf("mr-%d-%d", mapID, task.TaskID))
            for _, kv := range kvs {
                ch <- kv
            }
        }(i)
    }
    
    // 等待所有读取完成
    go func() {
        wg.Wait()
        close(ch)
    }()
    
    // 收集并排序
    var allKVs []KeyValue
    for kv := range ch {
        allKVs = append(allKVs, kv)
    }
    sort.Slice(allKVs, func(i, j int) bool {
        return allKVs[i].Key < allKVs[j].Key
    })
    
    // 执行 Reduce
    w.executeReduce(allKVs, task.TaskID)
    return nil
}
```

---

## 7. 配置设计

### 7.1 配置文件

```yaml
# config.yaml
coordinator:
  port: 8888
  heartbeat_timeout: 10s
  task_timeout: 60s
  max_retries: 3

worker:
  coordinator_addr: "localhost:8888"
  heartbeat_interval: 1s
  temp_dir: "/tmp/mapreduce"

storage:
  input_dir: "./testdata"
  output_dir: "./output"
  intermediate_dir: "/tmp/mapreduce"
```

### 7.2 运行时参数

```go
type Config struct {
    Coordinator CoordinatorConfig
    Worker      WorkerConfig
    Storage     StorageConfig
}
```

---

## 8. 测试设计

### 8.1 单元测试

```
测试覆盖:
  - ihash 函数
  - KeyValue 序列化
  - 文件读写
  - 任务状态转换
```

### 8.2 集成测试

```
测试场景:
  - 完整 MapReduce 流程
  - 多 Worker 并行
  - Worker 故障恢复
  - 任务超时重试
```

### 8.3 性能测试

```
测试指标:
  - 吞吐量 (MB/s)
  - 延迟 (ms)
  - CPU 使用率
  - 内存使用量
```
