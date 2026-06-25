# 分布式 MapReduce - 需求规格

## 1. 项目概述

### 1.1 项目目标

实现一个轻量级的分布式 MapReduce 框架，支持用户自定义 Map 和 Reduce 函数，自动处理数据分片、任务调度和容错。

### 1.2 目标用户

- 学习分布式系统的开发者
- 需要批量处理大数据的工程师
- 理解 MapReduce 编程模型的学生

---

## 2. 功能需求

### 2.1 核心功能

#### F1: Map 任务处理

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| F1.1 | 支持用户自定义 Map 函数 | P0 |
| F1.2 | 将输入文件分割为多个分片 | P0 |
| F1.3 | 生成中间键值对 (KeyValue) | P0 |
| F1.4 | 中间结果写入临时文件 | P0 |
| F1.5 | 支持 Combiner 本地聚合 | P1 |

#### F2: Reduce 任务处理

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| F2.1 | 支持用户自定义 Reduce 函数 | P0 |
| F2.2 | 按 key 分组中间数据 | P0 |
| F2.3 | 对 values 进行排序 | P0 |
| F2.4 | 输出最终结果到文件 | P0 |
| F2.5 | 支持多个 Reduce 任务并行 | P0 |

#### F3: 任务调度

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| F3.1 | Coordinator 管理任务生命周期 | P0 |
| F3.2 | Worker 向 Coordinator 请求任务 | P0 |
| F3.3 | 支持 Map 和 Reduce 两阶段调度 | P0 |
| F3.4 | 任务超时检测和重试 | P0 |
| F3.5 | Worker 故障检测 | P0 |
| F3.6 | 负载均衡调度 | P1 |

#### F4: 数据分片

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| F4.1 | 输入文件按大小分片 | P0 |
| F4.2 | 支持自定义分片大小 | P1 |
| F4.3 | 中间数据按 key hash 分区 | P0 |
| F4.4 | 分区数等于 Reduce 任务数 | P0 |

#### F5: 容错处理

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| F5.1 | Worker 心跳超时检测 | P0 |
| F5.2 | 任务执行超时检测 | P0 |
| F5.3 | 失败任务自动重试 | P0 |
| F5.4 | 最大重试次数限制 | P0 |
| F5.5 | 幂等性保证 (重试不产生重复结果) | P0 |

---

### 2.2 应用示例

#### A1: 词频统计 (WordCount)

```go
// 输入: 文本文件
// 输出: 每个单词出现的次数

Map("file.txt", "hello world hello") →
    [("hello", "1"), ("world", "1"), ("hello", "1")]

Reduce("hello", ["1", "1"]) → "2"
```

#### A2: 倒排索引 (InvertedIndex)

```go
// 输入: 文档集合
// 输出: 每个单词出现在哪些文档中

Map("doc1.txt", "hello world") →
    [("hello", "doc1.txt"), ("world", "doc1.txt")]

Reduce("hello", ["doc1.txt", "doc2.txt"]) → "doc1.txt,doc2.txt"
```

#### A3: 日志分析 (LogAnalysis)

```go
// 输入: Web 服务器日志
// 输出: 每个 URL 的访问次数

Map("access.log", "GET /api/users 200") →
    [("/api/users", "1")]

Reduce("/api/users", ["1", "1", "1"]) → "3"
```

---

## 3. 非功能需求

### 3.1 性能需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 吞吐量 | > 1GB/min | 单节点处理能力 |
| 延迟 | < 100ms | 任务分配延迟 |
| 并发度 | 可配置 | Worker 数量 |
| 启动时间 | < 5s | 系统启动时间 |

### 3.2 可靠性需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 任务成功率 | > 99.9% | 含自动重试 |
| 故障恢复时间 | < 30s | Worker 故障后恢复 |
| 数据一致性 | 最终一致 | 重试保证正确性 |

### 3.3 可扩展性需求

| 维度 | 要求 | 说明 |
|------|------|------|
| 水平扩展 | 支持动态增减 Worker | 不需重启系统 |
| 功能扩展 | 插件式 Map/Reduce | 用户自定义函数 |
| 数据规模 | 支持 TB 级数据 | 取决于集群规模 |

### 3.4 可维护性需求

| 维度 | 要求 | 说明 |
|------|------|------|
| 日志 | 结构化日志 | 便于问题排查 |
| 监控 | 任务状态可视化 | Web UI 或 CLI |
| 配置 | 配置文件管理 | YAML/JSON 格式 |

---

## 4. 接口设计

### 4.1 用户接口

```go
// 用户需要实现的接口
type MapReduceApp interface {
    // Map 函数: 输入文件内容，输出键值对
    Map(filename string, contents string) []KeyValue

    // Reduce 函数: 输入 key 和 values，输出聚合结果
    Reduce(key string, values []string) string
}

// 启动 MapReduce 任务
func Run(app MapReduceApp, files []string, nReduce int) error
```

### 4.2 RPC 接口

```go
// Worker 向 Coordinator 请求任务
type RequestTaskArgs struct {
    WorkerID string
}

type RequestTaskReply struct {
    TaskType   TaskType   // Map, Reduce, Wait, Exit
    TaskID     int
    Filename   string
    NReduce    int
    AllMapDone bool
}

// Worker 报告任务完成
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

### 4.3 文件接口

```
输入文件:
  /path/to/input/file1.txt
  /path/to/input/file2.txt

中间文件 (Map 输出):
  /tmp/mr-<mapID>-<reduceID>

最终输出:
  /tmp/mr-out-<reduceID>
```

---

## 5. 数据模型

### 5.1 核心数据结构

```go
// 键值对
type KeyValue struct {
    Key   string
    Value string
}

// 任务状态
type TaskStatus int
const (
    TaskIdle     TaskStatus = iota
    TaskInProgress
    TaskCompleted
    TaskFailed
)

// 任务阶段
type Phase int
const (
    MapPhase    Phase = iota
    ReducePhase
    AllDone
)
```

### 5.2 状态机

```
任务状态转换:

  Idle ──→ InProgress ──→ Completed
    │            │
    │            ▼
    └──────→ Failed ──→ Idle (重试)
```

---

## 6. 约束条件

### 6.1 技术约束

- 使用 Go 1.21+ 开发
- 使用标准库 net/rpc 进行通信
- 不依赖外部存储系统 (使用本地文件系统)

### 6.2 环境约束

- 支持 Linux/macOS 操作系统
- 单机模拟分布式环境
- Worker 通过 localhost 通信

### 6.3 安全约束

- 仅在可信网络环境运行
- 不处理敏感数据加密
- 文件权限由操作系统控制

---

## 7. 验收标准

### 7.1 功能验收

- [ ] WordCount 示例正确运行
- [ ] InvertedIndex 示例正确运行
- [ ] LogAnalysis 示例正确运行
- [ ] Worker 故障后任务自动重试
- [ ] 任务超时后自动重新分配

### 7.2 性能验收

- [ ] 1GB 数据处理时间 < 5 分钟
- [ ] 10 个 Worker 并行运行稳定
- [ ] 任务分配延迟 < 100ms

### 7.3 代码质量验收

- [ ] 单元测试覆盖率 > 70%
- [ ] 无 race condition (go test -race)
- [ ] 代码通过 go vet 检查
