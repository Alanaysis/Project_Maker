# 自适应控制器 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────┐
│           端到端测试 (E2E)              │  系统级测试
├─────────────────────────────────────────┤
│           集成测试                       │  模块间交互
├─────────────────────────────────────────┤
│           单元测试                       │  独立模块测试
└─────────────────────────────────────────┘
```

### 1.2 测试类型

| 测试类型 | 目的 | 覆盖范围 | 执行频率 |
|---------|------|---------|---------|
| 单元测试 | 验证独立函数/方法 | 每个模块 | 每次提交 |
| 集成测试 | 验证模块交互 | 模块组合 | 每次构建 |
| 系统测试 | 验证完整功能 | 整个系统 | 每次发布 |
| 性能测试 | 验证性能指标 | 关键路径 | 定期执行 |

## 2. 单元测试

### 2.1 测试目录结构

```
tests/
├── __init__.py
├── test_adaptive_controller.py   # 控制器测试
├── test_reference_model.py       # 参考模型测试
├── test_plant_model.py          # 被控对象测试
├── test_parameter_estimator.py  # 参数估计器测试
├── test_simulation.py          # 仿真引擎测试
└── test_analyzer.py            # 性能分析器测试
```

### 2.2 测试用例设计

#### 自校正控制器测试

```python
class TestSelfTuningController:
    def test_initialization(self):
        """测试初始化"""
        controller = SelfTuningController(n_params=2, desired_poles=[0.5])
        assert controller.n_params == 2
        assert controller.desired_poles[0] == 0.5

    def test_parameter_estimation(self):
        """测试参数估计"""
        controller = SelfTuningController(n_params=2, estimation_method="rls")
        plant = create_first_order_plant(time_constant=1.0, gain=1.0)

        for _ in range(500):
            y = plant.get_output()
            phi = np.array([1.0, -y])
            u = controller.compute_control(1.0, y, 0.01, phi)
            plant.update(u, 0.01)

        # 检查参数估计不为零
        assert not np.all(controller.estimated_params == 0)

    def test_pole_placement(self):
        """测试极点配置"""
        controller = SelfTuningController(n_params=2, desired_poles=[0.5])
        controller.estimated_params = np.array([-1.0, 2.0])
        controller._design_controller()

        # 验证增益计算正确
        assert abs(controller.controller_gains[0] - 0.75) < 0.01
        assert abs(controller.controller_gains[1] - 0.25) < 0.01
```

#### 控制器测试

```python
class TestMRACController:
    def test_initialization(self):
        """测试初始化"""
        assert self.controller.adaptation_law == AdaptationLaw.LYAPUNOV
        assert self.controller.gamma == 0.5
        assert "theta_r" in self.controller.params

    def test_compute_control(self):
        """测试控制信号计算"""
        u = self.controller.compute_control(
            reference_input=1.0,
            plant_output=0.5,
            dt=0.01,
        )
        assert isinstance(u, float)
        assert len(self.controller.history) == 1

    def test_parameter_update(self):
        """测试参数更新"""
        initial_theta_r = self.controller.params["theta_r"]

        # 运行几步
        for _ in range(100):
            self.controller.compute_control(1.0, 0.5, 0.01)

        # 验证参数已更新
        assert self.controller.params["theta_r"] != initial_theta_r
```

#### 参考模型测试

```python
class TestReferenceModel:
    def test_first_order_model(self):
        """测试一阶参考模型"""
        model = create_first_order_model(time_constant=1.0, steady_state_gain=1.0)

        # 阶跃响应
        outputs = []
        for _ in range(1000):
            y = model.update(1.0, 0.01)
            outputs.append(y)

        # 验证稳态值接近 1.0
        assert abs(outputs[-1] - 1.0) < 0.1

    def test_second_order_model(self):
        """测试二阶参考模型"""
        model = create_second_order_model(natural_frequency=2.0, damping_ratio=0.7)

        # 阶跃响应
        outputs = []
        for _ in range(2000):
            y = model.update(1.0, 0.005)
            outputs.append(y)

        # 验证稳态值接近 1.0
        assert abs(outputs[-1] - 1.0) < 0.1
```

#### 参数估计器测试

```python
class TestParameterEstimator:
    def test_rls_estimation(self):
        """测试 RLS 估计"""
        n_params = 3
        estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.RLS,
        )

        # 生成测试数据: y = 2*x1 + 3*x2 + 1*x3 + noise
        true_params = np.array([2.0, 3.0, 1.0])
        n_samples = 100

        for i in range(n_samples):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params) + np.random.randn() * 0.1
            estimator.update(phi, y, 0.1)

        # 检查估计参数接近真实参数
        estimated = estimator.get_parameters()
        assert np.allclose(estimated, true_params, atol=0.5)
```

### 2.3 测试运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_adaptive_controller.py -v

# 运行特定测试类
pytest tests/test_adaptive_controller.py::TestMRACController -v

# 运行特定测试方法
pytest tests/test_adaptive_controller.py::TestMRACController::test_lyapunov_adaptation -v
```

## 3. 集成测试

### 3.1 测试场景

```python
class TestIntegration:
    def test_full_mrac_system(self):
        """测试完整的 MRAC 系统"""
        # 创建参考模型
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

        # 创建被控对象 (与参考模型参数不同)
        plant = create_first_order_plant(time_constant=2.0, gain=0.5)

        # 创建自适应控制器
        controller = MRACController(
            reference_model=ref_model,
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=0.3,
        )

        # 运行长时间仿真
        for _ in range(2000):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 验证跟踪误差在减小
        errors = [s.tracking_error for s in controller.history]
        early_error = np.mean(np.abs(errors[:100]))
        late_error = np.mean(np.abs(errors[-100:]))

        assert late_error < early_error
```

