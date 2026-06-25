# 状态空间模型 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────┐
│         集成测试                      │
│   (完整工作流、端到端测试)            │
├─────────────────────────────────────┤
│         单元测试                      │
│   (单个函数/方法测试)                 │
├─────────────────────────────────────┤
│         数学验证                      │
│   (数值精度、边界条件)                │
└─────────────────────────────────────┘
```

### 1.2 测试目标

| 目标 | 描述 | 优先级 |
|------|------|--------|
| 功能正确性 | 验证算法实现正确 | 高 |
| 数值精度 | 确保计算结果精确 | 高 |
| 边界条件 | 处理极值和特殊情况 | 中 |
| 错误处理 | 验证异常情况处理 | 中 |
| 性能 | 测量计算效率 | 低 |

## 2. 单元测试

### 2.1 StateSpaceModel测试

#### 测试用例：初始化

```python
def test_initialization():
    """测试模型初始化"""
    A = np.array([[0.9, 0.1], [-0.1, 0.8]])
    B = np.array([[1.0], [0.5]])
    C = np.array([[1.0, 0.0]])
    D = np.array([[0.0]])

    model = StateSpaceModel(A, B, C, D)

    assert model.n_states == 2
    assert model.n_inputs == 1
    assert model.n_outputs == 1
    np.testing.assert_array_almost_equal(model.A, A)
```

#### 测试用例：仿真

```python
def test_simulate():
    """测试系统仿真"""
    x0 = np.array([1.0, 0.0])
    u = np.zeros((10, 1))
    states, outputs = model.simulate(x0, u)

    assert states.shape == (11, 2)
    assert outputs.shape == (10, 1)
    np.testing.assert_array_almost_equal(states[0], x0)
```

#### 测试用例：稳定性

```python
def test_stability():
    """测试稳定性判断"""
    # 稳定系统
    A_stable = np.array([[0.5, 0.0], [0.0, 0.3]])
    model_stable = StateSpaceModel(A_stable, B, C)
    assert model_stable.is_stable()

    # 不稳定系统
    A_unstable = np.array([[1.5, 0.0], [0.0, 0.3]])
    model_unstable = StateSpaceModel(A_unstable, B, C)
    assert not model_unstable.is_stable()
```

### 2.2 KalmanFilter测试

#### 测试用例：预测步骤

```python
def test_predict():
    """测试预测步骤"""
    u = np.array([1.0])
    x_hat_prior, P_prior = kf.predict(u)

    assert x_hat_prior.shape == (2,)
    assert P_prior.shape == (2, 2)
```

#### 测试用例：更新步骤

```python
def test_update():
    """测试更新步骤"""
    y = np.array([1.0])
    x_hat, P, K = kf.update(y)

    assert x_hat.shape == (2,)
    assert P.shape == (2, 2)
    assert K.shape == (2, 1)
```

#### 测试用例：估计误差

```python
def test_estimation_error():
    """测试估计误差计算"""
    true_states = np.array([[1.0, 0.5], [2.0, 1.0], [3.0, 1.5]])
    kf = KalmanFilter(A, B, C, Q, R)

    for state in true_states:
        y = kf.C @ state
        kf.update(y)

    errors = kf.get_estimation_error(true_states)
    assert errors.shape == (3, 2)
```

### 2.3 分析函数测试

#### 测试用例：可控性矩阵

```python
def test_controllability_matrix():
    """测试可控性矩阵计算"""
    Co = controllability_matrix(A, B)
    expected = np.hstack([B, A @ B])
    np.testing.assert_array_almost_equal(Co, expected)
```

#### 测试用例：可控性判断

```python
def test_is_controllable():
    """测试可控性判断"""
    assert is_controllable(A, B)

    # 不可控系统
    A_unc = np.array([[1, 0], [0, 2]])
    B_unc = np.array([[1], [0]])
    assert not is_controllable(A_unc, B_unc)
```

### 2.4 Controller测试

#### 测试用例：极点配置

```python
def test_place_poles():
    """测试极点配置"""
    controller = StateFeedbackController(A, B)
    desired_poles = np.array([0.5, 0.3])
    K = controller.place_poles(desired_poles)

    assert K.shape == (1, 2)

    # 检查闭环极点
    closed_loop_poles = controller.get_closed_loop_poles()
    np.testing.assert_array_almost_equal(
        np.sort(np.abs(closed_loop_poles)),
        np.sort(np.abs(desired_poles)),
        decimal=5,
    )
```

#### 测试用例：LQR控制器

```python
def test_lqr_controller():
    """测试LQR控制器"""
    lqr = LQRController(A, B, Q, R)

    assert lqr.K.shape == (1, 2)
    assert lqr.P.shape == (2, 2)

    # 闭环系统应稳定
    A_cl, _ = lqr.get_closed_loop_system()
    eigenvalues = np.linalg.eigvals(A_cl)
    assert np.all(np.abs(eigenvalues) < 1.0)
