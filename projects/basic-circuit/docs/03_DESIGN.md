# 设计文档：基本电路模拟

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层                             │
│  (示例程序、可视化、命令行)                                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    应用层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 分压器   │  │ 滤波器   │  │ 放大器   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    分析层                                 │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ DC分析器     │  │ AC分析器     │                    │
│  │ - 节点分析   │  │ - 阻抗计算   │                    │
│  │ - KCL/KVL   │  │ - 频率响应   │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    电路层                                 │
│  ┌──────────────────────────────────────┐              │
│  │ 电路网络 (Circuit)                   │              │
│  │ - 节点管理                           │              │
│  │ - 元件管理                           │              │
│  │ - 连接关系                           │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    元件层                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐             │
│  │ R   │ │ C   │ │ L   │ │ V   │ │ I   │             │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘             │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

| 模块 | 文件 | 职责 |
|------|------|------|
| 元件模块 | components.py | 定义基本电路元件 |
| 电路模块 | circuit.py | 管理电路网络 |
| DC分析模块 | dc_analysis.py | 直流电路分析 |
| AC分析模块 | ac_analysis.py | 交流电路分析 |
| 应用模块 | applications.py | 实际应用电路 |

## 2. 类设计

### 2.1 元件类层次

```
Component (基类)
├── Resistor (电阻)
├── Capacitor (电容)
├── Inductor (电感)
├── VoltageSource (电压源)
└── CurrentSource (电流源)
```

#### Component 基类

```python
@dataclass
class Component:
    name: str
    node1: int
    node2: int
    component_type: ComponentType
```

#### Resistor

```python
@dataclass
class Resistor(Component):
    resistance: float

    def impedance(self, frequency: float = 0) -> complex
    def conductance(self) -> float
```

#### Capacitor

```python
@dataclass
class Capacitor(Component):
    capacitance: float

    def impedance(self, frequency: float) -> complex
    def reactance(self, frequency: float) -> float
```

#### Inductor

```python
@dataclass
class Inductor(Component):
    inductance: float

    def impedance(self, frequency: float) -> complex
    def reactance(self, frequency: float) -> float
```

### 2.2 电路类

```python
class Circuit:
    name: str
    nodes: Dict[int, Node]
    components: List[Component]
    _ground_node: Optional[int]

    # 节点管理
    def add_node(self, name: str) -> int
    def set_ground(self, node_id: int)

    # 元件添加
    def add_resistor(self, name, node1, node2, resistance) -> Resistor
    def add_capacitor(self, name, node1, node2, capacitance) -> Capacitor
    def add_inductor(self, name, node1, node2, inductance) -> Inductor
    def add_voltage_source(self, name, node1, node2, voltage, ...) -> VoltageSource
    def add_current_source(self, name, node1, node2, current, ...) -> CurrentSource

    # 查询
    def get_components_between(self, node1, node2) -> List[Component]
    def get_node_components(self, node_id) -> List[Component]
    def get_resistors(self) -> List[Resistor]
    # ... 其他查询方法

    # 信息
    def summary(self) -> str
```

### 2.3 分析器类

#### DCAnalyzer

```python
class DCAnalyzer:
    def __init__(self, circuit: Circuit)
    def solve(self) -> DCResult
    def _nodal_analysis(self) -> Dict[int, float]
    def _verify_kcl(self, ...) -> Dict[int, float]
    def _verify_kvl(self, ...) -> Dict[str, float]
```

#### ACAnalyzer

```python
class ACAnalyzer:
    def __init__(self, circuit: Circuit)
    def solve(self, frequency: float) -> ACResult
    def frequency_response(self, f_start, f_stop, f_points, node_id) -> FrequencyResponse
```

### 2.4 应用类

```python
class VoltageDivider:
    def __init__(self, v_in, r1, r2, r_load=None)
    def output_voltage(self) -> float
    def transfer_ratio(self) -> float
    def output_impedance(self) -> float

class RCFilter:
    def __init__(self, r, c, filter_type='low')
    def cutoff_frequency(self) -> float
    def transfer_function(self, frequency) -> complex
    def frequency_response(self, f_start, f_stop, f_points) -> FrequencyResponse

class RLCFilter:
    def __init__(self, r, l, c, filter_type='bandpass')
    def resonance_freq(self) -> float
    def quality_factor(self) -> float
    def transfer_function(self, frequency) -> complex

class Amplifier:
    def __init__(self, r_in, r_f, config='inverting')
    def gain(self) -> float
    def output_voltage(self, v_in) -> float
    def input_impedance(self) -> float
```

## 3. 算法设计

### 3.1 节点分析法 (MNA)

**输入**：电路网络

**输出**：节点电压

**步骤**：

1. **初始化**
   - 获取节点列表
   - 创建节点索引映射
   - 初始化导纳矩阵 Y 和电流向量 I

2. **填充导纳矩阵**
   ```
   对于每个电阻:
     Y[i1,i1] += 1/R
     Y[i1,i2] -= 1/R
     Y[i2,i1] -= 1/R
     Y[i2,i2] += 1/R

   对于每个电导元件:
     Y[i1,i1] += G
     Y[i1,i2] -= G
     Y[i2,i1] -= G
     Y[i2,i2] += G
   ```

