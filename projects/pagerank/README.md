# PageRank 算法学习项目

## 项目简介 / Project Description

本项目实现 PageRank 网页排序算法及其变体，用于理解网页重要性的计算原理。

This project implements the PageRank web ranking algorithm and its variants to understand how webpage importance is computed.

## 学习目标 / Learning Objectives

### 核心目标 / Core Goals
- **理解 PageRank 原理**: 掌握 PageRank 的数学推导和直观理解
- **掌握迭代计算**: 学习幂迭代法 (Power Iteration) 的实现
- **学会稀疏矩阵**: 使用稀疏矩阵优化大规模图计算

### 进阶目标 / Advanced Goals
- 实现阻尼因子 (Damping Factor) 处理
- 实现个性化 PageRank (Personalized PageRank)
- 实现 HITS 算法 (Hub/Authority) 作为扩展

## 算法原理 / Algorithm Principle

PageRank 的核心思想：一个网页的重要性取决于指向它的其他网页的重要性。

The core idea of PageRank: A webpage's importance depends on the importance of pages that link to it.

### PageRank 公式

```
PR(p_i) = (1-d)/N + d * sum(PR(p_j)/L(p_j)) for all p_j linking to p_i
```

其中：
- `d`: 阻尼因子 (damping factor)，通常取 0.85
- `N`: 网页总数
- `L(p_j)`: 页面 p_j 的外链数量
- `p_j -> p_i`: p_j 指向 p_i 的链接

### 矩阵形式

```
PR = (1-d)/N * 1 + d * M^T * PR
```

其中 M 是转移矩阵 (transition matrix)。

## 项目结构 / Project Structure

```
pagerank/
├── src/                    # 源代码 / Source code
│   ├── __init__.py
│   ├── graph.py            # 图表示 (Graph representation)
│   ├── pagerank.py         # PageRank 核心算法
│   ├── sparse_utils.py     # 稀疏矩阵工具
│   └── hits.py             # HITS 算法
├── examples/               # 示例脚本 / Examples
│   ├── simple_pagerank.py
│   ├── large_scale.py
│   ├── personalized_pagerank.py
│   └── convergence_viz.py
├── tests/                  # 单元测试 / Unit tests
│   ├── __init__.py
│   └── test_pagerank.py
├── requirements.txt
└── README.md
```

## 运行示例 / Run Examples

```bash
# 安装依赖 / Install dependencies
pip install -r requirements.txt

# 运行简单 PageRank 示例
python -m examples.simple_pagerank

# 运行大规模图模拟
python -m examples.large_scale

# 运行个性化 PageRank
python -m examples.personalized_pagerank

# 运行收敛可视化
python -m examples.convergence_viz
```

## 算法推导 / Algorithm Derivation

### 从随机游走到 PageRank

1. 将网页图建模为有向图 G = (V, E)
2. 定义转移矩阵 M，其中 M_ij = 1/L(i) 如果 j 指向 i
3. PageRank 是 M^T 的主特征向量
4. 通过幂迭代法求解

### 阻尼因子 (Damping Factor)

阻尼因子 d 模拟用户随机点击的概率：
- 以概率 d 继续点击链接
- 以概率 (1-d) 随机跳转到任意页面

### 悬垂节点 (Dangling Nodes)

没有外链的页面会"泄漏" PageRank 值，需要特别处理。

## License: MIT