```

### 2.5 Observer测试

#### 测试用例：观测器设计

```python
def test_observer_design():
    """测试观测器设计"""
    observer = FullOrderObserver(A, B, C)
    desired_poles = np.array([0.5, 0.3])
    L = observer.design_by_poles(desired_poles)

    assert L.shape == (2, 1)

    # 检查观测器极点
    obs_poles = observer.get_observer_poles()
    np.testing.assert_array_almost_equal(
        np.sort(np.abs(obs_poles)),
        np.sort(np.abs(desired_poles)),
        decimal=5,
    )
```

## 3. 集成测试

### 3.1 LQR与卡尔曼滤波器集成

```python
def test_lqr_with_kalman_filter():
    """测试LQR与卡尔曼滤波器集成"""
    # 系统定义
    A = np.array([[1.0, 1.0], [0.0, 1.0]])
    B = np.array([[0.5], [1.0]])
    C = np.array([[1.0, 0.0]])

    # LQR控制器
    Q = np.eye(2)
    R = np.array([[1.0]])
    lqr = LQRController(A, B, Q, R)

    # 卡尔曼滤波器
    Qn = 0.01 * np.eye(2)
    Rn = np.array([[0.1]])
    kf = KalmanFilter(A, B, C, Qn, Rn)

    # 仿真
    x_true = np.array([1.0, 0.0])
    n_steps = 50

    for _ in range(n_steps):
        # 测量
        y = C @ x_true + np.random.randn() * np.sqrt(Rn[0, 0])

        # 状态估计
        kf.predict()
        x_hat, _, _ = kf.update(y)

        # 控制
        u = lqr.compute_control(x_hat)

        # 状态演化
        x_true = A @ x_true + B @ u

    # 最终状态应接近零
    assert np.linalg.norm(x_true) < 0.5
```

### 3.2 基于观测器的控制

```python
def test_observer_based_control():
    """测试基于观测器的控制"""
    # 设计控制器
    controller = StateFeedbackController(A, B)
    K = controller.place_poles(np.array([0.5, 0.3]))

    # 设计观测器
    observer = FullOrderObserver(A, B, C)
    L = observer.design_by_poles(np.array([0.2, 0.1]))

    # 仿真
    x_true = np.array([1.0, 0.0])
    n_steps = 30

    for _ in range(n_steps):
        # 测量
        y = C @ x_true

        # 状态估计
        x_hat = observer.update(y)

        # 控制
        u = controller.compute_control(x_hat)

        # 状态演化
        x_true = A @ x_true + B @ u

    # 最终状态应接近零
    assert np.linalg.norm(x_true) < 0.5
```

## 4. 数学验证

### 4.1 矩阵运算验证

```python
def test_matrix_operations():
    """验证矩阵运算正确性"""
    A = np.array([[1, 2], [3, 4]])
    B = np.array([[5, 6], [7, 8]])

    # 矩阵乘法
    C = A @ B
    np.testing.assert_array_almost_equal(C, np.array([[19, 22], [43, 50]]))

    # 矩阵转置
    np.testing.assert_array_almost_equal(A.T, np.array([[1, 3], [2, 4]]))

    # 矩阵求逆
    A_inv = np.linalg.inv(A)
    np.testing.assert_array_almost_equal(A @ A_inv, np.eye(2))
```

### 4.2 特征值验证

```python
def test_eigenvalues():
    """验证特征值计算"""
    A = np.array([[2, 1], [1, 2]])
    eigenvalues = np.linalg.eigvals(A)

    # 特征值应为3和1
    np.testing.assert_array_almost_equal(np.sort(eigenvalues), np.array([1, 3]))
```

### 4.3 可控性验证

```python
def test_controllability():
    """验证可控性判断"""
    # 可控系统
    A = np.array([[0, 1], [-2, -3]])
    B = np.array([[0], [1]])
    Co = controllability_matrix(A, B)
    assert np.linalg.matrix_rank(Co) == 2

    # 不可控系统
    A_unc = np.array([[1, 0], [0, 2]])
    B_unc = np.array([[1], [0]])
    Co_unc = controllability_matrix(A_unc, B_unc)
    assert np.linalg.matrix_rank(Co_unc) == 1
```

## 5. 边界条件测试

### 5.1 零输入

```python
def test_zero_input():
    """测试零输入响应"""
    x0 = np.array([1.0, 0.5])
    u = np.zeros((10, 1))
    states, outputs = model.simulate(x0, u)

    # 零输入响应应衰减（稳定系统）
    assert np.linalg.norm(states[-1]) < np.linalg.norm(x0)
```

### 5.2 单位输入

```python
def test_unit_input():
    """测试单位阶跃响应"""
    x0 = np.array([0.0, 0.0])
    u = np.ones((10, 1))
    states, outputs = model.simulate(x0, u)

    # 输出应趋于稳态值
    assert np.abs(outputs[-1, 0] - outputs[-2, 0]) < 0.01
