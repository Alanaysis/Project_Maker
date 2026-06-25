# 01 - 研究: HyperLogLog 技术调研

## 什么是 HyperLogLog?

HyperLogLog (HLL) 是一种概率数据结构，用于估计多集合的基数（不同元素的数量）。它由 Philippe Flajolet 等人在 2007 年提出，是 LogLog 算法的改进版本。

## 核心思想

### 基数估计问题

传统方法计算基数需要存储所有元素:
```
问题: 统计网站的独立访客数 (UV)
传统方法: 存储所有访客 ID → 去重 → 计数
内存需求: O(N)，N 为访客数量
```

### HyperLogLog 的解决方案

HyperLogLog 使用概率方法估计基数:
```
核心思想: 观察哈希值的前导零数量
- 哈希值均匀分布
- 前导零越多，基数越大
- 使用多个寄存器取平均值
```

## 算法原理

### 1. 哈希函数

将每个元素映射到均匀分布的哈希值:
```
元素 → 哈希函数 → 64 位哈希值
```

### 2. 分桶

使用前 p 位选择寄存器 (桶):
```
哈希值: [b1 b2 ... bp | bp+1 bp+2 ... b64]
         ↑ 分桶索引 (p 位)    ↑ 前导零计数 (64-p 位)
```

### 3. 前导零计数

计算剩余位的前导零数量:
```
剩余位: 000101... → 前导零 = 3
剩余位: 000001... → 前导零 = 4
```

### 4. 更新寄存器

每个寄存器存储看到的最大前导零数量:
```
register[bucket] = max(register[bucket], leadingZeros)
```

### 5. 基数估计

使用调和平均数计算估计值:
```
E = α * m² * (∑ 2^(-register[i]))^(-1)

其中:
- α: 偏差校正常数
- m: 寄存器数量 (2^p)
- register[i]: 第 i 个寄存器的值
```

## 精度分析

### 理论精度

```
标准误差 (SE) = 1.04 / √m

其中 m = 2^p (寄存器数量)
```

### 精度与资源权衡

| 精度 (p) | 寄存器数 | 内存占用 | 标准误差 |
|----------|----------|----------|----------|
| 4        | 16       | 16 字节  | 26%      |
| 8        | 256      | 256 字节 | 6.5%     |
| 10       | 1024     | 1 KB     | 3.25%    |
| 12       | 4096     | 4 KB     | 1.6%     |
| 14       | 16384    | 16 KB    | 0.8%     |
| 16       | 65536    | 64 KB    | 0.4%     |

## 业界实现对比

| 系统 | 语言 | 精度 | 特点 |
|------|------|------|------|
| Redis | C | p=14 | 内置 HLL 数据结构 |
| Google | C++ | p=16 | 高精度实现 |
| PostgreSQL | C | p=10 | 扩展插件 |
| Presto | Java | p=12 | 分布式查询引擎 |

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

## 与其他算法比较

### Linear Counting

```
适用: 小基数 (m/V > 2.5)
精度: 高
内存: O(m)
公式: E = m * ln(m/V)
```

### LogLog

```
适用: 中等基数
精度: 中等 (1.30/√m)
内存: O(m)
改进: HyperLogLog 使用调和平均数
```

### HyperLogLog

```
适用: 大基数
精度: 高 (1.04/√m)
内存: O(m)
优势: 更好的偏差校正
```

## 参考资料

1. [HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm](https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf)
2. [HyperLogLog in Practice: Algorithmic Engineering of a State of The Art Cardinality Estimation Algorithm](https://research.google/pubs/archive/40671.pdf)
3. [Redis HyperLogLog Documentation](https://redis.io/commands/pfadd)
4. [Wikipedia: HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog)
