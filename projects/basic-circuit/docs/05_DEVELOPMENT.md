# 开发文档：基本电路模拟

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip 或 conda
- Git

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-cov
```

### 1.3 依赖列表

| 包 | 版本 | 用途 |
|----|------|------|
| numpy | >=1.21.0 | 数值计算 |
| matplotlib | >=3.5.0 | 可视化 |
| scipy | >=1.7.0 | 科学计算 |
| pytest | >=6.0 | 测试框架 |
| pytest-cov | >=2.0 | 覆盖率 |

## 2. 项目结构

```
basic-circuit/
├── src/
│   ├── __init__.py          # 包初始化，导出公共API
│   ├── components.py        # 电路元件定义
│   ├── circuit.py           # 电路网络管理
│   ├── dc_analysis.py       # 直流电路分析
│   ├── ac_analysis.py       # 交流电路分析
│   └── applications.py      # 实际应用电路
├── tests/
│   ├── __init__.py
│   ├── test_components.py   # 元件测试
│   ├── test_circuit.py      # 电路测试
│   ├── test_dc_analysis.py  # DC分析测试
│   ├── test_ac_analysis.py  # AC分析测试
│   └── test_applications.py # 应用测试
├── examples/
│   ├── basic_dc_circuit.py  # DC电路示例
│   ├── ac_analysis_demo.py  # AC分析示例
│   └── filter_design.py     # 滤波器设计示例
├── docs/
│   ├── 01_RESEARCH.md       # 调研文档
│   ├── 02_REQUIREMENTS.md   # 需求文档
│   ├── 03_DESIGN.md         # 设计文档
│   ├── 04_PRODUCT.md        # 产品文档
│   └── 05_DEVELOPMENT.md    # 开发文档
├── requirements.txt
├── setup.py
└── README.md
```

## 3. 开发流程

### 3.1 模块开发顺序

1. **元件模块** (components.py)
   - 定义基类Component
   - 实现Resistor、Capacitor、Inductor
   - 实现VoltageSource、CurrentSource
   - 实现ohms_law、power函数

2. **电路模块** (circuit.py)
   - 实现Node类
   - 实现Circuit类
   - 实现节点管理
   - 实现元件添加和查询

3. **DC分析模块** (dc_analysis.py)
   - 实现DCAnalyzer类
   - 实现节点分析法
   - 实现KCL/KVL验证
   - 实现辅助函数

4. **AC分析模块** (ac_analysis.py)
   - 实现Phasor类
   - 实现ACAnalyzer类
   - 实现频率响应计算
   - 实现阻抗函数

5. **应用模块** (applications.py)
   - 实现VoltageDivider
   - 实现RCFilter、RLCFilter
   - 实现Amplifier
   - 实现Integrator、Differentiator

### 3.2 测试驱动开发

```python
# 1. 先写测试
def test_resistor_impedance():
    r = Resistor("R1", 0, 1, 1000)
    assert r.impedance(1000) == complex(1000, 0)

# 2. 再写实现
class Resistor(Component):
    def impedance(self, frequency):
        return complex(self.resistance, 0)
```

## 4. 代码规范

### 4.1 命名规范

- **类名**：PascalCase (如 `Resistor`, `DCAnalyzer`)
- **函数名**：snake_case (如 `add_resistor`, `solve`)
- **变量名**：snake_case (如 `node_voltages`, `branch_currents`)
- **常量**：UPPER_CASE (如 `ComponentType`)

### 4.2 文档规范

```python
def impedance(self, frequency: float) -> complex:
    """
    计算阻抗

    参数:
        frequency: 频率 (赫兹)

    返回:
        complex: 阻抗值

    示例:
        >>> r = Resistor("R1", 0, 1, 1000)
        >>> r.impedance(1000)
        (1000+0j)
    """
    return complex(self.resistance, 0)
```

### 4.3 类型提示

```python
from typing import Dict, List, Optional, Tuple

def solve(self) -> DCResult:
    ...

def frequency_response(
    self,
    f_start: float,
    f_stop: float,
    f_points: int = 1000,
    node_id: Optional[int] = None
) -> FrequencyResponse:
    ...
```

## 5. 核心实现

### 5.1 元件阻抗计算

```python
# 电阻：与频率无关
class Resistor(Component):
    def impedance(self, frequency: float = 0) -> complex:
        return complex(self.resistance, 0)

# 电容：Z = 1/(jωC) = -j/(2πfC)
class Capacitor(Component):
    def impedance(self, frequency: float) -> complex:
        if frequency == 0:
            return complex(float('inf'), 0)  # 直流开路
        omega = 2 * np.pi * frequency
        return complex(0, -1.0 / (omega * self.capacitance))

# 电感：Z = jωL
class Inductor(Component):
    def impedance(self, frequency: float) -> complex:
        omega = 2 * np.pi * frequency
        return complex(0, omega * self.inductance)
```

### 5.2 节点分析法

```python
def _nodal_analysis(self) -> Dict[int, float]:
    """MNA方法求解节点电压"""
    nodes = list(self.circuit.nodes.keys())
    n = len(nodes)
    node_index = {nid: i for i, nid in enumerate(nodes)}

    # MNA矩阵
    vs_list = self.circuit.get_voltage_sources()
    m = len(vs_list)
    size = n + m
    A = np.zeros((size, size))
    b = np.zeros(size)

    # 填充导纳矩阵
    for comp in self.circuit.components:
        if isinstance(comp, Resistor):
            g = 1.0 / comp.resistance
            i1 = node_index.get(comp.node1)
            i2 = node_index.get(comp.node2)
            # ... 填充矩阵

    # 处理电压源
    for idx, vs in enumerate(vs_list):
        k = n + idx
        # ... 添加约束

    # 移除接地点行列
    # ...

    # 求解
    x = np.linalg.solve(A_reduced, b_reduced)

    # 提取结果
    # ...
