# 03 - 实现细节

## 1. 粒子类实现

### 1.1 初始化

```python
class Particle:
    def __init__(self, dimensions, bounds, rng):
        # 在边界内随机初始化位置
        self.position = rng.uniform(low, high, size=dimensions)

        # 初始化速度（搜索范围的10%）
        v_max = (high - low) * 0.1
        self.velocity = rng.uniform(-v_max, v_max, size=dimensions)

        # 个体最佳
        self.personal_best = self.position.copy()
        self.personal_best_fitness = float("inf")
```

**设计决策**：
- 速度初始化为搜索范围的 10%，避免初始速度过大
- 使用独立的随机数生成器，便于复现

### 1.2 适应度评估

```python
def evaluate(self, objective_function):
    fitness = float(objective_function(self.position))

    # 更新个体最佳
    if fitness < self.personal_best_fitness:
        self.personal_best_fitness = fitness
        self.personal_best = self.position.copy()

    return fitness
```

**设计决策**：
- 评估时自动更新个体最佳
- 使用 `float()` 确保返回值类型一致

### 1.3 速度更新

```python
def update_velocity(self, global_best, w, c1, c2):
    r1 = self._rng.random(self.dimensions)
    r2 = self._rng.random(self.dimensions)

    inertia = w * self.velocity
    cognitive = c1 * r1 * (self.personal_best - self.position)
    social = c2 * r2 * (global_best - self.position)

    self.velocity = inertia + cognitive + social
```

**设计决策**：
- 每个维度使用独立的随机数
- 三部分相加，清晰明了

### 1.4 位置更新

```python
def update_position(self, bounds=None):
    self.position = self.position + self.velocity

    if bounds is not None:
        low, high = bounds
        self.position = np.clip(self.position, low, high)
```

**设计决策**：
- 使用 `np.clip` 进行边界约束，简单高效
- 边界约束是可选的

## 2. 粒子群类实现

### 2.1 初始化

```python
class Swarm:
    def __init__(self, config):
        self.particles = [
            Particle(config.dimensions, config.bounds, self._rng)
            for _ in range(config.n_particles)
        ]
```

**设计决策**：
- 所有粒子共享同一个随机数生成器
- 配置参数集中管理

### 2.2 适应度评估

```python
def _evaluate_swarm(self, objective_function):
    for particle in self.particles:
        fitness = particle.evaluate(objective_function)

        if fitness < self.global_best_fitness:
            self.global_best_fitness = fitness
            self.global_best = particle.position.copy()
            self._stagnation_count = 0
```

**设计决策**：
- 遍历所有粒子进行评估
- 发现更好的解时重置停滞计数器

### 2.3 惯性权重策略

```python
def _get_inertia_weight(self, iteration):
    if self.config.w_strategy == "fixed":
        return self.config.w
    elif self.config.w_strategy == "linear_decay":
        return self.config.w_max - (self.config.w_max - self.config.w_min) * \
               (iteration / self.config.max_iterations)
    elif self.config.w_strategy == "adaptive":
        if self._stagnation_count > 5:
            return min(self.config.w * 1.1, self.config.w_max)
        else:
            return max(self.config.w * 0.9, self.config.w_min)
```

**设计决策**：
- 线性递减：从 w_max 衰减到 w_min
- 自适应：根据收敛情况动态调整

### 2.4 收敛检测

```python
def _check_convergence(self, tolerance):
    if len(self.convergence_history) < 2:
        return False

    recent_improvement = abs(
        self.convergence_history[-1] - self.convergence_history[-2]
    )
    return recent_improvement < tolerance
```

**设计决策**：
- 基于连续两代的改善量判断
- 使用停滞计数器避免过早停止

### 2.5 主循环

```python
def optimize(self, objective_function):
    for iteration in range(self.config.max_iterations):
        # 评估
        self._evaluate_swarm(objective_function)
        self.convergence_history.append(self.global_best_fitness)

        # 更新惯性权重
        w = self._get_inertia_weight(iteration)

        # 更新粒子
        for particle in self.particles:
            particle.update_velocity(self.global_best, w, self.config.c1, self.config.c2)
            particle.update_position(self.config.bounds)

        # 收敛检测
        if self._check_convergence(self.config.tolerance):
            self._stagnation_count += 1
        else:
            self._stagnation_count = 0

        # 提前停止
        if self._stagnation_count >= self.config.patience:
            break
```

**设计决策**：
- 先评估后更新，确保每代都有正确的全局最佳
- 支持提前停止以节省计算

## 3. 测试函数实现

### 3.1 Sphere 函数

```python
def sphere(x):
    return float(np.sum(x**2))
```

**特点**：单峰、凸函数，最简单的测试函数。

### 3.2 Rosenbrock 函数

```python
def rosenbrock(x):
    n = len(x)
    result = 0.0
    for i in range(n - 1):
        result += 100 * (x[i + 1] - x[i]**2)**2 + (1 - x[i])**2
    return float(result)
```

**特点**：单峰但有狭窄的全局最优谷，难以收敛。

### 3.3 Rastrigin 函数

```python
def rastrigin(x):
    n = len(x)
    return float(10 * n + np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))
```

**特点**：多峰，大量局部最优，但所有局部最优的值相同。

### 3.4 Ackley 函数

```python
def ackley(x):
    n = len(x)
    sum_sq = np.sum(x**2) / n
    sum_cos = np.sum(np.cos(2 * np.pi * x)) / n
    return float(-20 * np.exp(-0.2 * np.sqrt(sum_sq)) - np.exp(sum_cos) + 20 + np.e)
```

**特点**：多峰，大量局部最优，指数函数使搜索困难。

### 3.5 Griewank 函数

```python
def griewank(x):
    sum_sq = np.sum(x**2) / 4000
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return float(1 + sum_sq - prod_cos)
```

**特点**：多峰，但随着维度增加，局部最优数量减少。

## 4. 可视化实现

### 4.1 收敛曲线

```python
@staticmethod
def plot_convergence(history, title, figsize):
    plt.figure(figsize=figsize)
    plt.plot(history, linewidth=2, color="#2196F3")
    plt.xlabel("迭代次数")
    plt.ylabel("最佳适应度")
    plt.yscale("log")
    plt.grid(True, alpha=0.3)
```

### 4.2 2D 搜索空间

```python
@staticmethod
def plot_2d_search_space(particles, bounds, objective_function, global_best):
    # 绘制等高线
    # 绘制粒子
    # 绘制全局最佳
```

### 4.3 粒子轨迹

```python
@staticmethod
def plot_trajectory(trajectories, bounds, objective_function, global_best):
    # 绘制等高线
    # 绘制轨迹
    # 标记起点和终点
```

## 5. 性能优化

### 5.1 NumPy 向量化

- 使用 NumPy 数组操作替代循环
- 利用广播机制进行批量计算

### 5.2 内存优化

- 可选的轨迹追踪
- 及时释放不需要的数组

### 5.3 计算优化

- 避免不必要的数组复制
- 使用原地操作

## 6. 错误处理

### 6.1 参数验证

- 检查维度 > 0
- 检查边界合法性
- 检查学习因子范围

### 6.2 数值稳定性

- 使用 `float()` 确保类型一致
- 使用 `np.clip` 防止越界
- 处理除零等异常情况

## 7. 代码风格

### 7.1 命名规范

- 类名：PascalCase
- 方法名：snake_case
- 常量：UPPER_SNAKE_CASE

### 7.2 文档

- 每个类和方法都有 docstring
- 包含参数说明和返回值说明
- 包含使用示例

### 7.3 类型提示

- 使用 Python 类型提示
- 导入 `typing` 模块
