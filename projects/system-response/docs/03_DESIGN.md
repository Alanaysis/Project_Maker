# Design: System Response Analysis

## 架构设计

```
┌─────────────────────────────────────────────────┐
│                   用户接口层                      │
├─────────────────────────────────────────────────┤
│  TransferFunction  │  ControllerDesigner        │
│  TimeResponse      │  SystemIdentifier          │
│  FrequencyResponse │  StabilityAnalyzer         │
│  PerformanceMetrics│                            │
├─────────────────────────────────────────────────┤
│                   计算引擎层                      │
│  scipy.signal  │  numpy.polynomial  │  numpy    │
└─────────────────────────────────────────────────┘
```

## 模块设计

### TransferFunction

核心数据结构，表示 G(s) = N(s)/D(s)。

```python
@dataclass
class TransferFunction:
    num: np.ndarray   # 分子系数 (降幂)
    den: np.ndarray   # 分母系数 (降幂)
    name: str         # 标识符
```

**设计决策**：
- 系数按 scipy 约定存储 (最高次在前)
- 创建时自动归一化首项系数
- 支持运算符重载 (*, +, -)

### TimeResponse

时域响应计算封装。

```python
class TimeResponse:
    def __init__(self, tf: TransferFunction)
    def step(self, T=None) -> TimeResponseData
    def impulse(self, T=None) -> TimeResponseData
    def ramp(self, T=None) -> TimeResponseData
    def lsim(self, u, T) -> TimeResponseData
```

**设计决策**：
- 内部转换为 scipy.signal.lti 对象
- 自动估计合理的时间范围
- 返回统一的 TimeResponseData 数据类

### FrequencyResponse

频域分析封装。

```python
class FrequencyResponse:
    def bode(self, omega=None) -> BodeData
    def nyquist(self, omega=None) -> NyquistData
    def margins(self) -> StabilityMargins
    def bandwidth(self, db_drop=-3) -> float
```

**设计决策**：
- 频率默认使用对数分布
- 裕度计算使用 scipy.signal.margin
- 带宽使用插值提高精度

### PerformanceMetrics

性能指标计算。

```python
class PerformanceMetrics:
    def step_metrics(self, T=None) -> PerformanceData
    def steady_state_error(self, input_type) -> float
    @staticmethod
    def second_order_metrics(omega_n, zeta) -> PerformanceData
```

**设计决策**：
- 上升时间使用线性插值
- 调节时间从末尾向前扫描
- 提供解析公式用于标准二阶系统

### StabilityAnalyzer

稳定性分析工具。

```python
class StabilityAnalyzer:
    def routh(self, den=None) -> RouthTable
    def root_locus(self, k_range=None) -> RootLocusData
    def closed_loop_poles(self, k=1) -> np.ndarray
    def is_stable(self, k=1) -> bool
```

**设计决策**：
- 劳斯表使用数值计算，处理零行特殊情况
- 根轨迹对每个增益值独立求根
- 稳定性判断基于极点实部

### SystemIdentifier

系统辨识工具。

```python
class SystemIdentifier:
    @staticmethod
    def from_step_response(t, y, model_order) -> IdentificationResult
    @staticmethod
    def from_frequency_response(omega, mag_db, phase_deg, order) -> IdentificationResult
```

**设计决策**：
- 阶跃响应法使用特征参数提取
- 频域法使用 Nelder-Mead 优化
- 返回辨识结果 + 拟合残差

### ControllerDesigner

控制器设计工具。

```python
class ControllerDesigner:
    def pid_ziegler_nichols(self, method) -> PIDParams
    def design_lead(self, phase_boost, omega_cross) -> TransferFunction
    def design_lag(self, low_freq_boost, omega_cross) -> TransferFunction
```

**设计决策**：
- PID 使用 Ziegler-Nichols 经典整定
- 超前/滞后补偿器基于频域设计
- 返回 TransferFunction 对象，可直接串联

## 数据流

```
用户输入 ──> TransferFunction ──> 各分析模块 ──> 结果数据类
                │
                ├── TimeResponse ──> TimeResponseData
                ├── FrequencyResponse ──> BodeData/NyquistData
                ├── PerformanceMetrics ──> PerformanceData
                ├── StabilityAnalyzer ──> RouthTable/RootLocusData
                └── ControllerDesigner ──> TransferFunction
```

## 错误处理

- 输入验证：检查系数维度、增益范围
- 数值稳定性：处理零除、奇异矩阵
- 异常传播：使用标准 Python 异常
