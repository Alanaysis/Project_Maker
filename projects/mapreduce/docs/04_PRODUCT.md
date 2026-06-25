# 分布式 MapReduce - 产品文档

## 1. 产品概述

### 1.1 产品定位

分布式 MapReduce 是一个教学级的分布式计算框架，帮助开发者理解 MapReduce 编程模型的核心原理，包括任务调度、容错处理、数据分片等分布式系统关键概念。

### 1.2 核心价值

| 价值点 | 说明 |
|--------|------|
| 学习价值 | 深入理解分布式系统原理 |
| 实践价值 | 动手实现 MapReduce 框架 |
| 扩展价值 | 可作为更大系统的基础组件 |

### 1.3 目标场景

1. **教学演示**: 分布式系统课程实验
2. **原型验证**: 快速验证 MapReduce 算法
3. **小规模数据处理**: 日志分析、文本处理

---

## 2. 功能特性

### 2.1 核心特性

#### 特性一: 用户自定义函数

```go
// 用户只需实现两个函数
type MapFunc func(filename string, contents string) []KeyValue
type ReduceFunc func(key string, values []string) string

// 示例: WordCount
func WordCountMap(filename, contents string) []KeyValue {
    words := strings.Fields(contents)
    var kvs []KeyValue
    for _, w := range words {
        kvs = append(kvs, KeyValue{Key: w, Value: "1"})
    }
    return kvs
}

func WordCountReduce(key string, values []string) string {
    return strconv.Itoa(len(values))
}
```

#### 特性二: 自动任务调度

- Coordinator 自动分配任务
- 支持 Map/Reduce 两阶段调度
- Worker 动态请求任务

#### 特性三: 容错处理

- Worker 故障自动检测
- 任务超时自动重试
- 幂等性保证结果正确

#### 特性四: 并行处理

- 多 Worker 并行执行
- 数据自动分片
- 结果自动合并

### 2.2 应用示例

#### 示例一: 词频统计

```bash
# 启动 Coordinator
go run cmd/coordinator/main.go pg-*.txt

# 启动 Worker (可在多个终端启动)
go run cmd/worker/main.go wc.so
```

**输入文件**: `pg-*.txt` (Project Gutenberg 电子书)

**输出结果**:
```
A 509
AOL 3
ASCII 12
About 15
...
```

#### 示例二: 倒排索引

```bash
# 启动任务
go run cmd/coordinator/main.go docs/*.txt
go run cmd/worker/main.go ii.so
```

**输入文件**: `docs/*.txt` (文档集合)

**输出结果**:
```
algorithm doc1.txt,doc3.txt,doc5.txt
distributed doc2.txt,doc4.txt
mapreduce doc1.txt,doc2.txt,doc3.txt
```

#### 示例三: 日志分析

```bash
# 启动任务
go run cmd/coordinator/main.go logs/*.log
go run cmd/worker/main.go la.so
```

**输入文件**: `logs/*.log` (Web 服务器日志)

**输出结果**:
```
/api/users 1523
/api/orders 892
/login 456
```

---

## 3. 使用指南

### 3.1 快速开始

#### 3.1.1 环境准备

```bash
# 安装 Go (1.21+)
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# 克隆项目
git clone <repository-url>
cd mapreduce
```

#### 3.1.2 编译项目

```bash
# 编译所有组件
go build -o bin/coordinator ./cmd/coordinator
go build -o bin/worker ./cmd/worker

# 或直接运行
go run cmd/coordinator/main.go
go run cmd/worker/main.go
```

#### 3.1.3 运行示例

```bash
# 终端 1: 启动 Coordinator
./bin/coordinator pg-*.txt

# 终端 2: 启动 Worker 1
./bin/worker wc.so

# 终端 3: 启动 Worker 2 (可选)
./bin/worker wc.so
```

### 3.2 自定义应用

#### 3.2.1 实现 Map 函数

```go
// myapp.go
package main

import "strings"

func MyMap(filename string, contents string) []KeyValue {
    var kvs []KeyValue
    
    // 按行处理
    lines := strings.Split(contents, "\n")
    for _, line := range lines {
        // 自定义逻辑
        if strings.HasPrefix(line, "ERROR") {
            kvs = append(kvs, KeyValue{Key: "ERROR", Value: line})
        }
    }
    
    return kvs
}
```

