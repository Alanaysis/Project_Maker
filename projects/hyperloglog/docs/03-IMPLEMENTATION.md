# 03 - 实现: HyperLogLog 核心实现

## 实现顺序

1. Hash 函数 → 2. HyperLogLog 核心 → 3. 基数估算 → 4. 合并操作 → 5. 辅助功能

## 1. Hash 函数实现

### 核心代码

```go
package hyperloglog

import (
    "hash/fnv"
)

// Hash computes a 64-bit hash using FNV-1a algorithm.
func Hash(data []byte) uint64 {
    h := fnv.New64a()
    h.Write(data)
    return h.Sum64()
}

// HashString is a convenience function for hashing strings.
func HashString(s string) uint64 {
    return Hash([]byte(s))
}
```

**实现要点**:
- 使用 FNV-1a 算法，Go 标准库支持
- 64 位输出，足够分散
- 简单高效，适合高频调用

## 2. HyperLogLog 核心实现

### 创建实例

```go
func New(p uint8) (*HyperLogLog, error) {
    if p < 4 || p > 16 {
        return nil, ErrInvalidPrecision
    }

    m := uint32(1) << p
    alpha := calculateAlpha(m)

    return &HyperLogLog{
        p:         p,
        m:         m,
        registers: make([]uint8, m),
        alpha:     alpha,
    }, nil
}
```

**实现要点**:
- 验证精度参数范围
- 预计算 alpha 常数
- 分配寄存器数组

### 偏差校正常数

```go
func calculateAlpha(m uint32) float64 {
    switch m {
    case 16:
        return 0.673
    case 32:
        return 0.697
    case 64:
        return 0.709
    default:
        return 0.7213 / (1.0 + 1.079/float64(m))
    }
}
```

**实现要点**:
- 不同寄存器数量使用不同的 alpha 值
- 小 m 值使用经验常数
- 大 m 值使用公式计算

### 添加元素

```go
func (h *HyperLogLog) Add(data []byte) {
    hash := Hash(data)
    h.AddHash(hash)
}

func (h *HyperLogLog) AddHash(hash uint64) {
    // 分桶索取前 p 位
    bucketIdx := hash >> (64 - h.p)

    // 剩余位左移，去掉分桶位
    remainingBits := hash << h.p

    // 计算前导零 (加 1 避免 log(0))
    leadingZeros := uint8(bits.LeadingZeros64(remainingBits)) + 1

    // 更新寄存器 (取最大值)
    if leadingZeros > h.registers[bucketIdx] {
        h.registers[bucketIdx] = leadingZeros
    }
}
```

**实现要点**:
- 使用位运算提取分桶索引
- 使用 `bits.LeadingZeros64` 计算前导零
- 只更新最大值，保证单调性

## 3. 基数估算实现

### 核心估算

```go
func (h *HyperLogLog) Estimate() uint64 {
    // 计算调和平均数
    var sum float64
    for _, v := range h.registers {
        sum += 1.0 / float64(uint64(1)<<v)
    }

    // 原始估算
    estimate := h.alpha * float64(h.m) * float64(h.m) / sum

    // 小基数校正 (Linear Counting)
    if estimate <= 2.5*float64(h.m) {
        var emptyRegisters uint32
        for _, v := range h.registers {
            if v == 0 {
                emptyRegisters++
            }
        }
        if emptyRegisters > 0 {
            return uint64(float64(h.m) * math.Log(float64(h.m)/float64(emptyRegisters)))
        }
    }

    // 大基数校正
    if estimate > 143165576.5 { // 2^32 / 30
        estimate = -math.Pow(2, 32) * math.Log(1-estimate/math.Pow(2, 32))
    }

    return uint64(estimate)
}
```

**实现要点**:
- 使用调和平均数而非算术平均数
- 小基数使用 Linear Counting 更准确
- 大基数校正避免浮点溢出

### 为什么使用调和平均数?

```
算术平均数: (a + b + c) / 3
调和平均数: 3 / (1/a + 1/b + 1/c)

调和平均数的优势:
- 对离群值不敏感
- 更适合倒数关系的数据
- HyperLogLog 的估计基于 2^(-register)
```

## 4. 合并操作实现

```go
func (h *HyperLogLog) Merge(other *HyperLogLog) error {
    if h.p != other.p {
        return fmt.Errorf("cannot merge HyperLogLog with different precision: %d vs %d", h.p, other.p)
    }

    for i := uint32(0); i < h.m; i++ {
        if other.registers[i] > h.registers[i] {
            h.registers[i] = other.registers[i]
        }
    }

    return nil
}
```

**实现要点**:
- 验证精度参数相同
- 逐寄存器取最大值
- 合并是幂等的

### 合并的应用场景

```
分布式场景:
1. 多个节点各自统计
2. 定期合并结果
3. 获得全局估算

示例:
节点 A: 统计用户 1-1000
节点 B: 统计用户 500-1500
合并后: 估算用户 1-1500 的基数
```

## 5. 辅助功能实现

### 重置

```go
func (h *HyperLogLog) Reset() {
    for i := range h.registers {
        h.registers[i] = 0
    }
}
```

### 统计信息

```go
func (h *HyperLogLog) GetRegisterStats() RegisterStats {
    var min, max uint8
    var sum uint64
    var empty, nonEmpty uint32

    min = 255
    for _, v := range h.registers {
        if v < min {
            min = v
        }
        if v > max {
            max = v
        }
        sum += uint64(v)
        if v == 0 {
            empty++
        } else {
            nonEmpty++
        }
    }

    return RegisterStats{
        Min:      min,
        Max:      max,
        Average:  float64(sum) / float64(h.m),
        Empty:    empty,
        NonEmpty: nonEmpty,
    }
}
```

## 关键技术点

### 1. 位运算技巧

```go
// 提取前 p 位 (分桶索引)
bucketIdx := hash >> (64 - p)

// 去掉前 p 位
remainingBits := hash << p

// 计算前导零
leadingZeros := bits.LeadingZeros64(remainingBits) + 1
```

### 2. 前导零计数

```go
// Go 标准库提供了高效的前导零计数
import "math/bits"

// 使用 CPU 指令 (如果可用)
leadingZeros := bits.LeadingZeros64(x)
```

### 3. 浮点精度

```go
// 使用 float64 进行计算
// 避免整数溢出
// 注意大基数校正的阈值
```

## 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| hash.go | ~20 | 哈希函数 |
| hyperloglog.go | ~250 | 核心算法 |
| **总计** | **~270** | |

## 性能优化

### 1. 内存对齐

```go
// 寄存器数组连续存储
// 利用 CPU 缓存行
// 减少内存分配
```

### 2. 位运算优化

```go
// 使用位运算代替乘除
// 使用 CPU 指令计算前导零
// 避免不必要的类型转换
```

### 3. 预计算

```go
// 预计算 alpha 常数
// 预计算寄存器数量
// 避免重复计算
```
