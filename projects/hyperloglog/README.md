# HyperLogLog 基数估计 / HyperLogLog Cardinality Estimation

> **实现 HyperLogLog 基数估计算法的学习项目**
> **A learning project implementing the HyperLogLog cardinality estimation algorithm**

---

## 项目描述 / Project Description

**中文**：
HyperLogLog 是一种概率型数据结构和算法，用于估算大规模数据集合的基数（不同元素的数量）。
本实现使用 Go 语言编写，包含详细的算法注释和多个演示程序，帮助理解 HyperLogLog 的核心原理。

**English**:
HyperLogLog is a probabilistic data structure and algorithm for estimating the cardinality (number of distinct elements)
of large-scale datasets. This implementation is written in Go with detailed algorithm comments and demo programs
to help understand the core principles of HyperLogLog.

---

## 学习目标 / Learning Objectives

### 中文
- **理解 HyperLogLog 原理**：掌握概率计数、桶分配、前导零统计的核心思想
- **掌握精度调优**：学习如何通过调整 p 参数在内存和精度之间取得平衡
- **学会偏差校正**：理解小范围线性计数和大范围指数校正的作用

### English
- **Understand HyperLogLog principles**: Master probabilistic counting, bucket assignment, and leading zero statistics
- **Master precision tuning**: Learn to balance memory and accuracy by adjusting the p parameter
- **Learn bias correction**: Understand linear counting for small ranges and exponential correction for large ranges

---

## 算法原理 / Algorithm Explanation

### 核心思想 / Core Idea

HyperLogLog 通过以下巧妙的方法估算基数：

1. **哈希**：将每个元素哈希为固定长度的二进制串
2. **桶分配**：用哈希的前 p 位决定使用哪个桶
3. **前导零统计**：用剩余位统计最左边的 1 的位置（rho 值）
4. **基数估计**：通过所有桶的调和平均数估算基数

### How It Works

1. **Hash**: Hash each element to a fixed-length binary string
2. **Bucket Assignment**: Use the first p bits to determine which bucket to use
3. **Leading Zero Counting**: Count the position of the leftmost 1-bit (rho value) in remaining bits
4. **Cardinality Estimation**: Estimate cardinality using harmonic mean of bucket values

### 数学基础 / Mathematical Foundation

```
对于均匀分布的随机比特流：
- rho 的期望值 E[rho] ≈ log2(n) + γ (γ 是欧拉常数)
- 因此：n ≈ 2^rho

HyperLogLog 使用调和平均数减少异常值影响：
- Z = m * (1/m) * Σ(2^(-rho_i))
- estimate = α_m * m² / Z
```

### 精度与内存权衡 / Precision vs Memory Trade-off

| 精度 (p) | 桶数量 (m) | 内存使用 | 标准误差 | 适用基数范围 |
|-----------|-----------|---------|---------|-------------|
| 4 | 16 | 16 bytes | ~12% | 仅教学用途 |
| 8 | 256 | 256 bytes | ~4.5% | 小规模 |
| 10 | 1,024 | ~1 KB | ~2% | 通用（推荐） |
| 14 | 16,384 | ~16 KB | ~0.8% | 高精度 |
| 16 | 65,536 | ~64 KB | ~0.5% | 超高精度 |

---

## 项目结构 / Project Structure

```
hyperloglog/
├── src/                          # 核心包
│   ├── hyperloglog.go            # HyperLogLog 算法核心实现
│   └── visualize.go              # 可视化和调试工具
├── examples/                     # 演示程序
│   ├── basic_demo.go             # 基础基数估计演示
│   ├── accuracy_comparison.go    # 不同精度的准确性对比
│   ├── memory_comparison.go      # 内存使用对比
│   └── stress_test.go            # 压力测试
├── tests/                        # 单元测试
│   └── hyperloglog_test.go       # 核心算法测试
├── go.mod                        # Go 模块定义
└── README.md                     # 本文件
```

---

## 如何运行 / How to Run

### 运行演示程序 / Run Examples