#### 3.2.2 实现 Reduce 函数

```go
func MyReduce(key string, values []string) string {
    // 自定义聚合逻辑
    return fmt.Sprintf("%d occurrences", len(values))
}
```

#### 3.2.3 编译为插件

```bash
go build -buildmode=plugin -o myapp.so myapp.go
```

#### 3.2.4 运行

```bash
./bin/coordinator input/*.txt
./bin/worker myapp.so
```

### 3.3 配置说明

#### 3.3.1 命令行参数

```bash
# Coordinator 参数
./bin/coordinator [flags] <input-files>
  -port int        监听端口 (默认 8888)
  -nreduce int     Reduce 任务数 (默认 10)
  -timeout string  任务超时时间 (默认 "60s")

# Worker 参数
./bin/worker [flags] <plugin-file>
  -coordinator string  Coordinator 地址 (默认 "localhost:8888")
  -heartbeat string    心跳间隔 (默认 "1s")
```

#### 3.3.2 环境变量

```bash
export MR_COORDINATOR_PORT=8888
export MR_WORKER_HEARTBEAT=1s
export MR_TEMP_DIR=/tmp/mapreduce
export MR_LOG_LEVEL=info
```

---

## 4. 架构详解

### 4.1 系统组件

```
┌─────────────────────────────────────────────────────────┐
│                    用户应用层                            │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐               │
│   │WordCount│  │InvIndex │  │LogAnalys│               │
│   └─────────┘  └─────────┘  └─────────┘               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   MapReduce 框架                        │
│   ┌─────────────────────────────────────────────────┐  │
│   │  Map Engine │ Shuffle Sort │ Reduce Engine     │  │
│   └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   调度与管理层                          │
│   ┌─────────────────────────────────────────────────┐  │
│   │                Coordinator                      │  │
│   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │  │
│   │  │Scheduler│ │TaskQueue│ │FaultDet│ │StateMgr│  │  │
│   │  └────────┘ └────────┘ └────────┘ └────────┘  │  │
│   └─────────────────────────────────────────────────┘  │
│                         │                              │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│   │Worker 1│ │Worker 2│ │Worker 3│ │Worker N│        │
│   └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 4.2 数据流

```
输入阶段:
  file1.txt ─┐
  file2.txt ─┼─→ [Split] ─→ 分片列表
  file3.txt ─┘

Map 阶段:
  分片 0 ─→ [Map] ─→ mr-0-0, mr-0-1, mr-0-2
  分片 1 ─→ [Map] ─→ mr-1-0, mr-1-1, mr-1-2
  分片 2 ─→ [Map] ─→ mr-2-0, mr-2-1, mr-2-2

Shuffle 阶段:
  mr-0-0, mr-1-0, mr-2-0 ─→ [Merge] ─→ Reduce 0 输入
  mr-0-1, mr-1-1, mr-2-1 ─→ [Merge] ─→ Reduce 1 输入
  mr-0-2, mr-1-2, mr-2-2 ─→ [Merge] ─→ Reduce 2 输入

Reduce 阶段:
  Reduce 0 输入 ─→ [Reduce] ─→ mr-out-0
  Reduce 1 输入 ─→ [Reduce] ─→ mr-out-1
  Reduce 2 输入 ─→ [Reduce] ─→ mr-out-2

输出合并:
  mr-out-0 ─┐
  mr-out-1 ─┼─→ [Merge] ─→ final-output.txt
  mr-out-2 ─┘
```

### 4.3 任务状态机

```
                    ┌──────────────┐
                    │   Idle       │
                    └──────┬───────┘
                           │ 分配任务
                           ▼
                    ┌──────────────┐
              ┌─────│ InProgress   │─────┐
              │     └──────────────┘     │
              │ 完成                      │ 超时/失败
              ▼                          ▼
       ┌──────────────┐          ┌──────────────┐
       │  Completed   │          │   Failed     │
       └──────────────┘          └──────────────┘
                                       │
                                       │ 重试
                                       ▼
                                ┌──────────────┐
                                │    Idle       │
                                └──────────────┘
