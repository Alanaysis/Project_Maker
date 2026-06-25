# 梯度下降家族 - 项目架构设计

## 1. 项目结构

```
gradient-descent/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖说明
├── docs/
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-ARCHITECTURE.md      # 架构设计（本文件）
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发指南
├── src/
│   ├── __init__.py
│   ├── optimizers/
│   │   ├── __init__.py
│   │   ├── base.py             # 优化器基类
│   │   ├── sgd.py              # SGD 及其变体
│   │   ├── adam.py             # Adam 系列
│   │   ├── adagrad.py          # AdaGrad
│   │   ├── rmsprop.py          # RMSProp
│   │   └── momentum.py         # 动量法
│   ├── schedulers/
│   │   ├── __init__.py
│   │   ├── base.py             # 调度器基类
│   │   ├── step.py             # 阶梯衰减
│   │   ├── exponential.py      # 指数衰减
│   │   ├── cosine.py           # 余弦退火
│   │   └── warmup.py           # Warmup
│   ├── functions/
│   │   ├── __init__.py
│   │   ├── base.py             # 测试函数基类
│   │   ├── quadratic.py        # 二次函数
│   │   ├── rosenbrock.py       # Rosenbrock 函数
│   │   └── himmelblau.py       # Himmelblau 函数
│   └── visualizer/
│       ├── __init__.py
│       ├── contour.py          # 等高线图
│       ├── trajectory.py       # 优化轨迹
│       └── comparison.py       # 对比可视化
├── tests/
│   ├── __init__.py
│   ├── test_optimizers.py      # 优化器测试
│   ├── test_schedulers.py      # 调度器测试
│   ├── test_functions.py       # 测试函数验证
│   └── test_integration.py     # 集成测试
└── examples/
    ├── basic_optimization.py   # 基础优化示例
    ├── compare_optimizers.py   # 优化器对比
    ├── learning_rate_schedule.py # 学习率调度
    └── visualization_demo.py   # 可视化演示
```

## 2. 核心模块设计

### 2.1 优化器模块 (optimizers/)

#### 基类设计

```python
class BaseOptimizer:
    """优化器基类"""

    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate
        self.state = {}  # 存储优化器状态

    def step(self, params, grads):
        """执行一步优化"""
        raise NotImplementedError

    def zero_grad(self):
        """清零梯度"""
        pass

    def get_state(self):
        """获取优化器状态"""
        return self.state

    def set_state(self, state):
        """设置优化器状态"""
        self.state = state
```

#### 优化器接口

所有优化器实现统一接口：

```python
class SGD(BaseOptimizer):
    def __init__(self, learning_rate=0.01, momentum=0, weight_decay=0):
        super().__init__(learning_rate)
        self.momentum = momentum
        self.weight_decay = weight_decay

    def step(self, params, grads):
        """更新参数"""
        # 实现 SGD 更新逻辑
        pass
```

### 2.2 学习率调度器模块 (schedulers/)

#### 基类设计

```python
class BaseScheduler:
    """学习率调度器基类"""

    def __init__(self, optimizer, last_epoch=-1):
        self.optimizer = optimizer
        self.last_epoch = last_epoch

    def step(self):
        """更新学习率"""
        self.last_epoch += 1
        lr = self.get_lr()
        self.optimizer.learning_rate = lr

    def get_lr(self):
        """计算当前学习率"""
        raise NotImplementedError
```

#### 调度器类型

1. **StepLR**: 阶梯衰减
2. **ExponentialLR**: 指数衰减
3. **CosineAnnealingLR**: 余弦退火
4. **WarmupScheduler**: 热身调度

### 2.3 测试函数模块 (functions/)

#### 基类设计

```python
class TestFunction:
    """测试函数基类"""

    def __init__(self, name, ndim=2):
        self.name = name
        self.ndim = ndim

    def __call__(self, x):
        """计算函数值"""
        raise NotImplementedError

    def gradient(self, x):
        """计算梯度"""
        raise NotImplementedError

    def minimum(self):
        """返回理论最小值"""
        raise NotImplementedError

    def initial_point(self):
        """返回初始点"""
        raise NotImplementedError
```

#### 标准测试函数

1. **QuadraticFunction**: 简单二次函数
2. **RosenbrockFunction**: 经典优化测试函数
3. **HimmelblauFunction**: 多模态测试函数
4. **BealeFunction**: 复杂优化问题

### 2.4 可视化模块 (visualizer/)

#### 等高线图绘制

```python
class ContourPlotter:
    """等高线图绘制器"""

    def __init__(self, func, x_range, y_range):
        self.func = func
        self.x_range = x_range
        self.y_range = y_range

    def plot(self, trajectories=None, title=""):
        """绘制等高线图和优化轨迹"""
        pass
```

#### 轨迹可视化

```python
class TrajectoryPlotter:
    """优化轨迹可视化"""

    def plot_trajectory(self, points, label="", color="blue"):
        """绘制单个优化轨迹"""
        pass

    def compare_trajectories(self, trajectories, labels, colors):
        """对比多个优化轨迹"""
        pass
```

## 3. 数据流设计

### 3.1 优化流程

```
初始化
  ├── 创建测试函数
  ├── 创建优化器
  └── 创建调度器（可选）

优化循环
  ├── 计算当前函数值
  ├── 计算梯度
  ├── 优化器更新参数
  ├── 调度器更新学习率（可选）
  └── 记录轨迹

后处理
  ├── 收敛分析
  └── 可视化
```

