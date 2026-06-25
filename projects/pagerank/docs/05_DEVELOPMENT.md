# 05 - PageRank 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip 或 conda
- Git

### 1.2 依赖安装

```bash
cd projects/pagerank
pip install -r requirements.txt
```

**依赖列表**:
```
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
networkx>=2.6.0
pytest>=6.0.0
```

### 1.3 开发工具

- **IDE**: VSCode, PyCharm
- **代码风格**: PEP 8
- **类型检查**: mypy (可选)
- **格式化**: black (可选)

## 2. 项目结构

```
pagerank/
├── src/                    # 源代码
│   ├── __init__.py         # 模块导出
│   ├── graph.py            # 图数据结构
│   ├── pagerank.py         # PageRank 算法
│   ├── evaluation.py       # 评估模块
│   ├── applications.py     # 应用模块
│   └── visualizer.py       # 可视化
├── tests/                  # 测试代码
│   ├── test_graph.py
│   ├── test_pagerank.py
│   └── test_advanced.py
├── examples/               # 示例代码
│   ├── personalized_pagerank.py
│   ├── topic_sensitive_pagerank.py
│   ├── web_ranking.py
│   ├── social_network.py
│   └── recommendation_system.py
├── docs/                   # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_DESIGN.md
│   ├── 03_IMPLEMENTATION.md
│   ├── 04_TESTING.md
│   └── 05_DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
├── requirements.txt
└── .gitignore
```

## 3. 核心模块

### 3.1 graph.py - 图数据结构

**职责**: 管理网页图结构

**类**:
- `WebGraph`: 网页图

**方法**:
- `add_page(name)`: 添加页面
- `add_link(from_page, to_page)`: 添加链接
- `build_adjacency_matrix()`: 构建邻接矩阵
- `build_transition_matrix()`: 构建转移矩阵

**使用示例**:
```python
from src.graph import WebGraph

graph = WebGraph()
graph.add_link("A", "B")
graph.add_link("B", "C")

adj = graph.build_adjacency_matrix()
```

### 3.2 pagerank.py - PageRank 算法

**职责**: 实现 PageRank 算法变体

**类**:
- `PageRank`: PageRank 计算器
- `PageRankResult`: 结果容器
- `ConvergenceAnalysis`: 收敛分析
- `RankingQualityMetrics`: 排序质量指标

**算法**:
- `compute()`: 标准 PageRank
- `compute_personalized()`: 个性化 PageRank
- `compute_topic_sensitive()`: Topic-Sensitive PageRank
- `compute_power_iteration()`: 幂迭代法
- `compute_algebraic()`: 代数法

**使用示例**:
```python
from src.pagerank import PageRank

pr = PageRank(damping_factor=0.85)
result = pr.compute(graph)

for page, score in result.ranked_pages:
    print(f"{page}: {score:.4f}")
```

### 3.3 evaluation.py - 评估模块

**职责**: 评估 PageRank 算法性能

**类**:
- `PageRankEvaluator`: 评估器
- `GraphStatistics`: 图统计
- `DampingFactorAnalysis`: 阻尼因子分析
- `RobustnessAnalysis`: 鲁棒性分析

**方法**:
- `analyze_graph()`: 图结构分析
- `analyze_convergence()`: 收敛性分析
- `analyze_damping_factor_impact()`: 阻尼因子影响
- `analyze_robustness()`: 鲁棒性分析
- `compare_algorithms()`: 算法比较
- `sensitivity_analysis()`: 敏感性分析

**使用示例**:
```python
from src.evaluation import PageRankEvaluator

evaluator = PageRankEvaluator(damping_factor=0.85)
stats = evaluator.analyze_graph(graph)
print(stats)
```

### 3.4 applications.py - 应用模块

**职责**: 实际应用场景

**类**:
- `WebRankingSystem`: 网页排名系统
- `SocialNetworkAnalyzer`: 社交网络分析器
- `RecommendationSystem`: 推荐系统

**使用示例**:
```python
from src.applications import WebRankingSystem, WebPage

system = WebRankingSystem()
system.add_page(WebPage(url="example.com", title="Example", content="", links=[]))
result = system.compute_ranking()
```

## 4. 开发流程

### 4.1 新增功能

1. **创建分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码**
   - 遵循 PEP 8
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
   ```python
   def test_new_feature():
       # 测试代码
       pass
   ```

4. **运行测试**
   ```bash
   pytest tests/ -v
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **创建 Pull Request**

### 4.2 修复 Bug

1. **重现 Bug**
   ```bash
   pytest tests/test_bug.py -v
   ```

2. **修复代码**

3. **添加回归测试**

4. **验证修复**
   ```bash
   pytest tests/ -v
   ```

### 4.3 代码审查

**检查清单**:
- [ ] 代码风格符合 PEP 8
- [ ] 有完整的文档字符串
- [ ] 有类型注解
- [ ] 有充分的测试
- [ ] 测试全部通过
- [ ] 没有引入新依赖
- [ ] 性能没有明显下降

## 5. 编码规范

### 5.1 命名规范

```python
# 类名: PascalCase
class PageRank:
    pass

# 函数名: snake_case
def compute_pagerank():
    pass

# 变量名: snake_case
damping_factor = 0.85

