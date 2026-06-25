# 04 - 测试说明

## 1. 测试概述

### 1.1 测试目标

- 验证 MPC 控制器的正确性
- 验证约束处理的正确性
- 验证仿真环境的可靠性
- 测试边界条件和异常情况

### 1.2 测试框架

- 测试框架: pytest
- 覆盖率工具: pytest-cov
- 断言方法: numpy.testing

### 1.3 测试结构

```
tests/
├── test_plant_model.py        # 被控对象测试
├── test_models.py             # 预测模型测试
├── test_mpc_controller.py     # MPC 控制器测试
├── test_qp_solver.py          # QP 求解器测试
├── test_feedback_correction.py # 反馈校正测试
├── test_applications.py       # 应用测试
└── test_simulation.py         # 仿真环境测试
```

## 2. 测试用例

### 2.1 被控对象测试 (test_plant_model.py)

#### 线性系统测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化测试 | 维度、矩阵值 |
| test_step | 状态更新 | 数值正确性 |
| test_output | 输出计算 | C*x 计算 |
| test_linearize | 线性化 | 返回自身矩阵 |

#### 双积分器测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 维度、采样时间 |
| test_dynamics | 动力学特性 | 物理意义正确 |
| test_stability | 稳定性 | 无控制时稳定 |

#### 倒立摆测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 维度正确 |
| test_downward_equilibrium | 向下平衡点 | 稳定性 |
| test_output | 输出 | 角度输出 |

#### 水箱系统测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 参数设置 |
| test_steady_state | 稳态 | 液位非负 |
| test_output | 输出 | 液位输出 |

#### 非线性模型测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_custom_dynamics | 自定义动力学 | 收敛性 |
| test_rk4_accuracy | RK4 精度 | 数值精度 |

### 2.2 MPC 控制器测试 (test_mpc_controller.py)

#### 基本功能测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 配置正确 |
| test_compute_control | 控制计算 | 输出形状、类型 |
| test_reset | 重置 | 历史清空 |

#### 约束满足测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_constraint_satisfaction | 约束满足 | 输入范围 |
| test_different_reference | 不同参考 | 适应性 |

#### 跟踪性能测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_tracking_performance | 跟踪性能 | 稳态误差 |
| test_operating_point | 工作点 | 设置正确 |

#### 线性系统测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_siso_system | SISO 系统 | 跟踪误差 |
| test_mimo_system | MIMO 系统 | 多变量控制 |

#### 优化器测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_unconstrained_optimization | 无约束优化 | 收敛性 |
| test_constrained_optimization | 有约束优化 | 约束满足 |

### 2.3 仿真环境测试 (test_simulation.py)

#### 基本功能测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_simulation_initialization | 初始化 | 配置正确 |
| test_step_response | 阶跃响应 | 响应特性 |
| test_sinusoidal_response | 正弦响应 | 跟踪能力 |

#### 配置测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_simulation_config | 仿真配置 | 时间长度 |
| test_custom_reference | 自定义参考 | 灵活性 |
| test_random_reference | 随机参考 | 鲁棒性 |

#### 噪声测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_noisy_simulation | 带噪声仿真 | 误差存在 |

#### 边界条件测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_zero_initial_state | 零初始状态 | 控制输入小 |
| test_large_initial_error | 大初始误差 | 大控制输入 |
| test_short_simulation | 短仿真 | 步数正确 |

### 2.4 预测模型测试 (test_models.py)

#### 状态空间模型测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization | 初始化 | 维度、矩阵值 |
| test_predict | 状态预测 | 数值正确性 |
| test_stability_check | 稳定性检查 | 特征值 |
| test_controllability | 可控性检查 | 秩条件 |
| test_prediction_matrices | 预测矩阵 | 矩阵形状 |

#### 脉冲响应模型测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_initialization_siso | SISO 初始化 | 维度 |
| test_predict_siso | SISO 预测 | 输出正确性 |
| test_from_step_response | 阶跃响应创建 | 差分计算 |
| test_from_state_space | 状态空间转换 | 脉冲响应 |

### 2.5 QP 求解器测试 (test_qp_solver.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_unconstrained_hildreth | 无约束 Hildreth | 最优解 |
| test_constrained_hildreth | 有约束 Hildreth | 约束满足 |
| test_active_set_solver | 活动集方法 | 最优解 |
| test_scipy_solver | scipy 求解器 | 最优解 |
| test_solvers_give_same_result | 求解器一致性 | 结果相同 |

### 2.6 反馈校正测试 (test_feedback_correction.py)

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_error_feedback | 误差反馈 | 校正量 |
| test_model_adaptive | 自适应校正 | 参数收敛 |
| test_extended_state | 增广状态 | 扰动估计 |
| test_disturbance_observer | 扰动观测器 | 扰动估计 |

