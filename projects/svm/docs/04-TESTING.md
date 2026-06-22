# 04 - 测试文档

## 1. 测试概述

### 1.1 测试目标

- 验证核函数的正确性
- 验证 SMO 算法的收敛性
- 验证 SVM 分类器的功能
- 确保代码质量

### 1.2 测试策略

- **单元测试**：测试每个函数和类的方法
- **集成测试**：测试完整流程
- **边界测试**：测试边界情况和异常处理

### 1.3 测试工具

- **pytest**：测试框架
- **numpy.testing**：数值比较工具

## 2. 核函数测试

### 2.1 线性核测试

```python
class TestLinearKernel:
    """线性核函数测试"""

    def test_basic_dot_product(self):
        """测试基本的点积计算"""
        kernel = linear_kernel()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
        assert kernel(x, y) == 32.0

    def test_orthogonal_vectors(self):
        """测试正交向量的核值为 0"""
        kernel = linear_kernel()
        x = np.array([1.0, 0.0])
        y = np.array([0.0, 1.0])
        assert kernel(x, y) == 0.0

    def test_same_vector(self):
        """测试向量与自身的核值等于模的平方"""
        kernel = linear_kernel()
        x = np.array([3.0, 4.0])
        # ||x||^2 = 9 + 16 = 25
        assert kernel(x, x) == 25.0

    def test_symmetry(self):
        """测试核函数的对称性: K(x,y) = K(y,x)"""
        kernel = linear_kernel()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        assert kernel(x, y) == kernel(y, x)

    def test_zero_vector(self):
        """测试零向量的核值为 0"""
        kernel = linear_kernel()
        x = np.array([0.0, 0.0])
        y = np.array([1.0, 2.0])
        assert kernel(x, y) == 0.0
```

**测试覆盖**：
- 基本点积计算
- 正交向量
- 自身点积
- 对称性
- 零向量

### 2.2 RBF 核测试

```python
class TestRBFKernel:
    """RBF 核函数测试"""

    def test_same_vector(self):
        """测试向量与自身的核值为 1"""
        kernel = rbf_kernel(gamma=1.0)
        x = np.array([1.0, 2.0, 3.0])
        assert kernel(x, x) == 1.0

    def test_symmetry(self):
        """测试核函数的对称性"""
        kernel = rbf_kernel(gamma=1.0)
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        assert kernel(x, y) == kernel(y, x)

    def test_range(self):
        """测试核函数值在 (0, 1] 范围内"""
        kernel = rbf_kernel(gamma=1.0)
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        value = kernel(x, y)
        assert 0 < value <= 1.0

    def test_gamma_effect(self):
        """测试 gamma 参数的影响"""
        x = np.array([0.0, 0.0])
        y = np.array([1.0, 1.0])

        kernel_small = rbf_kernel(gamma=0.1)
        kernel_large = rbf_kernel(gamma=10.0)

        # gamma 越大，核值越小
        assert kernel_small(x, y) > kernel_large(x, y)

    def test_invalid_gamma(self):
        """测试无效的 gamma 值"""
        with pytest.raises(ValueError):
            rbf_kernel(gamma=-1.0)
        with pytest.raises(ValueError):
            rbf_kernel(gamma=0.0)

    def test_far_points(self):
        """测试远距离点的核值接近 0"""
        kernel = rbf_kernel(gamma=1.0)
        x = np.array([0.0, 0.0])
        y = np.array([100.0, 100.0])
        assert kernel(x, y) < 1e-10
```

**测试覆盖**：
- 自身核值
- 对称性
- 值范围
- gamma 参数影响
- 无效参数
- 远距离点

### 2.3 多项式核测试

