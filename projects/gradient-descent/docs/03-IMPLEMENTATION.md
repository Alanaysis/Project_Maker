# 梯度下降家族 - 实现细节

## 1. 项目结构

```
gradient-descent/
├── src/
│   ├── __init__.py
│   ├── optimizer.py           # 优化工具函数
│   ├── optimizers/            # 优化器实现
│   │   ├── __init__.py
│   │   ├── base.py           # 基类
│   │   ├── bgd.py            # BGD, Mini-Batch GD
│   │   ├── sgd.py            # SGD
│   │   ├── momentum.py       # Momentum, NAG
│   │   ├── adagrad.py        # AdaGrad
│   │   ├── rmsprop.py        # RMSProp
│   │   ├── adam.py           # Adam, AdamW
│   │   └── nadam.py          # Nadam
│   ├── schedulers/           # 学习率调度器
│   │   ├── __init__.py
│   │   ├── base.py           # 基类
│   │   ├── step.py           # StepLR
│   │   ├── exponential.py    # ExponentialLR
│   │   ├── cosine.py         # CosineAnnealingLR
│   │   └── warmup.py         # WarmupScheduler
│   ├── functions/            # 测试函数
│   │   ├── __init__.py
│   │   ├── base.py           # 基类
│   │   ├── quadratic.py      # 二次函数
│   │   ├── rosenbrock.py     # Rosenbrock 函数
│   │   └── himmelblau.py     # Himmelblau 函数
│   └── visualizer/           # 可视化
│       ├── __init__.py
│       ├── contour.py        # 等高线图
│       ├── trajectory.py     # 轨迹图
│       └── comparison.py     # 对比图
├── tests/                    # 测试
├── examples/                 # 示例
└── docs/                     # 文档
```

## 2. 核心算法实现

### 2.1 BGD (批量梯度下降)

**文件**: `src/optimizers/bgd.py`

**数学公式**:
```
θ_{t+1} = θ_t - η * (1/N) * Σ∇J(θ_t, x_i)
```

**实现要点**:
- 使用整个训练集计算梯度
- 收敛稳定，适合小数据集
- 支持权重衰减

### 2.2 Mini-Batch GD (小批量梯度下降)

**文件**: `src/optimizers/bgd.py`

**数学公式**:
```
θ_{t+1} = θ_t - η * (1/B) * Σ∇J(θ_t, x_i)
```

**实现要点**:
- 结合 BGD 和 SGD 的优点
- 支持配置批量大小
- 适合大规模数据集

### 2.3 SGD (随机梯度下降)

**文件**: `src/optimizers/sgd.py`

**数学公式**:
```
θ_{t+1} = θ_t - η * ∇J(θ_t)
```

**实现要点**:
- 基本的参数更新
- 支持权重衰减 (L2 正则化)
- 支持梯度裁剪

**关键代码**:
```python
def step(self, params, grads):
    # 应用权重衰减
    if self.weight_decay != 0:
        grads = grads + self.weight_decay * params

    # 更新参数
    params = params - self.learning_rate * grads
    return params
```

### 2.2 Momentum (动量法)

**文件**: `src/optimizers/momentum.py`

**数学公式**:
```
v_t = γ * v_{t-1} + η * ∇J(θ_t)
θ_{t+1} = θ_t - v_t
```

**实现要点**:
- 维护动量缓冲区
- 支持 Nesterov 动量
- 动量系数通常设为 0.9

**关键代码**:
```python
def step(self, params, grads):
    # 初始化动量缓冲区
    if 'momentum_buffer' not in self.state:
        self.state['momentum_buffer'] = np.zeros_like(params)

    # 更新动量缓冲区
    self.state['momentum_buffer'] = (
        self.momentum * self.state['momentum_buffer'] + grads
    )

    # 更新参数
    params = params - self.learning_rate * self.state['momentum_buffer']
    return params
```

### 2.3 AdaGrad (自适应学习率)

