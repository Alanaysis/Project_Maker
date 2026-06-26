# 外部排序 (External Sorting)

> 实现大文件外部排序算法的学习项目

## English

A learning project implementing the **External Sorting** algorithm for sorting
large files that exceed available memory.

## 中文

一个实现**外部排序**算法的学习项目，用于排序超出可用内存的大文件。

---

## 学习目标 / Learning Objectives

### 核心概念 / Core Concepts

1. **外部排序原理** - Understand External Sorting Principles
   - 为什么需要外部排序 (Why external sorting is needed)
   - 内存与磁盘的权衡 (Memory vs. disk trade-offs)
   - 时间复杂度与 I/O 复杂度的关系 (Time vs. I/O complexity)

2. **多路归并** - Master K-Way Merge
   - 最小堆在归并中的应用 (Min-heap for merge)
   - 归并路数对性能的影响 (Impact of merge degree on performance)
   - 多阶段归并策略 (Multi-stage merge strategies)

3. **I/O 优化** - I/O Optimization
   - 缓冲读取与写入 (Buffered reading and writing)
   - 块大小对性能的影响 (Impact of chunk size on performance)
   - 写合并技术 (Write combining techniques)

### 算法流程 / Algorithm Flow

```
文件分块 → 内存排序 → 多路归并 → 输出
Chunk Split → In-Memory Sort → K-Way Merge → Output
```

---

## 算法详解 / Algorithm Explanation

### 外部排序的两阶段过程 / Two-Phase Process

#### 阶段 1: 生成有序段 (Run Generation)

```
1. 将大文件按大小分割成块 (Split large file into chunks)
2. 每个块在内存中排序 (Sort each chunk in memory)
3. 将排序后的块写入临时文件 (Write sorted chunks to temp files)
```

每个临时文件称为一个 **run**（有序段）。

#### 阶段 2: 多路归并 (K-Way Merge)

```
1. 从每个 run 读取当前最小值 (Read current min from each run)
2. 放入最小堆 (Push to min-heap)
3. 弹出最小值，写入输出 (Pop min, write to output)
4. 从对应 run 读取下一个值 (Read next value from corresponding run)
5. 重复直到所有 run 耗尽 (Repeat until all runs exhausted)
```

### 时间复杂度 / Time Complexity

| 阶段 | 复杂度 | 说明 |
|------|--------|------|
| 分块 | O(n) | 读取所有记录 |
| 内存排序 | O(n log m) | m 为块大小 |
| 归并 | O(n log<sub>k</sub> r) | r 为 runs 数，k 为归并路数 |
| **总计** | **O(n log<sub>k</sub> r)** | |

### 空间复杂度 / Space Complexity

- **O(k + m)**: k 个堆槽位 + 一个块的内存

### I/O 复杂度 / I/O Complexity

- **I/O 次数**: 2n(1 + log<sub>k</sub> r)
  - 2: 每次读/写各计 1
  - n: 记录总数
  - log<sub>k</sub> r: 归并轮数

---

## 项目结构 / Project Structure

```
external-sort/
├── src/
│   ├── __init__.py           # 模块初始化
│   ├── chunk.py              # 文件分块
│   ├── in_memory_sort.py     # 内存排序 (Timsort, QuickSort, MergeSort)
│   ├── k_way_merge.py        # k 路归并 (最小堆实现)
│   ├── external_sort.py      # 外部排序主逻辑
│   ├── memory_management.py  # 内存管理
│   └── io_optimization.py    # I/O 优化
├── examples/
│   ├── example_basic_sort.py      # 基本排序演示
│   ├── example_comparison.py      # 内存排序 vs 外部排序
│   ├── example_benchmark.py       # 性能基准测试
│   └── example_visualize.py       # 可视化排序过程
├── tests/
│   └── test_external_sort.py     # 单元测试
├── data/                         # 测试数据目录
├── README.md
└── requirements.txt
```

---

## 运行示例 / Running Examples

### 1. 基本排序演示

```bash
cd projects/external-sort
python examples/example_basic_sort.py
```

### 2. 内存排序 vs 外部排序对比

```bash
python examples/example_comparison.py
```

### 3. 性能基准测试

```bash
python examples/example_benchmark.py
```

### 4. 可视化排序过程

```bash
python examples/example_visualize.py
```

### 5. 运行测试

```bash
pip install pytest
pytest tests/ -v
```

---

## 复杂度分析 / Complexity Analysis

### 时间复杂度 / Time Complexity

- **外部排序**: O(n log<sub>k</sub> r)，其中 r = n/m，m 为块大小
- **内存排序**: O(n log n)
- **比较**: 当 n >> m 时，外部排序的 log<sub>k</sub> r 远小于内存排序的 log n

### 空间复杂度 / Space Complexity

- **外部排序**: O(k + m)，k 为归并路数，m 为块大小
- **内存排序**: O(n)，需要存储全部数据

### I/O 复杂度 / I/O Complexity

- **外部排序**: 2n(1 + log<sub>k</sub> r) 次 I/O 操作
- **优化**: 增大 k 可减少归并轮数，但受内存限制

---

## 学习资源 / Learning Resources

- 📖 Cormen et al., *Introduction to Algorithms*, Chapter on External Sorting
- 📊 [External Sorting - Wikipedia](https://en.wikipedia.org/wiki/External_sorting)
- 🎥 [K-Way Merge Explained](https://www.youtube.com/watch?v=IUA2miqjGJk)

---

## License

MIT