```python
class TestPolynomialKernel:
    """多项式核函数测试"""

    def test_degree_1(self):
        """测试 degree=1 时等价于线性核加偏置"""
        kernel = polynomial_kernel(degree=1, coef0=1.0)
        linear = linear_kernel()
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        assert kernel(x, y) == linear(x, y) + 1.0

    def test_symmetry(self):
        """测试核函数的对称性"""
        kernel = polynomial_kernel(degree=3, coef0=1.0)
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        assert kernel(x, y) == kernel(y, x)

    def test_degree_effect(self):
        """测试 degree 参数的影响"""
        x = np.array([2.0, 3.0])
        y = np.array([4.0, 5.0])

        kernel_d2 = polynomial_kernel(degree=2, coef0=1.0)
        kernel_d3 = polynomial_kernel(degree=3, coef0=1.0)

        assert kernel_d3(x, y) > kernel_d2(x, y)

    def test_invalid_degree(self):
        """测试无效的 degree 值"""
        with pytest.raises(ValueError):
            polynomial_kernel(degree=0)
        with pytest.raises(ValueError):
            polynomial_kernel(degree=-1)
```

### 2.4 核矩阵测试

```python
class TestKernelMatrix:
    """核矩阵预计算测试"""

    def test_shape(self):
        """测试核矩阵的形状"""
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)
        assert K.shape == (3, 3)

    def test_symmetry(self):
        """测试核矩阵的对称性"""
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)
        assert_array_almost_equal(K, K.T)

    def test_diagonal(self):
        """测试线性核矩阵的对角线元素"""
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)
        assert K[0, 0] == 5.0
        assert K[1, 1] == 25.0
```

## 3. SMO 算法测试

### 3.1 基本功能测试

```python
class TestSMO:
    """SMO 算法测试"""

    def test_simple_linear_separable(self):
        """测试简单线性可分数据"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=20)
        alpha, b = smo.optimize(K, y)

        # 检查 alpha 非负
        assert np.all(alpha >= -1e-7)

        # 检查 alpha 不超过 C
        assert np.all(alpha <= 1.0 + 1e-7)

        # 检查约束: sum(alpha_i * y_i) = 0
        assert abs(np.sum(alpha * y)) < 0.1
```

### 3.2 收敛性测试

```python
    def test_convergence(self):
        """测试算法收敛"""
        np.random.seed(42)
        X_pos = np.random.randn(20, 2) + 2
        X_neg = np.random.randn(20, 2) - 2
        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 20 + [-1] * 20)

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=50)
        alpha, b = smo.optimize(K, y)

        # 应该有一些非零的 alpha
        assert np.sum(alpha > 1e-5) > 0
```

### 3.3 KKT 条件测试

```python
    def test_kkt_conditions(self):
        """测试 KKT 条件是否满足"""
        X = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        y = np.array([1, 1, -1, -1])

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=20)
        alpha, b = smo.optimize(K, y)

        # 计算预测值
        predictions = np.sum(alpha * y * K, axis=1) + b

        # 验证 KKT 条件
        for i in range(len(y)):
            margin = y[i] * predictions[i]
            if alpha[i] < 1e-7:
                assert margin >= 1 - 0.5
            elif alpha[i] > 1.0 - 1e-7:
                assert margin <= 1 + 0.5
```

## 4. SVM 分类器测试

### 4.1 初始化测试

```python
class TestSVM:
    """SVM 分类器测试"""

    def test_initialization(self):
        """测试 SVM 初始化"""
        svm = SVM(kernel="linear", C=1.0)
        assert svm.kernel_type == "linear"
        assert svm.C == 1.0
```

### 4.2 训练和预测测试

```python
    def test_fit_predict_linear(self):
        """测试线性核的训练和预测"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_fit_predict_rbf(self):
        """测试 RBF 核的训练和预测"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="rbf", C=1.0, gamma=1.0, max_passes=50)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)
```

### 4.3 异常处理测试

```python
    def test_invalid_labels(self):
        """测试无效的标签"""
        X = np.array([[1, 1], [2, 2]])
        y = np.array([0, 1])

        svm = SVM(kernel="linear")
        with pytest.raises(ValueError):
            svm.fit(X, y)

    def test_predict_before_fit(self):
        """测试在训练前预测"""
        svm = SVM(kernel="linear")
        X = np.array([[1, 1]])
        with pytest.raises(RuntimeError):
            svm.predict(X)
```