**文件**: `src/optimizers/adagrad.py`

**数学公式**:
```
G_t = G_{t-1} + (∇J(θ_t))^2
θ_{t+1} = θ_t - (η / √(G_t + ε)) * ∇J(θ_t)
```

**实现要点**:
- 累积梯度平方和
- 自适应调整学习率
- 对稀疏特征友好
- 学习率单调递减

**关键代码**:
```python
def step(self, params, grads):
    # 初始化梯度平方累积和
    if 'sum_square_grads' not in self.state:
        self.state['sum_square_grads'] = np.zeros_like(params)

    # 累积梯度平方
    self.state['sum_square_grads'] += grads ** 2

    # 计算自适应学习率
    adjusted_lr = self.learning_rate / (
        np.sqrt(self.state['sum_square_grads']) + self.eps
    )

    # 更新参数
    params = params - adjusted_lr * grads
    return params
```

### 2.4 RMSProp (均方根传播)

**文件**: `src/optimizers/rmsprop.py`

**数学公式**:
```
G_t = β * G_{t-1} + (1-β) * (∇J(θ_t))^2
θ_{t+1} = θ_t - (η / √(G_t + ε)) * ∇J(θ_t)
```

**实现要点**:
- 使用移动平均代替累积平方和
- 解决 AdaGrad 学习率过早衰减的问题
- 支持动量变体

**关键代码**:
```python
def step(self, params, grads):
    # 更新平方平均
    self.state['square_avg'] = (
        self.alpha * self.state['square_avg'] +
        (1 - self.alpha) * grads ** 2
    )

    # 计算更新量
    update = grads / (np.sqrt(self.state['square_avg']) + self.eps)

    # 更新参数
    params = params - self.learning_rate * update
    return params
```

### 2.5 Adam (自适应矩估计)

**文件**: `src/optimizers/adam.py`

**数学公式**:
```
m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)
v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2
m̂_t = m_t / (1 - β1^t)
v̂_t = v_t / (1 - β2^t)
θ_{t+1} = θ_t - (η / (√v̂_t + ε)) * m̂_t
```

**实现要点**:
- 结合动量法和 RMSProp
- 偏差修正机制
- 支持 AMSGrad 变体
- 默认超参数: β1=0.9, β2=0.999, ε=1e-8

**关键代码**:
```python
def step(self, params, grads):
    # 更新一阶矩估计
    self.state['exp_avg'] = (
        self.betas[0] * self.state['exp_avg'] +
        (1 - self.betas[0]) * grads
    )

    # 更新二阶矩估计
    self.state['exp_avg_sq'] = (
        self.betas[1] * self.state['exp_avg_sq'] +
        (1 - self.betas[1]) * grads ** 2
    )

    # 偏差修正
    bias_correction1 = 1 - self.betas[0] ** self.step_count
    bias_correction2 = 1 - self.betas[1] ** self.step_count

    corrected_exp_avg = self.state['exp_avg'] / bias_correction1
    corrected_exp_avg_sq = self.state['exp_avg_sq'] / bias_correction2

    # 计算更新量
    update = corrected_exp_avg / (np.sqrt(corrected_exp_avg_sq) + self.eps)

    # 更新参数
    params = params - self.learning_rate * update
    return params
```

### 2.6 AdamW (解耦权重衰减的 Adam)

**文件**: `src/optimizers/adam.py`

**数学公式**:
```
m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)
v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2
m̂_t = m_t / (1 - β1^t)
v̂_t = v_t / (1 - β2^t)
θ_{t+1} = θ_t - η * (m̂_t / (√v̂_t + ε) + λ * θ_t)
```

**实现要点**:
- 将权重衰减与梯度更新解耦
- 直接对参数应用权重衰减
- 通常比 L2 正则化的 Adam 更有效

