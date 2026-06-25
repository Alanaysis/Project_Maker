# 02 - 设计: HyperLogLog 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    HyperLogLog                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    输入层                            ││
│  │   Add([]byte) → Hash → AddHash(uint64)              ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │                    处理层                            ││
│  │   分桶 (p bits) → 前导零计数 → 更新寄存器            ││
│  └─────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────┐│
│  │                    估算层                            ││
│  │   调和平均数 → 小基数校正 → 大基数校正 → 估算值      ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## 组件设计

### 1. HyperLogLog 核心结构

```go
type HyperLogLog struct {
    p         uint8     // 精度参数 (4-16)
    m         uint32    // 寄存器数量 (2^p)
    registers []uint8   // 寄存器数组
    alpha     float64   // 偏差校正常数
}
```

**设计决策**:
- 使用 `uint8` 存储寄存器值 (最大前导零数不超过 64)
- 使用 `uint32` 存储寄存器数量 (最多 65536 个)
- 预计算 `alpha` 常数，避免重复计算

### 2. 哈希函数

```go
func Hash(data []byte) uint64 {
    h := fnv.New64a()
    h.Write(data)
    return h.Sum64()
}
```

**设计决策**:
- 使用 FNV-1a 哈希算法
- 64 位输出，足够分散
- 实现简单，性能好

### 3. 分桶逻辑

```
哈希值 (64 位):
┌────────────────────────────────────────────────────────┐
│ b1 b2 ... bp │ bp+1 bp+2 ... b64                      │
└────────────────────────────────────────────────────────┘
      ↑                    ↑
  分桶索引 (p 位)      前导零计数 (64-p 位)
```

**实现**:
```go
// 分桶索取前 p 位
bucketIdx := hash >> (64 - h.p)

// 剩余位左移，去掉分桶位
remainingBits := hash << h.p

// 计算前导零
leadingZeros := uint8(bits.LeadingZeros64(remainingBits)) + 1
```

### 4. 寄存器更新

```go
// 更新寄存器 (取最大值)
if leadingZeros > h.registers[bucketIdx] {
    h.registers[bucketIdx] = leadingZeros
}
```

**设计决策**:
- 使用最大值而非平均值
- 只能增加，不能减少
- 支持增量更新

### 5. 基数估算

```go
// 调和平均数估算
var sum float64
for _, v := range h.registers {
    sum += 1.0 / float64(uint64(1)<<v)
}
estimate := h.alpha * float64(h.m) * float64(h.m) / sum
```

**校正策略**:

1. **小基数校正** (Linear Counting):
   ```
   当 estimate <= 2.5 * m 时:
   E = m * ln(m / V)
   其中 V = 空寄存器数量
   ```

2. **大基数校正**:
   ```
   当 estimate > 2^32 / 30 时:
   E = -2^32 * ln(1 - E/2^32)
   ```

### 6. 合并操作

```go
func (h *HyperLogLog) Merge(other *HyperLogLog) error {
    // 检查精度是否相同
    if h.p != other.p {
        return fmt.Errorf("precision mismatch")
    }

    // 取每个寄存器的最大值
    for i := uint32(0); i < h.m; i++ {
        if other.registers[i] > h.registers[i] {
            h.registers[i] = other.registers[i]
        }
    }
    return nil
}
```

**设计决策**:
- 要求精度相同才能合并
- 合并是幂等的
- 支持分布式场景

## 数据流设计

### 添加元素流程

```
1. Add([]byte data)
   │
   ├─→ 2. Hash(data) → uint64
   │
   └─→ 3. AddHash(uint64 hash)
           │
           ├─→ 4. bucketIdx = hash >> (64 - p)
           │
           ├─→ 5. remainingBits = hash << p
           │
           ├─→ 6. leadingZeros = LeadingZeros64(remainingBits) + 1
           │
           └─→ 7. registers[bucketIdx] = max(registers[bucketIdx], leadingZeros)
```

### 估算基数流程

```
1. Estimate()
   │
   ├─→ 2. 计算调和平均数
   │       sum = ∑ 2^(-register[i])
   │
   ├─→ 3. 原始估算
   │       E = α * m² / sum
   │
   ├─→ 4. 小基数校正 (如果 E <= 2.5m)
   │       E = m * ln(m / V)
   │
   └─→ 5. 大基数校正 (如果 E > 2^32/30)
           E = -2^32 * ln(1 - E/2^32)
```

### 合并流程

```
1. Merge(other HyperLogLog)
   │
   ├─→ 2. 检查精度是否相同
   │       if h.p != other.p → error
   │
   └─→ 3. 合并寄存器
           for i in 0..m:
               registers[i] = max(registers[i], other.registers[i])
```

## 关键设计决策

### 1. 精度参数范围

选择 p ∈ [4, 16]:
- p < 4: 寄存器太少，精度太低
- p > 16: 内存占用太大，收益递减
- 实践中 p=12 是常用选择 (4KB, 1.6% 误差)

### 2. 哈希函数选择

选择 FNV-1a:
- 实现简单，Go 标准库支持
- 64 位输出，足够分散
- 性能好，适合高频调用

### 3. 寄存器存储

选择 `[]uint8`:
- 每个寄存器 1 字节
- 前导零数量不超过 64，uint8 足够
- 内存占用小

### 4. 偏差校正

使用调和平均数 + Linear Counting:
- 调和平均数比算术平均数更抗离群值
- Linear Counting 对小基数更准确
- 大基数校正避免溢出

## 错误处理策略

| 场景 | 处理 |
|------|------|
| 精度参数无效 | 返回 ErrInvalidPrecision |
| 合并精度不匹配 | 返回 error |
| 哈希函数失败 | 无 (FNV-1a 不会失败) |

## 并发安全

当前实现: 非并发安全

```go
// 使用场景:
// 1. 单线程构建，多线程读取 (只读)
// 2. 使用互斥锁保护 (需要自行实现)

// 未来优化:
// - 使用原子操作更新寄存器
// - 分段锁减少竞争
```

## 内存布局

```
HyperLogLog 内存布局:
┌─────────────────────────────────────┐
│ p (uint8)                          │ 1 字节
│ m (uint32)                         │ 4 字节
│ alpha (float64)                    │ 8 字节
│ registers ([]uint8)                │ m 字节
└─────────────────────────────────────┘

示例 (p=12):
- 固定开销: 13 字节
- 寄存器数组: 4096 字节
- 总计: ~4KB
```
