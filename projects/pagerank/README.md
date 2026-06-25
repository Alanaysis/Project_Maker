# PageRank 算法实现

## 项目简介

这是一个完整的 PageRank 网页排序算法实现项目，包含标准 PageRank、个性化 PageRank、Topic-Sensitive PageRank 等多种变体，以及评估模块和实际应用场景。

## 核心功能

### 1. PageRank 算法变体
- **标准 PageRank**: 经典幂迭代法，支持阻尼因子配置
- **个性化 PageRank (PPR)**: 基于偏好向量的个性化排名
- **Topic-Sensitive PageRank**: 基于主题的敏感排名

### 2. 求解方法
- **迭代法**: 逐步更新直到收敛
- **幂迭代法**: 计算 Google 矩阵主特征向量
- **代数法**: 直接求解线性方程组

### 3. 评估模块
- **收敛性分析**: 迭代次数、收敛历史、谱半径估计
- **排序质量**: Kendall's tau、Spearman's rho、NDCG
- **图结构分析**: 度分布、密度、连通分量
- **敏感性分析**: 阻尼因子影响、鲁棒性测试

### 4. 实际应用
- **网页排名**: WebRankingSystem 类
- **社交网络分析**: SocialNetworkAnalyzer 类
- **推荐系统**: RecommendationSystem 类

## 项目结构

```
pagerank/
├── src/
│   ├── __init__.py           # 模块导出
│   ├── graph.py              # 网页图数据结构
│   ├── pagerank.py           # PageRank 算法实现
│   ├── evaluation.py         # 评估模块
│   ├── applications.py       # 应用模块
│   └── visualizer.py         # 可视化工具
├── tests/
│   ├── test_graph.py         # 图结构测试
│   ├── test_pagerank.py      # 基础算法测试
│   └── test_advanced.py      # 高级功能测试
├── examples/
│   ├── personalized_pagerank.py    # 个性化 PageRank 示例
│   ├── topic_sensitive_pagerank.py # Topic-Sensitive 示例
│   ├── web_ranking.py              # 网页排名应用
│   ├── social_network.py           # 社交网络分析
│   └── recommendation_system.py    # 推荐系统
├── docs/                     # 学习文档
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
graph = WebGraph.from_edges([
    ("A", "B"), ("B", "C"), ("C", "A"), ("D", "C")
])

# 标准 PageRank
pr = PageRank(damping_factor=0.85)
result = pr.compute(graph)

for page, score in result.ranked_pages:
    print(f"{page}: {score:.4f}")
```

### 个性化 PageRank

```python
# 用户偏好科技内容
personalization = {"Tech": 0.5, "Science": 0.3, "Blog": 0.2}
result = pr.compute_personalized(graph, personalization_vector=personalization)
```

### Topic-Sensitive PageRank

```python
topics = {
    "News": ["CNN", "BBC", "Reuters"],
    "Tech": ["TechCrunch", "Wired"]
}
result = pr.compute_topic_sensitive_combined(graph, topic_pages=topics)
```

### 运行示例

```bash
python examples/personalized_pagerank.py
python examples/topic_sensitive_pagerank.py
python examples/web_ranking.py
python examples/social_network.py
python examples/recommendation_system.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 算法原理

### 标准 PageRank 公式

```
PR(i) = (1-d)/N + d * Σ(PR(j)/L(j))
```

### 个性化 PageRank 公式

```
PR(i) = (1-d) * p(i) + d * Σ(PR(j)/L(j))
```

其中 `p(i)` 是个性化偏好概率分布。

### Topic-Sensitive PageRank

为每个主题计算独立的 PageRank 向量，然后按主题权重组合：

```
PR_combined = Σ(w_t * PR_t)
```

## API 参考

### PageRank 类

| 方法 | 说明 |
|------|------|
| `compute(graph)` | 标准 PageRank |
| `compute_personalized(graph, personalization_vector)` | 个性化 PageRank |
| `compute_topic_sensitive(graph, topic_pages)` | Topic-Sensitive PageRank |
| `compute_topic_sensitive_combined(graph, topic_pages)` | 组合 Topic-Sensitive PageRank |
| `compute_power_iteration(graph)` | 幂迭代法 |
| `compute_algebraic(graph)` | 代数法 |
| `analyze_convergence(graph)` | 收敛性分析 |

### 评估模块

| 类 | 说明 |
|----|------|
| `PageRankEvaluator` | 评估器，提供图分析、收敛分析、鲁棒性分析 |
| `GraphStatistics` | 图结构统计 |
| `ConvergenceAnalysis` | 收敛性分析结果 |
| `RankingQualityMetrics` | 排序质量指标 |

### 应用模块

| 类 | 说明 |
|----|------|
| `WebRankingSystem` | 网页排名系统 |
| `SocialNetworkAnalyzer` | 社交网络分析器 |
| `RecommendationSystem` | 推荐系统 |

## 技术栈

- **Python 3.8+**
- **NumPy**: 数值计算
- **SciPy**: 稀疏矩阵
- **Matplotlib**: 可视化
- **NetworkX**: 图结构分析

## 测试覆盖

- 62 个测试用例
- 覆盖所有核心功能
- 包含边界条件测试

## 参考资料

- [PageRank Wikipedia](https://en.wikipedia.org/wiki/PageRank)
- [Original PageRank Paper](http://ilpubs.stanford.edu:8090/422/)
- [Topic-Sensitive PageRank](http://ilpubs.stanford.edu:8090/854/)
- [Personalized PageRank](https://en.wikipedia.org/wiki/Personalized_PageRank)