**关键代码**:
```python
def step(self, params, grads):
    # 注意：AdamW 不对梯度应用权重衰减

    # 更新一阶矩和二阶矩
    # ...

    # 计算更新量 (不包含权重衰减)
    update = corrected_exp_avg / (np.sqrt(corrected_exp_avg_sq) + self.eps)

    # 更新参数 (包含权重衰减)
    params = params - self.learning_rate * (update + self.weight_decay * params)
    return params
```

### 2.7 Nadam (Nesterov 加速自适应矩估计)

**文件**: `src/optimizers/nadam.py`

**数学公式**:
```
m_t = β1 * m_{t-1} + (1-β1) * ∇J(θ_t)
v_t = β2 * v_{t-1} + (1-β2) * (∇J(θ_t))^2
m̂_t = m_t / (1 - β1^t)
v̂_t = v_t / (1 - β2^t)
θ_{t+1} = θ_t - η * ((1-β1) * ∇J(θ_t) + β1 * m̂_t) / (√v̂_t + ε)
```

**实现要点**:
- 结合 Nesterov 动量的前瞻性和 Adam 的自适应学习率
- 使用当前梯度和修正后的一阶矩的加权平均
- 通常比 Adam 收敛更快

**关键代码**:
```python
def step(self, params, grads):
    # 更新一阶矩和二阶矩
    # ...

    # 偏差修正
    corrected_exp_avg = self.state['exp_avg'] / bias_correction1
    corrected_exp_avg_sq = self.state['exp_avg_sq'] / bias_correction2

    # Nadam: 结合 Nesterov 动量
    nesterov_update = (1 - self.betas[0]) * grads + self.betas[0] * corrected_exp_avg

    # 计算更新量
    update = nesterov_update / (np.sqrt(corrected_exp_avg_sq) + self.eps)

    # 更新参数
    params = params - self.learning_rate * update
    return params
```

## 3. 学习率调度器实现

### 3.1 StepLR (阶梯衰减)

**文件**: `src/schedulers/step.py`

**数学公式**:
```
lr = base_lr * gamma^(epoch // step_size)
```

**实现要点**:
- 每隔固定 epoch 衰减学习率
- 简单有效

### 3.2 ExponentialLR (指数衰减)

**文件**: `src/schedulers/exponential.py`

**数学公式**:
```
lr = base_lr * gamma^epoch
```

**实现要点**:
- 每个 epoch 乘以衰减因子
- 平滑衰减

### 3.3 CosineAnnealingLR (余弦退火)

**文件**: `src/schedulers/cosine.py`

**数学公式**:
```
lr = lr_min + 0.5 * (lr_max - lr_min) * (1 + cos(π * t / T))
```

**实现要点**:
- 平滑的周期性衰减
- 有助于跳出局部最优
- 最小学习率限制

### 3.4 WarmupScheduler (热身调度)

**文件**: `src/schedulers/warmup.py`

**实现要点**:
- 训练初期线性增加学习率
- 防止梯度爆炸
- 可与其他调度器结合使用

## 4. 测试函数实现

### 4.1 QuadraticFunction (二次函数)

**数学公式**:
```
f(x, y) = 0.5 * (a * (x - x0)^2 + b * (y - y0)^2)
```

**特点**:
- 凸函数
- 有唯一最小值
- 梯度是线性的
- 适合验证算法基本功能

### 4.2 RosenbrockFunction (Rosenbrock 函数)

**数学公式**:
```
f(x, y) = (a - x)^2 + b * (y - x^2)^2
```

**特点**:
- 非凸函数
- 有狭长的"峡谷"
- 全局最小值在 (1, 1)
- 优化难度大

### 4.3 HimmelblauFunction (Himmelblau 函数)

**数学公式**:
```
f(x, y) = (x^2 + y - 11)^2 + (x + y^2 - 7)^2
```

**特点**:
- 非凸函数
- 有四个全局最小值
- 所有最小值 f(x) = 0
- 适合测试多起点优化

## 5. 可视化实现

