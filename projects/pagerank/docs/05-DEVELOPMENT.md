# PageRank 算法开发文档

## 1. 开发环境

### 1.1 系统要求

- **操作系统**：Linux、macOS、Windows
- **Python 版本**：3.8 或更高
- **内存**：≥ 4GB
- **磁盘空间**：≥ 100MB

### 1.2 依赖安装

```bash
# 克隆项目
cd projects/pagerank

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.3 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| NumPy | ≥ 1.21.0 | 数值计算 |
| SciPy | ≥ 1.7.0 | 稀疏矩阵 |
| Matplotlib | ≥ 3.4.0 | 可视化 |
| NetworkX | ≥ 2.6.0 | 图结构可视化 |
| pytest | ≥ 6.0.0 | 测试框架 |

## 2. 项目结构

```
pagerank/
├── src/
│   ├── __init__.py
│   ├── graph.py          # 网页图数据结构
│   ├── pagerank.py       # PageRank 算法实现
│   └── visualizer.py     # 可视化工具
├── tests/
│   ├── __init__.py
│   ├── test_graph.py     # 图结构测试
│   └── test_pagerank.py  # 算法测试
├── examples/
│   ├── basic_usage.py    # 基础用法示例
│   └── visualization.py  # 可视化示例
├── docs/
│   ├── 01-RESEARCH.md    # 研究文档
│   ├── 02-DESIGN.md      # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md     # 测试文档
│   └── 05-DEVELOPMENT.md # 开发文档
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 3. 开发流程

### 3.1 功能开发

1. **需求分析**
   - 理解 PageRank 算法原理
   - 确定功能需求
   - 设计算法接口

2. **设计阶段**
   - 设计类结构
   - 设计算法流程
   - 设计数据结构

3. **实现阶段**
   - 实现 WebGraph 类
   - 实现 PageRank 类
   - 实现 PageRankResult 类
   - 实现 PageRankVisualizer 类

4. **测试阶段**
   - 编写单元测试
   - 编写集成测试
   - 执行测试并修复问题

5. **文档阶段**
   - 编写 README
   - 编写学习笔记
   - 编写技术文档

### 3.2 代码规范

**命名规范**：
- 类名：PascalCase（如 `WebGraph`）
- 函数名：snake_case（如 `build_adjacency_matrix`）
- 变量名：snake_case（如 `page_names`）
- 常量名：UPPER_SNAKE_CASE（如 `MAX_ITERATIONS`）

**文档规范**：
- 使用 Google 风格文档字符串
- 包含参数说明和返回值说明
- 包含使用示例

**类型注解**：
- 使用 Python 类型注解
- 使用 typing 模块
- 提供类型提示

### 3.3 提交规范

**提交信息格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`：新功能
- `fix`：修复问题
- `docs`：文档更新
- `style`：代码格式调整
- `refactor`：重构代码
- `test`：测试相关
- `chore`：构建过程或辅助工具的变动

**示例**：
```
feat(pagerank): 实现 PageRank 算法核心功能

- 实现 WebGraph 类管理网页图
- 实现 PageRank 类计算排名
- 实现 PageRankResult 类存储结果
- 添加单元测试和集成测试

Closes #1
```

## 4. 核心模块开发

### 4.1 WebGraph 模块

**文件**：`src/graph.py`

**功能**：
- 管理页面和链接
- 构建邻接矩阵
- 构建转移矩阵

**开发要点**：

1. **数据结构选择**
   - 使用字典存储页面名称到索引的映射
   - 使用列表存储边
   - 使用稀疏矩阵构建图结构

2. **稀疏矩阵优化**
   - 使用 CSR 格式存储邻接矩阵
   - 避免稠密矩阵运算
   - 利用 SciPy 优化

3. **悬挂节点处理**
   - 检测没有出链的页面
   - 将其 PageRank 均匀分配给所有页面

**代码示例**：
```python
class WebGraph:
    def __init__(self):
        self._edges: List[Tuple[int, int]] = []
        self._page_names: Dict[int, str] = {}
        self._name_to_index: Dict[str, int] = {}
        self._next_index: int = 0

    def add_page(self, name: str) -> int:
        if name in self._name_to_index:
            return self._name_to_index[name]

        index = self._next_index
        self._next_index += 1
        self._page_names[index] = name
        self._name_to_index[name] = index
        return index

    def build_adjacency_matrix(self) -> sparse.csr_matrix:
        rows = [e[0] for e in self._edges]
        cols = [e[1] for e in self._edges]
        data = np.ones(len(self._edges))

        return sparse.csr_matrix(
            (data, (rows, cols)),
            shape=(self.num_pages, self.num_pages)
        )
