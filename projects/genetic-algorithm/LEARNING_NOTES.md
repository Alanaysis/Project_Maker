# 遗传算法 - 学习笔记

## 学习目标

通过实现遗传算法项目，深入理解：
1. 进化算法的基本原理
2. 遗传算法的核心算子设计
3. 适应度函数的设计方法
4. 组合优化问题的求解策略

---

## 第 1 天：遗传算法基础

### 核心概念

遗传算法是一种模拟自然选择过程的优化算法，核心思想来自达尔文的进化论。

**关键术语**：
- **染色体 (Chromosome)**: 问题解的编码表示
- **基因 (Gene)**: 染色体上的一个单元
- **适应度 (Fitness)**: 评估个体优劣的指标
- **种群 (Population)**: 一组个体的集合

### 生物学类比

```
生物进化                    遗传算法
─────────────────────────────────────
环境         →              优化问题
个体         →              解
染色体       →              编码
适应度       →              目标函数
自然选择     →              选择算子
基因重组     →              交叉算子
基因突变     →              变异算子
```

### 算法流程

```python
def genetic_algorithm():
    # 1. 初始化种群
    population = initialize_population(size=100)

    for generation in range(max_generations):
        # 2. 适应度评估
        evaluate_fitness(population)

        # 3. 选择
        parents = selection(population)

        # 4. 交叉
        offspring = crossover(parents)

        # 5. 变异
        offspring = mutate(offspring)

        # 6. 新种群
        population = replacement(population, offspring)

    return best_individual(population)
```

### 关键理解

1. **随机性**: GA 依赖随机搜索，但通过选择压力引导搜索方向
2. **并行性**: 种群中的个体同时评估，天然支持并行
3. **全局性**: 不易陷入局部最优（相比梯度下降）
4. **通用性**: 不需要问题的梯度信息

---

## 第 2 天：编码与解码

### 编码方式

#### 1. 二进制编码
```python
# 示例：表示 0-15 的整数
chromosome = [1, 0, 1, 1]  # 表示 11

# 编码
def encode(value, bits=4):
    return [int(b) for b in format(value, f'0{bits}b')]

# 解码
def decode(chromosome):
    return int(''.join(map(str, chromosome)), 2)
```

**优点**: 简单，理论基础完善
**缺点**: 长度固定，精度有限

#### 2. 实数编码
```python
# 示例：表示三维空间中的点
chromosome = [1.5, -2.3, 4.7]

# 直接使用，无需编解码
```

**优点**: 精度高，适合连续优化
**缺点**: 算子设计复杂

#### 3. 排列编码
```python
# 示例：TSP 路径
chromosome = [0, 3, 1, 2]  # 表示 0→3→1→2→0

# 每个数字只出现一次
```

**优点**: 天然满足约束
**缺点**: 算子需要特殊设计

### TSP 问题编码选择

对于 TSP 问题，排列编码是最佳选择：
1. 自动保证每个城市访问一次
2. 路径长度计算简单
3. 有成熟的交叉变异算子

---

## 第 3 天：适应度函数设计

### 设计原则

1. **非负性**: 适应度应为非负值
2. **单调性**: 越好的解适应度越高
3. **区分度**: 不同解的适应度应有明显差异
4. **计算效率**: 尽量快速计算

### 常见设计

#### 1. 直接映射（最大化问题）
```python
def fitness(solution):
    return objective_function(solution)  # 越大越好
```

#### 2. 倒数映射（最小化问题）
```python
def fitness(solution):
    return 1.0 / (1.0 + objective_function(solution))
```

#### 3. 常数减（最小化问题）
```python
def fitness(solution):
    return C - objective_function(solution)  # C 为足够大的常数
```

### TSP 适应度设计

```python
def fitness(route):
    distance = calculate_total_distance(route)
    return 1.0 / distance  # 距离越短，适应度越高
```

**思考**:
- 为什么用倒数而不是负数？
- 倒数映射的数值稳定性如何？
- 如何处理极端情况（距离为 0）？

---

## 第 4 天：选择算子

### 轮盘赌选择

```python
def roulette_wheel_selection(population, n):
    fitnesses = [ind.fitness for ind in population]
    total = sum(fitnesses)
    probabilities = [f / total for f in fitnesses]

    selected = np.random.choice(
        population,
        size=n,
        p=probabilities,
        replace=True
    )
    return selected
```

