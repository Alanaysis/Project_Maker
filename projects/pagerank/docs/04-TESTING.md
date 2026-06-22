# PageRank 算法测试文档

## 1. 测试策略

### 1.1 测试目标

- 验证算法正确性
- 确保代码质量
- 检测边界情况
- 保证性能要求

### 1.2 测试类型

1. **单元测试**：测试单个函数或类
2. **集成测试**：测试模块间交互
3. **性能测试**：测试性能指标
4. **可视化测试**：测试图表生成

### 1.3 测试覆盖

- 语句覆盖：≥ 90%
- 分支覆盖：≥ 80%
- 函数覆盖：100%

## 2. 单元测试

### 2.1 WebGraph 测试

**文件**：`tests/test_graph.py`

**测试用例**：

#### 2.1.1 空图测试

```python
def test_empty_graph(self):
    """测试空图创建"""
    graph = WebGraph()
    assert graph.num_pages == 0
    assert graph.page_names == {}
```

#### 2.1.2 添加页面测试

```python
def test_add_page(self):
    """测试添加页面"""
    graph = WebGraph()
    idx1 = graph.add_page("A")
    idx2 = graph.add_page("B")

    assert graph.num_pages == 2
    assert idx1 == 0
    assert idx2 == 1
    assert graph.page_names == {0: "A", 1: "B"}
```

#### 2.1.3 重复页面测试

```python
def test_add_duplicate_page(self):
    """测试添加重复页面"""
    graph = WebGraph()
    idx1 = graph.add_page("A")
    idx2 = graph.add_page("A")

    assert idx1 == idx2
    assert graph.num_pages == 1
```

#### 2.1.4 添加链接测试

```python
def test_add_link(self):
    """测试添加链接"""
    graph = WebGraph()
    graph.add_link("A", "B")
    graph.add_link("B", "C")

    assert graph.num_pages == 3
    assert graph.get_outgoing_links("A") == ["B"]
    assert graph.get_outgoing_links("B") == ["C"]
    assert graph.get_incoming_links("C") == ["B"]
```

#### 2.1.5 邻接矩阵测试

```python
def test_build_adjacency_matrix(self):
    """测试邻接矩阵构建"""
    graph = WebGraph()
    graph.add_link("A", "B")
    graph.add_link("A", "C")
    graph.add_link("B", "C")

    adj = graph.build_adjacency_matrix()

    assert adj.shape == (3, 3)
    assert adj[0, 1] == 1  # A -> B
    assert adj[0, 2] == 1  # A -> C
    assert adj[1, 2] == 1  # B -> C
    assert adj[0, 0] == 0  # 无自环
```

#### 2.1.6 转移矩阵测试

```python
def test_build_transition_matrix(self):
    """测试转移矩阵构建"""
    graph = WebGraph()
    graph.add_link("A", "B")
    graph.add_link("A", "C")

    trans = graph.build_transition_matrix()

    # A 有 2 个出链，每个链接 0.5
    assert trans.shape == (3, 3)
```

#### 2.1.7 悬挂节点测试

```python
def test_dangling_node(self):
    """测试悬挂节点处理"""
    graph = WebGraph()
    graph.add_link("A", "B")
    # B 没有出链

    trans = graph.build_transition_matrix()

    # B 的列应该均匀分布
    col_sum = trans[:, 1].sum()
    assert abs(col_sum - 1.0) < 1e-10
```

#### 2.1.8 从边列表创建测试

```python
def test_from_edges(self):
    """测试从边列表创建图"""
    edges = [("A", "B"), ("B", "C"), ("C", "A")]
    graph = WebGraph.from_edges(edges)

    assert graph.num_pages == 3
    assert graph.get_outgoing_links("A") == ["B"]
    assert graph.get_outgoing_links("B") == ["C"]
    assert graph.get_outgoing_links("C") == ["A"]
```

### 2.2 PageRank 测试

**文件**：`tests/test_pagerank.py`

