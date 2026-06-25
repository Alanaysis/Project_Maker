# PID 控制器 - 开发文档

## 1. 环境配置

### 1.1 依赖

- Python 3.7+
- numpy (数值计算)
- matplotlib (可视化，可选)
- pytest (测试)

### 1.2 安装

```bash
pip install numpy matplotlib pytest
```

## 2. 开发流程

### 2.1 实现顺序

1. **PIDController**: 核心算法实现
2. **Plant**: 被控对象模型
3. **Simulator**: 闭环仿真
4. **Tuner**: 参数整定
5. **Tests**: 测试覆盖
6. **Examples**: 使用示例
7. **Visualization**: 可视化

### 2.2 设计原则

- **单一职责**: 每个类只负责一个功能
- **接口清晰**: 公共方法简洁明了
- **可测试性**: 内部状态可访问用于测试
- **文档完善**: 每个方法都有 docstring

## 3. 核心实现细节

### 3.1 PID 离散化

连续 PID:
```
u(t) = Kp*e(t) + Ki*∫e(τ)dτ + Kd*de(t)/dt
```

离散化:
- 积分: 梯形法 `∫e dt ≈ Σ(e[n]+e[n-1])/2 * dt`
- 微分: 后向差分 `de/dt ≈ (e[n]-e[n-1])/dt`

### 3.2 数值稳定性

- 一阶系统: Euler 法 (简单，dt 足够小时稳定)
- 二阶系统: Runge-Kutta 4 阶 (精度高，适合刚性系统)
- 微分滤波: 一阶低通滤波器减少噪声

### 3.3 抗饱和实现

```python
# 反计算抗饱和
output = p + i + d
clamped = clip(output, min, max)
if output != clamped:
    integral -= (output - clamped) / Ki
```

## 4. 扩展点

### 4.1 添加新的被控对象

继承或实现 `update(input) -> output` 和 `reset()` 接口:

```python
class MyPlant:
    def __init__(self):
        self._state = 0.0

    def update(self, control_input):
        # 实现系统动力学
        self._state = ...
        return self._state

    def reset(self):
        self._state = 0.0

    @property
    def output(self):
        return self._state
```

### 4.2 添加新的整定方法

在 `PIDTuner` 类中添加新方法:

```python
def my_tuning_method(self, plant_fn, **kwargs):
    # 1. 识别系统参数
    # 2. 计算 PID 增益
    return {"Kp": ..., "Ki": ..., "Kd": ..., "method": "my_method"}
```

### 4.3 添加新的性能指标

在 `SimulationResult._compute_metrics()` 中添加:

```python
def _compute_metrics(self):
    # 现有指标...
    self.my_metric = self._calculate_my_metric()
```

## 5. 已知限制

1. **线性系统**: 只支持 LTI 系统，不支持非线性
2. **单输入单输出**: 不支持 MIMO 系统
3. **固定步长**: 不支持变步长仿真
4. **无前馈**: 只有反馈控制，无前馈补偿

## 6. 后续改进

- [x] 添加非线性被控对象 (如饱和、死区)
- [x] 支持改进 PID 变体 (积分分离、不完全微分、死区)
- [x] 添加延迟系统模型
- [ ] 支持增量式 PID
- [ ] 添加前馈控制
- [ ] 支持串级 PID
- [ ] 添加自适应 PID
- [ ] 支持 MIMO 系统

## 7. 参考资源

- Åström, K. J., & Hägglund, T. (2006). *Advanced PID Control*.
- [Python Control Systems Library](https://python-control.readthedocs.io/)
- [MATLAB PID Tuner](https://www.mathworks.com/help/controls/ug/pid-tuner.html)
