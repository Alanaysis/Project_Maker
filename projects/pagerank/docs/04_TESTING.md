# 04 - PageRank 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────┐
│           端到端测试 (E2E)              │
├─────────────────────────────────────────┤
│           集成测试                       │
├─────────────────────────────────────────┤
│           单元测试                       │
└─────────────────────────────────────────┘
```

### 1.2 测试覆盖目标

- 代码覆盖率: > 90%
- 分支覆盖率: > 85%
- 所有公共 API 测试
- 边界条件测试

## 2. 测试文件组织

```
tests/
├── test_graph.py          # 图结构测试
├── test_pagerank.py       # 基础 PageRank 测试
└── test_advanced.py       # 高级功能测试
    ├── TestPersonalizedPageRank
    ├── TestTopicSensitivePageRank
    ├── TestPageRankEvaluation
    ├── TestRankingQuality
    ├── TestWebRankingApplication
    ├── TestSocialNetworkApplication
    └── TestRecommendationSystem
```

## 3. 单元测试

### 3.1 图结构测试 (test_graph.py)

**测试类**: TestWebGraph

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_empty_graph | 空图创建 | num_pages=0, page_names={} |
| test_add_page | 添加页面 | 索引分配, 名称映射 |
| test_add_duplicate_page | 重复页面 | 返回相同索引 |
| test_add_link | 添加链接 | 出链, 入链正确 |
| test_build_adjacency_matrix | 邻接矩阵 | 矩阵形状, 值正确 |
| test_build_transition_matrix | 转移矩阵 | 列随机性 |
| test_dangling_node | 悬挂节点 | 均匀分布 |
| test_from_edges | 边列表创建 | 图结构正确 |
| test_get_page_index | 页面索引查询 | 存在/不存在 |
| test_complex_graph | 复杂图 | 多链接正确 |

**示例测试**:

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

### 3.2 基础 PageRank 测试 (test_pagerank.py)

**测试类**: TestPageRank

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_simple_triangle | 三角形图 | 对称性, 分数相等 |
| test_star_graph | 星形图 | 中心节点最高 |
| test_chain_graph | 链式图 | 末端节点最高 |
| test_damping_factor_effect | 阻尼因子影响 | 不同 d 结果不同 |
| test_invalid_damping_factor | 无效阻尼因子 | ValueError |
| test_empty_graph | 空图 | 收敛, 空分数 |
| test_single_page | 单页面 | 分数为 1 |
| test_convergence_detection | 收敛检测 | 迭代次数, 最终差异 |
| test_max_iterations | 最大迭代 | 不收敛时停止 |
| test_ranked_pages | 排名页面 | 排序正确 |
| test_get_score | 获取分数 | 存在/不存在 |
| test_power_iteration | 幂迭代法 | 结果一致 |
| test_algebraic_method | 代数法 | 结果一致 |
| test_wikipedia_example | Wikipedia 示例 | C 最高 |
| test_initial_scores | 自定义初始值 | 求和为 1 |
| test_invalid_initial_scores | 无效初始值 | ValueError |

**示例测试**:

```python
def test_simple_triangle(self):
    """测试三角形图的 PageRank"""
    graph = WebGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])

    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    assert result.converged
    assert len(result.scores) == 3

    # 对称环形图中所有页面分数相等
    assert abs(result.scores[0] - result.scores[1]) < 1e-6
    assert abs(result.scores[1] - result.scores[2]) < 1e-6

    # 分数求和为 1
    assert abs(result.scores.sum() - 1.0) < 1e-10
