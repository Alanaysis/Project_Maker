# 分布式 MapReduce

> 一个教学级的分布式 MapReduce 框架，支持用户自定义 Map/Reduce 函数，实现自动任务调度、容错处理和并行计算。

---

## 项目概述

本项目实现了一个轻量级的分布式 MapReduce 框架，参考 Google MapReduce 论文和 MIT 6.824 课程设计。用户只需实现 Map 和 Reduce 两个函数，框架自动处理数据分片、任务调度、故障恢复等分布式系统核心问题。

### 核心特性

- **用户自定义函数**: 只需实现 Map 和 Reduce 接口
- **自动任务调度**: Coordinator 自动分配 Map/Reduce 任务
- **容错处理**: Worker 故障检测和任务自动重试
- **并行执行**: 多 Worker 并行处理
- **应用示例**: 词频统计、倒排索引、日志分析

---

## 快速开始

### 环境要求

- Go 1.21+
- Linux/macOS

### 编译

```bash
# 编译所有组件
make build

# 或单独编译
go build -o bin/coordinator ./cmd/coordinator
go build -o bin/worker ./cmd/worker
```

### 运行示例

```bash
# 终端 1: 启动 Coordinator
./bin/coordinator -port 8888 -nreduce 3 testdata/pg-*.txt

# 终端 2: 启动 Worker 1
./bin/worker -coordinator localhost:8888 -app wordcount

# 终端 3: 启动 Worker 2 (可选)
./bin/worker -coordinator localhost:8888 -app wordcount
```

### 查看结果

```bash
# 合并输出文件
cat mr-out-* | sort | head -20
```

输出示例:
```
a 156
about 23
all 45
and 234
are 67
...
```

---

## 架构设计

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

### 核心组件

| 组件 | 职责 | 通信方式 |
|------|------|----------|
| Coordinator | 任务调度、状态管理、故障检测 | RPC Server |
| Worker | 执行 Map/Reduce 任务 | RPC Client |

---

## 应用示例

### 1. 词频统计 (WordCount)

```go
// Map 函数
func WordCountMap(filename string, contents string) []KeyValue {
    words := strings.Fields(contents)
    var kvs []KeyValue
    for _, w := range words {
        kvs = append(kvs, KeyValue{Key: w, Value: "1"})
    }
    return kvs
}

// Reduce 函数
func WordCountReduce(key string, values []string) string {
    return strconv.Itoa(len(values))
}
```

### 2. 倒排索引 (InvertedIndex)

```go
// Map 函数
func InvertedIndexMap(filename string, contents string) []KeyValue {
    words := strings.Fields(contents)
    wordSet := make(map[string]bool)
    for _, w := range words {
        wordSet[w] = true
    }
    var kvs []KeyValue
    for w := range wordSet {
        kvs = append(kvs, KeyValue{Key: w, Value: filename})
    }
    return kvs
}

// Reduce 函数
func InvertedIndexReduce(key string, values []string) string {
    return strings.Join(values, ",")
}
```

### 3. 日志分析 (LogAnalysis)

```go
// Map 函数
func LogAnalysisMap(filename string, contents string) []KeyValue {
    lines := strings.Split(contents, "\n")
    var kvs []KeyValue
    for _, line := range lines {
        // 解析日志行，提取 URL
        if matches := logRegex.FindStringSubmatch(line); matches != nil {
            kvs = append(kvs, KeyValue{Key: matches[3], Value: "1"})
        }
    }
    return kvs
}

// Reduce 函数
func LogAnalysisReduce(key string, values []string) string {
    return strconv.Itoa(len(values))
}
```

---

## 命令行参数

### Coordinator

```bash
./bin/coordinator [flags] <input-files>

参数:
  -port int        监听端口 (默认 8888)
  -nreduce int     Reduce 任务数 (默认 10)
  -verbose         输出详细日志 (默认 true)
```

### Worker

```bash
./bin/worker [flags]

参数:
  -coordinator string  Coordinator 地址 (默认 "localhost:8888")
  -app string         应用程序名称 (默认 "wordcount")
  -verbose            输出详细日志 (默认 true)
```

---

## 测试

### 运行单元测试

```bash
# 运行所有测试
make test

# 运行特定包的测试
go test ./internal/coordinator/
go test ./internal/worker/
go test ./pkg/applications/

# 带 race 检测的测试
go test -race ./...

# 查看测试覆盖率
make test-cover
```

### 运行基准测试

```bash
make benchmark
```

---

## 项目结构

```
mapreduce/
├── cmd/                          # 可执行文件入口
│   ├── coordinator/             # Coordinator 主程序
│   │   └── main.go
│   └── worker/                  # Worker 主程序
│       └── main.go
├── internal/                    # 内部实现
│   ├── coordinator/             # Coordinator 核心逻辑
│   │   ├── coordinator.go
│   │   └── coordinator_test.go
│   ├── worker/                  # Worker 核心逻辑
│   │   └── worker.go
│   ├── mapreduce/               # MapReduce 框架
│   │   ├── types.go
│   │   └── types_test.go
│   └── rpc/                     # RPC 定义
│       └── rpc.go
├── pkg/                         # 公共包
│   └── applications/            # 应用示例
│       ├── wordcount.go
│       ├── inverted_index.go
│       ├── log_analysis.go
│       └── applications_test.go
├── docs/                        # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── testdata/                    # 测试数据
├── scripts/                     # 脚本
├── Makefile                     # 构建配置
├── go.mod                       # Go 模块定义
└── README.md                    # 项目说明
```

---

## 文档

- [技术调研](docs/01_RESEARCH.md) - MapReduce 原理和技术选型
- [需求规格](docs/02_REQUIREMENTS.md) - 功能和非功能需求
- [系统设计](docs/03_DESIGN.md) - 架构和模块设计
- [产品文档](docs/04_PRODUCT.md) - 使用指南和最佳实践
- [开发文档](docs/05_DEVELOPMENT.md) - 开发环境和贡献指南

---

## 技术栈

| 技术 | 用途 |
|------|------|
| Go 1.21+ | 编程语言 |
| net/rpc | RPC 通信 |
| sync | 并发控制 |
| encoding/json | 数据序列化 |
| hash/fnv | 哈希分区 |

---

## 性能指标

| 测试场景 | 数据量 | Worker 数 | 耗时 | 吞吐量 |
|----------|--------|-----------|------|--------|
| WordCount | 100MB | 1 | 45s | 2.2 MB/s |
| WordCount | 100MB | 4 | 15s | 6.7 MB/s |
| WordCount | 1GB | 4 | 2.5min | 6.8 MB/s |

---

## 学习资源

- [Google MapReduce 论文](https://research.google.com/archive/mapreduce.html)
- [MIT 6.824 Distributed Systems](https://pdos.csail.mit.edu/6.824/)
- [Hadoop MapReduce 文档](https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)

---

## 许可证

MIT License
