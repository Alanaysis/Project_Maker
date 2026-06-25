# 03 - PageRank 实现细节

## 1. 核心算法实现

### 1.1 标准 PageRank (迭代法)

**文件**: `src/pagerank.py`

**关键代码**:

```python
def compute(self, graph: WebGraph, max_iterations: int = 100,
            tolerance: float = 1e-6) -> PageRankResult:
    n = graph.num_pages

    # 构建转移矩阵
    transition = graph.build_transition_matrix()

    # 初始化分数
    scores = np.ones(n) / n

    # 阻尼向量
    damping_vector = np.ones(n) * (1 - self.damping_factor) / n

    for iteration in range(max_iterations):
        # PageRank 公式: PR = (1-d)/N + d * M * PR
        new_scores = damping_vector + self.damping_factor * (transition @ scores)

        # 归一化
        new_scores = new_scores / new_scores.sum()

        # 检查收敛
        diff = np.abs(new_scores - scores).sum()

        if diff < tolerance:
            return PageRankResult(scores=new_scores, ...)

        scores = new_scores

    return PageRankResult(scores=scores, converged=False, ...)
```

**实现要点**:
1. 使用稀疏矩阵存储转移矩阵
2. 每次迭代后归一化确保概率分布
3. 使用 L1 范数检测收敛
4. 支持自定义初始分数

### 1.2 幂迭代法

**实现**:

```python
def compute_power_iteration(self, graph: WebGraph) -> PageRankResult:
    n = graph.num_pages

    # 构建 Google 矩阵: G = d*M + (1-d)/N * E
    transition = graph.build_transition_matrix()
    ones_matrix = sparse.csr_matrix(np.ones((n, n)) / n)
    google_matrix = self.damping_factor * transition + \
                    (1 - self.damping_factor) * ones_matrix

    # 初始化
    scores = np.ones(n) / n

    for iteration in range(max_iterations):
        new_scores = google_matrix @ scores
        new_scores = new_scores / new_scores.sum()
        # ... 收敛检查
```

**特点**:
- 直接计算 Google 矩阵的主特征向量
- 理论上等价于迭代法
- 内存消耗较大（需要存储完整 Google 矩阵）

### 1.3 代数法

**实现**:

```python
def compute_algebraic(self, graph: WebGraph) -> PageRankResult:
    n = graph.num_pages
    transition = graph.build_transition_matrix()

    # 构建线性系统: (I - d*M) * r = (1-d)/N * e
    I = sparse.eye(n)
    A = I - self.damping_factor * transition
    b = np.ones(n) * (1 - self.damping_factor) / n

    # 直接求解
    from scipy.sparse.linalg import spsolve
    scores = spsolve(A.tocsc(), b)
```

**特点**:
- 直接求解线性方程组
- 无需迭代
- 对大规模图效率较低

## 2. 个性化 PageRank 实现

### 2.1 核心逻辑

```python
def compute_personalized(self, graph: WebGraph,
                         personalization_vector: Dict[str, float]) -> PageRankResult:
    n = graph.num_pages

    # 构建个性化向量
    if personalization_vector is None:
        p = np.ones(n) / n  # 均匀分布
    else:
        p = np.zeros(n)
        for name, weight in personalization_vector.items():
            idx = graph.get_page_index(name)
            if idx is not None:
                p[idx] = weight
        p = p / p.sum()  # 归一化

    # 迭代计算
    for iteration in range(max_iterations):
        # PPR 公式: PR = (1-d)*p + d * M * PR
        new_scores = (1 - self.damping_factor) * p + \
                     self.damping_factor * (transition @ scores)
```

### 2.2 向量处理

**问题**: 用户输入的个性化向量可能包含无效页面

**解决方案**:
1. 检查页面是否存在
2. 忽略无效页面
3. 自动归一化

```python
# 处理无效页面
for name, weight in personalization_vector.items():
    if name in name_to_idx:
        p[name_to_idx[name]] = weight

# 检查是否全为零
total = p.sum()
if total > 0:
    p = p / total
else:
    p = np.ones(n) / n  # 回退到均匀分布
```

## 3. Topic-Sensitive PageRank 实现

### 3.1 单主题计算

```python
def compute_topic_sensitive(self, graph: WebGraph,
                            topic_pages: Dict[str, List[str]]) -> Dict[str, PageRankResult]:
    results = {}

    for topic, pages in topic_pages.items():
        # 为每个主题创建个性化向量
        personalization = {page: 1.0 / len(pages) for page in pages}

        # 计算该主题的 PageRank
        result = self.compute_personalized(graph, personalization)
        results[topic] = result

    return results
```

### 3.2 多主题组合

```python
def compute_topic_sensitive_combined(self, graph: WebGraph,
                                     topic_pages: Dict,
                                     topic_weights: Dict) -> PageRankResult:
    # 计算每个主题的 PageRank
    topic_results = self.compute_topic_sensitive(graph, topic_pages, ...)

    # 按权重组合
    combined_scores = np.zeros(n)
    for topic, result in topic_results.items():
        weight = topic_weights.get(topic, 0.0)
        combined_scores += weight * result.scores

    # 归一化
    combined_scores = combined_scores / combined_scores.sum()
```

## 4. 评估模块实现

### 4.1 图结构分析