```

### 5.3 频率响应计算

```python
def frequency_response(self, f_start, f_stop, f_points, node_id):
    """计算频率响应"""
    frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), f_points)
    magnitude = np.zeros(f_points)
    phase = np.zeros(f_points)

    for i, freq in enumerate(frequencies):
        result = self.solve(freq)
        v_out = result.node_voltages.get(node_id, 0)
        v_in = vs_list[0].voltage

        transfer = v_out / v_in
        magnitude[i] = abs(transfer)
        phase[i] = np.degrees(np.angle(transfer))

    return FrequencyResponse(frequencies, magnitude, phase)
```

## 6. 测试

### 6.1 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src --cov-report=html

# 运行特定测试文件
pytest tests/test_components.py

# 运行特定测试类
pytest tests/test_components.py::TestResistor

# 运行特定测试方法
pytest tests/test_components.py::TestResistor::test_impedance
```

### 6.2 测试示例

```python
import pytest
from src.components import Resistor

class TestResistor:
    def test_create_resistor(self):
        r = Resistor("R1", 0, 1, 1000)
        assert r.name == "R1"
        assert r.resistance == 1000

    def test_invalid_resistance(self):
        with pytest.raises(ValueError):
            Resistor("R1", 0, 1, 0)
        with pytest.raises(ValueError):
            Resistor("R1", 0, 1, -100)

    def test_impedance(self):
        r = Resistor("R1", 0, 1, 1000)
        assert r.impedance(0) == complex(1000, 0)
        assert r.impedance(1000) == complex(1000, 0)

    def test_conductance(self):
        r = Resistor("R1", 0, 1, 1000)
        assert r.conductance() == 0.001
```

### 6.3 测试覆盖

目标覆盖率：> 90%

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 7. 调试

### 7.1 常见问题

**问题1：奇异矩阵**
```
LinAlgError: Singular matrix
```
原因：电路无法求解，可能是：
- 未设置接地点
- 电路拓扑问题
- 元件参数问题

**问题2：节点不存在**
```
ValueError: 节点 99 不存在
```
原因：使用了未创建的节点编号

**问题3：阻抗为无穷大**
```
Capacitor @ DC: impedance = inf
```
原因：电容在直流时开路

### 7.2 调试技巧

```python
# 查看电路结构
print(circuit.summary())

# 查看分析结果
print(result.summary())

# 验证KCL/KVL
print(result.kcl_violations)
print(result.kvl_violations)

# 打印中间结果
print(f"导纳矩阵:\n{A}")
print(f"电流向量:\n{b}")
```

## 8. 性能优化

### 8.1 矩阵运算

- 使用NumPy进行矩阵运算
- 避免Python循环，使用向量化操作
- 使用稀疏矩阵处理大规模电路

### 8.2 频率响应计算

- 使用对数频率间隔
- 预分配数组内存
- 并行计算多个频率点

### 8.3 缓存

- 缓存导纳矩阵分解结果
- 缓存元件阻抗计算

## 9. 扩展开发

### 9.1 添加新元件

```python
# 1. 定义新元件类
class Diode(Component):
    """二极管"""
    forward_voltage: float = 0.7

    def __post_init__(self):
        self.component_type = ComponentType.DIODE

    def impedance(self, frequency: float) -> complex:
        # 简化模型
        return complex(self.forward_voltage / 0.026, 0)

# 2. 在Circuit类中添加方法
def add_diode(self, name, node1, node2, forward_voltage=0.7):
    d = Diode(name=name, node1=node1, node2=node2,
              forward_voltage=forward_voltage)
    self.components.append(d)
    return d
```

### 9.2 添加新分析方法

```python
# 1. 定义结果类
@dataclass
class TransientResult:
    time: np.ndarray
    voltages: Dict[int, np.ndarray]
    currents: Dict[str, np.ndarray]

# 2. 实现分析器
class TransientAnalyzer:
    def __init__(self, circuit: Circuit):
        self.circuit = circuit

    def solve(self, t_start, t_stop, t_step) -> TransientResult:
        # 瞬态分析实现
        ...
```

### 9.3 添加新应用

```python
class Transformer:
    """变压器"""
    def __init__(self, l_primary, l_secondary, coupling):
        ...

    def turns_ratio(self):
        ...

    def transfer_function(self, frequency):
        ...
```

## 10. 发布

### 10.1 版本管理

```bash
# 更新版本号
# setup.py
version="1.0.0"

# 提交更改
git add .
git commit -m "release: v1.0.0"
git tag v1.0.0
git push origin v1.0.0
```

### 10.2 打包

```bash
# 安装打包工具
pip install setuptools wheel

# 打包
python setup.py sdist bdist_wheel

# 检查包
twine check dist/*
```

### 10.3 发布到PyPI

```bash
# 安装twine
pip install twine

# 上传
twine upload dist/*
```

## 11. 贡献指南

### 11.1 开发流程

1. Fork项目
2. 创建特性分支
3. 编写代码和测试
4. 提交Pull Request

### 11.2 代码审查

- 代码风格一致
- 测试覆盖充分
- 文档完整
- 无性能问题

### 11.3 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
perf: 性能优化
```
