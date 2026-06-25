# 学习笔记：模拟退火算法

## 1. 算法原理

### 1.1 物理类比

模拟退火来源于金属退火的物理过程：

**金属退火**：
1. 将金属加热到足够高的温度，原子可以自由运动
2. 缓慢冷却，原子逐渐达到低能态的稳定结构
3. 如果冷却过快，原子会陷入高能态的亚稳定结构

**优化问题**：
- **温度 T**：控制搜索的随机性
- **能量 E**：目标函数值
- **状态**：解空间中的点
- **平衡状态**：最优解

### 1.2 核心思想

模拟退火的关键创新：

1. **允许接受差解**：以一定概率接受比当前解更差的解
2. **逐渐降低接受概率**：随着温度降低，接受差解的概率减小
3. **跳出局部最优**：通过接受差解，有机会跳出局部最优

### 1.3 Metropolis 准则

接受概率公式：

```
P(accept) = {
    1,                      if ΔE ≤ 0
    exp(-ΔE / T),          if ΔE > 0
}
```

其中：
- ΔE = E_new - E_old（能量差）
- T = 当前温度

**直觉理解**：
- 如果新解更优（ΔE ≤ 0），总是接受
- 如果新解更差（ΔE > 0）：
  - 温度高时，接受概率高（探索）
  - 温度低时，接受概率低（开发）
  - 能量差越大，接受概率越低

### 1.4 温度调度

温度随时间降低的策略：

**指数冷却**：
```
T(t) = T₀ × α^t
```
- α 是冷却速率（0.95-0.99）
- 冷却速度快

**线性冷却**：
```
T(t) = T₀ - (T₀ - T_f) × t/t_max
```
- 温度均匀下降
- 可预测

**对数冷却**：
```
T(t) = T₀ / (1 + α × ln(1+t))
```
- 冷却速度慢
- 理论上能保证收敛

### 1.5 收敛性

**理论保证**：在一定条件下，模拟退火能收敛到全局最优

**条件**：
1. 温度降低足够慢
2. 每个温度下达到平衡
3. 无限时间

**实际应用**：
- 使用启发式冷却策略
- 设置合理的终止条件
- 接受近似最优解

## 2. TSP 问题

### 2.1 问题定义

**旅行商问题（TSP）**：
- 给定 n 个城市和城市间的距离
- 找到访问所有城市并回到起点的最短路径
- 每个城市只能访问一次

**复杂度**：
- 穷举法：O(n!)
- 动态规划：O(n² × 2^n)
- 启发式算法：O(n² × max_iterations)

### 2.2 邻域操作

**2-opt 交换**：
- 随机选择两个位置 i 和 j
- 反转 i 到 j 之间的子路径
- 时间复杂度：O(n)

**示例**：
```
原路径: A-B-C-D-E-F
选择 i=1, j=3
新路径: A-E-D-C-B-F
```

**Or-opt 操作**：
- 随机选择 1-3 个连续城市
- 将它们移动到路径的另一个位置
- 时间复杂度：O(n)

**3-opt 交换**：
- 随机选择三个位置
- 重新连接三个子路径
- 更强的搜索能力，但更慢

### 2.3 距离计算

**欧几里得距离**：
```python
def distance(city1, city2):
    return sqrt((city1.x - city2.x)² + (city1.y - city2.y)²)
```

**曼哈顿距离**：
```python
def distance(city1, city2):
    return abs(city1.x - city2.x) + abs(city1.y - city2.y)
```

**距离矩阵**：
- 预计算所有城市对之间的距离
- 避免重复计算
- 空间换时间

## 3. 实现细节

### 3.1 数据结构

**城市表示**：
```python
@dataclass
class City:
    x: float
    y: float
    name: str = ""
```

**路径表示**：
```python
path = [0, 3, 1, 4, 2]  # 城市索引列表
```

**历史记录**：
```python
history = {
    'temperature': [],
    'current_cost': [],
    'best_cost': [],
    'acceptance_rate': []
}
```

### 3.2 算法流程

```python
def simulated_annealing():
    # 初始化
    current = initial_solution
    best = current
    T = initial_temp

    while not should_stop():
        # 生成邻域解
        new = neighbor(current)

        # 计算成本差
        delta = cost(new) - cost(current)

        # Metropolis 准则
        if delta <= 0 or random() < exp(-delta/T):
            current = new
            if cost(current) < cost(best):
                best = current

        # 降低温度
        T = cooling(T)

    return best
```

### 3.3 参数调优

**初始温度**：
- 目标：初始接受率 80-95%
- 方法：从高温度开始，观察接受率

**冷却速率**：
- 经验值：0.95-0.99
- 更慢的冷却 → 更好的结果，但更慢

**终止条件**：
- 温度足够低（如 T < 0.01）
- 达到最大迭代次数
- 接受率太低（如 < 1%）

## 4. 调试经验

### 4.1 常见问题

