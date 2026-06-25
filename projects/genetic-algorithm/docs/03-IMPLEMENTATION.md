# 03 - 实现细节

## 核心算法实现

### 1. Individual 类实现

```python
class Individual:
    """表示遗传算法中的一个个体"""

    def __init__(self, chromosome: List[Any]):
        self.chromosome = chromosome
        self.fitness = 0.0

    def evaluate(self, fitness_func: Callable[[List[Any]], float]) -> float:
        """评估个体适应度"""
        self.fitness = fitness_func(self.chromosome)
        return self.fitness

    def copy(self) -> 'Individual':
        """深拷贝个体"""
        new_ind = Individual(self.chromosome.copy())
        new_ind.fitness = self.fitness
        return new_ind

    def __repr__(self) -> str:
        return f"Individual(chromosome={self.chromosome}, fitness={self.fitness:.4f})"
```

### 2. Population 类实现

```python
class Population:
    """种群管理类"""

    def __init__(self):
        self.individuals: List[Individual] = []
        self.size: int = 0

    def initialize(self, size: int, chromosome_factory: Callable[[], List[Any]]):
        """初始化种群"""
        self.size = size
        self.individuals = [Individual(chromosome_factory()) for _ in range(size)]

    def evaluate(self, fitness_func: Callable[[List[Any]], float]):
        """评估所有个体"""
        for ind in self.individuals:
            ind.evaluate(fitness_func)

    def get_best(self) -> Individual:
        """获取最优个体"""
        return max(self.individuals, key=lambda x: x.fitness)

    def get_worst(self) -> Individual:
        """获取最差个体"""
        return min(self.individuals, key=lambda x: x.fitness)

    def get_statistics(self) -> Dict:
        """获取种群统计信息"""
        fitnesses = [ind.fitness for ind in self.individuals]
        return {
            'best': max(fitnesses),
            'worst': min(fitnesses),
            'average': sum(fitnesses) / len(fitnesses),
            'std': np.std(fitnesses)
        }

    def replace(self, new_individuals: List[Individual]):
        """替换种群中的个体"""
        self.individuals = new_individuals
        self.size = len(new_individuals)
```

## 选择算子实现

### 1. 轮盘赌选择

```python
class RouletteWheelSelection(SelectionOperator):
    """轮盘赌选择：适应度越高，被选中概率越大"""

    def select(self, population: Population, n: int) -> List[Individual]:
        fitnesses = [ind.fitness for ind in population.individuals]

        # 处理负适应度
        min_fitness = min(fitnesses)
        if min_fitness < 0:
            fitnesses = [f - min_fitness + 1 for f in fitnesses]

        total_fitness = sum(fitnesses)
        probabilities = [f / total_fitness for f in fitnesses]

        selected_indices = np.random.choice(
            len(population.individuals),
            size=n,
            p=probabilities,
            replace=True
        )

        return [population.individuals[i].copy() for i in selected_indices]
```

### 2. 锦标赛选择

```python
class TournamentSelection(SelectionOperator):
    """锦标赛选择：随机选择k个个体，取最优"""

    def __init__(self, tournament_size: int = 3):
        self.tournament_size = tournament_size

    def select(self, population: Population, n: int) -> List[Individual]:
        selected = []
        for _ in range(n):
            # 随机选择 tournament_size 个个体
            tournament = random.sample(population.individuals, self.tournament_size)
            # 选择适应度最高的
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner.copy())
        return selected
```

### 3. 精英保留选择

```python
class ElitismSelection(SelectionOperator):
    """精英保留：保留最优的n个个体"""

    def select(self, population: Population, n: int) -> List[Individual]:
        sorted_pop = sorted(population.individuals, key=lambda x: x.fitness, reverse=True)
        return [ind.copy() for ind in sorted_pop[:n]]
```

## 交叉算子实现

### 1. 单点交叉

```python
class SinglePointCrossover(CrossoverOperator):
    """单点交叉：随机选择一个切点，交换两父代的后半部分"""

    def __init__(self, crossover_rate: float = 0.8):
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)
        point = random.randint(1, size - 1)

        child1_chromosome = parent1.chromosome[:point] + parent2.chromosome[point:]
        child2_chromosome = parent2.chromosome[:point] + parent1.chromosome[point:]

        return Individual(child1_chromosome), Individual(child2_chromosome)
```

### 2. 顺序交叉 (OX) - TSP 专用

```python
class OrderCrossover(CrossoverOperator):
    """顺序交叉：保持城市访问的相对顺序"""

    def __init__(self, crossover_rate: float = 0.8):
        self.crossover_rate = crossover_rate

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        size = len(parent1.chromosome)

        # 随机选择两个切点
        start = random.randint(0, size - 2)
        end = random.randint(start + 1, size - 1)

        # 生成子代1
        child1 = [None] * size
        child1[start:end+1] = parent1.chromosome[start:end+1]

        # 从 parent2 填充剩余位置
        remaining = [x for x in parent2.chromosome if x not in child1[start:end+1]]
        idx = 0
        for i in range(size):
            if child1[i] is None:
                child1[i] = remaining[idx]
                idx += 1

        # 生成子代2（对称操作）
        child2 = [None] * size
        child2[start:end+1] = parent2.chromosome[start:end+1]

        remaining = [x for x in parent1.chromosome if x not in child2[start:end+1]]
        idx = 0
        for i in range(size):
            if child2[i] is None:
                child2[i] = remaining[idx]
                idx += 1

        return Individual(child1), Individual(child2)
```

