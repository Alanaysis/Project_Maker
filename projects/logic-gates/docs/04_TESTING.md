# 测试文档：逻辑门模拟器

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────────────────────┐
│                    测试金字塔                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │              端到端测试 (E2E)                    │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │              集成测试                            │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │              单元测试                            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 测试覆盖目标

- **单元测试覆盖率**: 90%+
- **集成测试覆盖率**: 80%+
- **关键路径覆盖**: 100%

## 2. 单元测试

### 2.1 逻辑门测试

#### AND门测试

```python
class TestAndGate:
    """AND门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = AndGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "AND"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 0

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1

    def test_invalid_input_count(self):
        """测试无效输入数量"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0)

    def test_invalid_input_value(self):
        """测试无效输入值"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0, 2)

    def test_callable(self):
        """测试可调用接口"""
        assert self.gate(1, 1) == 1
        assert self.gate(0, 1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([0, 1], 0) in table
        assert ([1, 0], 0) in table
        assert ([1, 1], 1) in table
```

#### 所有逻辑门测试

```python
# 测试所有逻辑门
gates = [AndGate(), OrGate(), NotGate(), XorGate(), NandGate(), NorGate(), XnorGate()]

for gate in gates:
    # 测试名称
    assert gate.name is not None

    # 测试输入数量
    assert gate.num_inputs > 0

    # 测试真值表
    table = gate.truth_table()
    assert len(table) == 2 ** gate.num_inputs
```

### 2.2 组合电路测试

#### 多路选择器测试

```python
class TestMultiplexer:
    """多路选择器测试"""

    def test_2to1_mux(self):
        """测试2选1多路选择器"""
        mux = Multiplexer(1)
        assert mux.evaluate([0, 1], [0]) == 0
        assert mux.evaluate([0, 1], [1]) == 1

    def test_4to1_mux(self):
        """测试4选1多路选择器"""
        mux = Multiplexer(2)
        data = [1, 0, 1, 0]

        assert mux.evaluate(data, [0, 0]) == data[0]
        assert mux.evaluate(data, [1, 0]) == data[1]
        assert mux.evaluate(data, [0, 1]) == data[2]
        assert mux.evaluate(data, [1, 1]) == data[3]
```

#### 加法器测试

```python
class TestHalfAdder:
    """半加器测试"""

    def test_all_inputs(self):
        """测试所有输入组合"""
        ha = HalfAdder()

        sum_val, carry = ha.evaluate(0, 0)
        assert sum_val == 0 and carry == 0

        sum_val, carry = ha.evaluate(0, 1)
        assert sum_val == 1 and carry == 0

        sum_val, carry = ha.evaluate(1, 0)
        assert sum_val == 1 and carry == 0

        sum_val, carry = ha.evaluate(1, 1)
        assert sum_val == 0 and carry == 1
```

### 2.3 时序电路测试

#### D触发器测试

```python
class TestDFlipFlop:
    """D触发器测试"""

    def test_rising_edge(self):
        """测试上升沿触发"""
        ff = DFlipFlop()

        ff.set_data(1)

        result = ff.clock(0)
        assert result['Q'] == 0  # 还没触发

        result = ff.clock(1)
        assert result['Q'] == 1  # 触发

    def test_hold_on_falling_edge(self):
        """测试下降沿保持"""
        ff = DFlipFlop()

        ff.set_data(1)
        ff.clock(1)  # 上升沿触发

        ff.set_data(0)
        result = ff.clock(0)  # 下降沿，保持
        assert result['Q'] == 1  # 保持
```

#### 计数器测试

```python
class TestCounter:
    """计数器测试"""

    def test_increment(self):
        """测试递增"""
        counter = Counter(4)

        assert counter.get_count() == 0

        counter.increment()
        assert counter.get_count() == 1

        counter.increment()
        assert counter.get_count() == 2

    def test_overflow(self):
        """测试溢出"""
        counter = Counter(4)

        for _ in range(15):
            counter.increment()
        assert counter.get_count() == 15

        counter.increment()
        assert counter.get_count() == 0  # 溢出
```

## 3. 集成测试

### 3.1 电路测试