**特点**:
- 选择压力小
- 可能过早收敛
- 适应度差异小时效果差

### 锦标赛选择

```python
def tournament_selection(population, n, tournament_size=3):
    selected = []
    for _ in range(n):
        tournament = random.sample(population, tournament_size)
        winner = max(tournament, key=lambda x: x.fitness)
        selected.append(winner)
    return selected
```

**特点**:
- 选择压力可控
- 实现简单
- 适合并行化

### 精英保留

```python
def elitism_selection(population, n):
    sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
    return sorted_pop[:n]
```

**特点**:
- 保证最优个体不丢失
- 可能导致过早收敛
- 通常与其他选择结合使用

### 选择压力对比

| 选择方法 | 选择压力 | 多样性 | 收敛速度 |
|---------|---------|--------|---------|
| 轮盘赌   | 低      | 高     | 慢      |
| 锦标赛   | 中      | 中     | 中      |
| 精英保留 | 高      | 低     | 快      |

---

## 第 5 天：交叉算子

### 单点交叉

```python
def single_point_crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2
```

**示例**:
```
Parent1: [1, 2, 3 | 4, 5]
Parent2: [6, 7, 8 | 9, 10]
                ↓
Child1:  [1, 2, 3, 9, 10]
Child2:  [6, 7, 8, 4, 5]
```

### 两点交叉

```python
def two_point_crossover(parent1, parent2):
    point1 = random.randint(0, len(parent1) - 2)
    point2 = random.randint(point1 + 1, len(parent1) - 1)

    child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
    child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
    return child1, child2
```

### 顺序交叉 (OX) - TSP 专用

```python
def order_crossover(parent1, parent2):
    size = len(parent1)
    start = random.randint(0, size - 2)
    end = random.randint(start + 1, size - 1)

    # 保留 parent1 的一段
    child = [None] * size
    child[start:end+1] = parent1[start:end+1]

    # 从 parent2 填充剩余
    remaining = [x for x in parent2 if x not in child[start:end+1]]
    idx = 0
    for i in range(size):
        if child[i] is None:
            child[i] = remaining[idx]
            idx += 1

    return child
```

**关键理解**:
- OX 保持了城市的相对顺序
- 避免产生无效解（城市重复）
- 适合排列编码的问题

---

## 第 6 天：变异算子

### 位翻转变异

```python
def bit_flip_mutation(chromosome, mutation_rate=0.01):
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            chromosome[i] = 1 - chromosome[i]
    return chromosome
```

### 交换变异 - TSP 专用

```python
def swap_mutation(chromosome, mutation_rate=0.1):
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(chromosome)), 2)
        chromosome[i], chromosome[j] = chromosome[j], chromosome[i]
    return chromosome
```

### 逆序变异 - TSP 专用

```python
def inversion_mutation(chromosome, mutation_rate=0.1):
    if random.random() < mutation_rate:
        start = random.randint(0, len(chromosome) - 2)
        end = random.randint(start + 1, len(chromosome) - 1)
        chromosome[start:end+1] = reversed(chromosome[start:end+1])
    return chromosome
```

**变异的作用**:
1. 增加种群多样性
2. 防止过早收敛
3. 帮助跳出局部最优

---

## 第 7 天：TSP 问题求解

### 问题理解

旅行商问题 (TSP): 给定 n 个城市，找到访问每个城市一次并返回起点的最短路径。

### 距离计算

```python
def calculate_distance(city1, city2):
    return sqrt((city1[0] - city2[0])**2 + (city1[1] - city2[1])**2)
```

### 路径长度

```python
def total_distance(route, cities):
    dist = 0
    for i in range(len(route)):
        from_city = cities[route[i]]
        to_city = cities[route[(i + 1) % len(route)]]
        dist += calculate_distance(from_city, to_city)
    return dist
```

### 算子选择

TSP 问题需要特殊算子：
- **选择**: 锦标赛选择（可控选择压力）
- **交叉**: 顺序交叉 OX（保持排列有效性）
- **变异**: 交换变异 + 逆序变异

### 参数调优

```python
# 推荐参数
population_size = 100
crossover_rate = 0.8
mutation_rate = 0.2
tournament_size = 3
generations = 500
```

---

## 第 8 天：可视化与分析

### 进化曲线

```python
def plot_evolution(history):
    plt.figure(figsize=(10, 6))
    plt.plot(history['best_fitness'], label='Best')
    plt.plot(history['average_fitness'], label='Average')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.legend()
    plt.title('Evolution Progress')
    plt.show()
```

