"""
SVM 测试套件
============

测试 SVM 分类器的各个组件:
- 核函数
- SMO 算法
- SVM 分类器
"""

import pytest
import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/svm/src')

from kernel import linear_kernel, rbf_kernel, polynomial_kernel, precompute_kernel_matrix
from smo import SMO
from svm import SVM


# =============================================================================
# 核函数测试
# =============================================================================

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

        # gamma 越大，核值越小 (因为距离的影响更大)
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


class TestPolynomialKernel:
    """多项式核函数测试"""

    def test_degree_1(self):
        """测试 degree=1 时等价于线性核加偏置"""
        kernel = polynomial_kernel(degree=1, coef0=1.0)
        linear = linear_kernel()
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        # poly(1, 1) = (x·y + 1)^1 = x·y + 1
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

        # 对于相同的输入，更高 degree 的核值更大 (假设内积 > 0)
        assert kernel_d3(x, y) > kernel_d2(x, y)

    def test_invalid_degree(self):
        """测试无效的 degree 值"""
        with pytest.raises(ValueError):
            polynomial_kernel(degree=0)
        with pytest.raises(ValueError):
            polynomial_kernel(degree=-1)


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
        # 对角线元素应该是 ||xi||^2
        assert K[0, 0] == 5.0  # 1^2 + 2^2
        assert K[1, 1] == 25.0  # 3^2 + 4^2

    def test_rbf_diagonal(self):
        """测试 RBF 核矩阵的对角线元素为 1"""
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        kernel = rbf_kernel(gamma=1.0)
        K = precompute_kernel_matrix(X, kernel)
        assert_array_almost_equal(np.diag(K), [1.0, 1.0])


# =============================================================================
# SMO 算法测试
# =============================================================================

class TestSMO:
    """SMO 算法测试"""

    def test_simple_linear_separable(self):
        """测试简单线性可分数据"""
        # 创建简单的线性可分数据
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

    def test_convergence(self):
        """测试算法收敛"""
        np.random.seed(42)
        # 生成线性可分数据
        X_pos = np.random.randn(20, 2) + 2
        X_neg = np.random.randn(20, 2) - 2
        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 20 + [-1] * 20)

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=50)
        alpha, b = smo.optimize(K, y)

        # 应该有一些非零的 alpha (支持向量)
        assert np.sum(alpha > 1e-5) > 0

    def test_kkt_conditions(self):
        """测试 KKT 条件是否满足"""
        X = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        y = np.array([1, 1, -1, -1])

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=20)
        alpha, b = smo.optimize(K, y)

        # 计算每个样本的预测值
        predictions = np.sum(alpha * y * K, axis=1) + b

        # 对于 alpha = 0 的样本，yi * f(xi) >= 1 - tol
        # 对于 0 < alpha < C 的样本，yi * f(xi) ≈ 1
        # 对于 alpha = C 的样本，yi * f(xi) <= 1 + tol
        for i in range(len(y)):
            margin = y[i] * predictions[i]
            if alpha[i] < 1e-7:  # alpha ≈ 0
                assert margin >= 1 - 0.5  # 允许一定误差
            elif alpha[i] > 1.0 - 1e-7:  # alpha ≈ C
                assert margin <= 1 + 0.5


# =============================================================================
# SVM 分类器测试
# =============================================================================

class TestSVM:
    """SVM 分类器测试"""

    def test_initialization(self):
        """测试 SVM 初始化"""
        svm = SVM(kernel="linear", C=1.0)
        assert svm.kernel_type == "linear"
        assert svm.C == 1.0

    def test_fit_predict_linear(self):
        """测试线性核的训练和预测"""
        # 简单的线性可分数据
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_fit_predict_rbf(self):
        """测试 RBF 核的训练和预测"""
        # 简单数据
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="rbf", C=1.0, gamma=1.0, max_passes=50)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_invalid_labels(self):
        """测试无效的标签"""
        X = np.array([[1, 1], [2, 2]])
        y = np.array([0, 1])  # 无效标签

        svm = SVM(kernel="linear")
        with pytest.raises(ValueError):
            svm.fit(X, y)

    def test_predict_before_fit(self):
        """测试在训练前预测"""
        svm = SVM(kernel="linear")
        X = np.array([[1, 1]])
        with pytest.raises(RuntimeError):
            svm.predict(X)

    def test_support_vectors(self):
        """测试支持向量的提取"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        # 应该有支持向量
        assert svm.get_n_support_vectors() > 0

        # 支持向量应该是训练数据的子集
        sv = svm.get_support_vectors()
        assert sv.shape[1] == X.shape[1]

    def test_decision_function(self):
        """测试决策函数"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        # 正类应该有正的决策值
        decision = svm.decision_function(X)
        assert decision[0] > 0
        assert decision[1] > 0

        # 负类应该有负的决策值
        assert decision[2] < 0
        assert decision[3] < 0

    def test_score(self):
        """测试准确率计算"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy == 1.0

    def test_repr(self):
        """测试字符串表示"""
        svm = SVM(kernel="rbf", C=2.0, gamma=0.5)
        repr_str = repr(svm)
        assert "rbf" in repr_str
        assert "2.0" in repr_str
        assert "0.5" in repr_str

    def test_xor_problem_rbf(self):
        """测试 XOR 问题 (需要非线性核)"""
        # XOR 数据
        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y = np.array([-1, 1, 1, -1])

        svm = SVM(kernel="rbf", C=10.0, gamma=1.0, max_passes=100)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_linearly_separable_large(self):
        """测试较大的线性可分数据集"""
        np.random.seed(42)
        # 生成线性可分数据
        X_pos = np.random.randn(50, 2) + 3
        X_neg = np.random.randn(50, 2) - 3
        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 50 + [-1] * 50)

        svm = SVM(kernel="linear", C=1.0, max_passes=100)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy > 0.95  # 应该有很高的准确率

    def test_rbf_circle(self):
        """测试圆形分布的数据 (RBF 核应该表现好)"""
        np.random.seed(42)
        # 内圈 (正类)
        r1 = np.random.uniform(0, 1, 50)
        theta1 = np.random.uniform(0, 2 * np.pi, 50)
        X_pos = np.column_stack([r1 * np.cos(theta1), r1 * np.sin(theta1)])

        # 外圈 (负类)
        r2 = np.random.uniform(2, 3, 50)
        theta2 = np.random.uniform(0, 2 * np.pi, 50)
        X_neg = np.column_stack([r2 * np.cos(theta2), r2 * np.sin(theta2)])

        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 50 + [-1] * 50)

        svm = SVM(kernel="rbf", C=10.0, gamma=1.0, max_passes=100)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy > 0.8  # RBF 核应该能处理这种数据


# =============================================================================
# 集成测试
# =============================================================================

class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整的训练-预测流程"""
        np.random.seed(42)

        # 生成数据
        X_train = np.array([[1, 1], [2, 2], [3, 3],
                            [-1, -1], [-2, -2], [-3, -3]])
        y_train = np.array([1, 1, 1, -1, -1, -1])

        X_test = np.array([[1.5, 1.5], [-1.5, -1.5]])
        y_test = np.array([1, -1])

        # 训练
        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X_train, y_train)

        # 预测
        predictions = svm.predict(X_test)
        assert_array_equal(predictions, y_test)

        # 评估
        accuracy = svm.score(X_test, y_test)
        assert accuracy == 1.0

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
