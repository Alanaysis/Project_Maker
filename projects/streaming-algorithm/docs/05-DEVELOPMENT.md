# 开发手册

## 1. 环境搭建

```bash
cd projects/streaming-algorithm
go version  # 需要 1.21+
```

## 2. 项目结构

```
streaming-algorithm/
├── cmd/streaming-algorithm/  # 主入口
├── internal/                 # 核心库
├── test/                     # 测试
├── examples/                 # 示例
└── docs/                     # 文档
```

## 3. 核心模块

### SlidingWindow
循环缓冲区实现，O(1) 添加，O(k) 平均。

### ReservoirSampler
蓄水池采样算法，O(1) 添加，O(k) 读取。

### HyperLogLog
概率基数估计，O(1) 添加，O(m) 计数。

### TopK
Lossy Counting 简化实现。

## 4. 性能优化

- HyperLogLog 使用位运算加速
- TopK 使用 map 实现 O(1) 更新
- 无锁设计，适合单线程流处理
