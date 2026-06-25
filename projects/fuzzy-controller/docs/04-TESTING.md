# 测试文档

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**：测试单个组件的功能
2. **集成测试**：测试组件间的协作
3. **系统测试**：测试完整的控制流程
4. **性能测试**：测试系统性能

### 1.2 测试覆盖率目标

- 语句覆盖率：>90%
- 分支覆盖率：>80%
- 函数覆盖率：100%

## 2. 测试文件结构

```
tests/
├── __init__.py
├── test_fuzzy_set.py      # 模糊集合测试
├── test_fuzzifier.py      # 模糊化器测试
├── test_rule_engine.py    # 规则引擎测试
├── test_defuzzifier.py    # 去模糊化器测试
├── test_controller.py     # 控制器测试
├── test_sugeno.py         # Sugeno 推理测试
└── test_applications.py   # 温度/速度控制应用测试
```

## 3. 测试用例设计

### 3.1 模糊集合测试

#### 三角形隶属函数测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 边界点 | x=a | 0.0 | 左端点 |
| 峰值点 | x=b | 1.0 | 峰值 |
| 边界点 | x=c | 0.0 | 右端点 |
| 中间点 | x=(a+b)/2 | 0.5 | 上升段中点 |
| 范围外 | x<a | 0.0 | 左侧外部 |
| 范围外 | x>c | 0.0 | 右侧外部 |

#### 梯形隶属函数测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 左端点 | x=a | 0.0 | 左端点 |
| 左肩 | x=b | 1.0 | 左肩点 |
| 平台 | x=(b+c)/2 | 1.0 | 平台中点 |
| 右肩 | x=c | 1.0 | 右肩点 |
| 右端点 | x=d | 0.0 | 右端点 |

#### 高斯隶属函数测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 中心点 | x=m | 1.0 | 均值点 |
| 对称性 | x=m+k vs x=m-k | 相等 | 对称性验证 |
| 宽度 | x=m±2σ | <0.5 | 宽度验证 |

### 3.2 模糊化测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 单变量 | {'temp': 25} | {'temp': {'cold':0, 'warm':0.5, 'hot':0.5}} | 基本模糊化 |
| 多变量 | {'temp':25, 'hum':50} | 两个变量的隶属度 | 多变量模糊化 |
| 边界值 | {'temp': 0} | {'temp': {'cold':1, ...}} | 最小值 |
| 超范围 | {'temp': 50} | {'temp': {'hot':1, ...}} | 超出论域 |
| 未定义变量 | {'press': 100} | ValueError | 错误处理 |

### 3.3 规则引擎测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| IS 规则 | hot=0.8 | activation=0.8 | 简单IS规则 |
| AND 规则 | hot=0.8, humid=0.6 | activation=0.6 | AND连接 |
| OR 规则 | hot=0.8, humid=0.6 | activation=0.8 | OR连接 |
| NOT 规则 | cold=0.3 | activation=0.7 | NOT操作 |
| 权重规则 | hot=0.8, weight=0.5 | activation=0.4 | 权重应用 |

### 3.4 去模糊化测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 重心法 | 对称三角形 | 中心值 | COG验证 |
| 最大隶属度法 | 梯形 | 平台中心 | MOM验证 |
| 零隶属度 | 全零 | 论域中心 | 边界情况 |
| 非对称 | 偏左三角形 | <中心 | 非对称验证 |

### 3.5 控制器测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|---------|------|---------|------|
| 冷温度 | 5°C | 低速 | 低温控制 |
| 温暖温度 | 20°C | 中速 | 中温控制 |
| 热温度 | 35°C | 高速 | 高温控制 |
| 单调性 | 递增温度 | 递增输出 | 趋势验证 |
| 多输入 | temp+humidity | fan+humidifier | 多输入输出 |

## 4. 测试运行

### 4.1 运行所有测试

```bash
# 进入项目目录
cd projects/fuzzy-controller

# 运行所有测试
python -m pytest tests/

# 运行带详细输出的测试
python -m pytest tests/ -v

# 运行带覆盖率的测试
python -m pytest tests/ --cov=src
```

### 4.2 运行单个测试文件

```bash
python -m pytest tests/test_fuzzy_set.py -v
```

### 4.3 运行单个测试类

```bash
python -m pytest tests/test_fuzzy_set.py::TestTriangularMF -v
```

### 4.4 运行单个测试方法

```bash
python -m pytest tests/test_fuzzy_set.py::TestTriangularMF::test_basic_functionality -v
```

## 5. 测试数据

### 5.1 温度控制测试数据

```python
test_cases = [
    (5, 'slow'),     # 冷
    (10, 'slow'),    # 冷
    (15, 'slow'),    # 冷偏温
    (20, 'medium'),  # 温暖
    (25, 'medium'),  # 温暖
    (30, 'fast'),    # 热
    (35, 'fast'),    # 热
]
```

### 5.2 预期输出范围

| 温度范围 | 风扇转速范围 | 类别 |
|---------|-------------|------|
| 0-10°C | 0-30% | 慢速 |
| 10-25°C | 25-60% | 中速 |
| 25-40°C | 50-100% | 快速 |

## 6. 持续集成

### 6.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install numpy pytest pytest-cov
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=src --cov-report=xml
```

## 7. 测试报告

### 7.1 覆盖率报告

```bash
# 生成HTML覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 7.2 测试结果示例

```
tests/test_fuzzy_set.py::TestTriangularMF::test_basic_functionality PASSED
tests/test_fuzzy_set.py::TestTriangularMF::test_outside_range PASSED
tests/test_fuzzy_set.py::TestTriangularMF::test_numpy_array PASSED
tests/test_fuzzy_set.py::TestTrapezoidalMF::test_basic_functionality PASSED
tests/test_fuzzy_set.py::TestGaussianMF::test_basic_functionality PASSED
tests/test_fuzzy_set.py::TestFuzzySet::test_membership PASSED
tests/test_fuzzy_set.py::TestFuzzySet::test_complement PASSED
tests/test_fuzzy_set.py::TestFuzzySet::test_intersect PASSED
tests/test_fuzzy_set.py::TestFuzzySet::test_union PASSED
tests/test_fuzzy_set.py::TestFuzzySet::test_alpha_cut PASSED

---------- coverage: platform linux, python 3.10.x ----------
Name                        Stmts   Miss  Cover
-------------------------------------------------
src/fuzzy_set.py              120      8    93%
src/fuzzifier.py               45      2    96%
src/rule_engine.py             85      5    94%
src/defuzzifier.py             60      3    95%
src/controller.py              95      6    94%
-------------------------------------------------
TOTAL                         405     24    94%
```

## 8. 调试技巧

### 8.1 使用 control_step_by_step

```python
results = controller.control_step_by_step({'temperature': 25})

# 查看模糊化结果
print("模糊输入:", results['fuzzy_inputs'])

# 查看规则激活
print("规则激活:", results['rule_activations'])

# 查看精确输出
print("精确输出:", results['crisp_outputs'])
```

### 8.2 使用 pytest 调试

```bash
# 失败时进入调试器
python -m pytest tests/ --pdb

# 显示局部变量
python -m pytest tests/ -v --tb=long
```