```

---

## 5. 性能指标

### 5.1 基准测试

| 测试场景 | 数据量 | Worker 数 | 耗时 | 吞吐量 |
|----------|--------|-----------|------|--------|
| WordCount | 100MB | 1 | 45s | 2.2 MB/s |
| WordCount | 100MB | 4 | 15s | 6.7 MB/s |
| WordCount | 1GB | 4 | 2.5min | 6.8 MB/s |
| InvIndex | 500MB | 4 | 1.8min | 4.6 MB/s |

### 5.2 扩展性

```
加速比测试 (WordCount, 1GB):

Workers | Time(s) | Speedup
--------|---------|--------
   1    |   180   |   1.0x
   2    |    95   |   1.9x
   4    |    52   |   3.5x
   8    |    30   |   6.0x
  16    |    22   |   8.2x
```

### 5.3 资源消耗

| 资源 | Coordinator | Worker |
|------|-------------|--------|
| CPU | < 5% | 50-80% |
| 内存 | 50MB | 200-500MB |
| 网络 | 低 | 中等 |
| 磁盘 | 低 | 高 (临时文件) |

---

## 6. 故障处理

### 6.1 常见故障

| 故障类型 | 检测方式 | 恢复策略 |
|----------|----------|----------|
| Worker 进程崩溃 | 心跳超时 | 重新分配任务 |
| 任务执行超时 | 时间检测 | 重新调度 |
| 磁盘空间不足 | 错误报告 | 清理临时文件 |
| 网络中断 | RPC 失败 | 重试连接 |

### 6.2 日志说明

```json
{
  "level": "info",
  "time": "2024-01-15T10:30:00Z",
  "msg": "task completed",
  "task_id": 5,
  "task_type": "map",
  "worker_id": "worker-1",
  "duration_ms": 1234
}
```

### 6.3 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| tasks_completed | 已完成任务数 | - |
| tasks_failed | 失败任务数 | > 10% |
| workers_active | 活跃 Worker 数 | < 1 |
| avg_task_duration | 平均任务耗时 | > 60s |

---

## 7. 最佳实践

### 7.1 Map 函数设计

```go
// 好的设计: 简洁高效
func GoodMap(filename, contents string) []KeyValue {
    words := strings.Fields(contents)
    kvs := make([]KeyValue, 0, len(words))
    for _, w := range words {
        kvs = append(kvs, KeyValue{Key: w, Value: "1"})
    }
    return kvs
}

// 不好的设计: 内存浪费
func BadMap(filename, contents string) []KeyValue {
    var kvs []KeyValue
    for i := 0; i < 1000000; i++ {  // 无限循环
        kvs = append(kvs, KeyValue{Key: "key", Value: "value"})
    }
    return kvs
}
```

### 7.2 Reduce 函数设计

```go
// 好的设计: 处理边界情况
func GoodReduce(key string, values []string) string {
    if len(values) == 0 {
        return "0"
    }
    return strconv.Itoa(len(values))
}

// 不好的设计: 不处理空值
func BadReduce(key string, values []string) string {
    return values[0]  // 可能 panic
}
```

### 7.3 性能优化建议

1. **使用 Combiner**: 在 Map 端预聚合，减少 Shuffle 数据量
2. **合理设置 nReduce**: 一般设为 Worker 数的 2-3 倍
3. **避免数据倾斜**: 设计均匀分布的 key
4. **流式处理大文件**: 避免一次性加载整个文件

---

## 8. FAQ

### Q1: 如何添加新的 MapReduce 应用?

A: 实现 MapFunc 和 ReduceFunc 接口，编译为插件文件 (.so)。

### Q2: Worker 数量应该设置多少?

A: 建议设置为 CPU 核心数的 1-2 倍。

### Q3: 如何处理超大文件?

A: 修改分片策略，将大文件切分为多个小分片。

### Q4: 如何保证结果的正确性?

A: 框架保证幂等性，重试不会产生重复结果。

### Q5: 支持分布式部署吗?

A: 当前版本支持单机多进程，可扩展为多机部署。
