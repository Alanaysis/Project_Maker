# PageRank 算法设计文档

## 1. 架构设计

### 1.1 模块划分

```
pagerank/
├── src/
│   ├── graph.py          # 网页图数据结构
│   ├── pagerank.py       # PageRank 算法实现
│   └── visualizer.py     # 可视化工具
├── tests/
│   ├── test_graph.py     # 图结构测试
│   └── test_pagerank.py  # 算法测试
└── examples/
    ├── basic_usage.py    # 基础用法示例
    └── visualization.py  # 可视化示例
```

### 1.2 类设计

**WebGraph 类**：
- 管理页面和链接
- 构建邻接矩阵
- 构建转移矩阵

**PageRank 类**：
- 实现迭代法计算
- 实现幂迭代法计算
- 实现代数法计算

**PageRankResult 类**：
- 存储计算结果
- 提供查询接口

**PageRankVisualizer 类**：
- 可视化排名结果
- 可视化图结构
- 可视化收敛过程

### 1.3 数据流

```
输入：网页链接关系
    ↓
WebGraph：构建图结构
    ↓
PageRank：计算 PageRank
    ↓
PageRankResult：存储结果
    ↓
PageRankVisualizer：可视化
    ↓
输出：排名结果和图表
```

## 2. 接口设计

### 2.1 WebGraph 接口

```python
class WebGraph:
    def add_page(self, name: str) -> int
    def add_link(self, from_page: str, to_page: str) -> None
    def build_adjacency_matrix(self) -> sparse.csr_matrix
    def build_transition_matrix(self) -> sparse.csr_matrix
    def get_outgoing_links(self, page: str) -> List[str]
    def get_incoming_links(self, page: str) -> List[str]
```

### 2.2 PageRank 接口

```python
class PageRank:
    def __init__(self, damping_factor: float = 0.85)
    def compute(self, graph: WebGraph, max_iterations: int = 100,
                tolerance: float = 1e-6) -> PageRankResult
    def compute_power_iteration(self, graph: WebGraph) -> PageRankResult
    def compute_algebraic(self, graph: WebGraph) -> PageRankResult
```

### 2.3 PageRankResult 接口

```python
class PageRankResult:
    scores: np.ndarray
    iterations: int
    converged: bool
    final_diff: float
    page_names: Dict[int, str]

    @property
    def ranked_pages(self) -> List[Tuple[str, float]]
    def get_score(self, page_name: str) -> Optional[float]
```

## 3. 数据结构设计

### 3.1 图存储

**存储方式**：
- 页面：字典映射（名称 -> 索引）
- 链接：列表存储（from_idx, to_idx）
- 矩阵：稀疏矩阵

**优点**：
- 内存效率高
- 查询速度快
- 易于构建矩阵

### 3.2 稀疏矩阵

**选择**：
- CSR（Compressed Sparse Row）：按行压缩
- 适合矩阵向量乘法
- 内存效率高

**实现**：
```python
adj = sparse.csr_matrix(
    (data, (rows, cols)),
    shape=(num_pages, num_pages)
)
```

### 3.3 PageRank 向量

**存储**：
- NumPy 一维数组
- 长度等于页面数量
- 值为 PageRank 分数

**操作**：
- 矩阵向量乘法
- 归一化
- 收敛检查

## 4. 算法设计

### 4.1 迭代法

**步骤**：
1. 初始化：PR = 1/N * ones
2. 迭代：PR_new = (1-d)/N * ones + d * M * PR
3. 归一化：PR = PR / sum(PR)
4. 检查收敛：||PR_new - PR|| < tolerance

**收敛条件**：
- L1 范数小于阈值
- 达到最大迭代次数

### 4.2 幂迭代法

**步骤**：
1. 构建 Google 矩阵：G = d * M + (1-d)/N * ones
2. 初始化：PR = 1/N * ones
3. 迭代：PR = G * PR
4. 归一化：PR = PR / sum(PR)

**优点**：
- 数学形式简洁
- 易于理解

### 4.3 代数法

**步骤**：
1. 构建线性方程组：(I - d * M) * PR = (1-d)/N * e
2. 使用稀疏矩阵求解器求解

**优点**：
- 直接求解
- 精确解

## 5. 错误处理设计

### 5.1 输入验证

**验证点**：
- 阻尼因子在 [0, 1] 范围内
- 初始向量长度正确
- 图结构有效

**处理方式**：
- 抛出 ValueError
- 提供清晰的错误信息

### 5.2 边界情况

**处理情况**：
- 空图：返回空结果
- 单页面：返回 1.0
- 悬挂节点：均匀分配

### 5.3 收敛失败

**处理方式**：
- 检查最大迭代次数
- 返回当前结果
- 标记未收敛状态

## 6. 性能设计

### 6.1 时间复杂度

**迭代法**：O(E * k)
- E：边数
- k：迭代次数

**幂迭代法**：O(V^2 * k)
- V：顶点数
- k：迭代次数

**代数法**：O(V^3)
- V：顶点数

### 6.2 空间复杂度

**迭代法**：O(V + E)
- V：顶点数
- E：边数

**幂迭代法**：O(V^2)
- V：顶点数

**代数法**：O(V^2)
- V：顶点数

### 6.3 优化策略

**稀疏矩阵**：
- 使用 CSR 格式
- 避免稠密矩阵运算
- 利用 SciPy 优化

**收敛加速**：
- 良好的初始值
- 合理的阈值
- 高效的求解方法

## 7. 测试设计

### 7.1 单元测试

**测试覆盖**：
- WebGraph 类
- PageRank 类
- PageRankResult 类

**测试场景**：
- 正常情况
- 边界情况
- 错误情况

### 7.2 集成测试

**测试内容**：
- 不同求解方法的一致性
- 大规模图的性能
- 可视化功能

### 7.3 性能测试

**测试指标**：
- 计算时间
- 内存使用
- 收敛速度

## 8. 可视化设计

### 8.1 排名图表

**类型**：水平条形图
**元素**：
- 页面名称（Y 轴）
- PageRank 分数（X 轴）
- 颜色映射

### 8.2 图结构

**类型**：有向图
**元素**：
- 节点（页面）
- 边（链接）
- 节点大小（PageRank 分数）
- 节点颜色（PageRank 分数）

### 8.3 收敛过程

**类型**：折线图
**元素**：
- 迭代次数（X 轴）
- PageRank 分数（Y 轴）
- L1 差异（副图）

## 9. 扩展设计

### 9.1 新增求解方法

**步骤**：
1. 在 PageRank 类中添加新方法
2. 保持接口一致
3. 添加相应测试

### 9.2 新增可视化

**步骤**：
1. 在 PageRankVisualizer 类中添加新方法
2. 保持接口一致
3. 添加相应测试

### 9.3 性能优化

**方向**：
- 分布式计算
- GPU 加速
- 近似算法

## 10. 部署设计

### 10.1 依赖管理

**依赖**：
- NumPy
- SciPy
- Matplotlib
- NetworkX
- pytest

### 10.2 环境配置

**要求**：
- Python 3.8+
- pip 或 conda

### 10.3 打包发布

**方式**：
- setuptools
- wheel
- PyPI