## 交叉算子实现

### 1. 均匀交叉

```python
class UniformCrossover(CrossoverOperator):
    """均匀交叉：每个基因以相同概率从两个父代中随机选择"""

    def __init__(self, crossover_rate: float = 0.8, swap_probability: float = 0.5):
        self.crossover_rate = crossover_rate
        self.swap_probability = swap_probability

    def crossover(self, parent1, parent2):
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        child1, child2 = [], []
        for g1, g2 in zip(parent1.chromosome, parent2.chromosome):
            if random.random() < self.swap_probability:
                child1.append(g2)
                child2.append(g1)
            else:
                child1.append(g1)
                child2.append(g2)

        return Individual(child1), Individual(child2)
```

### 2. 算术交叉

```python
class ArithmeticCrossover(CrossoverOperator):
    """算术交叉：对实数编码的父代进行线性组合"""

    def __init__(self, crossover_rate: float = 0.8, alpha: float = 0.5):
        self.crossover_rate = crossover_rate
        self.alpha = alpha

    def crossover(self, parent1, parent2):
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        alpha = self.alpha
        child1 = [alpha * p1 + (1 - alpha) * p2 for p1, p2 in zip(parent1.chromosome, parent2.chromosome)]
        child2 = [(1 - alpha) * p1 + alpha * p2 for p1, p2 in zip(parent1.chromosome, parent2.chromosome)]

        return Individual(child1), Individual(child2)
```

## 变异算子实现

### 1. 位翻转变异

```python
class BitFlipMutation(MutationOperator):
    """位翻转变异：随机翻转染色体上的位"""

    def __init__(self, mutation_rate: float = 0.01):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                mutated.chromosome[i] = 1 - mutated.chromosome[i]
        return mutated
```

### 2. 交换变异 - TSP 专用

```python
class SwapMutation(MutationOperator):
    """交换变异：随机交换两个城市的位置"""

    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        if random.random() < self.mutation_rate:
            size = len(mutated.chromosome)
            i, j = random.sample(range(size), 2)
            mutated.chromosome[i], mutated.chromosome[j] = mutated.chromosome[j], mutated.chromosome[i]
        return mutated
```

### 3. 逆序变异 - TSP 专用

```python
class InversionMutation(MutationOperator):
    """逆序变异：随机选择一段子路径并反转"""

    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual) -> Individual:
        mutated = individual.copy()
        if random.random() < self.mutation_rate:
            size = len(mutated.chromosome)
            start = random.randint(0, size - 2)
            end = random.randint(start + 1, size - 1)
            mutated.chromosome[start:end+1] = reversed(mutated.chromosome[start:end+1])
        return mutated
```

### 4. 高斯变异

```python
class GaussianMutation(MutationOperator):
    """高斯变异：对实数编码的基因添加高斯噪声"""

    def __init__(self, mutation_rate=0.1, sigma=1.0, min_value=None, max_value=None):
        self.mutation_rate = mutation_rate
        self.sigma = sigma
        self.min_value = min_value
        self.max_value = max_value

    def mutate(self, individual):
        mutated = individual.copy()
        for i in range(len(mutated.chromosome)):
            if random.random() < self.mutation_rate:
                noise = random.gauss(0, self.sigma)
                mutated.chromosome[i] += noise
                if self.min_value is not None:
                    mutated.chromosome[i] = max(mutated.chromosome[i], self.min_value)
                if self.max_value is not None:
                    mutated.chromosome[i] = min(mutated.chromosome[i], self.max_value)
        return mutated
```

### 5. 自适应变异

```python
class AdaptiveMutation(MutationOperator):
    """自适应变异：根据种群适应度自动调整变异率"""

    def __init__(self, initial_mutation_rate=0.1, min_rate=0.01, max_rate=0.5,
                 sigma=1.0, stagnation_threshold=10, increase_factor=1.5, decrease_factor=0.8):
        self.mutation_rate = initial_mutation_rate
        # ... 其他参数

    def update(self, current_best_fitness):
        """根据当前最优适应度更新变异率"""
        if current_best_fitness > self._best_fitness:
            # 适应度改善，降低变异率
            self.mutation_rate = max(self.min_rate, self.mutation_rate * self.decrease_factor)
        else:
            # 适应度停滞，增加变异率
            self._stagnation_count += 1
            if self._stagnation_count >= self.stagnation_threshold:
                self.mutation_rate = min(self.max_rate, self.mutation_rate * self.increase_factor)

    def mutate(self, individual):
        # 使用当前变异率进行高斯变异
        ...
```

