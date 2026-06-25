# 凸优化测试文档

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**: 测试单个函数/类的正确性
2. **集成测试**: 测试模块间的交互
3. **系统测试**: 测试完整优化流程
4. **性能测试**: 测试算法效率和可扩展性

### 1.2 测试覆盖

- 凸函数：函数值、梯度、海森矩阵、凸性判断
- 优化算法：收敛性、精度、稳定性
- 约束优化：KKT 条件、对偶间隙
- 实际应用：最小二乘、SVM、投资组合

## 2. 单元测试

### 2.1 凸函数测试

**文件**: `tests/test_functions.py`

```python
class TestQuadraticFunction:
    def test_function_value(self):
        """测试函数值计算"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x = np.array([1, 1])
        assert abs(f(x) - 2.0) < 1e-10

    def test_gradient(self):
        """测试梯度计算"""
        A = np.array([[2, 0], [0, 2]])
        b = np.array([1, 1])
        f = QuadraticFunction(A, b)
        x = np.array([1, 1])
        grad = f.gradient(x)
        expected = np.array([3, 3])
        np.testing.assert_allclose(grad, expected)

    def test_convexity(self):
        """测试凸性判断"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x = np.array([1, 0])
        y = np.array([0, 1])
        assert f.is_convex_by_definition(x, y)

    def test_strong_convexity(self):
        """测试强凸性"""
        A = np.array([[4, 0], [0, 4]])
        f = QuadraticFunction(A)
        x = np.array([0, 0])
        assert f.is_strongly_convex(x, mu=2.0)
        assert not f.is_strongly_convex(x, mu=5.0)
```

### 2.2 优化算法测试

**文件**: `tests/test_optimizers.py`

```python
class TestGradientDescent:
    def test_quadratic_convergence(self):
        """测试二次函数收敛"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])
        
        optimizer = GradientDescent(learning_rate=0.1, max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)
        
        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-4)

class TestNewtonMethod:
    def test_quadratic_convergence(self):
        """测试二次函数收敛（应一步收敛）"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])
        
        optimizer = NewtonMethod(line_search=False, max_iter=10)
        result = optimizer.optimize(f, f.gradient, x0, f.hessian)
        
        assert result.success
        np.testing.assert_allclose(result.x, [0, 0], atol=1e-10)
        assert result.nit <= 1  # 二次函数应该一步收敛
```

### 2.3 约束优化测试

**文件**: `tests/test_constrained.py`

```python
class TestKKT:
    def test_simple_qp(self):
        """测试简单二次规划"""
        # min 0.5*x^2 + 0.5*y^2
        # s.t. x + y = 1
        # 最优解: x = y = 0.5, nu = -1
        
        grad_obj = lambda x: x
        eq_constraints = [lambda x: x[0] + x[1] - 1]
        grad_eq = [lambda x: np.array([1.0, 1.0])]
        
        checker = KKTChecker(
            grad_obj=grad_obj,
            grad_eq=grad_eq,
            eq_constraints=eq_constraints,
        )
        
        x = np.array([0.5, 0.5])
        nu = np.array([-1.0])
        
        result = checker.check(x, np.array([]), nu)
        assert result.stationarity
        assert result.primal_feasibility
```

### 2.4 应用测试

**文件**: `tests/test_applications.py`

```python
class TestLeastSquares:
    def test_analytical_solution(self):
        """测试解析解"""
        A = np.array([[1, 0], [0, 1], [1, 1]])
        b = np.array([1, 2, 3])
        ls = LeastSquares(A, b)
        
        x = ls.solve_analytical()
        residual = ls.residual(x)
        assert np.linalg.norm(residual) < 1e-10

class TestSVM:
    def test_linear_separable(self):
        """测试线性可分数据"""
        np.random.seed(42)
        X1 = np.random.randn(20, 2) + np.array([2, 2])
        X2 = np.random.randn(20, 2) + np.array([-2, -2])
        X = np.vstack([X1, X2])
        y = np.array([1] * 20 + [-1] * 20)
        
        svm = SVM(C=1.0, max_iter=1000)
        result = svm.fit(X, y)
        
        predictions = svm.predict(X, result)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.9
```

## 3. 集成测试

### 3.1 优化器对比测试

```python
class TestOptimizerComparison:
    def test_convergence_comparison(self):
        """比较不同优化器的收敛性"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])
        
        optimizers = {
            "GD": GradientDescent(learning_rate=0.1, max_iter=1000),
            "Newton": NewtonMethod(max_iter=10),
            "BFGS": BFGS(max_iter=100),
        }
        
        results = {}
        for name, opt in optimizers.items():
            if name == "Newton":
                results[name] = opt.optimize(f, f.gradient, x0, f.hessian)
            else:
                results[name] = opt.optimize(f, f.gradient, x0)
        
        # 所有优化器都应该收敛
        for name, result in results.items():
            assert result.success
            np.testing.assert_allclose(result.x, [0, 0], atol=1e-3)
```

### 3.2 端到端测试

```python
class TestEndToEnd:
    def test_least_squares_pipeline(self):
        """测试最小二乘完整流程"""
        # 生成数据
        np.random.seed(42)
        A = np.random.randn(20, 5)
        x_true = np.array([1, 2, 3, 4, 5])
        b = A @ x_true + 0.1 * np.random.randn(20)
        
        # 求解
        ls = LeastSquares(A, b)
        x = ls.solve_analytical()
        
        # 验证
        assert np.linalg.norm(x - x_true) < 0.5
        assert np.linalg.norm(ls.residual(x)) < 0.5
```

## 4. 性能测试

### 4.1 收敛速度测试

