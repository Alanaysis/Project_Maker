# 04 - 测试策略

## 测试目标

确保遗传算法框架的正确性、稳定性和性能，覆盖核心功能、边界情况和集成测试。

## 测试层次

### 1. 单元测试
- 测试各个组件的独立功能
- 验证算法实现的正确性

### 2. 集成测试
- 测试组件间的协作
- 验证完整流程的正确性

### 3. 性能测试
- 测试算法效率
- 验证收敛性

## 测试用例设计

### Individual 测试

```python
class TestIndividual:
    """个体类测试"""

    def test_creation(self):
        """测试个体创建"""
        ind = Individual([1, 2, 3])
        assert ind.chromosome == [1, 2, 3]
        assert ind.fitness == 0.0

    def test_evaluate(self):
        """测试适应度评估"""
        ind = Individual([1, 2, 3])
        fitness_func = lambda x: sum(x)
        ind.evaluate(fitness_func)
        assert ind.fitness == 6.0

    def test_copy(self):
        """测试深拷贝"""
        ind1 = Individual([1, 2, 3])
        ind1.fitness = 10.0
        ind2 = ind1.copy()

        assert ind2.chromosome == [1, 2, 3]
        assert ind2.fitness == 10.0

        # 修改副本不影响原件
        ind2.chromosome[0] = 99
        assert ind1.chromosome[0] == 1
```

### Population 测试

```python
class TestPopulation:
    """种群类测试"""

    def test_initialization(self):
        """测试种群初始化"""
        pop = Population()
        pop.initialize(10, lambda: [random.randint(0, 1) for _ in range(5)])

        assert pop.size == 10
        assert len(pop.individuals) == 10
        for ind in pop.individuals:
            assert len(ind.chromosome) == 5

    def test_evaluate(self):
        """测试种群评估"""
        pop = Population()
        pop.initialize(5, lambda: [1, 2, 3])
        pop.evaluate(lambda x: sum(x))

        for ind in pop.individuals:
            assert ind.fitness == 6.0

    def test_get_best(self):
        """测试获取最优个体"""
        pop = Population()
        pop.individuals = [
            Individual([1, 2, 3]),
            Individual([4, 5, 6]),
            Individual([7, 8, 9])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 15

        best = pop.get_best()
        assert best.fitness == 20

    def test_get_statistics(self):
        """测试统计信息"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30

        stats = pop.get_statistics()
        assert stats['best'] == 30
        assert stats['worst'] == 10
        assert stats['average'] == 20
```

### 选择算子测试

```python
class TestSelectionOperators:
    """选择算子测试"""

    def test_roulette_wheel_selection(self):
        """测试轮盘赌选择"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30

        selector = RouletteWheelSelection()
        selected = selector.select(pop, 3)

        assert len(selected) == 3
        # 适应度高的个体应该被选中更多次
        fitnesses = [ind.fitness for ind in selected]
        assert max(fitnesses) >= 20  # 至少选中一个高适应度个体

    def test_tournament_selection(self):
        """测试锦标赛选择"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30

        selector = TournamentSelection(tournament_size=2)
        selected = selector.select(pop, 2)

        assert len(selected) == 2
        # 锦标赛选择应该倾向于选择高适应度个体
        fitnesses = [ind.fitness for ind in selected]
        assert all(f >= 10 for f in fitnesses)

    def test_elitism_selection(self):
        """测试精英保留选择"""
        pop = Population()
        pop.individuals = [
            Individual([1]),
            Individual([2]),
            Individual([3]),
            Individual([4])
        ]
        pop.individuals[0].fitness = 10
        pop.individuals[1].fitness = 20
        pop.individuals[2].fitness = 30
        pop.individuals[3].fitness = 40

        selector = ElitismSelection()
        selected = selector.select(pop, 2)

        assert len(selected) == 2
        fitnesses = sorted([ind.fitness for ind in selected], reverse=True)
        assert fitnesses == [40, 30]  # 保留最优的两个
```

