# 技术设计文档

## 1. 架构概述

### 整体架构

```
┌──────────────────────────────────────────┐
│            streaming-algorithm            │
├────────────┬──────────┬──────────────────┤
│  窗口聚合   │ 概率结构  │  采样/统计       │
│ SlidingWin │ HLL/TopK │ ReservoirSample  │
└────────────┴──────────┴──────────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| SlidingWindow | 滑动窗口平均 | `internal/sliding_window.go` |
| ReservoirSampler | 蓄水池采样 | `internal/reservoir.go` |
| HyperLogLog | 基数估计 | `internal/hyperloglog.go` |
| TopK | 频繁项统计 | `internal/topk.go` |

## 2. 核心流程

### 主流程
```
数据流 → 选择算法 → 处理 → 结果输出
```

## 3. 数据设计

### HyperLogLog
```
registers: [uint8; m]  // 寄存器数组
m = 2^b                // 寄存器数量
b = 4..16              // 精度参数
```

### TopK
```
items: map[string]int  // 元素->计数
k: int                 // 保留 top-k
minKey: string         // 最小计数的 key
```

## 4. 接口设计

### SlidingWindow
```go
NewSlidingWindow(size int) *SlidingWindow
Add(value float64)
Average() (float64, bool)
Values() []float64
```

### ReservoirSampler
```go
NewReservoirSampler(k int) *ReservoirSampler
Sample(value int)
GetSample() []int
```

### HyperLogLog
```go
NewHyperLogLog(stdErr float64) *HyperLogLog
Add(item string)
Count() float64
Merge(other *HyperLogLog)
```

### TopK
```go
NewTopK(k int) *TopK
Add(item string)
Top() []struct{Item string; Count int}
```