### 3.2 状态管理

优化器状态包括：
- `step_count`: 迭代次数
- `momentum_buffer`: 动量缓存
- `exp_avg`: 一阶矩估计（Adam）
- `exp_avg_sq`: 二阶矩估计（Adam）

## 4. 接口设计

### 4.1 统一优化接口

```python
def optimize(func, optimizer, x_init, max_iter=1000, tol=1e-6):
    """统一优化接口

    Args:
        func: 测试函数
        optimizer: 优化器实例
        x_init: 初始点
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        优化结果
    """
    x = x_init.copy()
    trajectory = [x.copy()]

    for i in range(max_iter):
        # 计算梯度
        grad = func.gradient(x)

        # 检查收敛
        if np.linalg.norm(grad) < tol:
            break

        # 更新参数
        optimizer.step(x, grad)

        # 记录轨迹
        trajectory.append(x.copy())

    return {
        'x': x,
        'fun': func(x),
        'niter': i + 1,
        'trajectory': np.array(trajectory)
    }
```

### 4.2 批量对比接口

```python
def compare_optimizers(func, optimizers, x_init, max_iter=1000):
    """对比多个优化器

    Args:
        func: 测试函数
        optimizers: 优化器字典 {name: optimizer}
        x_init: 初始点
        max_iter: 最大迭代次数

    Returns:
        对比结果字典
    """
    results = {}
    for name, optimizer in optimizers.items():
        results[name] = optimize(func, optimizer, x_init, max_iter)
    return results
```

## 5. 配置管理

### 5.1 优化器配置

```python
OPTIMIZER_CONFIGS = {
    'sgd': {
        'learning_rate': 0.01,
        'momentum': 0,
        'weight_decay': 0
    },
    'momentum': {
        'learning_rate': 0.01,
        'momentum': 0.9,
        'weight_decay': 0
    },
    'adam': {
        'learning_rate': 0.001,
        'betas': (0.9, 0.999),
        'eps': 1e-8,
        'weight_decay': 0
    },
    # ... 其他优化器
}
```

### 5.2 测试函数配置

```python
FUNCTION_CONFIGS = {
    'quadratic': {
        'ndim': 2,
        'x_range': (-5, 5),
        'y_range': (-5, 5)
    },
    'rosenbrock': {
        'ndim': 2,
        'x_range': (-2, 2),
        'y_range': (-1, 3)
    },
    # ... 其他函数
}
```

## 6. 错误处理

### 6.1 常见错误

1. **梯度爆炸**: 检测并处理梯度范数过大
2. **数值不稳定**: 使用数值稳定的实现
3. **收敛失败**: 设置最大迭代次数和超时机制

### 6.2 错误处理策略

```python
def safe_optimize(func, optimizer, x_init, max_iter=1000, tol=1e-6):
    """带错误处理的优化"""
    try:
        return optimize(func, optimizer, x_init, max_iter, tol)
    except NumericalError:
        # 处理数值错误
        return {'success': False, 'message': 'Numerical instability'}
    except ConvergenceError:
        # 处理收敛失败
        return {'success': False, 'message': 'Failed to converge'}
```

## 7. 扩展性设计

### 7.1 添加新优化器

1. 继承 `BaseOptimizer`
2. 实现 `step` 方法
3. 注册到优化器工厂

```python
class NewOptimizer(BaseOptimizer):
    def __init__(self, learning_rate=0.01, param1=0.5):
        super().__init__(learning_rate)
        self.param1 = param1

    def step(self, params, grads):
        # 实现新算法
        pass
```

### 7.2 添加新测试函数

1. 继承 `TestFunction`
2. 实现函数值和梯度计算
3. 定义搜索范围

```python
class NewTestFunction(TestFunction):
    def __init__(self):
        super().__init__('new_function', ndim=2)

    def __call__(self, x):
        # 实现函数计算
        pass

    def gradient(self, x):
        # 实现梯度计算
        pass
```

## 8. 性能考虑

### 8.1 计算优化

1. **向量化**: 使用 NumPy 向量化操作
2. **缓存**: 缓存中间计算结果
3. **内存管理**: 避免不必要的数组复制

### 8.2 并行化

- 使用 NumPy 的底层并行化
- 可选：支持多进程批量实验

## 9. 测试策略

### 9.1 单元测试

- 测试每个优化器的更新规则
- 验证学习率调度器的计算
- 检查测试函数的正确性

### 9.2 集成测试

- 端到端优化流程测试
- 收敛性验证
- 性能基准测试

### 9.3 回归测试

- 保存基准结果
- 定期对比验证

## 10. 依赖管理

### 10.1 核心依赖

```python
# requirements.txt
numpy>=1.20.0
matplotlib>=3.3.0
```

### 10.2 可选依赖

```python
# 用于高级可视化
seaborn>=0.11.0
# 用于动画
matplotlib-animation
```

## 11. 总结

本架构设计遵循以下原则：

1. **模块化**: 每个功能独立封装
2. **可扩展**: 易于添加新算法和函数
3. **一致性**: 统一的接口设计
4. **可测试**: 便于编写测试
5. **可复用**: 组件可在其他项目中复用

通过这种设计，项目可以清晰地展示各种梯度下降算法的行为差异，并为学习和研究提供良好的基础。
