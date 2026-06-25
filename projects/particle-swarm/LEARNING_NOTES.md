# 学习笔记：粒子群优化

## 1. 项目目标

从零实现粒子群优化算法，深入理解群体智能的核心原理：
- 理解粒子群原理
- 掌握速度更新
- 学会全局最优搜索

## 2. 核心概念

### 2.1 什么是粒子群优化？

粒子群优化（PSO）是一种**群体智能优化算法**，由 Kennedy 和 Eberhart 于 1995 年提出。灵感来源于鸟群觅食行为。

**核心思想**：
- 每个粒子代表搜索空间中的一个候选解
- 粒子通过跟踪个体最佳和全局最佳来调整飞行方向
- 群体协作可以找到单个粒子难以找到的最优解

**类比**：
- 想象一群鸟在寻找食物
- 每只鸟记住自己找到的最好位置（个体最佳）
- 整个鸟群共享信息，记住群体找到的最好位置（全局最佳）
- 每只鸟根据自身经验和群体经验调整飞行方向

### 2.2 速度更新公式

PSO 的核心是速度更新公式：

```
v_new = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
```

**三部分含义**：

1. **惯性部分 (w * v)**
   - 保持粒子原有的运动趋势
   - w 大：探索能力强，但可能发散
   - w 小：开发能力强，但可能陷入局部最优

2. **认知部分 (c1 * r1 * (pbest - x))**
   - 粒子向自己的历史最佳位置移动
   - 代表"个体经验"
   - c1 大：更依赖个体经验

3. **社会部分 (c2 * r2 * (gbest - x))**
   - 粒子向群体的历史最佳位置移动
   - 代表"群体经验"
   - c2 大：更依赖群体经验

### 2.3 位置更新公式

```
x_new = x + v_new
```

位置更新很简单：当前位置加上速度就是新位置。

### 2.4 算法流程

```
初始化粒子群（随机位置和速度）
    ↓
评估适应度 → 更新个体最佳和全局最佳
    ↓
更新速度和位置
    ↓
是否满足终止条件？
    ↓ 否
返回上一步
    ↓ 是
输出全局最佳
```

## 3. 实现细节

### 3.1 粒子类 (Particle)

```python
class Particle:
    def __init__(self, dimensions, bounds, rng):
        # 随机初始化位置
        self.position = rng.uniform(low, high, size=dimensions)

        # 初始化速度（搜索范围的10%）
        v_max = (high - low) * 0.1
        self.velocity = rng.uniform(-v_max, v_max, size=dimensions)

        # 个体最佳
        self.personal_best = self.position.copy()
        self.personal_best_fitness = float("inf")

    def evaluate(self, objective_function):
        fitness = float(objective_function(self.position))
        if fitness < self.personal_best_fitness:
            self.personal_best_fitness = fitness
            self.personal_best = self.position.copy()
        return fitness

    def update_velocity(self, global_best, w, c1, c2):
        r1 = self._rng.random(self.dimensions)
        r2 = self._rng.random(self.dimensions)
        self.velocity = (w * self.velocity +
                        c1 * r1 * (self.personal_best - self.position) +
                        c2 * r2 * (global_best - self.position))

    def update_position(self, bounds):
        self.position = self.position + self.velocity
        self.position = np.clip(self.position, bounds[0], bounds[1])
```

**关键设计**：
- 使用独立的随机数生成器，便于复现
- 速度初始化为搜索范围的 10%
- 评估时自动更新个体最佳
- 使用 `np.clip` 进行边界约束

### 3.2 粒子群类 (Swarm)

```python
class Swarm:
    def __init__(self, config):
        self.particles = [
            Particle(config.dimensions, config.bounds, self._rng)
            for _ in range(config.n_particles)
        ]

    def optimize(self, objective_function):
        for iteration in range(self.config.max_iterations):
            # 评估所有粒子
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

**关键设计**：
- 先评估后更新，确保每代都有正确的全局最佳
- 支持多种惯性权重策略
- 支持收敛检测和提前停止
- 支持回调函数和轨迹追踪

### 3.3 惯性权重策略

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

**策略对比**：
- **固定权重**：简单，但难以平衡探索和开发
- **线性递减**：经典策略，前期探索，后期开发
- **自适应**：根据收敛情况动态调整

### 3.4 测试函数

```python
# Sphere 函数（最简单）
def sphere(x):
    return float(np.sum(x**2))