**问题 1：算法不收敛**
- 原因：冷却太快
- 解决：降低冷却速率，增加迭代次数

**问题 2：陷入局部最优**
- 原因：温度太低，无法跳出
- 解决：提高初始温度，使用更慢的冷却

**问题 3：结果不稳定**
- 原因：随机性
- 解决：使用固定随机种子，多次运行取最优

**问题 4：内存溢出**
- 原因：历史记录太多
- 解决：限制历史记录大小

### 4.2 调试技巧

**打印关键信息**：
```python
print(f"Iteration {i}: T={T:.4f}, cost={cost:.4f}, accepted={accepted}")
```

**可视化分析**：
- 绘制收敛曲线
- 观察温度变化
- 分析接受率

**单元测试**：
- 测试每个组件
- 使用已知最优解验证

## 5. 性能优化

### 5.1 计算优化

**缓存距离矩阵**：
```python
# 预计算
distance_matrix = calculate_distance_matrix(cities)

# 使用
dist = distance_matrix[i][j]
```

**向量化计算**：
```python
# 慢
for i in range(n):
    for j in range(n):
        dist[i][j] = calc(i, j)

# 快
dist = np.array([[calc(i, j) for j in range(n)] for i in range(n)])
```

### 5.2 算法优化

**自适应参数**：
```python
def adaptive_cooling(T, iteration, max_iter):
    progress = iteration / max_iter
    alpha = 0.99 - 0.05 * progress  # 后期冷却更快
    return T * alpha
```

**多起点搜索**：
```python
def multi_start_sa(n_starts=10):
    results = []
    for _ in range(n_starts):
        initial = random_solution()
        result = sa(initial)
        results.append(result)
    return min(results, key=cost)
```

**并行化**：
```python
from multiprocessing import Pool

def parallel_sa(n_workers=4):
    with Pool(n_workers) as pool:
        results = pool.map(run_sa, range(n_workers))
    return min(results)
```

## 6. 扩展学习

### 6.1 相关算法

**遗传算法（GA）**：
- 种群搜索
- 交叉和变异
- 适合多目标优化

**粒子群优化（PSO）**：
- 粒子飞行
- 速度和位置更新
- 适合连续优化

**蚁群算法（ACO）**：
- 信息素引导
- 正反馈机制
- 适合路径优化

### 6.2 高级主题

**自适应模拟退火（ASA）**：
- 动态调整参数
- 自适应冷却策略
- 自适应邻域大小

**并行模拟退火**：
- 多处理器并行
- 岛屿模型
- 主从模型

**混合算法**：
- SA + 局部搜索
- SA + 遗传算法
- SA + 禁忌搜索

### 6.3 应用领域

**组合优化**：
- TSP、VRP
- 调度问题
- 布局问题

**函数优化**：
- 连续函数
- 多模态函数
- 约束优化

**机器学习**：
- 特征选择
- 超参数调优
- 神经网络训练

**工程应用**：
- 电路设计
- 通信网络
- 物流配送

## 7. 学习资源

### 7.1 经典文献

1. Kirkpatrick, S., et al. (1983). "Optimization by Simulated Annealing"
2. Černý, V. (1985). "Thermodynamical Approach to the Traveling Salesman Problem"
3. Van Laarhoven, P. J., & Aarts, E. H. (1987). "Simulated Annealing: Theory and Applications"

### 7.2 在线课程

- Coursera: Discrete Optimization
- edX: Optimization Methods
- MIT OpenCourseWare: Combinatorial Optimization

### 7.3 开源项目

- [scipy.optimize.dual_annealing](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html)
- [Simulated Annealing Library (C++)](https://github.com/gsimbr/SimulatedAnnealing)

### 7.4 工具库

- Python: NumPy, Matplotlib, SciPy
- C++: Eigen, Boost
- Java: Apache Commons Math

## 8. 实践项目

### 8.1 入门项目

1. **一维函数优化**：最小化 f(x) = x²
2. **简单 TSP**：5-10 个城市
3. **参数调优**：调整冷却策略

### 8.2 进阶项目

1. **大规模 TSP**：50+ 个城市
2. **多目标优化**：同时优化多个目标
3. **混合算法**：结合局部搜索

### 8.3 挑战项目

1. **实时优化**：在线优化问题
2. **约束优化**：带约束的优化问题
3. **实际应用**：物流配送、生产调度

## 9. 总结

### 9.1 关键要点

1. **核心思想**：允许接受差解，逐渐降低接受概率
2. **温度调度**：控制搜索的随机性
3. **Metropolis 准则**：平衡探索和开发
4. **冷却策略**：影响收敛速度和结果质量

### 9.2 学习路径

1. **理论学习**：理解算法原理
2. **代码实现**：动手实现算法
3. **实验验证**：测试不同参数
4. **应用实践**：解决实际问题

### 9.3 后续计划

- [ ] 学习其他元启发式算法
- [ ] 研究自适应参数方法
- [ ] 探索并行化技术
- [ ] 应用到实际问题