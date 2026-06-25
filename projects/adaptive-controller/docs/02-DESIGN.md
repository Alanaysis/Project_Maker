# 自适应控制器 - 架构设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      仿真引擎 (SimulationEngine)              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  参考信号    │  │  参考模型    │  │  被控对象    │       │
│  │  Generator   │  │  RefModel    │  │  Plant       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                │                  │               │
│         └────────────────┼──────────────────┘               │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │  自适应控制器         │                      │
│              │  MRACController       │                      │
│              ├───────────────────────┤                      │
│              │  - 控制律计算         │                      │
│              │  - 参数自适应         │                      │
│              │  - 参数估计器         │                      │
│              └───────────────────────┘                      │
│                          │                                  │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │  性能分析器           │                      │
│              │  PerformanceAnalyzer  │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心循环

```
      ┌─────────────────────────────────────────┐
      │                                         │
      ▼                                         │
┌──────────┐    ┌──────────┐    ┌──────────┐    │
│ 参考输入 │───▶│ 控制器   │───▶│ 被控对象 │────┘
│ r(t)     │    │ u(t)     │    │ y(t)     │
└──────────┘    └──────────┘    └──────────┘
                     ▲                │
                     │                │
              ┌──────┴──────┐         │
              │ 参数自适应  │         │
              │ e = y - y_m │◀────────┘
              └─────────────┘
```

## 2. 模块设计

### 2.1 模块职责

| 模块 | 职责 | 主要接口 |
|------|------|---------|
| MRACController | 自适应控制核心 | compute_control(), update_params() |
| ReferenceModel | 定义期望行为 | update(), get_output() |
| PlantModel | 模拟被控系统 | update(), get_output() |
| ParameterEstimator | 在线参数估计 | update(), get_parameters() |
| SimulationEngine | 仿真运行 | run() |
| PerformanceAnalyzer | 性能评估 | compute_metrics(), generate_report() |

### 2.2 类图

```
┌─────────────────────────────────────────────────────────────┐
│                      核心类关系                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MRACController ◆─────▶ ReferenceModel                    │
│       │                                                     │
│       ├──────▶ ParameterEstimator                          │
│       │                                                     │
│       └──────▶ ControllerState                             │
│                                                             │
│  SimulationEngine ◆─────▶ MRACController                  │
│       │                                                     │
│       └─────▶ PlantModel                                   │
│                                                             │
│  PerformanceAnalyzer                                        │
│       │                                                     │
│       └─────▶ SimulationResult                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. 数据流设计

### 3.1 控制循环数据流

```
时间步 t:
  1. 生成参考输入: r(t)
  2. 读取被控对象输出: y(t)
  3. 计算参考模型输出: y_m(t) = ref_model.update(r(t), dt)
  4. 计算跟踪误差: e(t) = y(t) - y_m(t)
  5. 更新参数估计: θ(t) = estimator.update(φ(t), y(t), dt)
  6. 计算控制信号: u(t) = controller.compute_control(r(t), y(t), dt)
  7. 更新被控对象: y(t+dt) = plant.update(u(t), dt)
  8. 记录状态: history.append(...)
```

### 3.2 数据结构

```python
@dataclass
class ControllerState:
    """控制器状态"""
    time: float
    reference_output: float
    plant_output: float
    control_signal: float
    tracking_error: float
    parameters: dict

@dataclass
class SimulationResult:
    """仿真结果"""
    times: np.ndarray
    reference_signal: np.ndarray
    reference_model_output: np.ndarray
    plant_output: np.ndarray
    control_signal: np.ndarray
    tracking_error: np.ndarray
    parameter_history: Dict[str, np.ndarray]
    metrics: Dict[str, float]