# Rosenbrock 函数（窄谷）
def rosenbrock(x):
    n = len(x)
    result = 0.0
    for i in range(n - 1):
        result += 100 * (x[i + 1] - x[i]**2)**2 + (1 - x[i])**2
    return float(result)

# Rastrigin 函数（多峰）
def rastrigin(x):
    n = len(x)
    return float(10 * n + np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))
```

**函数选择**：
- Sphere：验证算法基本功能
- Rosenbrock：测试窄谷搜索能力
- Rastrigin：测试跳出局部最优能力

## 4. 关键收获

### 4.1 探索与开发的平衡

PSO 的核心挑战是平衡**探索**和**开发**：

- **探索 (Exploration)**：在搜索空间中广泛搜索，发现新的有希望区域
- **开发 (Exploitation)**：在已知的有希望区域中精细搜索，找到最优解

**惯性权重 w** 是平衡探索和开发的关键：
- w 大（接近 1）：探索能力强，粒子保持原有运动趋势
- w 小（接近 0）：开发能力强，粒子更依赖个体和群体经验

**线性递减策略**：
- 前期 w 大，侧重探索
- 后期 w 小，侧重开发
- 这是经典且有效的策略

### 4.2 个体学习与社会学习

**认知系数 c1** 和 **社会系数 c2** 控制学习的平衡：

- c1 大：更依赖个体经验，粒子更"固执"
- c2 大：更依赖群体经验，粒子更"从众"
- c1 = c2 = 2.0：经典平衡设置

**启示**：
- 如果 c1 = 0，粒子没有个体记忆，容易陷入局部最优
- 如果 c2 = 0，粒子独立搜索，无法利用群体信息
- 平衡两者才能发挥 PSO 的优势

### 4.3 粒子数量的影响

- **太少**（< 10）：搜索不充分，容易陷入局部最优
- **适中**（20-50）：平衡计算成本和搜索能力
- **太多**（> 100）：计算成本高，但边际收益递减

**经验法则**：
- 简单问题：20-30 个粒子
- 复杂问题：50-100 个粒子
- 高维问题：需要更多粒子

### 4.4 边界约束的重要性

边界约束可以：
- 防止粒子飞出搜索空间
- 引导粒子在有效区域内搜索
- 提高算法的稳定性

**实现方式**：
```python
self.position = np.clip(self.position, bounds[0], bounds[1])
```

## 5. 实际应用

### 5.1 优势

- **简单易懂**：算法原理直观，易于实现
- **参数少**：主要参数只有 w、c1、c2
- **收敛快**：对于单峰函数收敛速度快
- **无需梯度**：不需要目标函数的梯度信息
- **并行化**：粒子评估可以并行化

### 5.2 局限性

- **局部最优**：对多峰函数容易陷入局部最优
- **高维问题**：维度增加时性能下降
- **参数敏感**：不同问题需要不同的参数设置
- **不保证最优**：不保证收敛到全局最优

### 5.3 应用场景

**工程优化**：
- 结构优化设计
- 电力系统调度
- 流程优化

**机器学习**：
- 神经网络训练
- 特征选择
- 超参数调优

**图像处理**：
- 图像分割
- 目标检测
- 图像配准

**其他领域**：
- 路径规划
- 调度问题
- 金融投资组合优化

## 6. 参数调优指南

### 6.1 惯性权重 w

| 值 | 效果 | 适用场景 |
|---|---|---|
| w > 1 | 全局探索能力强，但可能发散 | 不推荐 |
| w ≈ 0.9 | 平衡探索和开发 | 早期迭代 |
| w ≈ 0.4 | 局部开发能力强 | 后期迭代 |
| w = 0 | 无记忆，容易陷入局部最优 | 不推荐 |

**推荐**：使用线性递减策略，w 从 0.9 递减到 0.4。

### 6.2 学习因子 c1 和 c2

| 设置 | 效果 |
|---|---|
| c1 = 0 | 无个体记忆，只向群体学习 |
| c2 = 0 | 无社会学习，粒子独立搜索 |
| c1 = c2 = 2.0 | 平衡个体和群体学习（经典设置） |
| c1 > c2 | 更依赖个体经验 |
| c1 < c2 | 更依赖群体经验 |

**推荐**：c1 = c2 = 1.5 或 c1 = c2 = 2.0。

### 6.3 粒子数量

- **太少**（< 10）：搜索不充分
- **适中**（20-50）：平衡计算成本和搜索能力
- **太多**（> 100）：计算成本高

**推荐**：30 个粒子作为起点。

### 6.4 最大迭代次数

- **太少**：可能未收敛
- **太多**：计算成本高
- **推荐**：100-500 次，根据问题复杂度调整

## 7. 与其他优化算法对比

| 算法 | 优点 | 缺点 | 适用场景 |
|---|---|---|---|
| PSO | 简单、参数少、收敛快 | 易陷入局部最优 | 连续优化 |
| 遗传算法 | 全局搜索能力强 | 参数多、收敛慢 | 组合优化 |
| 模拟退火 | 能跳出局部最优 | 收敛慢 | 离散优化 |
| 梯度下降 | 收敛快、精度高 | 需要梯度信息 | 凸优化 |

**PSO vs 遗传算法**：
- PSO 更简单，参数更少
- PSO 收敛更快
- 遗传算法全局搜索能力更强
- PSO 更适合连续优化，遗传算法更适合组合优化

## 8. 调试经验

### 8.1 常见问题

**问题 1：粒子发散**
- 原因：惯性权重 w 太大
- 解决：减小 w，或使用线性递减策略

**问题 2：陷入局部最优**
- 原因：惯性权重 w 太小，或粒子数量太少
- 解决：增大 w，增加粒子数量，或使用自适应策略

**问题 3：收敛太慢**
- 原因：学习因子 c1、c2 太小
- 解决：增大 c1、c2

**问题 4：结果不可复现**
- 原因：没有设置随机种子
- 解决：设置 `random_seed` 参数

### 8.2 调试技巧

1. **打印收敛历史**：观察适应度的变化趋势
2. **可视化粒子分布**：观察粒子是否覆盖搜索空间
3. **检查边界约束**：确保粒子没有飞出搜索空间
4. **对比不同参数**：找出最佳参数设置

### 8.3 性能优化

1. **使用 NumPy 向量化**：避免 Python 循环
2. **减少不必要的数组复制**：使用原地操作
3. **可选的轨迹追踪**：节省内存
4. **并行化粒子评估**：利用多核 CPU

## 9. 进一步学习

### 9.1 PSO 变体

- **混沌 PSO**：用混沌序列替代随机数
- **量子 PSO**：引入量子力学概念
- **多目标 PSO**：处理多目标优化问题
- **离散 PSO**：处理离散/组合优化问题

### 9.2 相关算法

- **蚁群算法**：模拟蚂蚁觅食行为
- **人工蜂群算法**：模拟蜜蜂采蜜行为
- **萤火虫算法**：模拟萤火虫发光行为
- **灰狼优化**：模拟灰狼捕食行为

### 9.3 深入主题

- 收敛性分析
- 参数自适应策略
- 拓扑结构优化
- 约束处理技术

### 9.4 参考资料

- Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.
- Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer.
- Poli, R., Kennedy, J., & Blackwell, T. (2007). Particle swarm optimization.
- [Wikipedia: Particle swarm optimization](https://en.wikipedia.org/wiki/Particle_swarm_optimization)
- [Swarm Intelligence](https://www.swarmintelligence.org/)
