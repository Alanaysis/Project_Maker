# 线性规划设计文档

## 1. 架构设计

### 1.1 模块划分

```
linear-programming/
├── linear_program.py    # 数据模型层
├── simplex.py          # 核心算法层
├── duality.py          # 理论分析层
├── sensitivity.py      # 敏感性分析层
└── applications.py     # 应用层
```

层次关系：
```
applications.py
    ↓
simplex.py, duality.py, sensitivity.py
    ↓
linear_program.py
```

### 1.2 核心类设计

#### LinearProgram - 问题表示

```python
class LinearProgram:
    """线性规划问题的标准表示。"""

    # 属性
    _objective_type: ObjectiveType    # MAX 或 MIN
    _objective_coeffs: np.ndarray     # 目标函数系数
    _constraints: List[Constraint]    # 约束列表
    _num_vars: int                    # 变量数

    # 方法
    set_objective(coefficients, names)
    add_constraint(coefficients, rhs, constraint_type)
    to_standard_form() -> (c, A, b, n)
```

设计决策：
- 使用 dataclass 表示约束，便于扩展
- to_standard_form() 返回新数组，不修改原问题
- 支持变量命名，便于结果解释

#### SimplexSolver - 求解器

```python
class SimplexSolver:
    """单纯形法求解器。"""

    # 配置
    method: str      # "standard", "big_m", "two_phase"
    M: float         # 大M法惩罚系数
    verbose: bool    # 调试输出

    # 方法
    solve(lp) -> LPResult
    _solve_standard(lp) -> LPResult
    _solve_big_m(lp) -> LPResult
    _solve_two_phase(lp) -> LPResult
    _simplex_iterations(tableau, basis, n_orig, lp) -> LPResult
```

设计决策：
- 策略模式：通过 method 参数选择算法
- 核心迭代逻辑抽取为 _simplex_iterations()，三种方法共用
- tableau_history 保存迭代过程，便于调试和教学

#### LPResult - 结果表示

```python
@dataclass
class LPResult:
    status: str                    # "optimal", "infeasible", "unbounded"
    optimal_value: Optional[float]
    solution: Optional[np.ndarray]
    dual_solution: Optional[np.ndarray]
    slack: Optional[np.ndarray]
    iterations: int
    tableau_history: List[np.ndarray]
    message: str
```

设计决策：
- 使用 Optional 类型处理无解情况
- tableau_history 保存完整迭代历史
- message 提供人类可读的状态描述

## 2. 算法设计

### 2.1 单纯形法流程

```
输入: c, A, b
输出: x*, z*

1. 初始化
   - 构造初始单纯形表
   - 初始基 = 松弛变量

2. 迭代
   WHILE 存在 σ_j > 0:
     2.1 选择入基变量: min{j : σ_j > 0}  (Bland规则)
     2.2 选择出基变量: min{b_i/a_ij : a_ij > 0}  (最小比值)
     2.3 枢轴运算:
         - pivot行 /= pivot元素
         - 其他行 -= pivot列 * pivot行

3. 终止
   IF 所有 σ_j <= 0: 返回最优解
   IF 无可行出基变量: 返回无界
```

### 2.2 大M法设计

```
输入: LP 问题 (可能含 >=, == 约束)
输出: 最优解或不可行

1. 对每个 >= 和 == 约束引入人工变量 a_i
2. 目标函数添加惩罚: max c^T x - M * sum(a_i)
3. 用标准单纯形法求解
4. IF 任何 a_i > 0: 原问题不可行
```

### 2.3 两阶段法设计

```
Phase I:
  min sum(a_i)  s.t. 原约束 + 人工变量
  IF min > 0: 不可行

Phase II:
  删除人工变量列
  恢复原目标函数
  在 Phase I 的基上继续优化
```

### 2.4 对偶单纯形法设计

```
输入: 初始对偶可行的 LP
输出: 最优解

1. 检查原始可行性: b_bar = B^{-1} b >= 0?
2. IF 可行: 返回最优
3. 选择出基: min{b_bar_i : b_bar_i < 0}
4. 选择入基: min{σ_j/a_{ij} : a_{ij} < 0}
5. 枢轴运算, 回到 1
```

## 3. 数据流设计

### 3.1 问题构建流程

```
用户输入
    ↓
LinearProgram
    .set_objective(c)
    .add_constraint(a, b, type)
    ↓
to_standard_form()
    ↓
(c_std, A_std, b_std, n_orig)
    ↓
SimplexSolver.solve()
    ↓
LPResult
```

### 3.2 敏感性分析流程

```
LPResult (含 tableau_history)
    ↓
SensitivityAnalyzer.analyze()
    ↓
_extract_basis()        # 提取基变量
_objective_coefficient_ranges()  # c_j 范围
_rhs_ranges()           # b_i 范围
    ↓
SensitivityReport
```

## 4. 关键数据结构

### 4.1 单纯形表

```
tableau = np.ndarray(shape=(m+1, n+m+1))

布局:
| A | I | b |
| c | 0 | z |

行: 前 m 行为约束, 最后 1 行为目标函数
列: 前 n 列为原始变量, 中间 m 列为松弛变量, 最后 1 列为右端项
```

### 4.2 基变量索引

```python
basis: List[int]  # 长度 m, 存储每个约束对应的基变量索引
                   # 0..n-1: 原始变量
                   # n..n+m-1: 松弛变量
```

## 5. 错误处理设计

### 5.1 输入验证

```python
# LinearProgram
assert len(coefficients) == num_vars  # 系数维度匹配
assert rhs >= 0 for standard form     # 右端项非负

# SimplexSolver
assert method in ("standard", "big_m", "two_phase")
```

### 5.2 求解状态

| 状态 | 含义 | 处理 |
|------|------|------|
| optimal | 找到最优解 | 返回解和目标值 |
| infeasible | 无可行解 | 返回 None |
| unbounded | 目标函数无界 | 返回 None |
| error | 输入错误 | 返回错误信息 |

## 6. 扩展性设计

### 6.1 添加新算法

继承 SimplexSolver 或创建新的求解器类：

```python
class InteriorPointSolver:
    def solve(self, lp: LinearProgram) -> LPResult:
        ...
```

### 6.2 添加新应用

创建新的应用类，内部使用 SimplexSolver：

```python
class NetworkFlowSolver:
    def solve(self, graph, source, sink) -> LPResult:
        lp = self._build_lp(graph, source, sink)
        return SimplexSolver().solve(lp)
```

### 6.3 添加整数规划

在 LP 松弛基础上添加分支定界：

```python
class BBSolver:
    def solve(self, lp: LinearProgram, integer_vars: List[int]) -> LPResult:
        ...
```