### TSP 路径可视化

```python
def plot_route(cities, route):
    plt.figure(figsize=(10, 10))

    # 绘制城市
    for i, (x, y) in enumerate(cities):
        plt.scatter(x, y, c='red', s=100)
        plt.annotate(str(i), (x, y))

    # 绘制路径
    route_coords = [cities[i] for i in route] + [cities[route[0]]]
    xs = [c[0] for c in route_coords]
    ys = [c[1] for c in route_coords]
    plt.plot(xs, ys, 'b-', linewidth=2)

    plt.title(f'Route Length: {total_distance(route, cities):.2f}')
    plt.show()
```

### 关键观察

1. **收敛曲线**: 通常呈指数衰减
2. **多样性**: 早期多样性高，后期逐渐降低
3. **最优解**: 通常在中期找到，后期微调

---

## 关键收获

### 1. 算法本质
遗传算法是一种**随机搜索算法**，通过模拟自然选择来寻找最优解。它不是万能的，但在很多问题上表现良好。

### 2. 参数敏感性
- **种群大小**: 太小容易早熟，太大计算慢
- **交叉率**: 太高破坏好解，太低搜索慢
- **变异率**: 太高变成随机搜索，太低容易陷入局部最优

### 3. 编码重要性
编码方式决定了：
- 算子的设计空间
- 搜索的效率
- 解的质量

### 4. 算子设计
好的算子应该：
- 保持解的有效性
- 平衡探索和利用
- 计算效率高

### 5. 适应度设计
适应度函数是算法的"指南针"，设计不当会导致：
- 搜索方向错误
- 收敛速度慢
- 陷入局部最优

---

## 常见陷阱

### 1. 过早收敛
**现象**: 种群多样性丧失，陷入局部最优
**解决**: 增加变异率，使用多样性维护机制

### 2. 选择压力过大
**现象**: 优秀个体迅速占据种群
**解决**: 降低锦标赛大小，使用轮盘赌选择

### 3. 适应度函数不当
**现象**: 算法收敛到错误的解
**解决**: 重新设计适应度函数，确保正确反映目标

### 4. 参数设置不当
**现象**: 算法性能差
**解决**: 参数调优，使用自适应参数

---

## 第 9 天：高级交叉算子

### 均匀交叉 (Uniform Crossover)

```python
def uniform_crossover(parent1, parent2, swap_prob=0.5):
    child1, child2 = [], []
    for g1, g2 in zip(parent1, parent2):
        if random.random() < swap_prob:
            child1.append(g2)
            child2.append(g1)
        else:
            child1.append(g1)
            child2.append(g2)
    return child1, child2
```

**特点**:
- 每个基因独立决定从哪个父代继承
- 比单点/两点交叉具有更强的探索能力
- 适用于二进制和实数编码

### 算术交叉 (Arithmetic Crossover)

```python
def arithmetic_crossover(parent1, parent2, alpha=0.5):
    child1 = [alpha * p1 + (1-alpha) * p2 for p1, p2 in zip(parent1, parent2)]
    child2 = [(1-alpha) * p1 + alpha * p2 for p1, p2 in zip(parent1, parent2)]
    return child1, child2
```

**特点**:
- 适用于实数编码
- 子代是父代的线性组合
- 保持种群的连续性

---

## 第 10 天：高级变异算子

### 高斯变异 (Gaussian Mutation)

```python
def gaussian_mutation(chromosome, mutation_rate=0.1, sigma=1.0):
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            chromosome[i] += random.gauss(0, sigma)
    return chromosome
```

**特点**:
- 适用于实数编码
- 变异幅度可控（通过 sigma）
- 可设置边界约束

### 自适应变异 (Adaptive Mutation)

```python
class AdaptiveMutation:
    def __init__(self, initial_rate=0.1, min_rate=0.01, max_rate=0.5):
        self.rate = initial_rate
        self.best_fitness = float('-inf')
        self.stagnation_count = 0

    def update(self, current_best_fitness):
        if current_best_fitness > self.best_fitness:
            # 适应度改善，降低变异率（利用）
            self.rate = max(self.min_rate, self.rate * 0.8)
            self.best_fitness = current_best_fitness
            self.stagnation_count = 0
        else:
            # 适应度停滞，增加变异率（探索）
            self.stagnation_count += 1
            if self.stagnation_count >= 10:
                self.rate = min(self.max_rate, self.rate * 1.5)
                self.stagnation_count = 0
```