### 5.1 等高线图 (ContourPlotter)

**功能**:
- 绘制函数等高线
- 显示优化轨迹
- 支持 3D 表面图

**实现要点**:
- 使用 matplotlib 的 contourf
- 支持自定义范围和分辨率
- 可叠加多个轨迹

### 5.2 轨迹图 (TrajectoryPlotter)

**功能**:
- 绘制优化轨迹
- 对比多个优化器
- 显示收敛曲线

**实现要点**:
- 支持多种图表类型
- 可自定义颜色和样式
- 支持保存图表

### 5.3 对比图 (ComparisonPlotter)

**功能**:
- 综合对比多个优化器
- 显示性能统计
- 生成对比表格

**实现要点**:
- 多子图布局
- 性能指标对比
- 自动生成报告

## 6. 优化流程实现

### 6.1 统一优化接口

**文件**: `src/optimizer.py`

**核心函数**:
- `optimize()`: 单次优化
- `compare_optimizers()`: 对比多个优化器
- `grid_search()`: 网格搜索超参数

**返回结果**:
```python
{
    'x': 最终参数,
    'fun': 最终函数值,
    'niter': 迭代次数,
    'trajectory': 优化轨迹,
    'values': 函数值序列,
    'grad_norms': 梯度范数序列,
    'learning_rates': 学习率序列,
    'success': 是否收敛,
    'message': 收敛信息
}
```

### 6.2 收敛检查

**收敛条件**:
- 梯度范数 < 容差
- 达到最大迭代次数

**数值稳定性**:
- 检测 NaN 和 Inf
- 梯度裁剪
- 学习率限制

## 7. 测试策略

### 7.1 单元测试

- 测试每个优化器的更新规则
- 验证学习率调度器的计算
- 检查测试函数的正确性

### 7.2 集成测试

- 端到端优化流程测试
- 收敛性验证
- 性能基准测试

### 7.3 数值测试

- 梯度一致性检查 (有限差分)
- 数值稳定性验证
- 边界情况测试

## 8. 性能优化

### 8.1 计算优化

- 使用 NumPy 向量化操作
- 避免不必要的数组复制
- 缓存中间计算结果

### 8.2 内存优化

- 及时释放不需要的数组
- 使用原地操作
- 控制轨迹记录频率

## 9. 扩展性设计

### 9.1 添加新优化器

1. 继承 `BaseOptimizer`
2. 实现 `step` 方法
3. 注册到优化器模块

### 9.2 添加新测试函数

1. 继承 `TestFunction`
2. 实现函数值和梯度计算
3. 定义搜索范围

### 9.3 添加新调度器

1. 继承 `BaseScheduler`
2. 实现 `get_lr` 方法
3. 注册到调度器模块

## 10. 依赖管理

### 10.1 核心依赖

- numpy >= 1.20.0
- matplotlib >= 3.3.0

### 10.2 可选依赖

- seaborn >= 0.11.0 (高级可视化)
- scipy >= 1.7.0 (优化算法对比)

## 11. 最佳实践

### 11.1 代码规范

- 遵循 PEP 8
- 详细的文档字符串
- 类型注解

### 11.2 测试覆盖

- 核心功能 100% 覆盖
- 边界情况测试
- 性能基准测试

### 11.3 文档完整性

- 每个模块有详细文档
- 示例代码
- 使用说明

## 12. 已知限制

### 12.1 功能限制

- 仅支持 NumPy 数组
- 不支持 GPU 加速
- 不支持分布式优化

### 12.2 性能限制

- 大规模问题性能有限
- 内存使用较高
- 不支持并行优化

## 13. 未来改进

### 13.1 功能扩展

- 支持更多优化算法
- 添加约束优化
- 支持多目标优化

### 13.2 性能优化

- 支持 GPU 加速
- 优化内存使用
- 添加并行支持

### 13.3 可视化增强

- 交互式可视化
- 动画支持
- Web 界面
