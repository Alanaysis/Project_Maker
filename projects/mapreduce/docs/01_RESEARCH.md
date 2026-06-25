# 分布式 MapReduce - 技术调研

## 1. MapReduce 概述

### 1.1 起源与发展

MapReduce 最早由 Google 在 2004 年提出，论文 "MapReduce: Simplified Data Processing on Large Clusters" 描述了这一编程模型。它将复杂的分布式计算抽象为两个简单的操作：Map 和 Reduce。

### 1.2 核心思想

```
输入数据 → [Split] → 数据分片
    ↓
[Map] → 中间键值对 → [Shuffle & Sort] → 分组数据
    ↓
[Reduce] → 最终输出
```

### 1.3 设计哲学

| 原则 | 说明 |
|------|------|
| 简单抽象 | 用户只需实现 Map 和 Reduce 函数 |
| 自动并行 | 框架自动处理数据分片和任务调度 |
| 容错处理 | 自动检测和恢复失败任务 |
| 数据本地性 | 尽量在数据所在节点执行计算 |

---

## 2. 核心算法分析

### 2.1 Map 阶段

```go
// Map 函数签名
type MapFunc func(filename string, contents string) []KeyValue

// 输入: (文件名, 文件内容)
// 输出: 中间键值对列表

// 示例: WordCount Map
func Map(filename, contents string) []KeyValue {
    words := strings.Fields(contents)
    var kvs []KeyValue
    for _, w := range words {
        kvs = append(kvs, KeyValue{Key: w, Value: "1"})
    }
    return kvs
}
```

### 2.2 Shuffle & Sort 阶段

```
Map 输出:
  ("hello", "1"), ("world", "1"), ("hello", "1")

Shuffle (按 key 分组):
  "hello" → ["1", "1"]
  "world" → ["1"]

Sort (排序):
  ["hello", "hello"] → ["1", "1"]
  ["world"] → ["1"]
```

### 2.3 Reduce 阶段

```go
// Reduce 函数签名
type ReduceFunc func(key string, values []string) string

// 输入: (key, values 列表)
// 输出: 聚合结果

// 示例: WordCount Reduce
func Reduce(key string, values []string) string {
    return strconv.Itoa(len(values))
}
```

---

## 3. 分布式架构研究

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Coordinator                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 任务队列  │  │ 状态管理  │  │ 故障检测  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Worker 1   │  │   Worker 2   │  │   Worker N   │
│  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │
│  │Map Task│  │  │  │Map Task│  │  │  │Map Task│  │
│  └────────┘  │  │  └────────┘  │  │  └────────┘  │
│  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │
│  │Red Task│  │  │  │Red Task│  │  │  │Red Task│  │
│  └────────┘  │  │  └────────┘  │  │  └────────┘  │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 3.2 任务调度策略

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| FIFO | 简单公平 | 不考虑优先级 | 通用场景 |
| 数据本地性 | 减少网络传输 | 可能不均衡 | 数据密集型 |
| 负载均衡 | 资源利用率高 | 调度复杂 | 计算密集型 |
| 推测执行 | 避免慢任务 | 资源浪费 | 异构环境 |

### 3.3 容错机制

```
Worker 故障检测流程:

1. Worker 心跳超时 (10s)
    ↓
2. Coordinator 标记任务失败
    ↓
3. 重新分配任务给其他 Worker
    ↓
4. 更新任务状态

任务超时处理:

1. 任务执行时间超过阈值 (60s)
    ↓
2. 标记为超时
    ↓
3. 重新调度到其他 Worker
```

---

## 4. 技术选型

### 4.1 编程语言: Go

| 特性 | 优势 |
|------|------|
| Goroutine | 轻量级并发，适合分布式通信 |
| Channel | 类型安全的消息传递 |
| net/rpc | 内置 RPC 框架 |
| sync 包 | 丰富的并发原语 |
| 编译型语言 | 高性能，易于部署 |

### 4.2 通信协议

```go
// RPC 通信设计
type Coordinator struct {
    mu          sync.Mutex
    tasks       []Task
    workers     map[string]*WorkerInfo
    taskPhase   Phase  // MapPhase or ReducePhase
}

type Task struct {
    ID       int
    Type     TaskType
    Filename string
    Status   TaskStatus
    WorkerID string
}
```

### 4.3 文件系统

```
项目文件结构:

mapreduce/
├── cmd/                    # 可执行文件
│   ├── coordinator/       # Coordinator 入口
│   └── worker/            # Worker 入口
├── internal/              # 内部实现
│   ├── coordinator/       # Coordinator 核心逻辑
│   ├── worker/            # Worker 核心逻辑
│   ├── mapreduce/         # MapReduce 框架
│   └── rpc/               # RPC 定义
├── pkg/                   # 公共包
│   └── applications/      # 应用示例
└── docs/                  # 文档
```

---

## 5. 性能分析

### 5.1 理论模型

```
总执行时间 = Map 时间 + Shuffle 时间 + Reduce 时间

其中:
- Map 时间 = max(各 Map 任务时间) / 并行度
- Shuffle 时间 = 数据量 / 网络带宽
- Reduce 时间 = max(各 Reduce 任务时间) / 并行度
```

### 5.2 性能优化点

| 优化点 | 方法 | 预期效果 |
|--------|------|----------|
| 数据本地性 | 优先调度到数据所在节点 | 减少 30% 网络传输 |
| Combiner | Map 端预聚合 | 减少 50% Shuffle 数据 |
| 数据压缩 | LZW/Snappy 压缩 | 减少 60% 传输量 |
| 推测执行 | 为慢任务启动备份 | 减少 20% 总时间 |

### 5.3 扩展性分析

```
假设:
- N 个 Worker 节点
- M 个 Map 任务
- R 个 Reduce 任务

理论加速比:
S(N) ≈ N (当 M, R >> N 时)

实际加速比:
S(N) = T(1) / T(N) < N
原因: 通信开销、负载不均衡、故障恢复
```

---

## 6. 参考资料

### 6.1 学术论文

1. **Dean, J., & Ghemawat, S. (2008)**. MapReduce: simplified data processing on large clusters. Communications of the ACM, 51(1), 107-113.
2. **Dean, J., & Ghemawat, S. (2004)**. MapReduce: Simplified Data Processing on Large Clusters. OSDI'04.

### 6.2 开源实现

| 项目 | 语言 | 特点 |
|------|------|------|
| Hadoop MapReduce | Java | 生产级实现，功能完整 |
| Go MapReduce (MIT 6.824) | Go | 教学实现，简洁清晰 |
| mrjob | Python | Python 封装，易于使用 |

### 6.3 学习资源

- MIT 6.824 Distributed Systems
- Google MapReduce 论文
- Hadoop 官方文档

---

## 7. 调研结论

### 7.1 技术可行性

- Go 语言适合实现分布式系统
- net/rpc 满足通信需求
- Goroutine 模型适合并发任务处理

### 7.2 设计方向

1. **简洁设计**: 参考 MIT 6.824 实现
2. **完整功能**: 支持 Map、Shuffle、Reduce 全流程
3. **容错机制**: Worker 故障检测和任务重试
4. **易于扩展**: 用户自定义 Map/Reduce 函数

### 7.3 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 网络延迟 | 性能下降 | 数据本地性优化 |
| Worker 故障 | 任务失败 | 超时重试机制 |
| 数据倾斜 | 负载不均 | 自定义分区函数 |
| 内存溢出 | 进程崩溃 | 流式处理大文件 |