### 2.7 应用测试 (test_applications.py)

#### 温度控制测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_dynamics | 热力学动力学 | 物理正确性 |
| test_heating | 加热过程 | 温度升高 |
| test_steady_state | 稳态 | 工作点稳定 |

#### 轨迹跟踪测试

| 测试用例 | 描述 | 验证点 |
|----------|------|--------|
| test_straight_line | 直线运动 | 位置正确 |
| test_circular_motion | 圆周运动 | 轨迹正确 |
| test_get_reference | 参考轨迹 | 轨迹形状 |

## 3. 运行测试

### 3.1 运行所有测试

```bash
cd projects/mpc-controller
python -m pytest tests/ -v
```

### 3.2 运行特定测试文件

```bash
python -m pytest tests/test_plant_model.py -v
```

### 3.3 运行特定测试用例

```bash
python -m pytest tests/test_mpc_controller.py::TestMPCController::test_compute_control -v
```

### 3.4 生成覆盖率报告

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 4. 测试结果示例

### 4.1 典型测试输出

```
tests/test_plant_model.py::TestLinearPlantModel::test_initialization PASSED
tests/test_plant_model.py::TestLinearPlantModel::test_step PASSED
tests/test_plant_model.py::TestDoubleIntegrator::test_dynamics PASSED
tests/test_plant_model.py::TestPendulumModel::test_initialization PASSED
tests/test_plant_model.py::TestTankSystem::test_steady_state PASSED
tests/test_mpc_controller.py::TestMPCController::test_compute_control PASSED
tests/test_mpc_controller.py::TestMPCController::test_constraint_satisfaction PASSED
tests/test_simulation.py::TestMPCSimulation::test_step_response PASSED
```

### 4.2 覆盖率报告

```
Name                         Stmts   Miss  Cover
--------------------------------------------------
src/plant_model.py             120     15    88%
src/mpc_controller.py          150     20    87%
src/optimizer.py               100     12    88%
src/simulation.py               80     10    88%
--------------------------------------------------
TOTAL                          450     57    87%
```

## 5. 测试数据

### 5.1 测试用例数据

```python
# 双积分器测试数据
DOUBLE_INTEGRATOR_DT = 0.1
DOUBLE_INTEGRATOR_A = np.array([[1, 0.1], [0, 1]])
DOUBLE_INTEGRATOR_B = np.array([[0.005], [0.1]])

# 倒立摆测试数据
PENDULUM_M = 1.0
PENDULUM_L = 1.0
PENDULUM_B = 0.1
PENDULUM_G = 9.81

# MPC 配置测试数据
MPC_PREDICTION_HORIZON = 10
MPC_CONTROL_HORIZON = 5
MPC_SAMPLE_TIME = 0.1
```

### 5.2 参考信号测试数据

```python
# 阶跃参考
STEP_REFERENCE = np.array([1.0, 0.0])
STEP_TIME = 0.5

# 正弦参考
SINE_AMPLITUDE = np.array([1.0, 0.0])
SINE_FREQUENCY = 0.1  # Hz
```

## 6. 持续集成

### 6.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=src
```

## 7. 测试最佳实践

### 7.1 测试原则

1. **独立性**: 每个测试用例独立
2. **可重复**: 测试结果可重复
3. **自验证**: 测试自动验证结果
4. **及时**: 代码变更后及时测试

### 7.2 测试命名规范

```python
def test_<功能>_<场景>_<预期结果>():
    """测试描述"""
    pass
```

### 7.3 断言使用

```python
# 使用 numpy 断言
np.testing.assert_array_almost_equal(actual, expected)
np.testing.assert_array_less(actual, expected)

# 使用 pytest 断言
assert result.success
assert len(history) > 0
```

## 8. 调试技巧

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 优化不收敛 | 权重设置不当 | 调整权重 |
| 约束违反 | 约束过紧 | 放松约束 |
| 数值不稳定 | 条件数过大 | 添加正则化 |
| 跟踪误差大 | 模型不准确 | 改进模型 |

### 8.2 调试方法

```python
# 打印中间结果
print(f"状态: {state}")
print(f"参考: {reference}")
print(f"控制输入: {result.u_optimal}")
print(f"优化信息: {result.info}")

# 可视化调试
import matplotlib.pyplot as plt
plt.plot(result.x_predicted)
plt.show()
```

### 8.3 日志记录

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"状态: {state}")
logger.info(f"优化成功: {result.info['success']}")
logger.warning(f"优化警告: {result.info['message']}")
```
