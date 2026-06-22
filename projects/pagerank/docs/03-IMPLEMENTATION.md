# PageRank 算法实现文档

## 1. 实现概述

### 1.1 实现目标

实现一个完整的 PageRank 算法，包括：
- 网页图数据结构
- 迭代法计算
- 阻尼因子支持
- 可视化结果

### 1.2 技术栈

- **Python 3.8+**：主语言
- **NumPy**：数值计算
- **SciPy**：稀疏矩阵
- **Matplotlib**：可视化
- **NetworkX**：图结构可视化
- **pytest**：测试框架

## 2. 核心实现

### 2.1 WebGraph 类实现

**文件**：`src/graph.py`

**核心功能**：
1. 管理页面和链接
2. 构建邻接矩阵
3. 构建转移矩阵

**关键实现**：

```python
class WebGraph:
    def __init__(self):
        self._edges: List[Tuple[int, int]] = []
        self._page_names: Dict[int, str] = {}
        self._name_to_index: Dict[str, int] = {}
        self._next_index: int = 0
```

**邻接矩阵构建**：
```python
def build_adjacency_matrix(self) -> sparse.csr_matrix:
    rows = [e[0] for e in self._edges]
    cols = [e[1] for e in self._edges]
    data = np.ones(len(self._edges))

    return sparse.csr_matrix(
        (data, (rows, cols)),
        shape=(self.num_pages, self.num_pages)
    )
```

**转移矩阵构建**：
```python
def build_transition_matrix(self) -> sparse.csr_matrix:
    adj = self.build_adjacency_matrix()

    # 计算每个页面的出链数
    out_degree = np.array(adj.sum(axis=1)).flatten()

    # 处理悬挂节点
    dangling_mask = out_degree == 0
    out_degree[dangling_mask] = 1

    # 创建对角矩阵
    inv_degree = sparse.diags(1.0 / out_degree)

    # 转移矩阵：列归一化
    transition = adj.T @ inv_degree

    # 处理悬挂节点
    dangling_pages = np.where(dangling_mask)[0]
    if len(dangling_pages) > 0:
        dangling_contribution = sparse.csr_matrix(
            (np.ones(len(dangling_pages)),
             (dangling_pages, np.zeros(len(dangling_pages), dtype=int))),
            shape=(self.num_pages, 1)
        ) / self.num_pages
        transition = transition + dangling_contribution

    return transition
```

### 2.2 PageRank 类实现

**文件**：`src/pagerank.py`

**核心功能**：
1. 迭代法计算
2. 幂迭代法计算
3. 代数法计算

**迭代法实现**：
```python
def compute(self, graph: WebGraph, max_iterations: int = 100,
            tolerance: float = 1e-6) -> PageRankResult:
    n = graph.num_pages
    if n == 0:
        return PageRankResult(...)

    # 构建转移矩阵
    transition = graph.build_transition_matrix()

    # 初始化分数
    scores = np.ones(n) / n

    # 阻尼向量
    damping_vector = np.ones(n) * (1 - self.damping_factor) / n

    # 迭代
    converged = False
    for iteration in range(max_iterations):
        # PageRank 公式：PR = (1-d)/N + d * M * PR
        new_scores = damping_vector + self.damping_factor * (transition @ scores)

        # 归一化
        new_scores = new_scores / new_scores.sum()

        # 检查收敛
        diff = np.abs(new_scores - scores).sum()
        if diff < tolerance:
            converged = True
            scores = new_scores
            break

        scores = new_scores

    return PageRankResult(...)
```

**幂迭代法实现**：
```python
def compute_power_iteration(self, graph: WebGraph) -> PageRankResult:
    n = graph.num_pages

    # 构建 Google 矩阵：G = d*M + (1-d)/N * ones
    transition = graph.build_transition_matrix()
    ones_matrix = sparse.ones((n, n)) / n
    google_matrix = self.damping_factor * transition + (1 - self.damping_factor) * ones_matrix

    # 初始化
    scores = np.ones(n) / n

    # 迭代
    for iteration in range(max_iterations):
        new_scores = google_matrix @ scores
        new_scores = new_scores / new_scores.sum()

        # 检查收敛
        diff = np.abs(new_scores - scores).sum()
        if diff < tolerance:
            scores = new_scores
            break

        scores = new_scores

    return PageRankResult(...)
```

**代数法实现**：
```python
def compute_algebraic(self, graph: WebGraph) -> PageRankResult:
    n = graph.num_pages
    transition = graph.build_transition_matrix()

    # 构建线性方程组：(I - d*M) * r = (1-d)/N * ones
    I = sparse.eye(n)
    A = I - self.damping_factor * transition
    b = np.ones(n) * (1 - self.damping_factor) / n

    # 使用稀疏矩阵求解器
    from scipy.sparse.linalg import spsolve
    scores = spsolve(A.tocsc(), b)

    # 归一化
    scores = np.abs(scores)
    scores = scores / scores.sum()

    return PageRankResult(...)
```

### 2.3 PageRankResult 类实现

**文件**：`src/pagerank.py`

**核心功能**：
1. 存储计算结果
2. 提供查询接口

**实现**：
```python
@dataclass
class PageRankResult:
    scores: np.ndarray
    iterations: int
    converged: bool
    final_diff: float
    page_names: Dict[int, str]

    @property
    def ranked_pages(self) -> List[Tuple[str, float]]:
        indices = np.argsort(-self.scores)
        return [
            (self.page_names[i], self.scores[i])
            for i in indices
        ]

    def get_score(self, page_name: str) -> Optional[float]:
        for idx, name in self.page_names.items():
            if name == page_name:
                return self.scores[idx]
        return None
```