```python
class TestConvergenceRate:
    def test_gradient_descent_rate(self):
        """测试梯度下降收敛速度"""
        A = np.array([[10, 0], [0, 1]])  # 条件数 10
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])
        
        optimizer = GradientDescent(learning_rate=0.01, max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)
        
        # 检查收敛速度
        grad_norms = result.grad_norms
        # 应该线性收敛
        for i in range(1, len(grad_norms) - 1):
            ratio = grad_norms[i] / grad_norms[i-1]
            assert ratio < 1.0  # 收敛

    def test_newton_rate(self):
        """测试牛顿法收敛速度"""
        A = np.array([[2, 0], [0, 2]])
        f = QuadraticFunction(A)
        x0 = np.array([10.0, 10.0])
        
        optimizer = NewtonMethod(max_iter=10)
        result = optimizer.optimize(f, f.gradient, x0, f.hessian)
        
        # 二次函数应该一步收敛
        assert result.nit <= 1
```

### 4.2 可扩展性测试

```python
class TestScalability:
    def test_large_scale(self):
        """测试大规模问题"""
        n = 1000
        A = np.eye(n)
        f = QuadraticFunction(A)
        x0 = np.ones(n) * 10
        
        optimizer = LBFGS(m=20, max_iter=500)
        result = optimizer.optimize(f, f.gradient, x0)
        
        assert result.success
        assert np.linalg.norm(result.x) < 1e-3
```

## 5. 边界测试

### 5.1 数值稳定性测试

```python
class TestNumericalStability:
    def test_ill_conditioned(self):
        """测试病态问题"""
        A = np.array([[1e6, 0], [0, 1e-6]])
        f = QuadraticFunction(A)
        x0 = np.array([1.0, 1.0])
        
        # 应该能够处理病态问题
        optimizer = BFGS(max_iter=1000)
        result = optimizer.optimize(f, f.gradient, x0)
        
        assert result.success

    def test_near_singular(self):
        """测试近奇异矩阵"""
        A = np.array([[1, 1], [1, 1 + 1e-10]])
        f = QuadraticFunction(A)
        x0 = np.array([1.0, 1.0])
        
        # 应该能够处理近奇异问题
        optimizer = NewtonMethod(regularization=1e-6)
        result = optimizer.optimize(f, f.gradient, x0, f.hessian)
        
        assert result.success
```

### 5.2 边界条件测试

```python
class TestBoundaryConditions:
    def test_zero_gradient(self):
        """测试零梯度情况"""
        A = np.array([[0, 0], [0, 0]])
        f = QuadraticFunction(A)
        x0 = np.array([1.0, 1.0])
        
        optimizer = GradientDescent(max_iter=100)
        result = optimizer.optimize(f, f.gradient, x0)
        
        # 应该立即收敛
        assert result.nit == 0

    def test_constant_function(self):
        """测试常数函数"""
        f = lambda x: 1.0
        grad_f = lambda x: np.zeros_like(x)
        x0 = np.array([1.0, 1.0])
        
        optimizer = GradientDescent(max_iter=100)
        result = optimizer.optimize(f, grad_f, x0)
        
        # 应该立即收敛
        assert result.nit == 0
```

## 6. 测试工具

### 6.1 测试辅助函数

```python
def assert_convergence(result, x_expected, tol=1e-4):
    """断言优化收敛"""
    assert result.success, f"优化未收敛: {result.message}"
    np.testing.assert_allclose(result.x, x_expected, atol=tol)

def assert_kkt_satisfied(checker, x, lambda_ineq, nu_eq):
    """断言 KKT 条件满足"""
    result = checker.check(x, lambda_ineq, nu_eq)
    assert result.is_satisfied, f"KKT 条件不满足: {result.violation}"

def generate_random_qp(n, condition_number=10):
    """生成随机二次规划问题"""
    eigenvalues = np.logspace(0, np.log10(condition_number), n)
    A = np.diag(eigenvalues)
    return QuadraticFunction(A)
```

### 6.2 测试数据生成

```python
def generate_linear_separable_data(n_samples=100, n_features=2, margin=1.0):
    """生成线性可分数据"""
    np.random.seed(42)
    X1 = np.random.randn(n_samples // 2, n_features) + margin
    X2 = np.random.randn(n_samples // 2, n_features) - margin
    X = np.vstack([X1, X2])
    y = np.array([1] * (n_samples // 2) + [-1] * (n_samples // 2))
    return X, y

def generate_sparse_signal(n_samples=100, n_features=50, n_nonzero=5):
    """生成稀疏信号"""
    np.random.seed(42)
    A = np.random.randn(n_samples, n_features)
    x_true = np.zeros(n_features)
    x_true[:n_nonzero] = np.random.randn(n_nonzero)
    b = A @ x_true + 0.1 * np.random.randn(n_samples)
    return A, b, x_true
```

## 7. 测试运行

### 7.1 运行所有测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_functions.py

# 运行特定测试类
pytest tests/test_functions.py::TestQuadraticFunction

# 运行特定测试方法
pytest tests/test_functions.py::TestQuadraticFunction::test_function_value
```

### 7.2 测试覆盖率

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行覆盖率测试
pytest --cov=src tests/

# 生成 HTML 报告
pytest --cov=src --cov-report=html tests/
```

### 7.3 性能测试

```bash
# 运行性能测试
pytest tests/test_performance.py -v

# 生成性能报告
pytest tests/test_performance.py --benchmark-only
```

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
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
    - name: Run tests
      run: |
        pytest tests/ -v
```

### 8.2 测试报告

```bash
# 生成 JUnit XML 报告
pytest tests/ --junitxml=test-results.xml

# 生成 Allure 报告
pytest tests/ --alluredir=allure-results
```
