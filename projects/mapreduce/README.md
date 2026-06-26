# MapReduce - 分布式 MapReduce 框架

## 简介 / Introduction

**中文**: 一个用于学习分布式 MapReduce 原理的 Go 实现。本项目实现了经典的 Master-Worker 模型，包含输入分片、Map 阶段、Shuffle 阶段、Reduce 阶段和输出等完整流程。

**English**: A Go implementation of the distributed MapReduce framework for learning purposes. This project implements the classic Master-Worker model, covering the complete pipeline: input splitting, Map phase, Shuffle phase, Reduce phase, and output.

---

## 学习目标 / Learning Objectives

### 核心概念 / Core Concepts

1. **MapReduce 原理** - 理解大规模数据并行处理的基本模型
2. **Map/Reduce 函数** - 掌握 Map 和 Reduce 函数的设计与实现
3. **任务调度** - 学习 Master-Worker 模型的任务分配机制
4. **Shuffle 机制** - 理解中间数据的分区与归并
5. **容错机制** - 实现心跳检测与任务重分配

### 技术要点 / Technical Points

- 输入分片 (Input Splitting)
- 中间文件管理 (Intermediate File Management)
- 分区函数 (Partitioning)
- 键排序 (Key Sorting)
- 多阶段流水线 (Multi-stage Pipelines)

---

## MapReduce 架构 / Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        Master                            │
│  (任务调度 / 状态管理 / 容错)                              │
└───────────────┬──────────────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker N│
│ Map/   │ │ Map/   │ │ Map/   │
│ Reduce │ │ Reduce │ │ Reduce │
└────────┘ └────────┘ └────────┘
    │           │           │
    ▼           ▼           ▼
┌──────────────────────────────────────────────────────────┐
│              中间文件 / 最终输出                            │
│         (Intermediate / Output Files)                     │
└──────────────────────────────────────────────────────────┘
```

### 执行流程 / Execution Flow

```
1. 输入分片 → 每个输入文件对应一个 Map 任务
2. Map 阶段 → Worker 读取输入，执行 Map 函数，输出中间键值对
3. Shuffle  → 按 Key 对中间数据进行分区，每个 Reduce 任务处理一个分区
4. Reduce 阶段 → Worker 读取对应分区，执行 Reduce 函数，输出最终结果
5. 输出 → 每个 Reduce 任务生成一个输出文件
```

---

## 运行示例 / Running Examples

### 1. 词频统计 (Word Count) - 经典 MapReduce 示例

```bash
cd examples
go run word_count.go
```

**描述**: 统计多个文本文件中每个单词出现的次数。

**Map 函数**: 将每行文本拆分为单词，输出 `(单词, 1)` 对
**Reduce 函数**: 对每个单词的所有值求和

### 2. 分布式排序 (Distributed Sorting)

```bash
cd examples
go run distributed_sort.go
```

**描述**: 对多个文件中的数字进行分布式排序。

**Map 函数**: 每行作为一个待排序元素
**Reduce 函数**: 对每个分区内的值排序

### 3. 日志分析 (Log Analysis)

```bash
cd examples
go run log_analysis.go
```

**描述**: 分析 HTTP 服务器日志，统计状态码、HTTP 方法和 IP 地址的分布。

**Map 函数**: 解析日志行，输出 `(status:XXX, 1)`, `(method:YYY, 1)`, `(ip:ZZZ, 1)`
**Reduce 函数**: 对每个键的值求和

### 4. 多阶段流水线 (Multi-Stage Pipeline)

```bash
cd examples
go run multi_stage_pipeline.go
```

**描述**: 展示如何链式运行多个 MapReduce 作业。

- **Stage 1**: 词频统计
- **Stage 2**: 按频率分组单词

---

## 项目结构 / Project Structure

```
mapreduce/
├── src/
│   ├── mr.go          # 核心框架：Master、Worker、Task、MapFunc、ReduceFunc
│   └── io.go          # 输入/输出：文件读取、分区写入、中间文件管理
├── examples/
│   ├── word_count.go       # 词频统计
│   ├── distributed_sort.go # 分布式排序
│   ├── log_analysis.go     # 日志分析
│   └── multi_stage_pipeline.go  # 多阶段流水线
├── tests/
│   └── mr_test.go     # 单元测试
├── go.mod
└── README.md
```

---

## 运行测试 / Running Tests

```bash
cd tests
go test -v
```

---

## 核心设计 / Key Design Decisions

### Master-Worker 模型

- **Master** 负责协调所有任务：创建任务、分配给 Worker、监控进度、处理故障
- **Worker** 负责执行具体的 Map 或 Reduce 任务
- 中间数据通过文件系统传递（Shuffle 阶段）

### 分区策略

- 使用哈希分区：`partition = hash(key) % numReduceTasks`
- 保证相同 Key 的数据总是发送到同一个 Reduce 任务

### 容错机制

- Worker 心跳检测
- 任务失败自动重分配
- Master 跟踪每个任务的状态

---

## 扩展方向 / Extensions

1. **真正的分布式**: 通过 RPC 实现多节点通信
2. **数据倾斜优化**: 动态调整分区大小
3. **Combiner 优化**: 在 Map 端进行局部聚合
4. **容错增强**: 检查点与任务重试策略
5. **大规模数据**: 支持超过内存的数据集处理

---

## 参考资源 / References

- Dean, J. & Ghemawat, S. "MapReduce: Simplified Data Processing on Large Clusters"
- Apache Hadoop MapReduce Documentation
- Google File System (GFS) Paper

---

## 许可证 / License

MIT License
