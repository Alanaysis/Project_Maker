# 04 - 测试策略

## 1. 测试框架

使用 **pytest** 作为测试框架，支持：
- 简洁的断言语法
- 参数化测试
- 测试夹具
- 详细的错误报告

## 2. 测试结构

```
tests/
├── __init__.py
├── test_particle.py      # 粒子类测试
├── test_swarm.py         # 粒子群测试
└── test_functions.py     # 测试函数测试
```

## 3. 粒子类测试

### 3.1 初始化测试

```python
def test_initialization(self):
    """测试粒子初始化"""
    particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)
    assert particle.dimensions == 2
    assert len(particle.position) == 2
    assert len(particle.velocity) == 2
```

**验证点**：
- 维度正确
- 位置和速度长度正确
- 个体最佳初始化正确

### 3.2 边界测试

```python
def test_initialization_bounds(self):
    """测试粒子初始化位置在边界内"""
    for _ in range(100):
        particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)
        assert np.all(particle.position >= -10.0)
        assert np.all(particle.position <= 10.0)
```

**验证点**：
- 位置在边界内
- 多次采样都满足

### 3.3 评估测试

```python
def test_evaluate_sphere(self):
    """测试球面函数评估"""
    particle.position = np.array([3.0, 4.0])
    fitness = particle.evaluate(lambda x: np.sum(x**2))
    assert fitness == pytest.approx(25.0)
```

**验证点**：
- 适应度计算正确
- 个体最佳更新正确

### 3.4 速度更新测试

```python
def test_update_velocity(self):
    """测试速度更新"""
    old_velocity = particle.velocity.copy()
    particle.update_velocity(global_best=global_best, w=0.5, c1=1.0, c2=1.0)
    assert not np.array_equal(particle.velocity, old_velocity)
```

**验证点**：
- 速度确实更新了
- 更新后的速度合理

### 3.5 位置更新测试

```python
def test_update_position_with_bounds(self):
    """测试带边界约束的位置更新"""
    particle.position = np.array([95.0, -95.0])
    particle.velocity = np.array([10.0, -10.0])
    particle.update_position(bounds=(-100.0, 100.0))
    assert particle.position[0] == pytest.approx(100.0)
```

**验证点**：
- 位置正确更新
- 边界约束生效

## 4. 粒子群测试

### 4.1 配置测试

```python
def test_default_config(self):
    """测试默认配置"""
    config = PSOConfig()
    assert config.n_particles == 30
    assert config.dimensions == 2
```

**验证点**：
- 默认值正确
- 自定义值正确

### 4.2 优化测试

```python
def test_optimize_sphere(self):
    """测试优化球面函数"""
    config = PSOConfig(n_particles=20, dimensions=2, random_seed=42)
    swarm = Swarm(config)
    result = swarm.optimize(sphere)
    assert result.best_fitness < 1.0
```

**验证点**：
- 优化能运行
- 结果质量可接受
- 收敛历史正确

### 4.3 可复现性测试

```python
def test_optimize_reproducibility(self):
    """测试优化结果可复现"""
    config = PSOConfig(random_seed=42)

    swarm1 = Swarm(config)
    result1 = swarm1.optimize(sphere)

    swarm2 = Swarm(config)
    result2 = swarm2.optimize(sphere)

    np.testing.assert_array_almost_equal(result1.best_position, result2.best_position)
```

**验证点**：
- 相同种子产生相同结果
- 位置和适应度都一致

### 4.4 收敛历史测试

```python
def test_convergence_history(self):
    """测试收敛历史记录"""
    result = swarm.optimize(sphere)
    assert len(result.convergence_history) <= config.max_iterations

    # 收敛历史应该单调递减
    for i in range(1, len(result.convergence_history)):
        assert result.convergence_history[i] <= result.convergence_history[i-1]
```

**验证点**：
- 历史长度正确
- 单调递减

### 4.5 惯性权重策略测试

```python
def test_linear_decay_strategy(self):
    """测试线性递减惯性权重策略"""
    w_first = swarm._get_inertia_weight(0)
    w_middle = swarm._get_inertia_weight(25)
    w_last = swarm._get_inertia_weight(49)

    assert w_first > w_middle > w_last
```

**验证点**：
- 权重递减
- 边界值正确

### 4.6 回调测试

```python
def test_callback(self):
    """测试回调函数"""
    callback_data = []
    def my_callback(iteration, fitness, position):
        callback_data.append((iteration, fitness))

    swarm.optimize(sphere, callback=my_callback)
    assert len(callback_data) > 0
```

**验证点**：
- 回调被调用
- 参数正确

### 4.7 轨迹追踪测试

```python
def test_track_trajectories(self):
    """测试轨迹追踪"""
    config = PSOConfig(track_trajectories=True)
    result = swarm.optimize(sphere)
    assert result.particle_trajectories is not None
    assert len(result.particle_trajectories) == 5
```

**验证点**：
- 轨迹被记录
- 长度正确

## 5. 测试函数测试

### 5.1 最优值测试

```python
def test_optimal(self):
    """测试最优解"""
    x = np.zeros(5)
    assert sphere(x) == pytest.approx(0.0)
```

**验证点**：
- 最优位置的函数值为 0

### 5.2 已知值测试

```python
def test_known_values(self):
    """测试已知值"""
    assert sphere(np.array([3.0, 4.0])) == pytest.approx(25.0)
```

**验证点**：
- 特定点的函数值正确

### 5.3 对称性测试

```python
def test_symmetry(self):
    """测试对称性"""
    x = np.array([3.0, -4.0])
    assert sphere(x) == pytest.approx(25.0)
```

**验证点**：
- 函数的对称性质

### 5.4 注册表测试

```python
def test_registry_complete(self):
    """测试注册表完整性"""
    expected = ["sphere", "rosenbrock", "rastrigin", "ackley", "griewank"]
    for name in expected:
        assert name in BENCHMARK_FUNCTIONS
```

**验证点**：
- 所有函数都注册了
- 结构正确

## 6. 测试运行

### 6.1 运行所有测试

```bash
pytest tests/ -v
```

### 6.2 运行特定测试

```bash
pytest tests/test_particle.py -v
pytest tests/test_swarm.py -v
pytest tests/test_functions.py -v
```

### 6.3 运行并显示覆盖率

```bash
pytest tests/ -v --tb=short
```

## 7. 测试覆盖

### 7.1 已覆盖的功能

- [x] 粒子初始化
- [x] 粒子评估
- [x] 速度更新
- [x] 位置更新
- [x] 边界约束
- [x] 粒子群初始化
- [x] 优化主循环
- [x] 惯性权重策略
- [x] 收敛检测
- [x] 提前停止
- [x] 回调机制
- [x] 轨迹追踪
- [x] 所有测试函数

### 7.2 测试质量指标

- 单元测试覆盖所有公共方法
- 边界条件测试
- 异常情况测试
- 可复现性测试

## 8. 持续集成

建议在 CI/CD 流程中：
1. 运行所有测试
2. 检查代码覆盖率
3. 验证不同 Python 版本兼容性