### 4.4 支持向量测试

```python
    def test_support_vectors(self):
        """测试支持向量的提取"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        assert svm.get_n_support_vectors() > 0

        sv = svm.get_support_vectors()
        assert sv.shape[1] == X.shape[1]
```

### 4.5 决策函数测试

```python
    def test_decision_function(self):
        """测试决策函数"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        decision = svm.decision_function(X)
        assert decision[0] > 0
        assert decision[1] > 0
        assert decision[2] < 0
        assert decision[3] < 0
```

### 4.6 准确率测试

```python
    def test_score(self):
        """测试准确率计算"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy == 1.0
```

### 4.7 复杂数据测试

```python
    def test_xor_problem_rbf(self):
        """测试 XOR 问题"""
        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y = np.array([-1, 1, 1, -1])

        svm = SVM(kernel="rbf", C=10.0, gamma=1.0, max_passes=100)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_rbf_circle(self):
        """测试圆形分布的数据"""
        np.random.seed(42)
        r1 = np.random.uniform(0, 1, 50)
        theta1 = np.random.uniform(0, 2 * np.pi, 50)
        X_pos = np.column_stack([r1 * np.cos(theta1), r1 * np.sin(theta1)])

        r2 = np.random.uniform(2, 3, 50)
        theta2 = np.random.uniform(0, 2 * np.pi, 50)
        X_neg = np.column_stack([r2 * np.cos(theta2), r2 * np.sin(theta2)])

        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 50 + [-1] * 50)

        svm = SVM(kernel="rbf", C=10.0, gamma=1.0, max_passes=100)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy > 0.8
```

## 5. 集成测试

### 5.1 完整流程测试

```python
class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整的训练-预测流程"""
        X_train = np.array([[1, 1], [2, 2], [3, 3],
                            [-1, -1], [-2, -2], [-3, -3]])
        y_train = np.array([1, 1, 1, -1, -1, -1])

        X_test = np.array([[1.5, 1.5], [-1.5, -1.5]])
        y_test = np.array([1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X_train, y_train)

        predictions = svm.predict(X_test)
        assert_array_equal(predictions, y_test)

        accuracy = svm.score(X_test, y_test)
        assert accuracy == 1.0
```

### 5.2 不同核函数测试

```python
    def test_different_kernels(self):
        """测试不同的核函数"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        # 线性核
        svm_linear = SVM(kernel="linear", C=1.0, max_passes=50)
        svm_linear.fit(X, y)
        assert svm_linear.score(X, y) == 1.0

        # RBF 核
        svm_rbf = SVM(kernel="rbf", C=1.0, gamma=1.0, max_passes=50)
        svm_rbf.fit(X, y)
        assert svm_rbf.score(X, y) == 1.0

        # 多项式核
        svm_poly = SVM(kernel="polynomial", C=1.0, degree=2, max_passes=50)
        svm_poly.fit(X, y)
        assert svm_poly.score(X, y) == 1.0
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
cd projects/svm
python -m pytest tests/ -v
```

### 6.2 运行特定测试

```bash
# 运行核函数测试
python -m pytest tests/test_svm.py::TestLinearKernel -v

# 运行 SMO 测试
python -m pytest tests/test_svm.py::TestSMO -v

# 运行 SVM 测试
python -m pytest tests/test_svm.py::TestSVM -v
```

### 6.3 生成覆盖率报告

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 7. 测试结果

### 7.1 预期结果

- 所有测试应该通过
- 核函数测试：验证数学正确性
- SMO 测试：验证收敛性和约束满足
- SVM 测试：验证分类功能

### 7.2 性能指标

- 训练时间：小数据集应该在几秒内完成
- 预测时间：应该很快
- 准确率：线性可分数据应该达到 100%

## 8. 测试维护

### 8.1 添加新测试

- 新功能必须有对应的测试
- 边界情况必须测试
- 异常处理必须测试

### 8.2 测试代码质量

- 测试代码应该清晰易读
- 测试应该独立，不依赖其他测试
- 测试应该快速执行
