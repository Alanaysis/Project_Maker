# 线性规划需求文档

## 1. 功能需求

### 1.1 核心求解器

#### FR-1: 单纯形法 - 标准形式
- **描述**：实现标准单纯形法求解 <= 约束、b >= 0 的 LP 问题
- **输入**：目标函数系数 c、约束矩阵 A、右端项 b
- **输出**：最优解 x*、最优值 z*、迭代次数
- **验收标准**：经典教材例题结果正确

#### FR-2: 单纯形法 - 大M法
- **描述**：通过引入人工变量和惩罚系数 M 处理任意约束类型
- **输入**：一般形式的 LP 问题
- **输出**：最优解或不可行报告
- **验收标准**：混合约束问题求解正确

#### FR-3: 单纯形法 - 两阶段法
- **描述**：Phase I 找可行解，Phase II 优化目标函数
- **输入**：一般形式的 LP 问题
- **输出**：最优解或不可行报告
- **验收标准**：与大M法结果一致

#### FR-4: 对偶问题构造
- **描述**：自动将原问题转换为对偶问题
- **输入**：原问题 LP
- **输出**：对偶问题 LP
- **验收标准**：对偶的对偶等于原问题

#### FR-5: 对偶单纯形法
- **描述**：保持对偶可行性，逐步恢复原始可行性
- **输入**：初始对偶可行的 LP 问题
- **输出**：最优解
- **验收标准**：右端项变化后重新优化正确

### 1.2 敏感性分析

#### FR-6: 目标函数系数分析
- **描述**：计算 c_j 的允许变化范围
- **输入**：最优单纯形表
- **输出**：每个 c_j 的上下界
- **验收标准**：范围内变化不改变最优基

#### FR-7: 右端项分析
- **描述**：计算 b_i 的允许变化范围
- **输入**：最优单纯形表
- **输出**：每个 b_i 的上下界和影子价格
- **验收标准**：范围内变化不改变最优基

#### FR-8: 互补松弛验证
- **描述**：验证最优解的互补松弛条件
- **输入**：原问题和对偶问题的最优解
- **输出**：条件是否满足
- **验收标准**：最优解必满足互补松弛

### 1.3 实际应用

#### FR-9: 生产计划问题
- **描述**：多产品、多资源的最优生产安排
- **输入**：资源容量、产品利润、资源消耗
- **输出**：最优产量和利润
- **验收标准**：资源约束满足，利润最大

#### FR-10: 运输问题
- **描述**：供需平衡的最小成本运输方案
- **输入**：成本矩阵、供给量、需求量
- **输出**：最优运输方案
- **验收标准**：供需约束满足，成本最小

#### FR-11: 指派问题
- **描述**：最优任务分配
- **输入**：成本矩阵
- **输出**：最优指派方案
- **验收标准**：每人一任务，每任务一人

## 2. 非功能需求

### 2.1 性能

#### NFR-1: 求解速度
- 100 变量、50 约束的问题 < 1 秒
- 1000 变量、500 约束的问题 < 60 秒

#### NFR-2: 数值精度
- 最优解误差 < 1e-6
- 最优值误差 < 1e-6

### 2.2 可用性

#### NFR-3: API 设计
- 类和函数命名清晰
- 参数类型明确
- 提供丰富的文档字符串

#### NFR-4: 错误处理
- 无界问题返回 "unbounded"
- 不可行问题返回 "infeasible"
- 输入验证和错误提示

### 2.3 可维护性

#### NFR-5: 代码质量
- 模块化设计
- 单一职责原则
- 完整的类型注解

#### NFR-6: 测试覆盖
- 核心功能测试覆盖率 > 90%
- 边界情况测试

## 3. 数据需求

### 3.1 输入数据

| 数据 | 类型 | 范围 |
|------|------|------|
| 目标函数系数 | List[float] | 任意实数 |
| 约束矩阵 | List[List[float]] | 任意实数 |
| 右端项 | List[float] | 通常 >= 0 |
| 约束类型 | List[Enum] | LE, GE, EQ |

### 3.2 输出数据

| 数据 | 类型 | 说明 |
|------|------|------|
| 最优解 | np.ndarray | 长度 = 变量数 |
| 最优值 | float | 目标函数值 |
| 对偶解 | np.ndarray | 长度 = 约束数 |
| 松弛变量 | np.ndarray | 长度 = 约束数 |
| 迭代次数 | int | 单纯形迭代次数 |
| 状态 | str | optimal/infeasible/unbounded |

## 4. 接口需求

### 4.1 核心类

```python
class LinearProgram:
    def set_objective(self, coefficients, names=None)
    def add_constraint(self, coefficients, rhs, constraint_type)
    def to_standard_form(self) -> Tuple[c, A, b, n]

class SimplexSolver:
    def solve(self, lp: LinearProgram) -> LPResult

class DualProblem:
    @staticmethod
    def construct_dual(primal: LinearProgram) -> LinearProgram

class SensitivityAnalyzer:
    def analyze(self, lp, result) -> SensitivityReport

class ProductionPlanner:
    def add_resource(self, name, capacity)
    def add_product(self, name, profit, cost, usage, max_demand)
    def optimize(self) -> LPResult

class TransportationSolver:
    def solve(self, cost, supply, demand) -> LPResult

class AssignmentSolver:
    def solve(self, cost) -> LPResult
```

### 4.2 数据类

```python
@dataclass
class LPResult:
    status: str
    optimal_value: Optional[float]
    solution: Optional[np.ndarray]
    dual_solution: Optional[np.ndarray]
    slack: Optional[np.ndarray]
    iterations: int

@dataclass
class SensitivityReport:
    objective_coefficients: List[SensitivityRange]
    rhs_values: List[SensitivityRange]
    shadow_prices: np.ndarray
    reduced_costs: np.ndarray
```

## 5. 约束条件

### 5.1 技术约束
- 仅依赖 NumPy，不使用其他优化库
- Python >= 3.8

### 5.2 业务约束
- 单纯形法支持最多 1000 变量
- 迭代次数上限 1000
- 浮点精度 1e-10
