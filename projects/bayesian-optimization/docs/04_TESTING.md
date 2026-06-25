# 贝叶斯优化 - 测试文档

## 1. 测试策略

### 1.1 测试层次

| 层次 | 目的 | 覆盖率目标 |
|------|------|-----------|
| 单元测试 | 验证各模块功能正确性 | 90%+ |
| 集成测试 | 验证模块间协作 | 80%+ |
| 系统测试 | 验证端到端功能 | 100% |
| 性能测试 | 验证性能指标 | 关键路径 |

### 1.2 测试原则

1. **独立性**: 每个测试用例独立运行
2. **可重复性**: 使用固定随机种子
3. **快速性**: 单元测试 < 1 秒
4. **全面性**: 覆盖正常和异常情况

## 2. 单元测试

### 2.1 核函数测试

#### 测试文件: `tests/test_gaussian_process.py`

| 测试ID | 测试内容 | 预期结果 |
|--------|---------|---------|
| UT-K01 | RBF 核对称性 | K == K^T |
| UT-K02 | RBF 核正定性 | 对角元素 > 0 |
| UT-K03 | RBF 核形状 | (n1, n2) |
| UT-K04 | Matérn 核对称性 | K == K^T |
| UT-K05 | 白噪声核 | 对角矩阵 |
| UT-K06 | 核参数设置 | 参数正确更新 |

#### 测试用例示例

```python
def test_rbf_kernel():
    """测试 RBF 核"""
    kernel = RBF(length_scale=1.0, signal_variance=1.0)
    X = np.random.randn(10, 2)
    K = kernel(X, X)

    # 对称性
    assert np.allclose(K, K.T)

    # 形状
    assert K.shape == (10, 10)

    # 正定性
    assert np.all(np.diag(K) > 0)
```

### 2.2 高斯过程测试

| 测试ID | 测试内容 | 预期结果 |
|--------|---------|---------|
| UT-GP01 | 初始化 | 默认参数正确 |
| UT-GP02 | 拟合 | 缓存正确设置 |
| UT-GP03 | 预测形状 | (n_test,) |
| UT-GP04 | 预测方差非负 | std >= 0 |
| UT-GP05 | 未拟合预测 | 抛出 RuntimeError |
| UT-GP06 | 采样形状 | (n_test, n_samples) |
| UT-GP07 | 边际似然 | 有限值 |
| UT-GP08 | 超参数优化 | 边际似然增加 |

#### 测试用例示例

```python
def test_predict_shape():
    """测试预测形状"""
    gp = GaussianProcess()
    X_train = np.random.randn(20, 2)
    y_train = np.random.randn(20)
    X_test = np.random.randn(10, 2)

    gp.fit(X_train, y_train)
    y_mean, y_std = gp.predict(X_test, return_std=True)

    assert y_mean.shape == (10,)
    assert y_std.shape == (10,)

def test_predict_variance_non_negative():
    """测试预测方差非负"""
    gp = GaussianProcess()
    X_train = np.random.randn(20, 2)
    y_train = np.random.randn(20)
    X_test = np.random.randn(10, 2)

    gp.fit(X_train, y_train)
    _, y_std = gp.predict(X_test, return_std=True)

    assert np.all(y_std >= 0)
```

### 2.3 采集函数测试

| 测试ID | 测试内容 | 预期结果 |
|--------|---------|---------|
| UT-AC01 | EI 形状 | (n_points,) |
| UT-AC02 | EI 非负 | >= 0 |
| UT-AC03 | UCB 形状 | (n_points,) |
| UT-AC04 | PI 形状 | (n_points,) |
| UT-AC05 | PI 范围 | [0, 1] |
| UT-AC06 | TS 形状 | (n_points,) |
| UT-AC07 | 工厂函数 | 正确创建 |

#### 测试用例示例

```python
def test_ei_shape():
    """测试 EI 形状"""
    gp = GaussianProcess()
    X_train = np.array([[0.0], [1.0], [2.0]])
    y_train = np.array([0.0, 1.0, 0.5])
    gp.fit(X_train, y_train)

    ei = ExpectedImprovement()
    X_test = np.linspace(-1, 3, 10).reshape(-1, 1)
    values = ei(X_test, gp, y_best=1.0)

    assert values.shape == (10,)

def test_pi_range():
    """测试 PI 范围"""
    pi = ProbabilityOfImprovement()
    X_test = np.linspace(-1, 3, 10).reshape(-1, 1)
    values = pi(X_test, gp, y_best=1.0)

    assert np.all(values >= 0)
    assert np.all(values <= 1)
```

### 2.4 优化器测试

| 测试ID | 测试内容 | 预期结果 |
|--------|---------|---------|
| UT-OP01 | 初始化 | 参数正确 |
| UT-OP02 | 初始采样 | 范围正确 |
| UT-OP03 | 1D 优化 | 接近最优 |
| UT-OP04 | 2D 优化 | 接近最优 |
| UT-OP05 | 最小化 | 正确处理 |
| UT-OP06 | 收敛数据 | 结构正确 |
| UT-OP07 | 不同核函数 | 均能工作 |
| UT-OP08 | 自定义采集函数 | 正确使用 |

#### 测试用例示例

```python
def test_optimize_1d():
    """测试 1D 优化"""
    def objective(x):
        return -x[0]**2

    optimizer = BayesianOptimizer(
        objective_function=objective,
        bounds=[(-5, 5)],
        n_initial=5,
        maximize=True,
        random_state=42
    )

    result = optimizer.optimize(n_iterations=10, verbose=False)

    assert 'best_x' in result
    assert 'best_y' in result
    assert result['best_y'] < 0.1  # 接近最优值 0
```

## 3. 集成测试

### 3.1 测试函数

