# 02 - PageRank 系统设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    PageRank 系统                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 图模块   │  │ 算法模块 │  │ 评估模块 │  │ 应用模块 │  │
│  │ (graph)  │  │(pagerank)│  │(evaluat) │  │(applic)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层                               │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  NumPy / SciPy   │  │  NetworkX / Matplotlib       │   │
│  └──────────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 主要类 |
|------|------|--------|
| graph.py | 图数据结构管理 | WebGraph |
| pagerank.py | PageRank 算法实现 | PageRank, PageRankResult |
| evaluation.py | 评估与分析 | PageRankEvaluator |
| applications.py | 实际应用 | WebRankingSystem, SocialNetworkAnalyzer, RecommendationSystem |
| visualizer.py | 可视化 | PageRankVisualizer |

## 2. 数据结构设计

### 2.1 WebGraph 类

```python
class WebGraph:
    """
    网页图数据结构

    核心属性:
    - _edges: 边列表
    - _page_names: 页面索引到名称映射
    - _name_to_index: 名称到索引映射
    - _next_index: 下一个可用索引

    核心方法:
    - add_page(): 添加页面
    - add_link(): 添加链接
    - build_adjacency_matrix(): 构建邻接矩阵
    - build_transition_matrix(): 构建转移矩阵
    """
```

**设计决策**:
- 使用邻接表存储边，支持动态添加
- 稀疏矩阵表示，节省内存
- 双向映射，支持按名称或索引访问

### 2.2 PageRankResult 类

```python
@dataclass
class PageRankResult:
    """
    PageRank 计算结果

    属性:
    - scores: PageRank 分数数组
    - iterations: 迭代次数
    - converged: 是否收敛
    - final_diff: 最终差异
    - page_names: 页面名称映射
    - variant: 算法变体类型
    - convergence_history: 收敛历史
    """
```

**设计决策**:
- 使用 dataclass 简化代码
- 包含收敛历史，支持分析
- 支持多种算法变体

## 3. 算法设计

### 3.1 标准 PageRank

**输入**:
- WebGraph 实例
- 阻尼因子 d (默认 0.85)
- 最大迭代次数
- 收敛阈值

**输出**:
- PageRankResult 实例

**算法流程**:

```
1. 构建转移矩阵 M
2. 初始化 PR = [1/N, 1/N, ..., 1/N]
3. 重复:
   a. PR_new = (1-d)/N + d * M * PR
   b. PR_new = PR_new / sum(PR_new)
   c. diff = ||PR_new - PR||_1
   d. 如果 diff < ε，停止
   e. PR = PR_new
4. 返回 PR
```

### 3.2 个性化 PageRank

**扩展**:
- 增加个性化向量 p
- 修改更新公式: PR = (1-d) * p + d * M * PR

**向量归一化**:
- 支持稀疏个性化向量
- 自动归一化为概率分布
- 处理无效页面名称

### 3.3 Topic-Sensitive PageRank

**实现策略**:
1. 为每个主题计算独立的 PPR
2. 按主题权重组合结果
3. 支持单独查询或组合查询

## 4. 接口设计

### 4.1 PageRank 类接口

```python
class PageRank:
    def __init__(self, damping_factor: float = 0.85)

    def compute(self, graph: WebGraph, ...) -> PageRankResult
    def compute_personalized(self, graph: WebGraph, personalization_vector: Dict, ...) -> PageRankResult
    def compute_topic_sensitive(self, graph: WebGraph, topic_pages: Dict, ...) -> Dict[str, PageRankResult]
    def compute_topic_sensitive_combined(self, graph: WebGraph, ...) -> PageRankResult
    def compute_power_iteration(self, graph: WebGraph, ...) -> PageRankResult
    def compute_algebraic(self, graph: WebGraph) -> PageRankResult
    def analyze_convergence(self, graph: WebGraph, ...) -> ConvergenceAnalysis
```

### 4.2 评估模块接口

```python
class PageRankEvaluator:
    def analyze_graph(self, graph: WebGraph) -> GraphStatistics
    def analyze_damping_factor_impact(self, graph: WebGraph, ...) -> DampingFactorAnalysis
    def analyze_convergence(self, graph: WebGraph, ...) -> ConvergenceAnalysis
    def analyze_robustness(self, graph: WebGraph, ...) -> RobustnessAnalysis
    def compare_algorithms(self, graph: WebGraph, ...) -> Dict[str, PageRankResult]
    def sensitivity_analysis(self, graph: WebGraph, ...) -> Dict
```

### 4.3 应用模块接口

```python
class WebRankingSystem:
    def add_page(self, page: WebPage) -> None
    def compute_ranking(self) -> PageRankResult
    def compute_personalized_ranking(self, ...) -> PageRankResult

class SocialNetworkAnalyzer:
    def add_user(self, user: SocialUser) -> None
    def compute_influence_ranking(self) -> PageRankResult
    def get_recommendations(self, user_id: str, ...) -> List[Tuple[str, float]]

class RecommendationSystem:
    def add_interaction(self, user_id: str, item_id: str, rating: float) -> None
    def recommend(self, user_id: str, ...) -> List[Tuple[str, float]]
    def recommend_similar(self, item_id: str, ...) -> List[Tuple[str, float]]
```

## 5. 性能设计

### 5.1 稀疏矩阵优化

- 使用 CSR 格式存储稀疏矩阵
- 矩阵向量乘法优化
- 内存占用: O(nnz) 而非 O(n^2)

### 5.2 收敛加速

- 使用前一次结果作为初始值
- 自适应阻尼因子
- 块迭代法

### 5.3 并行化支持

- 矩阵运算使用 NumPy/SciPy 的并行实现
- 支持分布式计算（扩展）

## 6. 错误处理

### 6.1 输入验证

- 阻尼因子范围检查: 0 ≤ d ≤ 1
- 向量长度匹配检查
- 页面存在性检查

### 6.2 边界条件

- 空图处理
- 单页面图处理
- 悬挂节点处理
- 不连通图处理

### 6.3 异常处理

```python
# 示例
if not 0 <= damping_factor <= 1:
    raise ValueError("Damping factor must be between 0 and 1")

if len(initial_scores) != n:
    raise ValueError(f"Initial scores length must be {n}")
```

## 7. 扩展性设计

### 7.1 新增算法变体

- 继承 PageRank 基类
- 实现 compute 方法
- 注册到算法工厂

### 7.2 新增应用场景

- 继承应用基类
- 实现图构建逻辑
- 复用 PageRank 核心

### 7.3 新增评估指标

- 在 PageRankEvaluator 中添加方法
- 返回标准化的指标类
- 支持自定义指标

## 8. 测试策略

### 8.1 单元测试

- 每个公共方法独立测试
- 边界条件测试
- 异常情况测试

### 8.2 集成测试

- 多模块协作测试
- 端到端流程测试

### 8.3 性能测试

- 大规模图测试
- 收敛速度测试
- 内存使用测试

## 9. 部署考虑

### 9.1 依赖管理

```
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
networkx>=2.6.0
pytest>=6.0.0
```

### 9.2 版本兼容

- Python 3.8+
- NumPy 1.21+
- SciPy 1.7+

### 9.3 安装方式

```bash
pip install -r requirements.txt
```
