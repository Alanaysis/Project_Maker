# 线性规划测试文档

## 1. 测试策略

### 1.1 测试层次

| 层次 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 单个函数/方法 | pytest |
| 集成测试 | 模块间协作 | pytest |
| 系统测试 | 完整问题求解 | pytest + 手动验证 |

### 1.2 测试覆盖目标

- 核心求解器：> 95% 代码覆盖
- 敏感性分析：> 90% 代码覆盖
- 应用模块：> 85% 代码覆盖

## 2. 单纯形法测试

### 2.1 标准单纯形法

| 测试用例 | 输入 | 期望输出 | 验证点 |
|----------|------|----------|--------|
| 教材例题 | max 3x1+5x2, 3约束 | z=33, x=(2,5) | 最优值和解 |
| 两变量 | max 5x1+4x2, 2约束 | z=20 | 最优值 |
| 三变量 | max 2x1+3x2+x3, 3约束 | z>0 | 可行性 |
| 最小化 | min 2x1+3x2, 2约束 | z>=0 | min 处理 |
| 单约束 | max 3x1+2x2, 1约束 | z=15 | 简单情况 |
| 退化 | 特殊约束 | 收敛 | 循环避免 |

### 2.2 大M法

| 测试用例 | 约束类型 | 期望 | 验证点 |
|----------|----------|------|--------|
| >= 约束 | 含 GE | 最优或不可行 | 人工变量处理 |
| == 约束 | 含 EQ | 最优 | 等式约束 |
| 混合约束 | LE+GE | 最优 | 多类型混合 |

### 2.3 两阶段法

| 测试用例 | 期望 | 验证点 |
|----------|------|--------|
| >= 约束 | 与大M一致 | Phase I 可行性 |
| == 约束 | 与大M一致 | Phase I 可行性 |
| 全等式 | z=6 | Phase I + II |

### 2.4 方法一致性

```python
def test_methods_agree():
    """三种方法对同一问题结果一致。"""
    for method in ("standard", "big_m", "two_phase"):
        result = solver.solve(lp)
        assert abs(result.optimal_value - expected) < 1e-4
```

## 3. 对偶理论测试

### 3.1 对偶构造

| 测试 | 验证点 |
|------|--------|
| 标准对偶 | 变量数 = 原约束数 |
| 对偶的对偶 | 等于原问题 |

### 3.2 强对偶定理

```python
def test_strong_duality():
    """c^T x* = b^T y*"""
    assert abs(primal_result.optimal_value - dual_result.optimal_value) < 1e-6
```

### 3.3 弱对偶定理

```python
def test_weak_duality():
    """对任意可行解: c^T x <= b^T y"""
    assert c @ x_feasible <= b @ y_feasible + 1e-6
```

### 3.4 互补松弛

```python
def test_complementary_slackness():
    """y_i * slack_i = 0, x_j * dual_slack_j = 0"""
    assert all(abs(y * slack) < 1e-6)
```

### 3.5 对偶单纯形法

| 测试 | 验证点 |
|------|--------|
| 基本问题 | 收敛到最优 |
| 可行性检查 | 初始解对偶可行 |

## 4. 敏感性分析测试

### 4.1 目标函数系数范围

| 测试 | 验证点 |
|------|--------|
| 范围计算 | lower <= current <= upper |
| 允许增减 | 有意义的数值 |

### 4.2 右端项范围

| 测试 | 验证点 |
|------|--------|
| 范围计算 | 有意义的数值 |
| 影子价格 | 有限值 |

### 4.3 变化分析

```python
def test_small_change_preserves_optimality():
    """小变化保持最优。"""
    new_result = analyzer.analyze_objective_change(lp, result, delta_c)
    assert new_result.status == "optimal"
```

### 4.4 退化性检查

```python
def test_degeneracy():
    """检查基变量是否为 0。"""
    assert isinstance(report.is_degenerate, bool)
```

## 5. 应用测试

### 5.1 生产计划

| 测试 | 输入 | 期望 |
|------|------|------|
| 基本问题 | 2资源2产品 | z>0 |
| 单产品 | 1资源1产品 | z=80 |
| 三产品 | 3资源3产品 | z>0 |
| 报告生成 | 任意 | 包含关键信息 |

### 5.2 运输问题

| 测试 | 供需 | 期望 |
|------|------|------|
| 平衡 | sum(s)=sum(d) | 最优 |
| 供大于求 | sum(s)>sum(d) | 添加虚拟需求 |
| 供不应求 | sum(s)<sum(d) | 添加虚拟供给 |
| 西北角法 | 任意 | 满足供需约束 |
| 最小元素法 | 任意 | 满足供需约束 |

### 5.3 指派问题

| 测试 | 期望 |
|------|------|
| 3x3 | 每行每列和=1 |
| 2x2 | 最优成本正确 |
| 匈牙利算法 | 返回有效指派 |

## 6. 边界测试

### 6.1 数值边界

```python
def test_zero_coefficients():
    """零系数目标函数。"""
    assert abs(result.optimal_value) < 1e-6

def test_large_problem():
    """100 变量 50 约束。"""
    result = solver.solve(large_lp)
    assert result.status in ("optimal", "unbounded")
```

### 6.2 鲁棒性测试

```python
def test_repeated_solves():
    """重复求解同一问题。"""
    for _ in range(5):
        result = solver.solve(lp)
        assert result.status == "optimal"
```

## 7. 测试运行

```bash
# 全部测试
pytest tests/ -v

# 单纯形法
pytest tests/test_simplex.py -v

# 对偶理论
pytest tests/test_duality.py -v

# 敏感性分析
pytest tests/test_sensitivity.py -v

# 应用
pytest tests/test_applications.py -v

# 覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 8. 已知测试限制

1. 大规模问题 (>1000 变量) 未充分测试
2. 退化问题的收敛性依赖 Bland 规则
3. 浮点精度可能导致极小误差
4. 对偶单纯形法的初始对偶可行性检查可能遗漏边界情况