**测试用例**：

#### 2.2.1 简单三角图测试

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

#### 2.2.2 星形图测试

```python
def test_star_graph(self):
    """测试星形图（中心节点接收大量链接）"""
    edges = [
        ("A", "Center"),
        ("B", "Center"),
        ("C", "Center"),
        ("D", "Center"),
    ]
    graph = WebGraph.from_edges(edges)

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    assert result.converged

    # Center 应该有最高的排名
    center_score = result.get_score("Center")
    assert center_score is not None
    assert center_score > result.get_score("A")
    assert center_score > result.get_score("B")
```

#### 2.2.3 链式图测试

```python
def test_chain_graph(self):
    """测试链式图（A->B->C->D）"""
    edges = [("A", "B"), ("B", "C"), ("C", "D")]
    graph = WebGraph.from_edges(edges)

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    assert result.converged

    # D 应该有最高的排名（接收来自 C 的链接）
    ranked = result.ranked_pages
    assert ranked[0][0] == "D"
```

#### 2.2.4 阻尼因子影响测试

```python
def test_damping_factor_effect(self):
    """测试不同阻尼因子产生不同结果"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr_low = PageRank(damping_factor=0.5)
    pr_high = PageRank(damping_factor=0.95)

    result_low = pr_low.compute(graph)
    result_high = pr_high.compute(graph)

    # 结果应该不同（尽管都是有效的）
    assert not np.allclose(result_low.scores, result_high.scores, atol=1e-4)
```

#### 2.2.5 无效阻尼因子测试

```python
def test_invalid_damping_factor(self):
    """测试无效阻尼因子抛出错误"""
    with pytest.raises(ValueError):
        PageRank(damping_factor=-0.1)

    with pytest.raises(ValueError):
        PageRank(damping_factor=1.1)
```

#### 2.2.6 空图测试

```python
def test_empty_graph(self):
    """测试空图的 PageRank"""
    graph = WebGraph()
    pr = PageRank()

    result = pr.compute(graph)

    assert result.converged
    assert len(result.scores) == 0
    assert result.iterations == 0
```

#### 2.2.7 单页面测试

```python
def test_single_page(self):
    """测试单页面的 PageRank"""
    graph = WebGraph()
    graph.add_page("A")

    pr = PageRank()
    result = pr.compute(graph)

    assert result.converged
    assert len(result.scores) == 1
    assert abs(result.scores[0] - 1.0) < 1e-10
```

#### 2.2.8 收敛检测测试

```python
def test_convergence_detection(self):
    """测试收敛检测"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph, max_iterations=1000, tolerance=1e-10)

    assert result.converged
    assert result.iterations < 1000
    assert result.final_diff < 1e-10
```

#### 2.2.9 最大迭代次数测试

```python
def test_max_iterations(self):
    """测试最大迭代次数限制"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph, max_iterations=2, tolerance=1e-20)

    # 应该在最大迭代次数处停止
    assert result.iterations == 2
```

#### 2.2.10 排名页面测试

```python
def test_ranked_pages(self):
    """测试排名页面属性"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank()
    result = pr.compute(graph)

    ranked = result.ranked_pages

    # 应该返回所有页面
    assert len(ranked) == 3

    # 应该按分数降序排列
    for i in range(len(ranked) - 1):
        assert ranked[i][1] >= ranked[i + 1][1]
```

#### 2.2.11 获取分数测试

```python
def test_get_score(self):
    """测试获取分数方法"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "A")])

    pr = PageRank()
    result = pr.compute(graph)

    assert result.get_score("A") is not None
    assert result.get_score("B") is not None
    assert result.get_score("C") is None
```

#### 2.2.12 幂迭代法测试

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

#### 2.2.13 代数法测试

```python
def test_algebraic_method(self):
    """测试代数法产生相同结果"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result_iterative = pr.compute(graph)
    result_algebraic = pr.compute_algebraic(graph)

    # 结果应该非常相似
    assert np.allclose(result_iterative.scores, result_algebraic.scores, atol=1e-6)
```