| 函数名 | 维度 | 最优值 | 特点 |
|--------|------|--------|------|
| Branin | 2D | 0.397887 | 多峰 |
| Rastrigin | nD | 0 | 多峰 |
| Rosenbrock | nD | 0 | 单峰但非凸 |
| Sphere | nD | 0 | 凸函数 |

### 3.2 集成测试用例

| 测试ID | 测试内容 | 通过标准 |
|--------|---------|---------|
| IT-01 | Branin 函数优化 | 最优值 < 1.0 |
| IT-02 | Rastrigin 函数优化 | 最优值 < 5.0 |
| IT-03 | 不同采集函数比较 | 均能收敛 |
| IT-04 | 不同核函数比较 | 均能工作 |
| IT-05 | 最大化/最小化 | 结果一致 |

### 3.3 集成测试示例

```python
def test_branin_optimization():
    """测试 Branin 函数优化"""
    def branin(x):
        x1, x2 = x[0], x[1]
        a = 1.0
        b = 5.1 / (4 * np.pi**2)
        c = 5.0 / np.pi
        d = 6.0
        e = 10.0
        f = 1.0 / (8 * np.pi)
        return a * (x2 - b * x1**2 + c * x1 - d)**2 + e * (1 - f) * np.cos(x1) + e

    optimizer = BayesianOptimizer(
        objective_function=branin,
        bounds=[(-5, 10), (0, 15)],
        n_initial=10,
        maximize=False,
        random_state=42
    )

    result = optimizer.optimize(n_iterations=30, verbose=False)

    assert result['best_y'] < 1.0
```

## 4. 性能测试

### 4.1 测试指标

| 测试ID | 测试内容 | 性能指标 |
|--------|---------|---------|
| PT-01 | 核矩阵计算 | < 1秒（n=1000） |
| PT-02 | GP 预测 | < 0.1秒（n=100） |
| PT-03 | 采集函数计算 | < 0.01秒（n=100） |
| PT-04 | 优化循环 | < 1分钟（n=100） |

### 4.2 性能测试示例

```python
import time

def test_kernel_performance():
    """测试核函数性能"""
    kernel = RBF()
    X = np.random.randn(1000, 2)

    start = time.time()
    K = kernel(X, X)
    elapsed = time.time() - start

    assert elapsed < 1.0  # < 1秒
    assert K.shape == (1000, 1000)

def test_optimization_performance():
    """测试优化性能"""
    def objective(x):
        return -np.sum(x**2)

    optimizer = BayesianOptimizer(
        objective_function=objective,
        bounds=[(-5, 5)] * 5,
        n_initial=10,
        random_state=42
    )

    start = time.time()
    result = optimizer.optimize(n_iterations=20, verbose=False)
    elapsed = time.time() - start

    assert elapsed < 60  # < 1分钟
```

## 5. 边界测试

### 5.1 边界情况

| 测试ID | 边界情况 | 预期行为 |
|--------|---------|---------|
| BT-01 | 单个训练点 | 正常预测 |
| BT-02 | 训练点重合 | 不崩溃 |
| BT-03 | 测试点 = 训练点 | 方差 ≈ 0 |
| BT-04 | 极端参数值 | 不崩溃 |
| BT-05 | 空输入 | 抛出异常 |
| BT-06 | 维度不匹配 | 抛出异常 |

### 5.2 边界测试示例

```python
def test_single_training_point():
    """测试单个训练点"""
    gp = GaussianProcess()
    X_train = np.array([[1.0]])
    y_train = np.array([1.0])
    X_test = np.array([[0.5], [1.5]])

    gp.fit(X_train, y_train)
    y_mean, y_std = gp.predict(X_test, return_std=True)

    assert y_mean.shape == (2,)
    assert y_std.shape == (2,)

def test_dimension_mismatch():
    """测试维度不匹配"""
    gp = GaussianProcess()
    X_train = np.array([[1.0, 2.0]])
    y_train = np.array([1.0, 2.0])  # 长度不匹配

    with pytest.raises(ValueError):
        gp.fit(X_train, y_train)
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_gaussian_process.py

# 运行特定测试类
pytest tests/test_gaussian_process.py::TestGaussianProcess

# 运行特定测试方法
pytest tests/test_gaussian_process.py::TestGaussianProcess::test_predict_shape

# 显示详细输出
pytest -v tests/

# 显示覆盖率
pytest --cov=src tests/
```

### 6.2 测试配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 7. 测试报告

### 7.1 覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 查看报告
open htmlcov/index.html
```

### 7.2 测试结果示例

```
tests/test_gaussian_process.py::TestGaussianProcess::test_initialization PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_fit PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_predict_shape PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_predict_variance PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_sample_shape PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_rbf_kernel PASSED
tests/test_gaussian_process.py::TestGaussianProcess::test_matern_kernel PASSED

----------- coverage: platform linux, python 3.8 -----------
Name                          Stmts   Miss  Cover
---------------------------------------------------
src/__init__.py                   5      0   100%
src/kernels.py                   85     10    88%
src/gaussian_process.py         120     15    88%
src/acquisition.py               95      8    92%
src/optimizer.py                 150     20    87%
---------------------------------------------------
TOTAL                           455     53    88%
```

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=src tests/
```

## 9. 测试维护

### 9.1 测试更新策略

- 新功能必须附带测试
- Bug 修复必须添加回归测试
- 定期审查测试覆盖率

### 9.2 测试数据管理

- 使用固定随机种子
- 测试数据与代码分离
- 避免硬编码测试数据

## 10. 参考资料

1. pytest 官方文档: https://docs.pytest.org/
2. pytest-cov 文档: https://pytest-cov.readthedocs.io/
3. Python 测试最佳实践: https://docs.python.org/3/library/unittest.html
