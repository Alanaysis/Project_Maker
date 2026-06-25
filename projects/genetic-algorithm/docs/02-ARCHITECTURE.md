# 02 - 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Genetic Algorithm Framework            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Problems    │  │  Operators   │  │    Core      │      │
│  │  (TSP, etc)  │  │  (Select,    │  │  (Population,│      │
│  │              │  │   Cross,     │  │   Individual,│      │
│  │              │  │   Mutate)    │  │   Engine)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                  │               │
│         └────────────────┼──────────────────┘               │
│                          │                                  │
│                    ┌─────▼─────┐                            │
│                    │  Runner   │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Core 模块

#### Individual (个体类)
```python
class Individual:
    """表示一个个体（解）"""
    chromosome: List[Any]  # 染色体
    fitness: float         # 适应度值

    def evaluate(self, fitness_func: Callable) -> float
    def copy(self) -> Individual
```

#### Population (种群类)
```python
class Population:
    """管理一组个体"""
    individuals: List[Individual]
    size: int

    def initialize(self, size: int, chromosome_factory: Callable)
    def evaluate(self, fitness_func: Callable)
    def get_best(self) -> Individual
    def get_statistics(self) -> Dict
```

#### GAEngine (遗传算法引擎)
```python
class GAEngine:
    """遗传算法核心引擎"""
    population: Population
    selection_operator: SelectionOperator
    crossover_operator: CrossoverOperator
    mutation_operator: MutationOperator

    def run(self, generations: int) -> Individual
    def evolve_one_generation(self) -> None
    def select_parents(self) -> List[Individual]
    def crossover(self, parents: List[Individual]) -> List[Individual]
    def mutate(self, offspring: List[Individual]) -> List[Individual]
```

### 2. Operators 模块

#### SelectionOperator (选择算子)
```python
class SelectionOperator(ABC):
    """选择算子基类"""
    @abstractmethod
    def select(self, population: Population, n: int) -> List[Individual]

class RouletteWheelSelection(SelectionOperator):
    """轮盘赌选择"""

class TournamentSelection(SelectionOperator):
    """锦标赛选择"""

class ElitismSelection(SelectionOperator):
    """精英保留选择"""
```

#### CrossoverOperator (交叉算子)
```python
class CrossoverOperator(ABC):
    """交叉算子基类"""
    @abstractmethod
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]

class SinglePointCrossover(CrossoverOperator):
    """单点交叉"""

class TwoPointCrossover(CrossoverOperator):
    """两点交叉"""

class OrderCrossover(CrossoverOperator):
    """顺序交叉 (OX) - 用于 TSP"""
```

#### MutationOperator (变异算子)
```python
class MutationOperator(ABC):
    """变异算子基类"""
    @abstractmethod
    def mutate(self, individual: Individual) -> Individual

class BitFlipMutation(MutationOperator):
    """位翻转变异"""

class SwapMutation(MutationOperator):
    """交换变异 - 用于 TSP"""

class InversionMutation(MutationOperator):
    """逆序变异 - 用于 TSP"""
```

### 3. Problems 模块

#### Problem (问题基类)
```python
class Problem(ABC):
    """优化问题基类"""
    @abstractmethod
    def create_individual(self) -> Individual

    @abstractmethod
    def fitness(self, individual: Individual) -> float

    @abstractmethod
    def display(self, individual: Individual) -> None
```

#### TSP (旅行商问题)
```python
class TSPProblem(Problem):
    """旅行商问题"""
    cities: List[Tuple[float, float]]
    distance_matrix: np.ndarray

    def create_individual(self) -> Individual
    def fitness(self, individual: Individual) -> float
    def calculate_distance(self, route: List[int]) -> float
    def display(self, individual: Individual) -> None
```

## 数据流

```
1. 初始化
   Problem.create_individual() → Individual
   Population.initialize() → [Individual, ...]

2. 迭代循环
   Population.evaluate(fitness)
   SelectionOperator.select(population, n)
   CrossoverOperator.crossover(parent1, parent2)
   MutationOperator.mutate(offspring)
   Population.update(offspring)

3. 输出
   Population.get_best() → 最优解
```

## 关键设计决策

### 1. 编码方式
- **二进制编码**: 适用于离散问题
- **实数编码**: 适用于连续优化
- **排列编码**: 适用于 TSP 等组合问题

### 2. 适应度函数
- 最大化问题: fitness = f(x)
- 最小化问题: fitness = 1 / f(x) 或 C - f(x)

### 3. 选择压力
- 轮盘赌: 选择压力较小
- 锦标赛: 选择压力可通过锦标赛大小调节
- 精英保留: 确保最优个体不丢失

### 4. 交叉率和变异率
- 交叉率: 通常 0.6-0.9
- 变异率: 通常 0.01-0.1

## 扩展性设计

### 添加新问题
1. 继承 `Problem` 基类
2. 实现 `create_individual()`, `fitness()`, `display()` 方法
3. 选择合适的编码和算子

### 添加新算子
1. 继承对应的基类
2. 实现 `select()`, `crossover()` 或 `mutate()` 方法
3. 在 GAEngine 中配置使用

## 性能优化

### 1. 适应度缓存
- 避免重复计算相同个体的适应度
- 使用哈希表存储已计算的适应度

### 2. 并行评估
- 使用多进程并行评估种群
- 特别适用于计算密集型适应度函数

### 3. 早停机制
- 当适应度不再提升时提前终止
- 节省计算资源

## 错误处理

### 1. 无效个体
- 检查染色体长度和范围
- 修复或替换无效个体

### 2. 种群多样性丧失
- 监测种群相似度
- 引入移民或重启机制

### 3. 参数越界
- 验证交叉率、变异率等参数
- 提供合理的默认值