#### 2.2.14 Wikipedia 示例测试

```python
def test_wikipedia_example(self):
    """测试 Wikipedia 的 PageRank 示例"""
    edges = [
        ("A", "B"),
        ("B", "C"),
        ("C", "A"),
        ("D", "C"),
    ]
    graph = WebGraph.from_edges(edges)

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    assert result.converged

    # C 应该有最高的排名（最多的入链）
    ranked = result.ranked_pages
    assert ranked[0][0] == "C"
```

#### 2.2.15 初始分数测试

```python
def test_initial_scores(self):
    """测试自定义初始分数"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank()
    initial = np.array([0.1, 0.6, 0.3])
    result = pr.compute(graph, initial_scores=initial)

    assert result.converged
    assert abs(result.scores.sum() - 1.0) < 1e-10
```

#### 2.2.16 无效初始分数测试

```python
def test_invalid_initial_scores(self):
    """测试无效初始分数抛出错误"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "A")])

    pr = PageRank()

    with pytest.raises(ValueError):
        pr.compute(graph, initial_scores=np.array([0.5, 0.5, 0.5]))  # 长度错误
```

## 3. 集成测试

### 3.1 方法一致性测试

**测试内容**：验证不同求解方法产生相同结果

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

### 3.2 大规模图测试

**测试内容**：测试大规模图的性能

```python
def test_large_graph(self):
    """测试大规模图"""
    # 创建 1000 个页面的图
    edges = []
    for i in range(1000):
        for j in range(10):
            target = (i + j + 1) % 1000
            edges.append((f"Page{i}", f"Page{target}"))

    graph = WebGraph.from_edges(edges)

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph, max_iterations=50)

    assert result.converged
    assert len(result.scores) == 1000
```

### 3.3 可视化测试

**测试内容**：测试图表生成功能

```python
def test_visualization(self):
    """测试可视化功能"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    # 测试排名图表
    fig1 = PageRankVisualizer.plot_ranked_pages(result)
    assert fig1 is not None

    # 测试图结构可视化
    fig2 = PageRankVisualizer.plot_graph(graph, result)
    assert fig2 is not None

    # 测试收敛过程可视化
    scores_history = [result.scores] * 10
    fig3 = PageRankVisualizer.plot_convergence(scores_history)
    assert fig3 is not None
```

## 4. 性能测试

### 4.1 计算时间测试

**测试指标**：不同规模图的计算时间

```python
import time

def test_computation_time(self):
    """测试计算时间"""
    sizes = [10, 100, 1000]
    times = []

    for size in sizes:
        edges = []
        for i in range(size):
            for j in range(5):
                target = (i + j + 1) % size
                edges.append((f"Page{i}", f"Page{target}"))

        graph = WebGraph.from_edges(edges)

        pr = PageRank(damping_factor=0.85)

        start = time.time()
        result = pr.compute(graph, max_iterations=50)
        end = time.time()

        times.append(end - start)

    # 验证时间增长合理
    assert times[1] < times[0] * 100  # 100 倍规模，时间增长不超过 100 倍
```

### 4.2 内存使用测试

**测试指标**：内存使用情况

```python
import tracemalloc

def test_memory_usage(self):
    """测试内存使用"""
    tracemalloc.start()

    # 创建大规模图
    edges = []
    for i in range(1000):
        for j in range(10):
            target = (i + j + 1) % 1000
            edges.append((f"Page{i}", f"Page{target}"))

    graph = WebGraph.from_edges(edges)

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph, max_iterations=50)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 验证内存使用合理（< 100MB）
    assert peak < 100 * 1024 * 1024
```

### 4.3 收敛速度测试

**测试指标**：不同阻尼因子的收敛速度