**核心思想**:
- 适应度改善时降低变异率（利用已找到的好区域）
- 适应度停滞时增加变异率（探索新区域）
- 平衡探索与利用

---

## 第 11 天：多目标优化 (NSGA-II)

### 什么是多目标优化？

多个目标函数需要同时优化，通常相互冲突：
- 最小化成本 vs 最大化性能
- 最小化重量 vs 最大化强度

### Pareto 最优

解 A 支配解 B 当且仅当：
1. A 在所有目标上都不比 B 差
2. A 至少在一个目标上严格优于 B

Pareto 最优解集：不被任何其他解支配的解的集合

### NSGA-II 算法核心

1. **快速非支配排序**: 将种群分为多个前沿
2. **拥挤度距离**: 保持种群多样性
3. **锦标赛选择**: 先比较前沿，再比较拥挤度

```python
def tournament_select(ind1, ind2, fronts, crowding_distances):
    # 先比较前沿（越小越优）
    if front[ind1] < front[ind2]:
        return ind1
    elif front[ind2] < front[ind1]:
        return ind2
    else:
        # 同一前沿，选择拥挤度距离大的（多样性）
        if crowding_distances[ind1] >= crowding_distances[ind2]:
            return ind1
        else:
            return ind2
```

### 关键理解

1. **非支配排序**: O(MN^2) 复杂度，M 为目标数，N 为种群大小
2. **拥挤度距离**: 边界个体距离为无穷大，保证极端解被保留
3. **精英保留**: 合并父代和子代，选择最优的 N 个个体

---

## 第 12 天：背包问题

### 0/1 背包问题

给定 n 个物品和背包容量，每个物品有重量和价值。
选择物品使得总价值最大，且总重量不超过容量。

**编码**: 二进制编码，1 表示选择，0 表示不选择

**适应度函数**:
```python
def fitness(chromosome, items, capacity):
    total_weight = sum(w * g for (w, _), g in zip(items, chromosome))
    total_value = sum(v * g for (_, v), g in zip(items, chromosome))

    if total_weight > capacity:
        penalty = (total_weight - capacity) / capacity
        return total_value * (1 - penalty)

    return total_value
```

### 约束处理

1. **罚函数法**: 超重时降低适应度
2. **修复策略**: 移除物品直到满足约束
3. **可行性规则**: 优先选择可行解

---

## 第 13 天：函数优化

### 经典测试函数

| 函数 | 特点 | 全局最优 |
|------|------|----------|
| Sphere | 单模态 | [0,...,0] |
| Rastrigin | 多模态 | [0,...,0] |
| Rosenbrock | 狭长山谷 | [1,...,1] |
| Ackley | 多模态+平坦 | [0,...,0] |
| Griewank | 多模态 | [0,...,0] |

### 选择合适的算子

| 问题类型 | 交叉算子 | 变异算子 |
|----------|----------|----------|
| 二进制编码 | 单点/两点/均匀 | 位翻转 |
| 实数编码 | 算术/均匀 | 高斯 |
| 排列编码 | 顺序交叉(OX) | 交换/逆序 |

---

## 进阶学习

### 1. 多目标优化
- NSGA-II 算法 ✓
- Pareto 最优 ✓
- 折衷解

### 2. 约束处理
- 罚函数法 ✓
- 修复策略
- 可行性规则

### 3. 并行遗传算法
- 岛屿模型
- 细胞模型
- 主从模型

### 4. 混合算法
- 遗传算法 + 局部搜索
- 遗传算法 + 模拟退火
- 遗传算法 + 粒子群

---

## 总结

通过这个项目，我深入理解了遗传算法的：

1. **基本原理**: 模拟自然选择的优化方法
2. **核心组件**: 编码、选择、交叉、变异
3. **设计技巧**: 适应度函数、算子设计
4. **实际应用**: TSP、背包问题、函数优化
5. **高级特性**: 自适应参数、精英保留、多目标优化

遗传算法虽然简单，但蕴含着深刻的进化思想。它教会我：
- 如何从自然界汲取灵感
- 如何平衡探索和利用
- 如何设计有效的搜索策略
- 如何处理多目标和约束问题

这些思想不仅适用于优化问题，也适用于很多其他领域。