3. **处理电流源**
   ```
   对于每个电流源:
     I[i1] -= I_source
     I[i2] += I_source
   ```

4. **处理电压源 (MNA扩展)**
   ```
   对于每个电压源 (索引 k):
     A[i1, n+k] += 1
     A[n+k, i1] += 1
     A[i2, n+k] -= 1
     A[n+k, i2] -= 1
     b[n+k] = V_source
   ```

5. **移除接地点行列**

6. **求解线性方程组**
   ```
   A_reduced * x = b_reduced
   x = solve(A_reduced, b_reduced)
   ```

7. **提取节点电压**

### 3.2 频率响应计算

**输入**：电路、频率范围、输出节点

**输出**：幅频响应、相频响应

**步骤**：

1. **生成频率数组**
   ```
   frequencies = logspace(log10(f_start), log10(f_stop), f_points)
   ```

2. **对每个频率点**
   ```
   对于每个频率 f:
     result = ac_analyzer.solve(f)
     H(f) = V_out(f) / V_in(f)
     magnitude[i] = |H(f)|
     phase[i] = angle(H(f))
   ```

3. **返回频率响应数据**

### 3.3 阻抗计算

**电阻**：
```
Z_R = R
```

**电容**：
```
Z_C = 1/(jωC) = -j/(2πfC)
```

**电感**：
```
Z_L = jωL
```

**串联**：
```
Z_total = Z_1 + Z_2 + ... + Z_n
```

**并联**：
```
1/Z_total = 1/Z_1 + 1/Z_2 + ... + 1/Z_n
```

## 4. 数据结构设计

### 4.1 节点

```python
@dataclass
class Node:
    id: int
    name: str = ""
    voltage: complex = 0.0
```

### 4.2 分析结果

```python
@dataclass
class DCResult:
    node_voltages: Dict[int, float]
    branch_currents: Dict[str, float]
    branch_voltages: Dict[str, float]
    power_dissipation: Dict[str, float]
    kcl_violations: Dict[int, float]
    kvl_violations: Dict[str, float]

@dataclass
class ACResult:
    frequency: float
    node_voltages: Dict[int, complex]
    branch_currents: Dict[str, complex]
    impedances: Dict[str, complex]
    total_impedance: complex

@dataclass
class FrequencyResponse:
    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
```

## 5. 接口设计

### 5.1 元件创建接口

```python
# 电阻
r = Resistor("R1", node1=0, node2=1, resistance=1000)

# 电容
c = Capacitor("C1", node1=0, node2=1, capacitance=1e-6)

# 电感
l = Inductor("L1", node1=0, node2=1, inductance=1e-3)

# 电压源
v = VoltageSource("V1", node1=0, node2=1, voltage=10, frequency=1000, phase=0)

# 电流源
i = CurrentSource("I1", node1=0, node2=1, current=0.01, frequency=1000, phase=0)
```

### 5.2 电路构建接口

```python
circuit = Circuit("My Circuit")
n0 = circuit.add_node("GND")
n1 = circuit.add_node("VCC")
circuit.set_ground(n0)

circuit.add_voltage_source("V1", n0, n1, 10)
circuit.add_resistor("R1", n1, n0, 1000)
```

### 5.3 分析接口

```python
# DC分析
dc_analyzer = DCAnalyzer(circuit)
dc_result = dc_analyzer.solve()

# AC分析
ac_analyzer = ACAnalyzer(circuit)
ac_result = ac_analyzer.solve(frequency=1000)

# 频率响应
fr = ac_analyzer.frequency_response(10, 1e6, 1000, node_id=n1)
```

## 6. 错误处理设计

### 6.1 输入验证

- 元件参数验证（电阻>0，电容>0等）
- 节点存在性验证
- 接地点设置验证

### 6.2 异常类型

```python
# 参数错误
class CircuitError(Exception): pass
class InvalidComponentError(CircuitError): pass
class InvalidNodeError(CircuitError): pass

# 分析错误
class AnalysisError(CircuitError): pass
class SingularMatrixError(AnalysisError): pass
class NoGroundError(AnalysisError): pass
```

### 6.3 错误处理策略

- 输入验证：立即抛出异常
- 分析错误：捕获并提供友好提示
- 数值问题：返回NaN或无穷大

## 7. 测试设计

### 7.1 单元测试

- 元件测试：阻抗计算、参数验证
- 电路测试：节点管理、元件添加
- 分析测试：DC/AC分析结果验证

### 7.2 集成测试

- 完整电路分析流程
- 多种电路拓扑测试
- 边界条件测试

### 7.3 性能测试

- 大规模电路分析
- 频率响应计算性能

## 8. 扩展性设计

### 8.1 添加新元件

1. 继承Component基类
2. 实现impedance()方法
3. 在Circuit类中添加添加方法

### 8.2 添加新分析方法

1. 创建新的分析器类
2. 实现solve()方法
3. 定义结果数据类

### 8.3 添加新应用

1. 创建新的应用类
2. 实现核心计算方法
3. 提供to_circuit()方法用于验证
