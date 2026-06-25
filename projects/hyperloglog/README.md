# HyperLogLog - 基数估计算法

## 项目概述

这是一个 HyperLogLog 基数估计算法的 Go 实现，用于理解概率数据结构的核心原理。HyperLogLog 是一种用于估计多集合基数的概率算法，使用极小的内存（通常 1.5KB）就能达到约 2% 的精度。

## 核心特性

- **高效内存**: 使用 1-64KB 内存估计数十亿级别的基数
- **高精度**: 标准误差 1.04 / √m，p=12 时约 1.6%
- **支持合并**: 多个 HyperLogLog 可以合并，适用于分布式场景
- **简单实现**: 核心代码约 270 行，易于理解和扩展

## 项目结构

```
hyperloglog/
├── internal/              # 核心实现
│   ├── hash.go           # 哈希函数
│   └── hyperloglog.go    # HyperLogLog 核心算法
├── cmd/hyperloglog/       # 命令行入口
│   └── main.go           # 演示程序
├── examples/              # 示例程序
│   ├── basic_usage.go    # 基本使用示例
│   ├── performance.go    # 性能测试示例
│   └── accuracy_analysis.go # 精度分析示例
├── test/                  # 测试文件
│   └── hyperloglog_test.go
├── docs/                  # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
└── go.mod
```

## 快速开始

### 运行演示

```bash
cd projects/hyperloglog
go run cmd/hyperloglog/main.go demo
```

### 运行测试

```bash
cd projects/hyperloglog
go test ./internal/ -v
```

### 运行示例

```bash
cd projects/hyperloglog
go run examples/basic_usage.go
go run examples/performance.go
go run examples/accuracy_analysis.go
```

## 核心概念

### HyperLogLog 算法流程

```
元素哈希 → 桶分配 → 最大前导零 → 基数估计
```

### 详细流程

1. **哈希**: 将元素映射到 64 位哈希值
2. **分桶**: 使用前 p 位选择寄存器 (桶)
3. **前导零计数**: 计算剩余位的前导零数量
4. **更新寄存器**: 保存每个桶的最大前导零数
5. **基数估计**: 使用调和平均数计算估计值

### 精度与资源权衡

| 精度 (p) | 寄存器数 | 内存占用 | 标准误差 |
|----------|----------|----------|----------|
| 4        | 16       | 16 字节  | 26%      |
| 8        | 256      | 256 字节 | 6.5%     |
| 10       | 1024     | 1 KB     | 3.25%    |
| 12       | 4096     | 4 KB     | 1.6%     |
| 14       | 16384    | 16 KB    | 0.8%     |
| 16       | 65536    | 64 KB    | 0.4%     |

## API 使用

```go
package main

import (
    "fmt"
    hyperloglog "github.com/hyperloglog/internal"
)

func main() {
    // 创建 HyperLogLog 实例
    hll, _ := hyperloglog.New(12) // p=12, 4096 registers

    // 添加元素
    for i := 0; i < 10000; i++ {
        hll.Add([]byte(fmt.Sprintf("user-%d", i)))
    }

    // 估算基数
    estimate := hll.Estimate()
    fmt.Printf("估算基数: %d\n", estimate)

    // 合并另一个 HyperLogLog
    hll2, _ := hyperloglog.New(12)
    for i := 0; i < 5000; i++ {
        hll2.Add([]byte(fmt.Sprintf("user-%d", i+8000)))
    }
    hll.Merge(hll2)

    // 重置
    hll.Reset()
}
```

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 哈希函数 | FNV-1a | 简单高效，Go 标准库支持 |
| 寄存器存储 | []uint8 | 内存占用小，前导零不超过 64 |
| 精度范围 | 4-16 | 平衡内存和精度 |
| 偏差校正 | 调和平均数 | 对离群值不敏感 |

## 学习目标

通过本项目，你将学到:
1. **HyperLogLog 原理**: 理解概率基数估计的核心思想
2. **概率计数**: 掌握使用概率方法估计基数
3. **精度调优**: 学会根据需求选择合适的精度参数
4. **位运算技巧**: 掌握分桶和前导零计数的实现
5. **浮点精度**: 理解偏差校正的实现

## 应用场景

### 1. 网站统计

```
场景: 统计独立访客数 (UV)
优势: 内存占用小，支持实时计算
精度: p=12 可达到 1.6% 误差
```

### 2. 数据库查询优化

```
场景: 估计查询结果集大小
优势: 快速估算，避免全表扫描
应用: 查询计划器选择最优执行计划
```

### 3. 网络流量分析

```
场景: 统计不同 IP 地址数量
优势: 流式处理，内存可控
精度: 可根据需求调整 p 值
```

### 4. 广告系统

```
场景: 估计广告覆盖人群
优势: 实时估算，支持大规模数据
应用: 去重统计、频次控制
```

## 参考资源

- [HyperLogLog 论文](https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf)
- [Google HyperLogLog 实践](https://research.google/pubs/archive/40671.pdf)
- [Redis HyperLogLog 文档](https://redis.io/commands/pfadd)
- [Wikipedia: HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog)

---

[返回主目录](../../README.md)