```

## 4. 接口设计

### 4.1 控制器接口

```python
class MRACController:
    def __init__(
        self,
        reference_model: ReferenceModel,
        adaptation_law: AdaptationLaw = AdaptationLaw.LYAPUNOV,
        adaptation_gain: float = 0.1,
        initial_params: Optional[dict] = None,
    ):
        """初始化自适应控制器"""

    def compute_control(
        self,
        reference_input: float,
        plant_output: float,
        dt: float,
    ) -> float:
        """计算控制信号"""

    def get_tracking_error_history(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取跟踪误差历史"""

    def get_parameter_history(self) -> Tuple[np.ndarray, dict]:
        """获取参数历史"""

    def reset(self):
        """重置控制器状态"""
```

### 4.2 参考模型接口

```python
class ReferenceModel:
    def __init__(
        self,
        model_order: ModelOrder = ModelOrder.FIRST_ORDER,
        params: Optional[ModelParameters] = None,
        initial_output: float = 0.0,
    ):
        """初始化参考模型"""

    def update(self, reference_input: float, dt: float) -> float:
        """更新模型输出"""

    def get_output(self) -> float:
        """获取当前输出"""

    def reset(self):
        """重置模型状态"""
```

### 4.3 被控对象接口

```python
class PlantModel:
    def __init__(
        self,
        plant_type: PlantType = PlantType.FIRST_ORDER,
        params: Optional[PlantParameters] = None,
        initial_output: float = 0.0,
    ):
        """初始化被控对象"""

    def update(self, control_input: float, dt: float) -> float:
        """更新系统状态"""

    def get_output(self) -> float:
        """获取当前输出"""

    def reset(self):
        """重置系统状态"""
```

### 4.4 参数估计器接口

```python
class ParameterEstimator:
    def __init__(
        self,
        n_params: int,
        estimation_method: EstimationMethod = EstimationMethod.RLS,
        adaptation_gain: float = 0.1,
        forgetting_factor: float = 0.99,
    ):
        """初始化参数估计器"""

    def update(
        self,
        phi: np.ndarray,
        y: float,
        dt: float,
    ) -> Tuple[np.ndarray, float]:
        """更新参数估计"""

    def get_parameters(self) -> np.ndarray:
        """获取当前参数估计值"""

    def reset(self):
        """重置估计器状态"""
```

## 5. 算法设计

### 5.1 MIT 规则

```
输入: e (跟踪误差), φ (回归向量), γ (自适应增益)
输出: Δθ (参数更新)

算法:
  1. 计算灵敏度导数: ∂e/∂θ ≈ -φ
  2. 计算梯度: g = e * ∂e/∂θ
  3. 更新参数: Δθ = -γ * g * dt
```

### 5.2 Lyapunov 方法

```
输入: e (跟踪误差), φ (回归向量), Γ (自适应增益矩阵)
输出: Δθ (参数更新)

算法:
  1. 定义 Lyapunov 函数: V = 0.5 * e² + 0.5 * (θ-θ*)ᵀ * Γ⁻¹ * (θ-θ*)
  2. 计算导数: dV/dt = e * de/dt + (θ-θ*)ᵀ * Γ⁻¹ * dθ/dt
  3. 选择自适应律使 dV/dt ≤ 0: dθ/dt = -Γ * e * φ
  4. 更新参数: Δθ = -Γ * e * φ * dt
```

### 5.3 RLS 算法

```
输入: φ (回归向量), y (观测值), P (协方差矩阵), λ (遗忘因子)
输出: θ (参数估计), P (更新后的协方差)

算法:
  1. 计算卡尔曼增益: K = P * φ / (λ + φᵀ * P * φ)
  2. 计算预测误差: e = y - φᵀ * θ
  3. 更新参数: θ = θ + K * e
  4. 更新协方差: P = (I - K * φᵀ) * P / λ
```

## 6. 扩展设计

### 6.1 添加新的自适应律

```python
class CustomAdaptationLaw:
    def compute_update(
        self,
        error: float,
        regression_vector: np.ndarray,
        current_params: np.ndarray,
        adaptation_gain: float,
        dt: float,
    ) -> np.ndarray:
        """计算参数更新"""
        # 实现自定义自适应律
        pass
```

### 6.2 添加新的被控对象

```python
class CustomPlant(PlantModel):
    def __init__(self, params):
        super().__init__()
        self.params = params

    def update(self, u, dt):
        # 实现自定义系统动态
        pass
```

### 6.3 添加新的参考模型

```python
class CustomReferenceModel(ReferenceModel):
    def __init__(self, params):
        super().__init__()
        self.params = params

    def update(self, r, dt):
        # 实现自定义参考模型
        pass
```

## 7. 性能考虑

### 7.1 计算复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 控制律计算 | O(n) | n 为参数数量 |
| MIT 更新 | O(n) | 简单梯度计算 |
| Lyapunov 更新 | O(n) | 向量运算 |
| RLS 更新 | O(n²) | 矩阵运算 |

### 7.2 内存使用

- 历史记录：O(N * n)，N 为时间步数，n 为参数数量
- 协方差矩阵：O(n²)

### 7.3 优化建议

1. **稀疏矩阵**：对于大规模系统，使用稀疏矩阵存储协方差
2. **滑动窗口**：限制历史记录长度
3. **并行计算**：对于蒙特卡洛仿真，可并行运行

## 8. 错误处理

### 8.1 异常情况

1. **数值不稳定**：参数发散
2. **奇异矩阵**：RLS 中协方差矩阵奇异
3. **除零错误**：分母为零

### 8.2 处理策略

```python
# 数值稳定性检查
if np.any(np.isnan(params)) or np.any(np.isinf(params)):
    logger.warning("参数数值异常，重置估计器")
    self.reset()

# 协方差矩阵正定性检查
if not np.all(np.linalg.eigvals(P) > 0):
    P = np.eye(n) * initial_covariance
```

## 9. 测试策略

### 9.1 单元测试

- 各模块独立测试
- 边界条件测试
- 异常情况测试

### 9.2 集成测试

- 完整控制回路测试
- 不同场景组合测试

### 9.3 性能测试

- 收敛速度测试
- 计算时间测试
- 内存使用测试

## 10. 部署架构

### 10.1 开发环境

```
adaptive-controller/
├── src/          # 源代码
├── tests/        # 测试代码
├── examples/     # 示例代码
└── docs/         # 文档
```

### 10.2 生产环境考虑

1. **实时性**：确保控制周期满足要求
2. **可靠性**：添加故障检测和恢复机制
3. **可监控性**：记录关键指标用于调试