```bash
# 基础基数估计演示
go run examples/basic_demo.go

# 精度对比演示
go run examples/accuracy_comparison.go

# 内存使用对比演示
go run examples/memory_comparison.go

# 压力测试
go run examples/stress_test.go
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
go test ./tests/

# 运行测试并显示详细输出
go test -v ./tests/

# 运行短测试（跳过耗时测试）
go test -short ./tests/

# 显示覆盖率
go test -cover ./tests/
```

### 构建项目 / Build

```bash
# 构建核心包
go build ./src/

# 构建所有示例
go build ./examples/...
```

---

## HyperLogLog 算法详解 / Algorithm Deep Dive

### 1. 哈希函数 / Hash Function

```go
// 使用 SHA-256 的前 8 字节作为 64 位哈希
hash := sha256.Sum256(data)
hash64 := binary.BigEndian.Uint64(hash[:8])
```

好的哈希函数必须满足：
- **均匀分布**：每个比特等概率为 0 或 1
- **雪崩效应**：输入微小变化导致输出巨大变化
- **确定性**：相同输入产生相同输出

### 2. 桶分配 / Bucket Assignment

```
hash = bbbbbbbbbb rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
       ^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
       p bits    64-p bits (for rho calculation)
       |
       bucket_index = hash >> (64 - p)
```

### 3. Rho 计算 / Rho Calculation

```
remaining = hash & ((1 << (64-p)) - 1)  // 去掉前 p 位
rho = position of first 1-bit from left
    = (64 - p) - floor(log2(remaining)) + 1

示例：remaining = 000101...
      rho = 4 (第 4 位是第一个 1)
```

### 4. 基数估计 / Cardinality Estimation

```
Z = m * Σ(2^(-register[i]))    // 调和平均数
estimate = α_m * m² / Z         // 标准公式

校正：
- 小范围：线性计数 (linear counting)
- 中等范围：标准 HyperLogLog
- 大范围：指数校正
```

### 5. 合并操作 / Merge Operation

```go
// 取对应桶的最大值
for i := range registers:
    merged[i] = max(registers1[i], registers2[i])
```

合并是 HyperLogLog 的关键特性，支持分布式估算。

---

## 关键概念 / Key Concepts

### 精度参数 p / Precision Parameter

```go
// p 决定桶数量 m = 2^p
// 增加 p = 更多桶 = 更好精度 = 更多内存
p = 10: 1024 buckets, 1KB memory, ~2% error
p = 14: 16384 buckets, 16KB memory, ~0.8% error
```

### 标准误差 / Standard Error

```
SE ≈ 0.81 / √m = 0.81 / √(2^p)

p=10: SE ≈ 2.55%
p=14: SE ≈ 0.64%
p=16: SE ≈ 0.28%
```

### 置信区间 / Confidence Interval

```
95% 置信区间: [estimate - 1.96*SE*estimate, estimate + 1.96*SE*estimate]
```

---

## 应用场景 / Use Cases

- **Redis**：`SCARD` 近似计数 (`PFADD`/`PFCOUNT`)
- **Apache Spark**：`approx_count_distinct`
- **Web 分析**：唯一访客计数
- **数据库**：查询优化中的基数估计
- **网络监控**：唯一 IP 地址计数
- **日志分析**：唯一用户/会话计数

---

## 技术栈 / Tech Stack

- **语言**：Go 1.21+
- **框架**：无
- **依赖**：无（仅使用标准库）

---

## 运行示例输出示例 / Example Output

```
=== HyperLogLog Basic Cardinality Estimation ===

Adding 10000 unique elements...

True cardinality:     10000
HLL estimate:         9847
Absolute error:       153
Relative error:       1.53%
Standard error:       2.55%

=== HyperLogLog Sketch Info ===
Precision (p):      10
Buckets (m=2^p):    1024
Memory usage:       1056 bytes
Estimate:           9847.00
Max register:       14
Avg register:       12.8452
Zero buckets:       0 / 1024
Standard error:     2.55%
Max possible rho:   55
Expected rho:       ~13.30
===============================
```

---

## 参考资料 / References

- **原始论文**：Flajolet et al., "HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm" (2007)
- **Redis 实现**：https://github.com/redis/redis/blob/unstable/src/t_stream.c
- **Spark 实现**：https://spark.apache.org/docs/latest/api/python/
- **维基百科**：https://en.wikipedia.org/wiki/HyperLogLog

---

## License

MIT License