### 交叉算子测试

```python
class TestCrossoverOperators:
    """交叉算子测试"""

    def test_single_point_crossover(self):
        """测试单点交叉"""
        parent1 = Individual([1, 2, 3, 4, 5])
        parent2 = Individual([6, 7, 8, 9, 10])

        crossover = SinglePointCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该是父代的组合
        assert sorted(child1.chromosome + child2.chromosome) == list(range(1, 11))

    def test_crossover_rate(self):
        """测试交叉率"""
        parent1 = Individual([1, 2, 3])
        parent2 = Individual([4, 5, 6])

        # 交叉率为 0 时，子代应该是父代的副本
        crossover = SinglePointCrossover(crossover_rate=0.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        assert child1.chromosome == [1, 2, 3]
        assert child2.chromosome == [4, 5, 6]

    def test_order_crossover(self):
        """测试顺序交叉 (OX)"""
        parent1 = Individual([1, 2, 3, 4, 5, 6])
        parent2 = Individual([4, 5, 6, 1, 2, 3])

        crossover = OrderCrossover(crossover_rate=1.0)
        child1, child2 = crossover.crossover(parent1, parent2)

        # 子代应该包含所有城市
        assert sorted(child1.chromosome) == list(range(1, 7))
        assert sorted(child2.chromosome) == list(range(1, 7))
```

### 变异算子测试

```python
class TestMutationOperators:
    """变异算子测试"""

    def test_bit_flip_mutation(self):
        """测试位翻转变异"""
        ind = Individual([0, 0, 0, 0, 0])

        # 变异率为 1.0 时，所有位都应该翻转
        mutator = BitFlipMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        assert mutated.chromosome == [1, 1, 1, 1, 1]
        # 原个体应该不变
        assert ind.chromosome == [0, 0, 0, 0, 0]

    def test_swap_mutation(self):
        """测试交换变异"""
        ind = Individual([1, 2, 3, 4, 5])

        # 变异率为 1.0 时，应该发生交换
        mutator = SwapMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        # 交换后应该仍然是排列
        assert sorted(mutated.chromosome) == [1, 2, 3, 4, 5]
        # 但顺序可能改变
        assert mutated.chromosome != [1, 2, 3, 4, 5]  # 很可能不同

    def test_inversion_mutation(self):
        """测试逆序变异"""
        ind = Individual([1, 2, 3, 4, 5])

        mutator = InversionMutation(mutation_rate=1.0)
        mutated = mutator.mutate(ind)

        # 逆序后应该仍然是排列
        assert sorted(mutated.chromosome) == [1, 2, 3, 4, 5]

    def test_mutation_preserves_validity(self):
        """测试变异保持解的有效性"""
        ind = Individual([0, 1, 2, 3, 4])

        mutator = SwapMutation(mutation_rate=0.5)
        mutated = mutator.mutate(ind)

        # 变异后应该仍然是有效排列
        assert sorted(mutated.chromosome) == [0, 1, 2, 3, 4]
```

### TSP 问题测试

```python
class TestTSPProblem:
    """TSP 问题测试"""

    def test_distance_matrix(self):
        """测试距离矩阵计算"""
        cities = [(0, 0), (1, 0), (0, 1)]
        problem = TSPProblem(cities)

        # 验证距离计算
        assert abs(problem.distance_matrix[0][1] - 1.0) < 1e-6
        assert abs(problem.distance_matrix[0][2] - 1.0) < 1e-6
        assert abs(problem.distance_matrix[1][2] - np.sqrt(2)) < 1e-6

    def test_fitness_calculation(self):
        """测试适应度计算"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        # 正方形路径
        route = [0, 1, 2, 3]
        distance = problem.calculate_distance(route)
        fitness = problem.fitness(route)

        assert abs(distance - 4.0) < 1e-6
        assert abs(fitness - 0.25) < 1e-6

    def test_create_individual(self):
        """测试个体创建"""
        cities = [(0, 0), (1, 0), (2, 0)]
        problem = TSPProblem(cities)

        individual = problem.create_individual()

        assert len(individual) == 3
        assert sorted(individual) == [0, 1, 2]  # 应该是排列

    def test_optimal_solution(self):
        """测试最优解"""
        # 简单的正方形，最优路径应该是 4
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        optimal_route = [0, 1, 2, 3]
        distance = problem.calculate_distance(optimal_route)

        assert abs(distance - 4.0) < 1e-6
```

