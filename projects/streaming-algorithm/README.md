# 流式算法

实现流式数据处理算法，支持滑动窗口、蓄水池采样、HyperLogLog 基数估计和 Top-K 频繁项统计。

## 核心循环

```
数据流入 → 窗口更新 → 聚合计算 → 结果输出
```

## 学习目标

- 理解流式算法原理（One-pass 计算）
- 掌握滑动窗口和蓄水池采样
- 学会概率数据结构（HyperLogLog）的应用

## 技术栈

- 主语言：Go
- 框架：无
- 依赖：无

## 项目结构

```
streaming-algorithm/
├── cmd/streaming-algorithm/  # 命令行入口
├── internal/                 # 核心算法实现
│   ├── sliding_window.go    # 滑动窗口
│   ├── reservoir.go         # 蓄水池采样
│   ├── hyperloglog.go       # HyperLogLog 基数估计
│   └── topk.go              # Top-K 频繁项
├── examples/                 # 使用示例
├── test/                     # 测试
└── docs/                     # 文档
```

## 快速开始

### 运行测试

```bash
go test ./test/... -v
```

### 运行示例

```bash
go run examples/basic_usage.go
go run examples/performance.go
go run examples/stream_analysis.go
```

### 命令行

```bash
go run cmd/streaming-algorithm/main.go
```

## 核心功能

### 1. 滑动窗口

```go
sw := stream.NewSlidingWindow(5)
sw.Add(10)
avg, ok := sw.Average()
```

### 2. 蓄水池采样

```go
rs := stream.NewReservoirSampler(3)
for _, v := range data {
    rs.Sample(v)
}
sample := rs.GetSample()
```

### 3. HyperLogLog

```go
hll := stream.NewHyperLogLog(0.01)
hll.Add("user_1")
count := hll.Count()
```

### 4. Top-K

```go
tk := stream.NewTopK(3)
tk.Add("item")
top := tk.Top()
```