# 常量: UPPER_SNAKE_CASE
DEFAULT_DAMPING_FACTOR = 0.85
```

### 5.2 文档字符串

```python
def compute(self, graph: WebGraph, max_iterations: int = 100) -> PageRankResult:
    """
    Compute PageRank scores for a web graph.

    Args:
        graph: WebGraph instance
        max_iterations: Maximum number of iterations

    Returns:
        PageRankResult with computed scores

    Raises:
        ValueError: If graph is invalid

    Example:
        >>> pr = PageRank()
        >>> result = pr.compute(graph)
        >>> print(result.ranked_pages)
    """
    pass
```

### 5.3 类型注解

```python
from typing import Dict, List, Optional, Tuple

def compute_personalized(
    self,
    graph: WebGraph,
    personalization_vector: Optional[Dict[str, float]] = None,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> PageRankResult:
    pass
```

### 5.4 错误处理

```python
def __init__(self, damping_factor: float = 0.85):
    if not 0 <= damping_factor <= 1:
        raise ValueError("Damping factor must be between 0 and 1")
    self.damping_factor = damping_factor
```

## 6. 测试规范

### 6.1 测试文件命名

```
test_<module>.py
```

### 6.2 测试类命名

```python
class Test<ClassName>:
    pass
```

### 6.3 测试方法命名

```python
def test_<功能>_<场景>():
    pass
```

### 6.4 测试结构

```python
def test_example():
    # Arrange - 准备
    graph = WebGraph.from_edges([("A", "B")])

    # Act - 执行
    result = PageRank().compute(graph)

    # Assert - 断言
    assert result.converged
    assert abs(result.scores.sum() - 1.0) < 1e-10
```

## 7. 性能优化

### 7.1 稀疏矩阵

```python
from scipy import sparse

# 使用 CSR 格式
adj = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))

# 矩阵向量乘法
result = adj @ vector
```

### 7.2 内存优化

```python
# 避免存储完整矩阵
# 使用迭代法而不是幂迭代法
new_scores = damping_vector + d * (transition @ scores)
```

### 7.3 收敛加速

```python
# 使用更好的初始值
if previous_result is not None:
    initial_scores = previous_result.scores
```

## 8. 扩展指南

### 8.1 新增算法变体

1. 在 `pagerank.py` 中添加新方法
2. 更新 `PageRankVariant` 枚举
3. 添加测试用例
4. 更新文档

**示例**:
```python
def compute_weighted(self, graph: WebGraph, weights: Dict) -> PageRankResult:
    """实现加权 PageRank"""
    pass
```

### 8.2 新增应用场景

1. 在 `applications.py` 中添加新类
2. 实现图构建逻辑
3. 复用 PageRank 核心
4. 添加测试用例

**示例**:
```python
class CitationNetworkAnalyzer:
    """引文网络分析器"""
    def __init__(self, damping_factor: float = 0.85):
        self.pagerank = PageRank(damping_factor=damping_factor)
        self.graph = WebGraph()

    def add_paper(self, paper_id: str, references: List[str]):
        for ref in references:
            self.graph.add_link(paper_id, ref)

    def compute_impact(self) -> PageRankResult:
        return self.pagerank.compute(self.graph)
```

### 8.3 新增评估指标

1. 在 `evaluation.py` 中添加新方法
2. 返回标准化的指标类
3. 添加测试用例

**示例**:
```python
def analyze_stability(self, graph: WebGraph) -> StabilityAnalysis:
    """分析 PageRank 稳定性"""
    pass
```

## 9. 部署发布

### 9.1 版本管理

使用语义化版本号:
- **主版本号**: 不兼容的 API 变更
- **次版本号**: 向后兼容的功能新增
- **修订号**: 向后兼容的问题修复

### 9.2 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 运行所有测试
4. 创建 Git 标签
5. 发布到 PyPI (可选)

### 9.3 文档更新

- 更新 README.md
- 更新 API 文档
- 更新示例代码

## 10. 故障排除

### 10.1 常见问题

**问题**: 导入错误
```python
ModuleNotFoundError: No module named 'src'
```

**解决**:
```python
import sys
sys.path.insert(0, '/path/to/pagerank')
```

**问题**: NumPy 版本不兼容

**解决**:
```bash
pip install numpy>=1.21.0
```

**问题**: 测试失败

**解决**:
```bash
pytest tests/ -v --tb=long
```

### 10.2 调试技巧

```python
# 打印中间结果
print(f"Scores: {result.scores}")
print(f"Converged: {result.converged}")

# 使用 pdb
import pdb; pdb.set_trace()

# 使用 logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 11. 参考资源

### 11.1 算法参考

- [PageRank Wikipedia](https://en.wikipedia.org/wiki/PageRank)
- [Original Paper](http://ilpubs.stanford.edu:8090/422/)

### 11.2 Python 参考

- [NumPy Documentation](https://numpy.org/doc/)
- [SciPy Documentation](https://docs.scipy.org/doc/)
- [NetworkX Documentation](https://networkx.org/documentation/)

### 11.3 开发工具

- [pytest Documentation](https://docs.pytest.org/)
- [black Formatter](https://github.com/psf/black)
- [mypy Type Checker](https://mypy-lang.org/)