```python
class TestCircuit:
    """电路测试"""

    def test_evaluate_simple(self):
        """测试简单电路"""
        circuit = Circuit("Test Circuit")
        circuit.add_gate(AndGate(), "AND1")
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)

        circuit.set_inputs({"A": 1, "B": 1})
        results = circuit.evaluate()
        assert results["AND1"] == 1

    def test_evaluate_multi_gate(self):
        """测试多门电路"""
        circuit = Circuit("Test Circuit")
        circuit.add_gate(AndGate(), "AND1")
        circuit.add_gate(OrGate(), "OR1")
        circuit.add_gate(NotGate(), "NOT1")

        # AND1 = A AND B
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)

        # OR1 = A OR B
        circuit.connect("A", "OR1", 0)
        circuit.connect("B", "OR1", 1)

        # NOT1 = NOT AND1
        circuit.connect("AND1", "NOT1", 0)

        # 测试 A=1, B=1
        circuit.set_inputs({"A": 1, "B": 1})
        results = circuit.evaluate()
        assert results["AND1"] == 1
        assert results["OR1"] == 1
        assert results["NOT1"] == 0
```

### 3.2 真值表测试

```python
class TestHalfAdder:
    """半加器测试"""

    def test_truth_table(self):
        """测试真值表"""
        circuit = Circuit("Half Adder")
        circuit.add_gate(XorGate(), "XOR")
        circuit.add_gate(AndGate(), "AND")

        circuit.connect("A", "XOR", 0)
        circuit.connect("B", "XOR", 1)
        circuit.connect("A", "AND", 0)
        circuit.connect("B", "AND", 1)

        circuit.mark_as_input("A")
        circuit.mark_as_input("B")
        circuit.mark_as_output("XOR")
        circuit.mark_as_output("AND")

        table = circuit.get_truth_table()
        assert len(table) == 4

        for row in table:
            a = row["inputs"]["A"]
            b = row["inputs"]["B"]
            sum_out = row["outputs"]["XOR"]
            carry_out = row["outputs"]["AND"]

            assert sum_out == (a ^ b)
            assert carry_out == (a & b)
```

## 4. 测试工具

### 4.1 测试夹具

```python
@pytest.fixture
def and_gate():
    """AND门夹具"""
    return AndGate()

@pytest.fixture
def half_adder_circuit():
    """半加器电路夹具"""
    circuit = Circuit("Half Adder")
    circuit.add_gate(XorGate(), "XOR")
    circuit.add_gate(AndGate(), "AND")
    circuit.connect("A", "XOR", 0)
    circuit.connect("B", "XOR", 1)
    circuit.connect("A", "AND", 0)
    circuit.connect("B", "AND", 1)
    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_output("XOR")
    circuit.mark_as_output("AND")
    return circuit
```

### 4.2 参数化测试

```python
@pytest.mark.parametrize("a,b,expected", [
    (0, 0, 0),
    (0, 1, 0),
    (1, 0, 0),
    (1, 1, 1),
])
def test_and_gate(a, b, expected):
    """参数化测试AND门"""
    gate = AndGate()
    assert gate.evaluate(a, b) == expected
```

### 4.3 测试标记

```python
@pytest.mark.slow
def test_large_circuit():
    """大型电路测试（标记为慢速测试）"""
    pass

@pytest.mark.integration
def test_cpu_integration():
    """CPU集成测试"""
    pass
```

## 5. 测试运行

### 5.1 运行所有测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行带详细输出的测试
python -m pytest tests/ -v

# 运行带覆盖率的测试
python -m pytest tests/ --cov=src
```

### 5.2 运行特定测试

```bash
# 运行特定测试文件
python -m pytest tests/test_gates.py

# 运行特定测试类
python -m pytest tests/test_gates.py::TestAndGate

# 运行特定测试方法
python -m pytest tests/test_gates.py::TestAndGate::test_evaluate_11
```

### 5.3 测试配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 6. 测试报告

### 6.1 覆盖率报告

```bash
# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 6.2 测试结果示例

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1
collected 198 items

tests/test_gates.py::TestAndGate::test_name PASSED                       [  0%]
tests/test_gates.py::TestAndGate::test_num_inputs PASSED                 [  1%]
tests/test_gates.py::TestAndGate::test_evaluate_00 PASSED                [  1%]
...
tests/test_applications.py::TestCacheLine::test_clear PASSED             [100%]

============================= 198 passed in 0.05s ==============================
```

## 7. 持续集成

### 7.1 GitHub Actions配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### 7.2 本地CI脚本

```bash
#!/bin/bash
# run_tests.sh

echo "Running tests..."
python -m pytest tests/ -v --cov=src

echo "Generating coverage report..."
python -m pytest tests/ --cov=src --cov-report=html

echo "Tests complete!"
```
