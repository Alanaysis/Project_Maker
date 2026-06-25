# 实现细节

## 1. 滑动窗口

### 数据结构
循环缓冲区实现，使用取模运算覆盖旧数据。

### 核心代码
```go
func (sw *SlidingWindow) Add(value float64) {
    sw.buffer[sw.pos] = value
    sw.pos = (sw.pos + 1) % sw.size
    if sw.count < sw.size {
        sw.count++
    }
}
```

## 2. 蓄水池采样

### 算法
对第 i 个元素，以 k/i 的概率替换采样池中的随机一个元素。

### 时间复杂度
O(n)，空间 O(k)

## 3. HyperLogLog

### 算法
使用 FNV-1a 哈希，前 b 位作为桶索引，剩余位计算前导零。

### 偏差修正
- 小基数（< 2.5m）：使用线性计数
- 普通基数：调和平均估计

## 4. Top-K

### 算法
Lossy Counting 简化版，维护 k 个高频项，低频项被淘汰。
