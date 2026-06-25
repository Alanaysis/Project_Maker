# 梯度下降家族 - 测试文档

## 1. 测试概述

本项目采用全面的测试策略，确保代码的正确性、可靠性和性能。

### 1.1 测试目标

- 验证优化算法的正确性
- 确保学习率调度器的准确性
- 检查测试函数的数学性质
- 验证端到端优化流程
- 确保数值稳定性

### 1.2 测试框架

- **pytest**: 测试框架
- **numpy.testing**: 数值比较工具
- **pytest-cov**: 代码覆盖率

## 2. 测试结构

```
tests/
├── __init__.py
├── test_optimizers.py      # 优化器测试
├── test_schedulers.py      # 调度器测试
├── test_functions.py       # 测试函数验证
└── test_integration.py     # 集成测试
```

## 3. 单元测试

### 3.1 优化器测试 (test_optimizers.py)

#### SGD 测试

```python
class TestSGD:
    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.01)
        assert optimizer.learning_rate == 0.01

    def test_invalid_learning_rate(self):
        """测试无效学习率"""
        with pytest.raises(ValueError):
            SGD(learning_rate=-0.01)

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = SGD(learning_rate=0.1)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected = params - 0.1 * grads
        np.testing.assert_array_almost_equal(new_params, expected)

    def test_weight_decay(self):
        """测试权重衰减"""
        optimizer = SGD(learning_rate=0.1, weight_decay=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected_grads = grads + 0.01 * params
        expected = params - 0.1 * expected_grads
        np.testing.assert_array_almost_equal(new_params, expected)
```

#### Momentum 测试

```python
class TestMomentum:
    def test_momentum_state(self):
        """测试动量状态"""
        optimizer = Momentum(learning_rate=0.1, momentum=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'momentum_buffer' in optimizer.state
        np.testing.assert_array_almost_equal(
            optimizer.state['momentum_buffer'], grads
        )
```

#### Adam 测试

```python
class TestAdam:
    def test_bias_correction(self):
        """测试偏差修正"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'exp_avg' in optimizer.state
        assert 'exp_avg_sq' in optimizer.state

        bias_correction1 = 1 - 0.9 ** 1
        bias_correction2 = 1 - 0.999 ** 1
        expected_exp_avg = grads * (1 - 0.9) / bias_correction1
        np.testing.assert_array_almost_equal(
            optimizer.state['exp_avg'] / bias_correction1,
            expected_exp_avg
        )
```

#### 数值稳定性测试

```python
class TestNumericalStability:
    def test_nan_detection(self):
        """测试 NaN 检测"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, np.nan])
        grads = np.array([0.5, 0.5])

        with pytest.raises(ValueError, match="NaN"):
            optimizer.step(params, grads)

    def test_inf_detection(self):
        """测试 Inf 检测"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, np.inf])
        grads = np.array([0.5, 0.5])

        with pytest.raises(ValueError, match="Inf"):
            optimizer.step(params, grads)
```

### 3.2 调度器测试 (test_schedulers.py)

#### StepLR 测试

```python
class TestStepLR:
    def test_step_decay(self):
        """测试阶梯衰减"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        # 初始学习率
        assert optimizer.learning_rate == 0.1

        # 9 步后学习率不变
        for _ in range(9):
            scheduler.step()
        assert optimizer.learning_rate == 0.1

        # 第 10 步学习率衰减
        scheduler.step()
        assert optimizer.learning_rate == 0.01
```

#### CosineAnnealingLR 测试

```python
class TestCosineAnnealingLR:
    def test_cosine_annealing(self):
        """测试余弦退火"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=0.0)

        # 中间点学习率应该接近最小值
        for _ in range(50):
            scheduler.step()
        mid_lr = optimizer.learning_rate
        assert mid_lr < 0.1
        assert mid_lr > scheduler.eta_min
```

#### WarmupScheduler 测试

```python
class TestWarmupScheduler:
    def test_warmup_phase(self):
        """测试预热阶段"""
        optimizer = SGD(learning_rate=0.0)
        scheduler = WarmupScheduler(optimizer, warmup_epochs=10, target_lr=0.1)

        # 预热阶段学习率应该线性增加
        for i in range(10):
            scheduler.step()
            expected_lr = 0.0 + (0.1 - 0.0) * (i + 1) / 10
            assert abs(optimizer.learning_rate - expected_lr) < 1e-10
```

### 3.3 测试函数验证 (test_functions.py)

#### 梯度一致性测试

```python
class TestFunctionProperties:
    def test_gradient_consistency(self):
        """测试梯度一致性"""
        epsilon = 1e-6

        functions = [
            QuadraticFunction(),
            RosenbrockFunction(),
            HimmelblauFunction()
        ]

        for func in functions:
            x = np.random.uniform(-2, 2, size=2)

            # 解析梯度
            grad_analytical = func.gradient(x)

            # 数值梯度
            grad_numerical = np.zeros_like(x)
            for i in range(len(x)):
                x_plus = x.copy()
                x_minus = x.copy()
                x_plus[i] += epsilon
                x_minus[i] -= epsilon
                grad_numerical[i] = (func(x_plus) - func(x_minus)) / (2 * epsilon)

            # 比较
            np.testing.assert_array_almost_equal(
                grad_analytical, grad_numerical, decimal=5
            )
```

