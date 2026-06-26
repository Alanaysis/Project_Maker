# Vector Database / 向量数据库

> 实现向量数据库，支持近似最近邻搜索 | Implement a vector database with approximate nearest neighbor search

---

## 概述 / Overview

本项目是一个向量数据库学习项目，从零实现核心向量搜索算法。通过对比不同索引结构（暴力搜索、LSH、KD-Tree）的行为，深入理解向量搜索原理和 ANN（近似最近邻）算法的工作机制。

This is a learning project that implements core vector search algorithms from scratch. By comparing different indexing structures (brute-force, LSH, KD-Tree), you gain deep understanding of vector search principles and ANN (Approximate Nearest Neighbor) algorithms.

**核心循环 / Core Loop:**
```
向量插入 → 索引构建 → 查询向量 → ANN 搜索 → 结果返回
Vector insert → Index build → Query vector → ANN search → Results return
```

---

## 学习目标 / Learning Objectives

### 理解向量搜索原理 / Understand Vector Search Principles
- 向量空间模型（Vector Space Model）
- 距离度量（Euclidean, Cosine, Dot Product）
- 相似度与距离的关系

### 掌握 ANN 算法 / Master ANN Algorithms
- **Brute-force KNN**: 暴力搜索，精确但慢
- **LSH (Locality Sensitive Hashing)**: 局部敏感哈希，近似但快
- **KD-Tree**: 空间划分树，低维精确

### 学会索引结构 / Learn Index Structures
- 如何权衡搜索速度与精度
- 维度灾难（Curse of Dimensionality）
- 索引构建 vs 查询时间的 trade-off

---

## 项目结构 / Project Structure

```
vector-db/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── metrics.py           # 向量相似度度量
│   ├── brute_force.py       # 暴力 KNN 搜索
│   ├── lsh.py               # 局部敏感哈希
│   ├── kdtree.py            # KD-Tree 精确搜索
│   └── vector_store.py      # 高层向量存储接口
├── examples/
│   ├── 01_basic_operations.py    # 基本向量操作
│   ├── 02_lsh_vs_brute.py        # LSH vs 暴力搜索对比
│   ├── 03_kdtree_search.py       # KD-Tree 搜索演示
│   └── 04_image_similarity.py    # 图像相似度搜索
├── tests/
│   ├── test_metrics.py
│   ├── test_brute_force.py
│   ├── test_kdtree.py
│   ├── test_lsh.py
│   └── test_vector_store.py
├── requirements.txt
└── README.md
```

---

## 快速开始 / Quick Start

### 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 运行示例 / Run Examples

```bash
# 1. 基本向量操作
python examples/01_basic_operations.py

# 2. LSH vs 暴力搜索对比
python examples/02_lsh_vs_brute.py

# 3. KD-Tree 搜索
python examples/03_kdtree_search.py

# 4. 图像相似度搜索
python examples/04_image_similarity.py
```

### 运行测试 / Run Tests

```bash
pytest tests/ -v
```

---

## ANN 算法详解 / ANN Algorithm Explanations

### 1. Brute-force KNN / 暴力 KNN

**原理**: 将查询向量与数据库中每个向量计算距离，返回最近的 k 个。

**优点**:
- 结果精确（ground truth）
- 实现简单

**缺点**:
- 查询时间 O(n × d)，n 为向量数，d 为维度
- 大规模数据不可行

**适用场景**: 小规模数据、验证其他算法的准确性

### 2. Locality Sensitive Hashing (LSH) / 局部敏感哈希

**原理**: 使用随机投影将向量映射到哈希桶。相似向量更可能落入同一桶。

**核心思想**:
- 传统哈希：相似 → 不同哈希值
- LSH：相似 → 相同哈希值（概率更高）

**参数影响**:
- `num_tables` 越大：精度越高，速度越慢
- `num_projections` 越大：阈值越尖锐，区分度越高

**数学基础**:
- 对于余弦相似度，随机投影的碰撞概率：p = 1 - θ/π
- 其中 θ 是两向量之间的夹角

**适用场景**: 高维向量、大规模数据、对精度要求不极端

### 3. KD-Tree / KD 树

**原理**: 递归地将空间沿方差最大的维度分割，构建二叉搜索树。

**搜索策略**:
1. 沿树向下，找到叶子节点
2. 回溯时，检查兄弟子树是否可能包含更近的点
3. 如果分割平面距离 < 当前最佳距离，搜索兄弟子树

**维度限制**:
- 低维（< 20）：高效
- 高维：性能退化（维度灾难）

**适用场景**: 低维精确搜索、范围查询

---

## 相似度度量 / Similarity Metrics

| 度量 | 公式 | 范围 | 适用场景 |
|------|------|------|----------|
| Euclidean | √Σ(aᵢ-bᵢ)² | [0, ∞) | 几何距离 |
| Cosine | (a·b)/(‖a‖‖b‖) | [-1, 1] | 文本/高维向量 |
| Dot Product | Σ(aᵢ×bᵢ) | (-∞, ∞) | 归一化向量 |

---

## 运行结果示例 / Example Output

运行 `02_lsh_vs_brute.py` 会输出类似以下结果：

```
============================================================
3. LSH vs Brute-Force Comparison
============================================================
Brute-force index: 1000 vectors, dim=128
LSH index: 1000 vectors, dim=128
  Tables: 10, Projections: 20

Running 50 queries...

k      Recall    BF avg (ms)   LSH avg (ms)   Speedup
------------------------------------------------------------
5     0.9500           0.120          0.035      3.43x
10    0.9200           0.135          0.038      3.55x
20    0.8800           0.150          0.042      3.57x
50    0.8200           0.200          0.055      3.64x
```

---

## 扩展阅读 / Further Reading

- [Similarity Estimation from Hash Tables](https://cs.nyu.edu/~mishra/COS/GA/Indyk98Similarity.pdf) - Indyk & Motwani, 1998
- [Multidimensional Binary Search Trees](https://dl.acm.org/doi/10.1145/360248.360256) - Bentley, 1975
- [Mining of Massive Datasets](https://www.mmds.org/) - Leskovec et al., Chapter 3 (LSH), Chapter 6 (KD-Tree)

---

## License

MIT