### 3.2 仿真引擎测试

```python
class TestSimulationEngine:
    def test_step_response(self):
        """测试阶跃响应仿真"""
        ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
        plant = create_first_order_plant(time_constant=1.0, gain=2.0)
        controller = MRACController(reference_model=ref_model)

        config = SimulationConfig(
            duration=5.0,
            dt=0.01,
            reference_type=ReferenceSignal.STEP,
            reference_amplitude=1.0,
        )

        engine = SimulationEngine(controller, plant, config)
        result = engine.run()

        # 验证结果
        assert len(result.times) == 500
        assert result.metrics["mse"] >= 0
        assert result.metrics["rise_time"] > 0
```

## 4. 系统测试

### 4.1 性能测试

```python
def test_performance_metrics():
    """测试性能指标计算"""
    # 运行仿真
    result = run_simulation()

    # 验证指标
    assert result.metrics["mse"] >= 0
    assert result.metrics["rmse"] >= 0
    assert result.metrics["mae"] >= 0
    assert result.metrics["rise_time"] > 0
    assert result.metrics["settling_time"] > 0
```

### 4.2 鲁棒性测试

```python
def test_robustness():
    """测试控制器鲁棒性"""
    # 测试不同参数的被控对象
    for a in [0.5, 1.0, 2.0]:
        for b in [0.5, 1.0, 2.0]:
            plant = create_first_order_plant(time_constant=1.0/a, gain=b)
            controller = MRACController(reference_model=create_first_order_model())

            # 运行仿真
            for _ in range(1000):
                y = plant.get_output()
                u = controller.compute_control(1.0, y, 0.01)
                plant.update(u, 0.01)

            # 验证系统稳定
            assert not np.any(np.isnan([s.plant_output for s in controller.history]))
```

## 5. 测试工具

### 5.1 测试夹具

```python
@pytest.fixture
def controller():
    """创建测试控制器"""
    ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)
    return MRACController(
        reference_model=ref_model,
        adaptation_law=AdaptationLaw.LYAPUNOV,
        adaptation_gain=0.5,
    )

@pytest.fixture
def plant():
    """创建测试被控对象"""
    return create_first_order_plant(time_constant=1.0, gain=2.0)
```

### 5.2 测试辅助函数

```python
def run_simulation(duration=10.0, dt=0.01):
    """运行仿真辅助函数"""
    ref_model = create_first_order_model()
    plant = create_first_order_plant()
    controller = MRACController(reference_model=ref_model)

    config = SimulationConfig(duration=duration, dt=dt)
    engine = SimulationEngine(controller, plant, config)
    return engine.run()
```

## 6. 测试覆盖率

### 6.1 覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|-----------|------|
| adaptive_controller.py | 90% | 核心模块 |
| reference_model.py | 85% | 参考模型 |
| parameter_estimator.py | 85% | 参数估计 |
| plant_model.py | 80% | 被控对象 |
| simulation.py | 80% | 仿真引擎 |
| analyzer.py | 75% | 性能分析 |

### 6.2 覆盖率检查

```bash
# 安装 coverage
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 7. 测试数据管理

### 7.1 测试数据生成

```python
def generate_test_data(n_samples=100, n_params=3, noise_std=0.1):
    """生成测试数据"""
    true_params = np.random.randn(n_params)
    X = np.random.randn(n_samples, n_params)
    y = X @ true_params + np.random.randn(n_samples) * noise_std

    return X, y, true_params
```

### 7.2 测试数据验证

```python
def validate_estimation(estimated, true_params, atol=0.5):
    """验证估计结果"""
    error = np.linalg.norm(estimated - true_params)
    return error < atol
```

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
name: Python Tests

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
        python -m pip install --upgrade pip
        pip install numpy scipy matplotlib pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 9. 测试报告

### 9.1 测试结果示例

```
============================= test session starts ==============================
platform linux -- Python 3.10.0, pytest-7.0.0, pluggy-1.0.0
collected 20 items

tests/test_adaptive_controller.py::TestMRACController::test_initialization PASSED
tests/test_adaptive_controller.py::TestMRACController::test_compute_control PASSED
tests/test_adaptive_controller.py::TestMRACController::test_parameter_update PASSED
tests/test_adaptive_controller.py::TestMRACController::test_lyapunov_adaptation PASSED
tests/test_adaptive_controller.py::TestIntegration::test_full_mrac_system PASSED

============================== 20 passed in 5.23s ===============================
```

### 9.2 覆盖率报告示例

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/__init__.py                      10      0   100%
src/adaptive_controller.py          120     12    90%
src/reference_model.py              80     12    85%
src/parameter_estimator.py          90     14    84%
src/plant_model.py                  70     14    80%
src/simulation.py                   85     17    80%
src/analyzer.py                     95     24    75%
-----------------------------------------------------
TOTAL                              550     93    83%
```

## 10. 调试技巧

### 10.1 调试输出

```python
# 添加调试输出
import logging
logging.basicConfig(level=logging.DEBUG)

def compute_control(self, r, y, dt):
    logging.debug(f"r={r}, y={y}, dt={dt}")
    # ...
    logging.debug(f"u={u}")
    return u
```

### 10.2 可视化调试

```python
# 绘制中间结果
import matplotlib.pyplot as plt

plt.figure()
plt.plot(times, tracking_error)
plt.xlabel('Time (s)')
plt.ylabel('Tracking Error')
plt.title('Debug: Tracking Error')
plt.grid(True)
plt.savefig('debug_tracking_error.png')
```

### 10.3 断点调试

```python
# 使用 pdb
import pdb

def compute_control(self, r, y, dt):
    pdb.set_trace()  # 设置断点
    # ...
```