```

### 5.3 初始状态为零

```python
def test_zero_initial_state():
    """测试零初始状态"""
    x0 = np.zeros(2)
    u = np.ones((10, 1))
    states, outputs = model.simulate(x0, u)

    # 状态应从零开始
    np.testing.assert_array_almost_equal(states[0], x0)
```

## 6. 错误处理测试

### 6.1 维度不匹配

```python
def test_dimension_mismatch():
    """测试维度不匹配错误"""
    with pytest.raises(AssertionError):
        StateSpaceModel(np.eye(2), np.array([[1.0]]), np.array([[1.0, 0.0]]))
```

### 6.2 未设置增益

```python
def test_unset_gain():
    """测试未设置增益错误"""
    controller = StateFeedbackController(A, B)
    with pytest.raises(ValueError, match="反馈增益K未设置"):
        controller.compute_control(np.array([1.0, 0.0]))
```

### 6.3 奇异矩阵

```python
def test_singular_matrix():
    """测试奇异矩阵处理"""
    A_singular = np.array([[1, 2], [2, 4]])  # 奇异矩阵
    with pytest.raises(np.linalg.LinAlgError):
        np.linalg.inv(A_singular)
```

## 7. 性能测试

### 7.1 仿真性能

```python
import time

def test_simulation_performance():
    """测试仿真性能"""
    n_steps = 10000
    u = np.zeros((n_steps, 1))
    x0 = np.array([1.0, 0.0])

    start = time.time()
    states, outputs = model.simulate(x0, u)
    elapsed = time.time() - start

    print(f"仿真{n_steps}步耗时: {elapsed:.3f}秒")
    assert elapsed < 1.0  # 应在1秒内完成
```

### 7.2 卡尔曼滤波性能

```python
def test_kalman_filter_performance():
    """测试卡尔曼滤波性能"""
    n_steps = 1000
    measurements = np.random.randn(n_steps)

    start = time.time()
    for k in range(n_steps):
        kf.predict()
        kf.update(measurements[k])
    elapsed = time.time() - start

    print(f"卡尔曼滤波{n_steps}步耗时: {elapsed:.3f}秒")
    assert elapsed < 1.0
```

## 8. 测试覆盖率

### 8.1 覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| state_space_model.py | >90% |
| kalman_filter.py | >90% |
| analysis.py | >85% |
| controller.py | >85% |
| observer.py | >80% |

### 8.2 覆盖率测量

```bash
# 使用pytest-cov
pytest --cov=src --cov-report=html tests/

# 查看报告
open htmlcov/index.html
```

## 9. 测试数据

### 9.1 标准测试系统

```python
# 二阶系统
A_2nd = np.array([[0, 1], [-2, -3]])
B_2nd = np.array([[0], [1]])
C_2nd = np.array([[1, 0]])

# 积分器
A_int = np.array([[1]])
B_int = np.array([[1]])
C_int = np.array([[1]])

# 双积分器
A_double = np.array([[1, 1], [0, 1]])
B_double = np.array([[0.5], [1]])
C_double = np.array([[1, 0]])
```

### 9.2 测试矩阵

```python
# 稳定矩阵
A_stable = np.array([[0.5, 0], [0, 0.3]])

# 不稳定矩阵
A_unstable = np.array([[1.5, 0], [0, 0.3]])

# 正交矩阵
Q_ortho = np.array([[0, 1], [1, 0]])
```

## 10. 持续集成

### 10.1 CI配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install numpy scipy matplotlib pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=src tests/
```

### 10.2 测试脚本

```bash
#!/bin/bash
# run_tests.sh

echo "运行单元测试..."
pytest tests/ -v

echo "运行覆盖率测试..."
pytest --cov=src --cov-report=html tests/

echo "生成测试报告..."
coverage report
```

## 11. 测试最佳实践

### 11.1 命名规范

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 11.2 测试结构

```python
class TestFeature:
    """功能测试"""

    def setup_method(self):
        """测试前准备"""
        pass

    def test_normal_case(self):
        """正常情况测试"""
        pass

    def test_edge_case(self):
        """边界情况测试"""
        pass

    def test_error_case(self):
        """错误情况测试"""
        pass
```

### 11.3 断言使用

```python
# 数组比较
np.testing.assert_array_almost_equal(actual, expected, decimal=10)

# 浮点数比较
assert abs(actual - expected) < 1e-10

# 异常检查
with pytest.raises(ValueError, match="错误消息"):
    function_that_raises()
```

## 12. 调试技巧

### 12.1 打印调试

```python
def test_debug():
    """调试测试"""
    print(f"A: {A}")
    print(f"eigenvalues: {np.linalg.eigvals(A)}")
    # ...
```

### 12.2 可视化调试

```python
def test_visualization():
    """可视化测试结果"""
    import matplotlib.pyplot as plt

    plt.plot(states[:, 0], states[:, 1])
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.title('State Trajectory')
    plt.grid(True)
    plt.savefig('debug_plot.png')
```

### 12.3 断点调试

```python
import pdb; pdb.set_trace()  # 设置断点
```
