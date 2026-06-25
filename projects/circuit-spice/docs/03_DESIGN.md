# 电路仿真 SPICE 设计文档

## 1. 系统架构

### 1.1 模块划分

```
circuit-spice/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── components.py        # 电路元件
│   ├── netlist.py           # 网表解析
│   ├── circuit.py           # 电路网络
│   ├── dc_analysis.py       # 直流分析
│   ├── ac_analysis.py       # 交流分析
│   └── transient_analysis.py # 突态分析
├── tests/
│   ├── __init__.py
│   ├── test_components.py   # 元件测试
│   ├── test_netlist.py      # 网表测试
│   ├── test_dc_analysis.py  # DC 分析测试
│   ├── test_ac_analysis.py  # AC 分析测试
│   └── test_transient.py    # 突态分析测试
├── examples/
│   ├── voltage_divider.py   # 分压器示例
│   ├── rc_filter.py         # 滤波器示例
│   └── transient_analysis.py # 突态分析示例
└── docs/
    ├── 01_RESEARCH.md       # 调研文档
    ├── 02_REQUIREMENTS.md   # 需求文档
    ├── 03_DESIGN.md         # 设计文档
    ├── 04_PRODUCT.md        # 产品文档
    └── 05_DEVELOPMENT.md    # 开发文档
```

### 1.2 模块依赖

```
netlist.py
    ↓
circuit.py
    ↓
components.py
    ↓
dc_analysis.py / ac_analysis.py / transient_analysis.py
```

### 1.3 核心类图

```
Component (ABC)
├── Resistor
├── Capacitor
├── Inductor
├── VoltageSource
└── CurrentSource

Circuit
├── components: List[Component]
├── voltage_sources: List[VoltageSource]
├── node_map: Dict[int, int]
└── methods: add_*, build_node_map

NetlistParser
├── parse(text) -> NetlistData
└── parse_file(filepath) -> NetlistData

DCAnalysis
├── circuit: Circuit
└── solve() -> DCOperatingPoint

ACAnalysis
├── circuit: Circuit
├── solve(freq) -> ACSolution
└── frequency_response() -> FrequencyResponse

TransientAnalysis
├── circuit: Circuit
├── method: str
└── solve() -> TransientResult
```

## 2. 详细设计

### 2.1 电路元件设计

#### 2.1.1 元件基类

```python
@dataclass
class Component(ABC):
    name: str
    node1: int
    node2: int
    value: float

    @abstractmethod
    def stamp_dc(self, G, I, node_map, v_idx):
        """直流印记"""
        pass

    @abstractmethod
    def stamp_ac(self, G, freq, node_map, v_idx):
        """交流印记"""
        pass

    @abstractmethod
    def stamp_transient(self, G, C, I, node_map, v_idx, h):
        """突态印记"""
        pass
```

#### 2.1.2 电阻实现

```python
class Resistor(Component):
    def __init__(self, name, node1, node2, resistance):
        super().__init__(name, node1, node2, resistance)
        self.resistance = resistance
        self.conductance = 1.0 / resistance

    def stamp_dc(self, G, I, node_map, v_idx):
        i, j = self._get_indices(node_map)
        g = self.conductance

        if i >= 0: G[i, i] += g
        if j >= 0: G[j, j] += g
        if i >= 0 and j >= 0:
            G[i, j] -= g
            G[j, i] -= g
```

#### 2.1.3 电容实现

```python
class Capacitor(Component):
    def stamp_ac(self, G, freq, node_map, v_idx):
        i, j = self._get_indices(node_map)
        omega = 2 * np.pi * freq
        y = 1j * omega * self.capacitance

        if i >= 0: G[i, i] += y
        if j >= 0: G[j, j] += y
        if i >= 0 and j >= 0:
            G[i, j] -= y
            G[j, i] -= y
```

### 2.2 网表解析设计

#### 2.2.1 解析流程

```
输入文本 → 分行 → 逐行解析 → 构建 NetlistData
                ↓
        忽略注释和空行
                ↓
        识别元件/命令
                ↓
        提取参数
                ↓
        验证数据
```

#### 2.2.2 元件解析

```python
def _parse_component(self, line):
    parts = line.split()
    prefix = parts[0][0].upper()

    if prefix == 'R':
        return self._parse_resistor(parts)
    elif prefix == 'C':
        return self._parse_capacitor(parts)
    # ...
```

#### 2.2.3 数值解析

```python
def _parse_value(self, value_str):
    units = {
        'T': 1e12, 'G': 1e9, 'MEG': 1e6,
        'K': 1e3, 'M': 1e-3, 'U': 1e-6,
        'N': 1e-9, 'P': 1e-12, 'F': 1e-15
    }

    for unit, multiplier in units.items():
        if value_str.endswith(unit):
            return float(value_str[:-len(unit)]) * multiplier

    return float(value_str)
```

### 2.3 直流分析设计

#### 2.3.1 MNA 矩阵构建

```
对于 n 个节点，m 个电压源：
矩阵大小 = (n + m) × (n + m)

G: n×n 电导矩阵
B: n×m 电压源连接
C: m×n 电压源连接 (B 的转置)
D: m×m 通常为零
```

#### 2.3.2 求解算法

```python
def solve(self):
    n = self.circuit.num_nodes
    m = self.circuit.num_v_sources
    size = n + m

    A = np.zeros((size, size))
    b = np.zeros(size)

    # 印记元件
    for comp in self.circuit.components:
        v_idx = n + self.circuit.voltage_sources.index(comp) \
                if isinstance(comp, VoltageSource) else -1
        comp.stamp_dc(A, b, self.circuit.node_map, v_idx)

    # 求解
    x = np.linalg.solve(A, b)

    # 提取结果
    node_voltages = {node: x[idx] for node, idx in self.circuit.node_map.items()}
    branch_currents = {vs.name: x[n + i] for i, vs in enumerate(self.circuit.voltage_sources)}

    return DCOperatingPoint(node_voltages, branch_currents)
```