```

### 4.2 PageRank 模块

**文件**：`src/pagerank.py`

**功能**：
- 迭代法计算 PageRank
- 幂迭代法计算 PageRank
- 代数法计算 PageRank

**开发要点**：

1. **迭代法实现**
   - 初始化 PageRank 向量
   - 迭代计算直到收敛
   - 检查收敛条件

2. **幂迭代法实现**
   - 构建 Google 矩阵
   - 迭代计算主特征向量
   - 归一化结果

3. **代数法实现**
   - 构建线性方程组
   - 使用稀疏矩阵求解器
   - 归一化结果

**代码示例**：
```python
class PageRank:
    def __init__(self, damping_factor: float = 0.85):
        if not 0 <= damping_factor <= 1:
            raise ValueError("Damping factor must be between 0 and 1")
        self.damping_factor = damping_factor

    def compute(self, graph: WebGraph, max_iterations: int = 100,
                tolerance: float = 1e-6) -> PageRankResult:
        n = graph.num_pages
        if n == 0:
            return PageRankResult(...)

        transition = graph.build_transition_matrix()
        scores = np.ones(n) / n
        damping_vector = np.ones(n) * (1 - self.damping_factor) / n

        converged = False
        for iteration in range(max_iterations):
            new_scores = damping_vector + self.damping_factor * (transition @ scores)
            new_scores = new_scores / new_scores.sum()

            diff = np.abs(new_scores - scores).sum()
            if diff < tolerance:
                converged = True
                scores = new_scores
                break

            scores = new_scores

        return PageRankResult(...)
```

### 4.3 Visualizer 模块

**文件**：`src/visualizer.py`

**功能**：
- 可视化排名结果
- 可视化图结构
- 可视化收敛过程

**开发要点**：

1. **排名图表**
   - 使用水平条形图
   - 显示前 N 个页面
   - 添加数值标签

2. **图结构可视化**
   - 使用 NetworkX 构建图
   - 节点大小基于 PageRank
   - 节点颜色基于 PageRank

3. **收敛过程可视化**
   - 显示迭代过程
   - 显示 L1 差异
   - 使用对数坐标

**代码示例**：
```python
class PageRankVisualizer:
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

        plt.tight_layout()
        return fig
```

## 5. 测试开发

### 5.1 单元测试

**文件**：`tests/test_graph.py` 和 `tests/test_pagerank.py`

**开发要点**：

1. **测试覆盖**
   - 测试正常情况
   - 测试边界情况
   - 测试错误情况

2. **测试夹具**
   - 创建通用测试图
   - 减少重复代码
   - 提高测试效率

3. **断言使用**
   - 使用 pytest 断言
   - 提供清晰的错误信息
   - 测试数值精度

**代码示例**：
```python
class TestPageRank:
    def test_simple_triangle(self):
        """测试简单三角形图"""
        graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

        pr = PageRank(damping_factor=0.85)
        result = pr.compute(graph)

        assert result.converged
        assert len(result.scores) == 3
        assert abs(result.scores.sum() - 1.0) < 1e-10