### 2.4 PageRankVisualizer 类实现

**文件**：`src/visualizer.py`

**核心功能**：
1. 可视化排名结果
2. 可视化图结构
3. 可视化收敛过程

**排名图表实现**：
```python
@staticmethod
def plot_ranked_pages(result: PageRankResult, top_n: int = 10) -> plt.Figure:
    ranked = result.ranked_pages[:top_n]
    pages = [p[0] for p in ranked]
    scores = [p[1] for p in ranked]

    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(pages))
    bars = ax.barh(y_pos, scores, color=plt.cm.viridis(np.linspace(0, 1, len(pages))))

    ax.set_yticks(y_pos)
    ax.set_yticklabels(pages)
    ax.invert_yaxis()
    ax.set_xlabel('PageRank Score')
    ax.set_title('PageRank Scores')

    plt.tight_layout()
    return fig
```

**图结构可视化实现**：
```python
@staticmethod
def plot_graph(graph: WebGraph, result: Optional[PageRankResult] = None) -> plt.Figure:
    # 构建 NetworkX 图
    G = nx.DiGraph()
    page_names = graph.page_names
    for idx, name in page_names.items():
        G.add_node(name)

    # 添加边
    adj = graph.build_adjacency_matrix()
    rows, cols = adj.nonzero()
    for r, c in zip(rows, cols):
        G.add_edge(page_names[r], page_names[c])

    fig, ax = plt.subplots(figsize=(12, 10))

    # 布局
    pos = nx.spring_layout(G, k=2, iterations=50)

    # 节点大小基于 PageRank
    if result is not None:
        node_sizes = []
        for node in G.nodes():
            score = result.get_score(node)
            if score is not None:
                node_sizes.append(score * 5000)
            else:
                node_sizes.append(100)
    else:
        node_sizes = 300

    # 绘制图
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, alpha=0.8)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', arrows=True, alpha=0.6)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight='bold')

    ax.set_title('Web Graph with PageRank')
    ax.axis('off')

    plt.tight_layout()
    return fig
```

## 3. 测试实现

### 3.1 单元测试

**文件**：`tests/test_graph.py` 和 `tests/test_pagerank.py`

**测试覆盖**：
- 空图
- 单页面
- 简单图（三角形、星形、链式）
- 复杂图
- 边界情况
- 错误情况

**测试示例**：
```python
def test_simple_triangle(self):
    """测试简单三角形图（A->B->C->A）"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    assert result.converged
    assert len(result.scores) == 3

    # 对称循环中，所有页面应该有相同的排名
    assert abs(result.scores[0] - result.scores[1]) < 1e-6
    assert abs(result.scores[1] - result.scores[2]) < 1e-6

    # 分数总和应该为 1
    assert abs(result.scores.sum() - 1.0) < 1e-10
```

### 3.2 集成测试

**测试内容**：
- 不同求解方法的结果一致性
- 大规模图的性能
- 可视化功能

**测试示例**：
```python
def test_power_iteration(self):
    """测试幂迭代法产生相同结果"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result_iterative = pr.compute(graph)
    result_power = pr.compute_power_iteration(graph)

    # 结果应该非常相似
    assert np.allclose(result_iterative.scores, result_power.scores, atol=1e-6)
```

## 4. 示例实现

### 4.1 基础用法示例

**文件**：`examples/basic_usage.py`

**功能**：
- 创建网页图
- 计算 PageRank
- 显示结果
- 比较不同阻尼因子
- 比较不同求解方法

### 4.2 可视化示例

**文件**：`examples/visualization.py`

**功能**：
- 创建样本网页图
- 计算 PageRank
- 生成可视化图表
- 保存图表文件

## 5. 依赖管理

### 5.1 依赖列表

```
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
networkx>=2.6.0
pytest>=6.0.0
```

### 5.2 安装方式

```bash
pip install -r requirements.txt
```

## 6. 运行方式

### 6.1 运行测试

```bash
cd projects/pagerank
pytest tests/ -v
```

### 6.2 运行示例

```bash
cd projects/pagerank
python examples/basic_usage.py
python examples/visualization.py
```

## 7. 代码规范

### 7.1 命名规范

- 类名：PascalCase
- 函数名：snake_case
- 变量名：snake_case
- 常量名：UPPER_SNAKE_CASE

### 7.2 文档规范

- 使用 Google 风格文档字符串
- 包含参数说明和返回值说明
- 包含使用示例

### 7.3 类型注解

- 使用 Python 类型注解
- 使用 typing 模块
- 提供类型提示

## 8. 性能优化

### 8.1 稀疏矩阵

- 使用 CSR 格式
- 避免稠密矩阵运算
- 利用 SciPy 优化

### 8.2 内存优化

- 使用生成器
- 避免不必要的复制
- 及时释放内存

### 8.3 计算优化

- 使用向量化操作
- 避免循环
- 使用 NumPy 内置函数

## 9. 错误处理

### 9.1 输入验证

- 验证阻尼因子范围
- 验证初始向量长度
- 验证图结构有效性

### 9.2 边界情况

- 空图处理
- 单页面处理
- 悬挂节点处理

### 9.3 异常处理

- 捕获并记录异常
- 提供清晰的错误信息
- 优雅降级

## 10. 未来改进

### 10.1 功能扩展

- 支持加权图
- 支持动态图
- 支持分布式计算

### 10.2 性能优化

- GPU 加速
- 并行计算
- 近似算法

### 10.3 可视化增强

- 交互式图表
- 3D 可视化
- 动态可视化
