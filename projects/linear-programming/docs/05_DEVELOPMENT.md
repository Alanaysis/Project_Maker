# 线性规划开发文档

## 1. 开发环境

### 1.1 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -e .

# 开发依赖
pip install pytest pytest-cov
```

### 1.2 项目结构

```
linear-programming/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── linear_program.py  # LP 问题表示
│   ├── simplex.py         # 单纯形法
│   ├── duality.py         # 对偶理论
│   ├── sensitivity.py     # 敏感性分析
│   └── applications.py    # 实际应用
├── tests/                  # 测试
├── examples/               # 示例
├── docs/                   # 文档
├── requirements.txt        # 依赖
└── setup.py                # 安装配置
```

## 2. 核心实现细节

### 2.1 单纯形表构造

```python
# 标准形式: max c^T x, s.t. Ax + Is = b, x,s >= 0
tableau = np.zeros((m + 1, n + m + 1))

# 约束部分
tableau[:m, :n] = A           # 原始变量系数
tableau[:m, n:n+m] = np.eye(m)  # 松弛变量系数
tableau[:m, -1] = b           # 右端项

# 目标函数行 (检验数)
tableau[m, :n] = c            # c_j - z_j, 初始 z_j = 0
```

### 2.2 枢轴运算

```python
# 选择入基变量 entering, 出基变量 leaving
pivot = tableau[leaving, entering]

# 归一化 pivot 行
tableau[leaving] /= pivot

# 消元其他行
for i in range(m + 1):
    if i != leaving:
        tableau[i] -= tableau[i, entering] * tableau[leaving]
```

### 2.3 大M法人工变量处理

```python
# 对 >= 约束: 减去剩余变量 + 加人工变量
# 对 == 约束: 仅加人工变量

# 目标函数惩罚
c_full[n_orig + num_slack + art_idx] = -M

# 消除基中人工变量在目标行的系数
for i in range(m):
    if basis[i] >= n_orig + num_slack:
        tableau[-1] -= tableau[-1, basis[i]] * tableau[i]
```

### 2.4 两阶段法 Phase I 到 Phase II

```python
# Phase I 结束后
# 1. 删除人工变量列
cols_to_keep = list(range(n_orig + num_slack)) + [total_vars]
tableau_p2 = tableau_p1[:, cols_to_keep]

# 2. 恢复原目标函数
c_p2 = np.zeros(n_orig + num_slack)
c_p2[:n_orig] = c_work  # 原始目标系数
tableau_p2[-1, :] = c_p2

# 3. 消除基变量在目标行的系数
for i in range(m):
    if basis[i] < n_orig + num_slack:
        tableau_p2[-1] -= tableau_p2[-1, basis[i]] * tableau_p2[i]
```

### 2.5 敏感性分析

```python
# 目标函数系数范围 (非基变量)
# sigma_j = c_j - z_j <= 0
# c_j 可以增加到 z_j

# 右端项范围
# x_B = B^{-1} b >= 0
# B^{-1} (b + delta_i e_i) >= 0
# b_bar_k + delta_i * (B^{-1})_{k,i} >= 0
```

## 3. 算法优化

### 3.1 Bland 规则避免循环

```python
# 选择最小索引的正检验数变量入基
for j in range(n_full):
    if obj_row[j] > EPS:
        entering = j
        break
```

### 3.2 最小比值检验

```python
# 选择使 b/a 最小的行对应的基变量出基
for i in range(m):
    if col[i] > EPS:
        ratios[i] = rhs[i] / col[i]
leaving = np.argmin(ratios)
```

### 3.3 数值稳定性

```python
EPS = 1e-10  # 浮点比较阈值

# 避免除以零
if abs(pivot) < EPS:
    raise ValueError("Pivot element too small")

# 避免负零
tableau[tableau == 0] = 0
```

## 4. 常见问题与解决

### 4.1 退化问题

**现象**：基变量值为 0，导致迭代停滞。

**解决**：
- 使用 Bland 规则（选择最小索引）
- 小扰动法（给 b 加微小随机扰动）

### 4.2 数值精度

**现象**：浮点误差累积导致错误结果。

**解决**：
- 使用适当的 EPS 阈值
- 关键判断使用相对误差
- 避免过大的 M 值

### 4.3 大M法的 M 选择

**问题**：M 太大导致数值不稳定，太小可能不满足惩罚要求。

**建议**：
- M = 10^6 适用于大多数问题
- 或使用两阶段法避免此问题

## 5. 性能分析

### 5.1 时间复杂度

| 操作 | 复杂度 |
|------|--------|
| 单次迭代 | O(m * (n+m)) |
| 总迭代 | O(min(C(n+m, m))) |
| 平均迭代 | O(m) ~ O(3m) |

### 5.2 空间复杂度

| 组件 | 空间 |
|------|------|
| 单纯形表 | O(m * (n+m)) |
| tableau_history | O(iter * m * (n+m)) |

### 5.3 性能瓶颈

1. 大规模问题的 tableau 存储
2. tableau_history 的内存消耗
3. 退化问题的迭代次数

## 6. 扩展开发

### 6.1 添加新求解方法

```python
class InteriorPointSolver:
    """内点法求解器。"""

    def solve(self, lp: LinearProgram) -> LPResult:
        c, A, b, n = lp.to_standard_form()
        # 实现内点法
        ...
        return LPResult(...)
```

### 6.2 添加整数规划

```python
class BranchAndBound:
    """分支定界法。"""

    def solve(self, lp: LinearProgram, integer_vars: List[int]) -> LPResult:
        # LP 松弛
        lp_result = SimplexSolver().solve(lp)

        # 分支
        if not self._is_integer(lp_result.solution, integer_vars):
            var, val = self._select_branch(lp_result, integer_vars)
            # 创建两个子问题
            ...

        return lp_result
```

### 6.3 添加网络流问题

```python
class NetworkSimplex:
    """网络单纯形法。"""

    def solve(self, graph, supplies) -> LPResult:
        # 利用网络结构的特殊性质
        ...
```

## 7. 调试技巧

### 7.1 启用详细输出

```python
solver = SimplexSolver(method="standard", verbose=True)
result = solver.solve(lp)
```

### 7.2 检查单纯形表

```python
for i, tableau in enumerate(result.tableau_history):
    print(f"Iteration {i}:")
    print(np.round(tableau, 4))
```

### 7.3 验证结果

```python
# 检查可行性
assert np.all(lp.A @ result.solution <= lp.b + 1e-6)
assert np.all(result.solution >= -1e-6)

# 检查最优性 (检验数 <= 0)
tableau = result.tableau_history[-1]
assert np.all(tableau[-1, :-1] <= 1e-6)
```

## 8. 版本历史

### v1.0.0 (当前版本)
- 标准单纯形法
- 大M法
- 两阶段法
- 对偶问题构造
- 对偶单纯形法
- 敏感性分析
- 生产计划、运输、指派问题

### 未来计划
- 内点法
- 整数规划 (分支定界)
- 网络单纯形法
- 并行计算支持
- 可视化工具