```

## 4. 高级功能测试 (test_advanced.py)

### 4.1 个性化 PageRank 测试

**测试类**: TestPersonalizedPageRank

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_personalized_basic | 基础 PPR | 收敛, 维度, 变体类型 |
| test_personalized_bias_towards_target | 偏向目标 | 目标分数更高 |
| test_personalized_multiple_targets | 多目标 | 目标分数 > 其他 |
| test_personalized_none_uses_uniform | None 向量 | 等同标准 PR |
| test_personalized_empty_vector | 空向量 | 回退到均匀 |
| test_personalized_invalid_page | 无效页面 | 忽略无效 |
| test_personalized_scores_sum_to_one | 求和为 1 | 概率分布 |
| test_personalized_convergence | 收敛性 | 高精度收敛 |
| test_personalized_with_history | 历史记录 | 递减趋势 |

**示例测试**:

```python
def test_personalized_bias_towards_target(self):
    """测试个性化 PageRank 偏向目标页面"""
    standard = self.pr.compute(self.graph)
    personal = self.pr.compute_personalized(
        self.graph,
        personalization_vector={"A": 1.0}
    )

    a_idx = self.graph.get_page_index("A")
    assert personal.scores[a_idx] > standard.scores[a_idx]
```

### 4.2 Topic-Sensitive PageRank 测试

**测试类**: TestTopicSensitivePageRank

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_topic_sensitive_basic | 基础 TSPR | 主题数量, 收敛 |
| test_topic_sensitive_variant | 变体类型 | TOPIC_SENSITIVE |
| test_topic_sensitive_bias | 主题偏向 | 主题页面排名更高 |
| test_topic_sensitive_with_weights | 自定义权重 | 正常计算 |
| test_topic_sensitive_combined | 组合 TSPR | 收敛, 求和为 1 |
| test_topic_sensitive_combined_weights | 不同权重 | 结果不同 |
| test_topic_sensitive_single_topic | 单主题 | 正常工作 |

**示例测试**:

```python
def test_topic_sensitive_bias(self):
    """测试 Topic-Sensitive PageRank 主题偏向"""
    topics = {
        "News": ["CNN", "BBC"],
        "Tech": ["TechCrunch", "Wired"]
    }

    results = self.pr.compute_topic_sensitive(self.graph, topic_pages=topics)

    # News 主题应该排名新闻页面更高
    news_result = results["News"]
    cnn_idx = self.graph.get_page_index("CNN")
    tc_idx = self.graph.get_page_index("TechCrunch")
    assert news_result.scores[cnn_idx] > news_result.scores[tc_idx]
```

### 4.3 评估模块测试

**测试类**: TestPageRankEvaluation

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_graph_statistics | 图统计 | 正确统计 |
| test_graph_statistics_empty | 空图统计 | 零值处理 |
| test_convergence_analysis | 收敛分析 | 历史记录 |
| test_convergence_history_decreasing | 递减性 | 单调递减 |
| test_damping_factor_analysis | 阻尼因子分析 | 多 d 值 |
| test_damping_factor_correlations | 相关性 | [-1, 1] 范围 |
| test_robustness_analysis | 鲁棒性分析 | 扰动测试 |
| test_algorithm_comparison | 算法比较 | 结果一致 |
| test_sensitivity_analysis | 敏感性分析 | 多参数 |

**示例测试**:

```python
def test_algorithm_comparison(self):
    """测试算法比较"""
    results = self.evaluator.compare_algorithms(self.graph)

    assert 'iterative' in results
    assert 'power_iteration' in results
    assert 'algebraic' in results

    # 结果应该相似
    assert np.allclose(results['iterative'].scores,
                       results['power_iteration'].scores, atol=1e-4)
```

### 4.4 排序质量测试

**测试类**: TestRankingQuality

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_identical_rankings | 相同排名 | tau=1, rho=1 |
| test_reversed_rankings | 反向排名 | tau=-1 |
| test_partial_overlap | 部分重叠 | 有效范围 |
| test_precision_recall_at_k | P@k, R@k | 正确计算 |

**示例测试**:

```python
def test_identical_rankings(self):
    """测试相同排名的质量指标"""
    ranking = [("A", 0.4), ("B", 0.3), ("C", 0.2), ("D", 0.1)]

    metrics = PageRank.evaluate_ranking_quality(ranking, ranking)

    assert metrics.kendall_tau == 1.0
    assert metrics.spearman_rho == 1.0