```python
def analyze_graph(self, graph: WebGraph) -> GraphStatistics:
    n = graph.num_pages
    adj = graph.build_adjacency_matrix()

    # 基本统计
    num_links = adj.nnz
    density = num_links / (n * (n - 1)) if n > 1 else 0.0

    # 度分布
    out_degrees = np.array(adj.sum(axis=1)).flatten()
    avg_out_degree = out_degrees.mean()
    num_dangling_nodes = (out_degrees == 0).sum()

    # 连通分量 (使用 NetworkX)
    import networkx as nx
    G = nx.DiGraph()
    # ... 构建 NetworkX 图
    num_components = nx.number_weakly_connected_components(G)
```

### 4.2 收敛性分析

```python
def analyze_convergence(self, graph: WebGraph) -> ConvergenceAnalysis:
    # 带历史记录的计算
    result = self.pagerank.compute(graph, track_history=True)

    return ConvergenceAnalysis(
        iterations=result.iterations,
        converged=result.converged,
        final_diff=result.final_diff,
        convergence_history=result.convergence_history
    )
```

### 4.3 排序质量评估

```python
def evaluate_ranking_quality(computed, ground_truth, k_values) -> RankingQualityMetrics:
    # Kendall's tau
    concordant, discordant = 0, 0
    for i in range(len(pages)):
        for j in range(i+1, len(pages)):
            # ... 计算一致对和不一致对
    kendall_tau = (concordant - discordant) / total_pairs

    # Spearman's rho
    rank_diffs_squared = sum((computed_rank[p] - truth_rank[p])**2 for p in pages)
    spearman_rho = 1 - 6 * rank_diffs_squared / (n * (n^2 - 1))

    # NDCG
    dcg = sum(relevance / log2(i+2) for i, relevance in enumerate(relevances))
    ndcg = dcg / ideal_dcg
```

## 5. 应用模块实现

### 5.1 网页排名系统

```python
class WebRankingSystem:
    def add_page(self, page: WebPage):
        self.pages[page.url] = page
        self.graph.add_page(page.url)
        for link in page.links:
            self.graph.add_link(page.url, link)

    def compute_personalized_ranking(self, preferred_categories):
        # 构建个性化向量
        personalization = {}
        for url, page in self.pages.items():
            if page.category in preferred_categories:
                personalization[url] = 1.0

        return self.pagerank.compute_personalized(self.graph, personalization)
```

### 5.2 社交网络分析

```python
class SocialNetworkAnalyzer:
    def get_recommendations(self, user_id, max_recommendations):
        # 计算个性化 PageRank
        result = self.pagerank.compute_personalized(
            self.graph,
            personalization_vector={user_id: 1.0}
        )

        # 过滤已关注用户
        following_set = set(self.users[user_id].following)
        recommendations = []
        for page, score in result.ranked_pages:
            if page not in following_set:
                recommendations.append((page, score))

        return recommendations[:max_recommendations]
```

### 5.3 推荐系统

```python
class RecommendationSystem:
    def recommend(self, user_id, num_recommendations, exclude_rated=True):
        # 计算个性化 PageRank
        result = self.pagerank.compute_personalized(
            self.graph,
            personalization_vector={f"user_{user_id}": 1.0}
        )

        # 提取物品推荐
        recommendations = []
        for page, score in result.ranked_pages:
            if page.startswith("item_"):
                item_id = page[5:]
                if item_id not in rated_items:
                    recommendations.append((item_id, score))

        return recommendations
```

## 6. 性能优化

### 6.1 稀疏矩阵

```python
# 使用 CSR 格式
from scipy import sparse

adj = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))

# 矩阵向量乘法
result = adj @ vector  # 高效稀疏运算
```

### 6.2 内存优化

```python
# 避免存储完整 Google 矩阵
# 使用迭代法而不是幂迭代法
new_scores = damping_vector + d * (transition @ scores)
# 而不是
# google_matrix = d * M + (1-d)/N * E  # 内存消耗大
# new_scores = google_matrix @ scores
```

### 6.3 收敛加速

```python
# 使用更好的初始值
if previous_result is not None:
    initial_scores = previous_result.scores
else:
    initial_scores = np.ones(n) / n
```

## 7. 错误处理

### 7.1 输入验证

```python
def __init__(self, damping_factor: float = 0.85):
    if not 0 <= damping_factor <= 1:
        raise ValueError("Damping factor must be between 0 and 1")
```

### 7.2 边界条件

```python
def compute(self, graph: WebGraph, ...) -> PageRankResult:
    n = graph.num_pages
    if n == 0:
        return PageRankResult(scores=np.array([]), ...)

    if initial_scores is not None:
        if len(initial_scores) != n:
            raise ValueError(f"Initial scores length must be {n}")
```

### 7.3 数值稳定性

```python
# 避免除以零
out_degree[dangling_mask] = 1  # 处理悬挂节点

# 归一化确保概率分布
new_scores = new_scores / new_scores.sum()

# 处理负值（代数法）
scores = np.abs(scores)
```

## 8. 测试实现

### 8.1 测试用例结构

```python
class TestPageRank:
    def test_simple_triangle(self):
        """简单环形图测试"""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])
        result = PageRank().compute(graph)
        assert result.converged
        assert abs(result.scores.sum() - 1.0) < 1e-10

    def test_star_graph(self):
        """星形图测试"""
        # ... 验证中心节点排名最高

    def test_convergence_detection(self):
        """收敛检测测试"""
        # ... 验证收敛判定正确
```

### 8.2 测试覆盖

- 基础功能测试
- 边界条件测试
- 异常情况测试
- 性能测试
- 集成测试
