# PageRank 算法实现

## 项目简介

这是一个 PageRank 网页排序算法的学习项目，实现了经典的 PageRank 算法，用于计算网页的重要性排名。

## 核心功能

- **PageRank 算法**：实现迭代法求解 PageRank
- **阻尼因子**：支持可配置的阻尼因子（默认 0.85）
- **稀疏矩阵**：使用 SciPy 稀疏矩阵优化计算
- **多种求解方法**：迭代法、幂迭代法、代数法
- **可视化**：图表展示排名结果和图结构

## 项目结构

```
pagerank/
├── src/
│   ├── __init__.py
│   ├── graph.py          # 网页图数据结构
│   ├── pagerank.py       # PageRank 算法实现
│   └── visualizer.py     # 可视化工具
├── tests/
│   ├── test_graph.py     # 图结构测试
│   └── test_pagerank.py  # 算法测试
├── examples/
│   ├── basic_usage.py    # 基础用法示例
│   └── visualization.py  # 可视化示例
├── docs/                 # 学习文档
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 快速开始

### 安装依赖

```bash
cd projects/pagerank
pip install -r requirements.txt
```

### 基础用法

```python
from src.graph import WebGraph
from src.pagerank import PageRank

# 创建网页图
graph = WebGraph()
graph.add_link("A", "B")
graph.add_link("B", "C")
graph.add_link("C", "A")

# 计算 PageRank
pr = PageRank(damping_factor=0.85)
result = pr.compute(graph)

# 查看结果
for page, score in result.ranked_pages:
    print(f"{page}: {score:.4f}")
```

### 运行示例

```bash
cd projects/pagerank
python examples/basic_usage.py
python examples/visualization.py
```

### 运行测试

```bash
cd projects/pagerank
pytest tests/ -v
```

## 算法原理

### PageRank 公式

```
PR(i) = (1-d)/N + d * Σ(PR(j)/L(j))
```

其中：
- `d`：阻尼因子（通常为 0.85）
- `N`：网页总数
- `L(j)`：页面 j 的出链数
- `PR(j)`：页面 j 的 PageRank 值

### 核心循环

```
网页图 → 迭代计算 → 收敛 → 排序
```

### 求解方法

1. **迭代法**：逐步更新 PageRank 值直到收敛
2. **幂迭代法**：计算 Google 矩阵的主特征向量
3. **代数法**：直接求解线性方程组

## 学习目标

- [x] 理解 PageRank 原理
- [x] 掌握迭代计算
- [x] 学会稀疏矩阵
- [x] 实现可视化结果

## 技术栈

- **Python 3.8+**
- **NumPy**：数值计算
- **SciPy**：稀疏矩阵
- **Matplotlib**：可视化
- **NetworkX**：图结构可视化

## 参考资料

- [PageRank Wikipedia](https://en.wikipedia.org/wiki/PageRank)
- [Original PageRank Paper](http://ilpubs.stanford.edu:8090/422/)
- [Google PageRank Algorithm](https://research.google/pubs/pageank/)