```

### 4.5 应用模块测试

**网页排名测试** (TestWebRankingApplication):

```python
def test_web_ranking_basic(self):
    system = WebRankingSystem()
    pages = [
        WebPage(url="A", title="Page A", content="", links=["B"]),
        WebPage(url="B", title="Page B", content="", links=["A"]),
    ]
    system.add_pages(pages)
    result = system.compute_ranking()
    assert result.converged
```

**社交网络测试** (TestSocialNetworkApplication):

```python
def test_social_network_recommendations(self):
    analyzer = SocialNetworkAnalyzer()
    users = [
        SocialUser(user_id="A", name="Alice", interests=[], followers=["B"], following=["B"]),
        SocialUser(user_id="B", name="Bob", interests=[], followers=["A", "C"], following=["A", "C"]),
        SocialUser(user_id="C", name="Charlie", interests=[], followers=["B"], following=["B"]),
    ]
    analyzer.add_users(users)
    recs = analyzer.get_recommendations("A", max_recommendations=2)
    assert len(recs) <= 2
```

**推荐系统测试** (TestRecommendationSystem):

```python
def test_recommendation_basic(self):
    rec_system = RecommendationSystem()
    rec_system.add_interaction("user1", "item1", 5.0)
    rec_system.add_interaction("user1", "item2", 4.0)
    rec_system.add_interaction("user2", "item1", 4.0)
    rec_system.add_interaction("user2", "item3", 5.0)

    recs = rec_system.recommend("user1", num_recommendations=2)
    assert len(recs) <= 2
    # 不应该推荐已评分的物品
    for item, _ in recs:
        assert item != "item1"
        assert item != "item2"
```

## 5. 测试运行

### 5.1 运行所有测试

```bash
cd projects/pagerank
pytest tests/ -v
```

### 5.2 运行特定测试文件

```bash
pytest tests/test_advanced.py -v
```

### 5.3 运行特定测试类

```bash
pytest tests/test_advanced.py::TestPersonalizedPageRank -v
```

### 5.4 运行特定测试用例

```bash
pytest tests/test_advanced.py::TestPersonalizedPageRank::test_personalized_basic -v
```

### 5.5 生成覆盖率报告

```bash
pytest tests/ --cov=src --cov-report=html
```

## 6. 测试结果

### 6.1 当前测试统计

```
总测试数: 62
通过: 62
失败: 0
错误: 0
跳过: 0

覆盖率: > 90%
```

### 6.2 测试分布

| 测试文件 | 测试数 | 通过 |
|----------|--------|------|
| test_graph.py | 10 | 10 |
| test_pagerank.py | 16 | 16 |
| test_advanced.py | 36 | 36 |

## 7. 测试最佳实践

### 7.1 测试命名

- 使用描述性名称
- 格式: `test_<功能>_<场景>`
- 示例: `test_personalized_bias_towards_target`

### 7.2 测试结构

```python
def test_example():
    # 1. 准备 (Arrange)
    graph = WebGraph.from_edges([...])

    # 2. 执行 (Act)
    result = pr.compute(graph)

    # 3. 断言 (Assert)
    assert result.converged
    assert abs(result.scores.sum() - 1.0) < 1e-10
```

### 7.3 边界条件

- 空输入
- 单元素
- 极大值
- 无效输入

### 7.4 数值精度

```python
# 使用容差比较浮点数
assert abs(result.scores.sum() - 1.0) < 1e-10

# 使用 numpy 的 allclose
assert np.allclose(scores1, scores2, atol=1e-6)
```

## 8. 持续集成

### 8.1 CI 配置

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=src
```

### 8.2 测试触发

- 每次提交
- Pull Request
- 定期回归测试