```

### 5.2 集成测试

**开发要点**：

1. **方法一致性测试**
   - 验证不同求解方法产生相同结果
   - 测试数值精度

2. **大规模图测试**
   - 测试性能
   - 测试内存使用
   - 测试收敛性

3. **可视化测试**
   - 测试图表生成
   - 测试图表保存
   - 测试图表质量

**代码示例**：
```python
def test_method_consistency(self):
    """测试不同求解方法的一致性"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)

    result_iterative = pr.compute(graph)
    result_power = pr.compute_power_iteration(graph)
    result_algebraic = pr.compute_algebraic(graph)

    assert np.allclose(result_iterative.scores, result_power.scores, atol=1e-6)
    assert np.allclose(result_iterative.scores, result_algebraic.scores, atol=1e-6)
```

### 5.3 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pagerank.py::TestPageRank::test_simple_triangle -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 6. 文档开发

### 6.1 README 文档

**内容**：
- 项目简介
- 核心功能
- 项目结构
- 快速开始
- 算法原理
- 学习目标
- 技术栈
- 参考资料

**编写要点**：
- 简洁明了
- 包含代码示例
- 提供使用指南

### 6.2 学习笔记

**内容**：
- 核心概念
- 算法原理
- 实现细节
- 测试策略
- 性能优化
- 扩展学习

**编写要点**：
- 详细解释
- 包含图表
- 提供参考资料

### 6.3 技术文档

**内容**：
- 研究文档（01-RESEARCH.md）
- 设计文档（02-DESIGN.md）
- 实现文档（03-IMPLEMENTATION.md）
- 测试文档（04-TESTING.md）
- 开发文档（05-DEVELOPMENT.md）

**编写要点**：
- 结构清晰
- 内容完整
- 包含代码示例

## 7. 示例开发

### 7.1 基础用法示例

**文件**：`examples/basic_usage.py`

**内容**：
- 创建网页图
- 计算 PageRank
- 显示结果
- 比较不同参数

**开发要点**：
- 代码简洁
- 注释清晰
- 输出友好

### 7.2 可视化示例

**文件**：`examples/visualization.py`

**内容**：
- 创建样本网页图
- 计算 PageRank
- 生成可视化图表
- 保存图表文件

**开发要点**：
- 图表美观
- 保存为图片
- 提供说明

## 8. 构建和发布

### 8.1 打包配置

**文件**：`setup.py` 或 `pyproject.toml`

```python
from setuptools import setup, find_packages

setup(
    name="pagerank",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="PageRank algorithm implementation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pagerank",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "networkx>=2.6.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
```

### 8.2 发布流程

1. **更新版本号**
2. **更新 CHANGELOG**
3. **运行测试**
4. **构建包**
5. **上传到 PyPI**

```bash
# 构建包
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

## 9. 持续集成

### 9.1 GitHub Actions

**文件**：`.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### 9.2 代码质量检查

```bash
# 代码格式检查
flake8 src/ tests/

# 类型检查
mypy src/

# 代码风格检查
pylint src/
```

## 10. 故障排除

### 10.1 常见问题

**问题 1**：ImportError: No module named 'src'
**解决**：确保在项目根目录运行，或添加 `sys.path`

**问题 2**：NumPy 版本不兼容
**解决**：更新 NumPy：`pip install --upgrade numpy`

**问题 3**：Matplotlib 无法显示图表
**解决**：使用非交互式后端：`matplotlib.use('Agg')`

**问题 4**：稀疏矩阵运算错误
**解决**：确保 SciPy 版本正确：`pip install --upgrade scipy`

### 10.2 调试技巧

1. **使用 print 语句**
   - 打印中间结果
   - 检查数据形状
   - 验证计算过程

2. **使用断点**
   - 使用 pdb 调试器
   - 设置断点检查变量
   - 单步执行代码

3. **使用日志**
   - 配置日志级别
   - 记录关键信息
   - 分析日志文件

### 10.3 性能分析

```bash
# 使用 cProfile 分析
python -m cProfile -s cumulative examples/basic_usage.py

# 使用 memory_profiler 分析内存
python -m memory_profiler examples/basic_usage.py

# 使用 line_profiler 逐行分析
kernprof -l -v examples/basic_usage.py
```

## 11. 最佳实践

### 11.1 代码质量

- 遵循 PEP 8 规范
- 使用类型注解
- 编写清晰的文档
- 保持代码简洁

### 11.2 测试驱动

- 先写测试再写实现
- 保持高测试覆盖率
- 定期运行测试
- 及时修复失败的测试

### 11.3 版本控制

- 使用语义化版本号
- 编写清晰的提交信息
- 使用分支管理功能
- 定期合并主分支

### 11.4 文档维护

- 及时更新文档
- 保持文档与代码同步
- 提供使用示例
- 包含故障排除信息

## 12. 扩展开发

### 12.1 功能扩展

- 支持加权图
- 支持动态图
- 支持分布式计算
- 支持 GPU 加速

### 12.2 性能优化

- 使用更高效的数据结构
- 优化算法实现
- 使用并行计算
- 使用近似算法

### 12.3 可视化增强

- 交互式图表
- 3D 可视化
- 动态可视化
- 自定义样式