### 集成测试

```python
class TestGAIntegration:
    """遗传算法集成测试"""

    def test_basic_optimization(self):
        """测试基础优化"""
        # 简单的函数优化
        def fitness_func(chromosome):
            return sum(x ** 2 for x in chromosome)

        class SimpleProblem(Problem):
            def create_individual(self):
                return [random.uniform(-10, 10) for _ in range(3)]

            def fitness(self, chromosome):
                return 1.0 / (1.0 + fitness_func(chromosome))

            def display(self, individual):
                pass

        problem = SimpleProblem()
        engine = GAEngine(problem, population_size=50)

        best = engine.run(generations=50, verbose=False)

        # 应该找到接近最优解的解
        assert best.fitness > 0.5  # 适应度应该足够高

    def test_tsp_convergence(self):
        """测试 TSP 收敛"""
        # 小规模 TSP 问题
        cities = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)]
        problem = TSPProblem(cities)

        engine = GAEngine(
            problem,
            population_size=50,
            selection=TournamentSelection(tournament_size=3),
            crossover=OrderCrossover(crossover_rate=0.8),
            mutation=SwapMutation(mutation_rate=0.2)
        )

        best = engine.run(generations=100, verbose=False)

        # 应该找到合理长度的路径
        distance = problem.calculate_distance(best.chromosome)
        assert distance < 5.0  # 路径长度应该小于某个阈值

    def test_convergence_history(self):
        """测试收敛历史"""
        cities = [(0, 0), (1, 0), (1, 1), (0, 1)]
        problem = TSPProblem(cities)

        engine = GAEngine(problem, population_size=30)
        engine.run(generations=50, verbose=False)

        # 应该有历史记录
        assert len(engine.history['best_fitness']) == 50
        assert len(engine.history['average_fitness']) == 50

        # 最优适应度应该有提升
        assert engine.history['best_fitness'][-1] >= engine.history['best_fitness'][0]
```

## 测试运行

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
pytest tests/test_operators.py -v
pytest tests/test_tsp.py -v
```

### 生成覆盖率报告
```bash
pytest tests/ --cov=src --cov-report=html
```

## 测试覆盖目标

| 模块 | 目标覆盖率 |
|------|-----------|
| Individual | 100% |
| Population | 100% |
| Selection Operators | 95% |
| Crossover Operators | 95% |
| Mutation Operators | 95% |
| TSP Problem | 100% |
| GA Engine | 90% |

## 边界情况测试

1. **空种群**: 测试种群大小为 0 的情况
2. **单个个体**: 测试种群大小为 1 的情况
3. **极高变异率**: 测试变异率为 1.0 的情况
4. **零交叉率**: 测试交叉率为 0.0 的情况
5. **单城市 TSP**: 测试只有一个城市的情况
6. **相同城市**: 测试所有城市坐标相同的情况

## 性能测试

```python
def test_performance():
    """测试算法性能"""
    import time

    cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(20)]
    problem = TSPProblem(cities)

    engine = GAEngine(problem, population_size=100)

    start = time.time()
    engine.run(generations=200, verbose=False)
    elapsed = time.time() - start

    # 应该在合理时间内完成
    assert elapsed < 10.0  # 10 秒内完成
```

## 持续集成

### GitHub Actions 配置
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
        python-version: '3.8'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest tests/ --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```