### 2.4 交流分析设计

#### 2.4.1 复数阻抗

```
电阻: Z = R
电容: Z = 1/(jωC)
电感: Z = jωL
```

#### 2.4.2 频率扫描

```python
def frequency_response(self, f_start, f_stop, points_per_decade):
    frequencies = np.logspace(log10(f_start), log10(f_stop), num_points)
    responses = []

    for freq in frequencies:
        result = self.solve(freq)
        responses.append(result)

    return FrequencyResponse(frequencies, responses)
```

### 2.5 突态分析设计

#### 2.5.1 伴随模型

**电容后向欧拉**:
```
G_eq = C/h
I_eq = (C/h) * v(t) + i(t)
```

**电容梯形法**:
```
G_eq = 2C/h
I_eq = (2C/h) * v(t) + i(t)
```

#### 2.5.2 时间步进

```python
def solve(self, t_step, t_stop):
    for step in range(1, num_steps):
        t = time_points[step]

        # 构建伴随模型矩阵
        A, b = build_companion_matrix(t, h)

        # 求解
        x = np.linalg.solve(A, b)

        # 更新状态
        update_companion_models(x)
```

## 3. 数据结构设计

### 3.1 元件数据

```python
@dataclass
class ComponentData:
    name: str
    type: str  # 'R', 'C', 'L', 'V', 'I'
    node1: int
    node2: int
    value: float
    extra: Dict  # 额外参数
```

### 3.2 网表数据

```python
@dataclass
class NetlistData:
    title: str
    components: List[Dict]
    analyses: List[AnalysisCommand]
    nodes: set
    ground_node: int
```

### 3.3 分析结果

```python
@dataclass
class DCOperatingPoint:
    node_voltages: Dict[int, float]
    branch_currents: Dict[str, float]

@dataclass
class ACSolution:
    frequency: float
    node_voltages: Dict[int, complex]

@dataclass
class FrequencyResponse:
    frequencies: np.ndarray
    responses: List[ACSolution]

@dataclass
class TransientResult:
    time: np.ndarray
    node_voltages: Dict[int, np.ndarray]
    branch_currents: Dict[str, np.ndarray]
```

## 4. 算法设计

### 4.1 线性方程组求解

```python
# 使用 NumPy 的 LAPACK 封装
x = np.linalg.solve(A, b)

# 处理奇异矩阵
try:
    x = np.linalg.solve(A, b)
except np.linalg.LinAlgError:
    x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
```

### 4.2 对数频率生成

```python
frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), num_points)
```

### 4.3 数值积分

```python
# 后向欧拉
g_eq = c / h
i_eq = g_eq * v_prev + i_prev

# 梯形法
g_eq = 2 * c / h
i_eq = g_eq * v_prev + i_prev
```

## 5. 接口设计

### 5.1 公共 API

```python
# 元件
from src.components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource

# 电路
from src.circuit import Circuit

# 分析
from src.dc_analysis import DCAnalysis
from src.ac_analysis import ACAnalysis
from src.transient_analysis import TransientAnalysis

# 网表
from src.netlist import NetlistParser
```

### 5.2 使用模式

```python
# 模式 1: 编程接口
circuit = Circuit("My Circuit")
circuit.add_resistor("R1", 1, 2, 1000)
circuit.add_voltage_source("V1", 0, 1, 10)
circuit.build_node_map()

analyzer = DCAnalysis(circuit)
result = analyzer.solve()

# 模式 2: 网表接口
parser = NetlistParser()
data = parser.parse(netlist_text)
circuit = Circuit.from_netlist(data)
```

## 6. 错误处理设计

### 6.1 元件错误

- 无效电阻值 (负数或零)
- 无效电容值
- 无效电感值
- 节点未定义

### 6.2 分析错误

- 矩阵奇异
- 无解
- 收敛失败

### 6.3 网表错误

- 语法错误
- 未知元件类型
- 缺少必需参数

## 7. 扩展性设计

### 7.1 添加新元件

```python
class NewComponent(Component):
    def stamp_dc(self, G, I, node_map, v_idx):
        # 实现 DC 印记
        pass

    def stamp_ac(self, G, freq, node_map, v_idx):
        # 实现 AC 印记
        pass

    def stamp_transient(self, G, C, I, node_map, v_idx, h):
        # 实现突态印记
        pass
```

### 7.2 添加新分析

```python
class NewAnalysis:
    def __init__(self, circuit):
        self.circuit = circuit

    def solve(self):
        # 实现分析算法
        pass
```

### 7.3 添加新网表命令

```python
def _parse_new_command(self, parts):
    # 解析新命令
    pass
```

## 8. 测试设计

### 8.1 单元测试

- 测试每个元件的印记
- 测试数值解析
- 测试网表解析

### 8.2 集成测试

- 测试完整电路分析
- 测试多元件组合
- 测试边界条件

### 8.3 验证测试

- 与理论值对比
- 与 SPICE 仿真结果对比
- 精度验证

## 9. 性能设计

### 9.1 矩阵优化

- 使用稀疏矩阵 (未来)
- 批量求解 (扫描分析)

### 9.2 内存优化

- 复用矩阵
- 及时释放资源

### 9.3 并行化 (未来)

- 多频率点并行
- 多参数并行