## GAEngine 实现

```python
class GAEngine:
    """遗传算法核心引擎"""

    def __init__(self,
                 problem: Problem,
                 population_size: int = 100,
                 selection: SelectionOperator = None,
                 crossover: CrossoverOperator = None,
                 mutation: MutationOperator = None):

        self.problem = problem
        self.population_size = population_size

        # 默认算子
        self.selection = selection or TournamentSelection()
        self.crossover = crossover or SinglePointCrossover()
        self.mutation = mutation or BitFlipMutation()

        # 初始化种群
        self.population = Population()
        self.population.initialize(population_size, problem.create_individual)

        # 历史记录
        self.history = {
            'best_fitness': [],
            'average_fitness': [],
            'best_individual': None
        }

    def evolve_one_generation(self):
        """进化一代"""
        # 评估种群
        self.population.evaluate(self.problem.fitness)

        # 记录统计信息
        stats = self.population.get_statistics()
        self.history['best_fitness'].append(stats['best'])
        self.history['average_fitness'].append(stats['average'])

        # 选择父代
        parents = self.selection.select(self.population, self.population_size)

        # 交叉产生子代
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            child1, child2 = self.crossover.crossover(parents[i], parents[i + 1])
            offspring.extend([child1, child2])

        # 变异
        offspring = [self.mutation.mutate(ind) for ind in offspring]

        # 更新种群
        self.population.replace(offspring)

    def run(self, generations: int = 100, verbose: bool = True) -> Individual:
        """运行遗传算法"""
        for gen in range(generations):
            self.evolve_one_generation()

            if verbose and gen % 10 == 0:
                stats = self.population.get_statistics()
                print(f"Generation {gen}: Best={stats['best']:.4f}, Avg={stats['average']:.4f}")

        # 返回最优解
        self.population.evaluate(self.problem.fitness)
        best = self.population.get_best()
        self.history['best_individual'] = best
        return best
```

## TSP 问题实现

```python
class TSPProblem(Problem):
    """旅行商问题"""

    def __init__(self, cities: List[Tuple[float, float]]):
        self.cities = cities
        self.n_cities = len(cities)
        self.distance_matrix = self._calculate_distance_matrix()

    def _calculate_distance_matrix(self) -> np.ndarray:
        """计算城市间距离矩阵"""
        matrix = np.zeros((self.n_cities, self.n_cities))
        for i in range(self.n_cities):
            for j in range(i + 1, self.n_cities):
                dist = np.sqrt(
                    (self.cities[i][0] - self.cities[j][0]) ** 2 +
                    (self.cities[i][1] - self.cities[j][1]) ** 2
                )
                matrix[i][j] = dist
                matrix[j][i] = dist
        return matrix

    def create_individual(self) -> List[int]:
        """创建随机路径"""
        route = list(range(self.n_cities))
        random.shuffle(route)
        return route

    def fitness(self, chromosome: List[int]) -> float:
        """计算适应度（路径长度的倒数）"""
        distance = self.calculate_distance(chromosome)
        return 1.0 / distance

    def calculate_distance(self, route: List[int]) -> float:
        """计算路径总长度"""
        total = 0
        for i in range(len(route)):
            from_city = route[i]
            to_city = route[(i + 1) % len(route)]
            total += self.distance_matrix[from_city][to_city]
        return total
```

## 可视化实现

```python
def plot_evolution(history: Dict, title: str = "Evolution Progress"):
    """绘制进化过程"""
    plt.figure(figsize=(10, 6))
    plt.plot(history['best_fitness'], label='Best Fitness')
    plt.plot(history['average_fitness'], label='Average Fitness')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_tsp_route(cities: List[Tuple], route: List[int], title: str = "TSP Route"):
    """绘制 TSP 路径"""
    plt.figure(figsize=(10, 10))

    # 绘制城市
    for i, (x, y) in enumerate(cities):
        plt.scatter(x, y, c='red', s=100)
        plt.annotate(f'{i}', (x, y), textcoords="offset points", xytext=(0,10), ha='center')

    # 绘制路径
    route_coords = [cities[i] for i in route] + [cities[route[0]]]
    xs = [c[0] for c in route_coords]
    ys = [c[1] for c in route_coords]
    plt.plot(xs, ys, 'b-', linewidth=2)

    plt.title(title)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.grid(True)
    plt.show()
```

## 关键实现要点

### 1. 编码设计
- 根据问题类型选择合适的编码
- TSP 使用排列编码，确保每个城市只访问一次

### 2. 算子选择
- 连续优化问题：单点/两点交叉 + 高斯变异
- 组合优化问题：顺序交叉 + 交换/逆序变异

### 3. 参数调优
- 种群大小：50-200
- 交叉率：0.6-0.9
- 变异率：0.01-0.1
- 锦标赛大小：2-5

### 4. 性能优化
- 使用 NumPy 进行向量化计算
- 避免不必要的深拷贝
- 实现适应度缓存