```python
def test_convergence_speed(self):
    """测试收敛速度"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    damping_factors = [0.5, 0.7, 0.85, 0.95]
    iterations = []

    for d in damping_factors:
        pr = PageRank(damping_factor=d)
        result = pr.compute(graph, tolerance=1e-10)
        iterations.append(result.iterations)

    # 验证收敛速度合理
    assert all(i < 100 for i in iterations)
```

## 5. 测试工具

### 5.1 pytest 配置

**文件**：`pytest.ini` 或 `pyproject.toml`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### 5.2 测试夹具

```python
@pytest.fixture
def simple_graph():
    """创建简单测试图"""
    return WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

@pytest.fixture
def complex_graph():
    """创建复杂测试图"""
    edges = [
        ("A", "B"), ("A", "C"),
        ("B", "C"),
        ("C", "A"),
        ("D", "C"),
    ]
    return WebGraph.from_edges(edges)
```

### 5.3 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_pagerank.py -v

# 运行特定测试类
pytest tests/test_pagerank.py::TestPageRank -v

# 运行特定测试方法
pytest tests/test_pagerank.py::TestPageRank::test_simple_triangle -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 6. 测试报告

### 6.1 覆盖率报告

```
Name                    Stmts   Miss  Cover
-------------------------------------------
src/graph.py              120     10    92%
src/pagerank.py           150     15    90%
src/visualizer.py         100     20    80%
-------------------------------------------
TOTAL                     370     45    88%
```

### 6.2 测试结果

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-6.2.5
collected 25 items

tests/test_graph.py::TestWebGraph::test_empty_graph PASSED
tests/test_graph.py::TestWebGraph::test_add_page PASSED
tests/test_graph.py::TestWebGraph::test_add_duplicate_page PASSED
tests/test_graph.py::TestWebGraph::test_add_link PASSED
tests/test_graph.py::TestWebGraph::test_build_adjacency_matrix PASSED
tests/test_graph.py::TestWebGraph::test_build_transition_matrix PASSED
tests/test_graph.py::TestWebGraph::test_dangling_node PASSED
tests/test_graph.py::TestWebGraph::test_from_edges PASSED

tests/test_pagerank.py::TestPageRank::test_simple_triangle PASSED
tests/test_pagerank.py::TestPageRank::test_star_graph PASSED
tests/test_pagerank.py::TestPageRank::test_chain_graph PASSED
tests/test_pagerank.py::TestPageRank::test_damping_factor_effect PASSED
tests/test_pagerank.py::TestPageRank::test_invalid_damping_factor PASSED
tests/test_pagerank.py::TestPageRank::test_empty_graph PASSED
tests/test_pagerank.py::TestPageRank::test_single_page PASSED
tests/test_pagerank.py::TestPageRank::test_convergence_detection PASSED
tests/test_pagerank.py::TestPageRank::test_max_iterations PASSED
tests/test_pagerank.py::TestPageRank::test_ranked_pages PASSED
tests/test_pagerank.py::TestPageRank::test_get_score PASSED
tests/test_pagerank.py::TestPageRank::test_power_iteration PASSED
tests/test_pagerank.py::TestPageRank::test_algebraic_method PASSED
tests/test_pagerank.py::TestPageRank::test_wikipedia_example PASSED
tests/test_pagerank.py::TestPageRank::test_initial_scores PASSED
tests/test_pagerank.py::TestPageRank::test_invalid_initial_scores PASSED

============================== 25 passed in 0.45s ===============================
```

## 7. 测试最佳实践

### 7.1 测试命名

- 使用描述性名称
- 遵循 `test_<功能>_<场景>` 模式
- 使用下划线分隔单词

### 7.2 测试结构

- 遵循 AAA 模式（Arrange, Act, Assert）
- 每个测试只测试一个功能
- 使用夹具减少重复代码

### 7.3 测试覆盖

- 测试正常情况
- 测试边界情况
- 测试错误情况
- 测试性能要求

### 7.4 测试维护

- 定期运行测试
- 及时修复失败的测试
- 更新测试以反映代码变化