## 4. 集成测试 (test_integration.py)

### 4.1 优化流程测试

```python
class TestOptimizationIntegration:
    def test_sgd_on_quadratic(self):
        """测试 SGD 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)
        assert result['fun'] < 1e-6
```

### 4.2 调度器集成测试

```python
class TestSchedulerIntegration:
    def test_step_lr_with_sgd(self):
        """测试阶梯衰减与 SGD 结合"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=100, gamma=0.5)
        x0 = np.array([3.0, 3.0])

        # 手动运行优化
        x = x0.copy()
        for i in range(500):
            grad = func.gradient(x)
            x = optimizer.step(x, grad)
            scheduler.step()

        # 应该收敛
        assert func(x) < 1e-4
```

### 4.3 优化器对比测试

```python
class TestCompareOptimizers:
    def test_compare_on_quadratic(self):
        """测试在二次函数上对比优化器"""
        func = QuadraticFunction(a=1.0, b=1.0)
        x0 = np.array([3.0, 3.0])

        optimizers = {
            'SGD': SGD(learning_rate=0.1),
            'Momentum': Momentum(learning_rate=0.01, momentum=0.9),
            'Adam': Adam(learning_rate=0.01),
        }

        results = compare_optimizers(func, optimizers, x0, max_iter=1000, tol=1e-6)

        # 所有优化器都应该收敛
        for name, result in results.items():
            assert result['success'], f"{name} failed to converge"
```

### 4.4 边界情况测试

```python
class TestEdgeCases:
    def test_zero_gradient(self):
        """测试零梯度情况"""
        func = QuadraticFunction(a=0.0, b=0.0)  # 常数函数
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([1.0, 1.0])

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 应该立即收敛
        assert result['niter'] == 1
        assert result['success']

    def test_already_at_minimum(self):
        """测试已经在最小值的情况"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([0.0, 0.0])  # 最小值点

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 应该立即收敛
        assert result['success']
        assert result['niter'] == 1
```

## 5. 测试运行

### 5.1 运行所有测试

```bash
# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 运行并显示覆盖率
pytest --cov=src

# 运行并生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html
```

### 5.2 运行特定测试

```bash
# 运行优化器测试
pytest tests/test_optimizers.py

# 运行调度器测试
pytest tests/test_schedulers.py

# 运行特定测试类
pytest tests/test_optimizers.py::TestSGD

# 运行特定测试方法
pytest tests/test_optimizers.py::TestSGD::test_basic_step
```

### 5.3 测试配置

**pytest.ini**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 6. 测试覆盖率

### 6.1 覆盖率目标

- 核心优化器: 100%
- 学习率调度器: 100%
- 测试函数: 100%
- 可视化模块: 90%+
- 工具函数: 100%

### 6.2 覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=term-missing

# 输出示例:
# Name                          Stmts   Miss  Cover   Missing
# -----------------------------------------------------------
# src/optimizers/__init__.py        5      0   100%
# src/optimizers/base.py           45      0   100%
# src/optimizers/sgd.py            30      0   100%
# src/optimizers/momentum.py       40      0   100%
# src/optimizers/adam.py           60      0   100%
# ...
```

## 7. 性能测试

### 7.1 基准测试

```python
import time

def benchmark_optimization():
    """基准测试优化性能"""
    func = QuadraticFunction(a=1.0, b=1.0)
    x0 = np.array([3.0, 3.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.1),
        'Adam': Adam(learning_rate=0.01),
    }

    for name, optimizer in optimizers.items():
        start = time.time()
        result = optimize(func, optimizer, x0.copy(), max_iter=1000)
        end = time.time()

        print(f"{name}: {end-start:.4f}s, {result['niter']} iterations")
```

### 7.2 性能指标

- 优化时间
- 迭代次数
- 内存使用
- 收敛速度

## 8. 持续集成

### 8.1 GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 9. 测试最佳实践

### 9.1 测试命名

- 使用描述性的测试名称
- 遵循 `test_<功能>_<场景>` 格式
- 示例: `test_sgd_basic_step`, `test_adam_bias_correction`

### 9.2 测试隔离

- 每个测试独立运行
- 不依赖其他测试的状态
- 使用 fixtures 管理测试数据

### 9.3 断言清晰

- 使用明确的断言
- 提供有用的错误信息
- 使用 `pytest.raises` 测试异常

### 9.4 测试数据

- 使用有意义的测试数据
- 覆盖正常和边界情况
- 使用参数化测试

## 10. 故障排除

### 10.1 常见问题

**测试失败**:
- 检查数值精度
- 验证数学公式
- 检查边界条件

**性能问题**:
- 减少测试数据规模
- 优化测试代码
- 使用并行测试

**内存问题**:
- 及时释放资源
- 减少数据复制
- 使用内存分析工具

### 10.2 调试技巧

```python
# 使用 pytest 调试
pytest --pdb  # 失败时进入调试器
pytest -s     # 显示 print 输出
pytest -x     # 首次失败后停止
```

## 11. 测试维护

### 11.1 定期审查

- 定期审查测试覆盖率
- 更新过时的测试
- 添加新功能的测试

### 11.2 测试重构

- 提取公共测试逻辑
- 使用 fixtures 管理状态
- 保持测试代码简洁

### 11.3 文档更新

- 更新测试文档
- 记录测试策略
- 分享测试经验
