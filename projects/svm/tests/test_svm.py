"""
SVM 测试套件
============

测试 SVM 分类器的各个组件:
- 核函数 (线性核、RBF核、多项式核、Sigmoid核)
- SMO 算法
- SVM 分类器
- SVR 回归器
- 多分类策略 (One-vs-Rest, One-vs-One)
- 模型评估指标
"""

import pytest
import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/svm')

from src.kernel import (
    linear_kernel, rbf_kernel, polynomial_kernel,
    sigmoid_kernel, precompute_kernel_matrix,
)
from src.smo import SMO
from src.svm import SVM
from src.svr import SVR
from src.multiclass import OneVsRestSVM, OneVsOneSVM
from src.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, mean_squared_error, r2_score, mean_absolute_error,
)


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


class TestSigmoidKernel:
    """Sigmoid 核函数测试"""

    def test_symmetry(self):
        """测试核函数的对称性"""
        kernel = sigmoid_kernel(gamma=1.0, coef0=0.0)
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        assert kernel(x, y) == kernel(y, x)

    def test_range(self):
        """测试核函数值在 (-1, 1) 范围内"""
        kernel = sigmoid_kernel(gamma=1.0, coef0=0.0)
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        value = kernel(x, y)
        assert -1 < value < 1

    def test_zero_vectors(self):
        """测试零向量的核值为 0"""
        kernel = sigmoid_kernel(gamma=1.0, coef0=0.0)
        x = np.array([0.0, 0.0])
        y = np.array([1.0, 2.0])
        assert kernel(x, y) == 0.0

    def test_coef0_effect(self):
        """测试 coef0 参数的影响"""
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])

        kernel_0 = sigmoid_kernel(gamma=1.0, coef0=0.0)
        kernel_1 = sigmoid_kernel(gamma=1.0, coef0=1.0)

        # 不同 coef0 应产生不同结果
        assert kernel_0(x, y) != kernel_1(x, y)

    def test_invalid_gamma(self):
        """测试无效的 gamma 值"""
        with pytest.raises(ValueError):
            sigmoid_kernel(gamma=-1.0)
        with pytest.raises(ValueError):
            sigmoid_kernel(gamma=0.0)


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
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=20)
        alpha, b = smo.optimize(K, y)

        assert np.all(alpha >= -1e-7)
        assert np.all(alpha <= 1.0 + 1e-7)
        assert abs(np.sum(alpha * y)) < 0.1

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

        assert np.sum(alpha > 1e-5) > 0

    def test_kkt_conditions(self):
        """测试 KKT 条件是否满足"""
        X = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        y = np.array([1, 1, -1, -1])

        kernel = linear_kernel()
        K = precompute_kernel_matrix(X, kernel)

        smo = SMO(C=1.0, tol=1e-3, max_passes=20)
        alpha, b = smo.optimize(K, y)

        predictions = np.sum(alpha * y * K, axis=1) + b

        for i in range(len(y)):
            margin = y[i] * predictions[i]
            if alpha[i] < 1e-7:
                assert margin >= 1 - 0.5
            elif alpha[i] > 1.0 - 1e-7:
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

    def test_fit_predict_sigmoid(self):
        """测试 Sigmoid 核的训练和预测"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="sigmoid", C=1.0, gamma=0.5, coef0=1.0, max_passes=50)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

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

    def test_support_vectors(self):
        """测试支持向量的提取"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        svm = SVM(kernel="linear", C=1.0, max_passes=50)
        svm.fit(X, y)

        assert svm.get_n_support_vectors() > 0
        sv = svm.get_support_vectors()
        assert sv.shape[1] == X.shape[1]

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
        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y = np.array([-1, 1, 1, -1])

        svm = SVM(kernel="rbf", C=10.0, gamma=1.0, max_passes=100)
        svm.fit(X, y)

        predictions = svm.predict(X)
        assert_array_equal(predictions, y)

    def test_linearly_separable_large(self):
        """测试较大的线性可分数据集"""
        np.random.seed(42)
        X_pos = np.random.randn(50, 2) + 3
        X_neg = np.random.randn(50, 2) - 3
        X = np.vstack([X_pos, X_neg])
        y = np.array([1] * 50 + [-1] * 50)

        svm = SVM(kernel="linear", C=1.0, max_passes=100)
        svm.fit(X, y)

        accuracy = svm.score(X, y)
        assert accuracy > 0.95

    def test_rbf_circle(self):
        """测试圆形分布的数据 (RBF 核应该表现好)"""
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


# =============================================================================
# SVR 回归器测试
# =============================================================================

class TestSVR:
    """SVR 回归器测试"""

    def test_initialization(self):
        """测试 SVR 初始化"""
        svr = SVR(kernel="rbf", C=1.0, epsilon=0.1)
        assert svr.kernel_type == "rbf"
        assert svr.C == 1.0
        assert svr.epsilon == 0.1

    def test_fit_predict_linear(self):
        """测试线性数据的回归"""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = 2 * X.flatten() + 1 + np.random.randn(50) * 0.5

        svr = SVR(kernel="linear", C=10.0, epsilon=0.5, max_passes=50)
        svr.fit(X, y)

        predictions = svr.predict(X)
        # 预测值应该接近真实值
        mse = np.mean((predictions - y) ** 2)
        assert mse < 5.0

    def test_fit_predict_rbf(self):
        """测试 RBF 核回归"""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = np.sin(X.flatten()) + np.random.randn(50) * 0.1

        svr = SVR(kernel="rbf", C=10.0, epsilon=0.1, gamma=0.1, max_passes=100)
        svr.fit(X, y)

        predictions = svr.predict(X)
        mse = np.mean((predictions - y) ** 2)
        # SVR 应该能拟合数据，MSE 不应太大
        assert mse < 2.0

    def test_predict_before_fit(self):
        """测试训练前预测"""
        svr = SVR(kernel="linear")
        X = np.array([[1.0]])
        with pytest.raises(RuntimeError):
            svr.predict(X)

    def test_support_vectors(self):
        """测试支持向量"""
        np.random.seed(42)
        X = np.linspace(0, 10, 30).reshape(-1, 1)
        y = 2 * X.flatten() + 1

        svr = SVR(kernel="linear", C=10.0, epsilon=0.1, max_passes=50)
        svr.fit(X, y)

        n_sv = svr.get_n_support_vectors()
        assert n_sv > 0

    def test_score(self):
        """测试 R2 分数"""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = 2 * X.flatten() + 1

        svr = SVR(kernel="linear", C=10.0, epsilon=0.01, max_passes=50)
        svr.fit(X, y)

        r2 = svr.score(X, y)
        assert r2 > 0.9

    def test_repr(self):
        """测试字符串表示"""
        svr = SVR(kernel="rbf", C=2.0, epsilon=0.2)
        repr_str = repr(svr)
        assert "rbf" in repr_str
        assert "2.0" in repr_str
        assert "0.2" in repr_str


# =============================================================================
# 多分类测试
# =============================================================================

class TestOneVsRest:
    """One-vs-Rest 多分类测试"""

    def test_initialization(self):
        """测试初始化"""
        ovr = OneVsRestSVM(kernel="rbf", C=1.0)
        assert ovr.kernel == "rbf"
        assert ovr.C == 1.0

    def test_fit_predict_3_classes(self):
        """测试三分类"""
        np.random.seed(42)
        X = np.vstack([
            np.random.randn(20, 2) + [3, 3],
            np.random.randn(20, 2) + [-3, -3],
            np.random.randn(20, 2) + [3, -3],
        ])
        y = np.array([0] * 20 + [1] * 20 + [2] * 20)

        ovr = OneVsRestSVM(kernel="rbf", C=1.0, gamma=0.5, max_passes=50)
        ovr.fit(X, y)

        predictions = ovr.predict(X)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.8

    def test_n_classifiers(self):
        """测试分类器数量等于类别数"""
        np.random.seed(42)
        X = np.vstack([
            np.random.randn(10, 2) + [3, 3],
            np.random.randn(10, 2) + [-3, -3],
            np.random.randn(10, 2) + [3, -3],
        ])
        y = np.array([0] * 10 + [1] * 10 + [2] * 10)

        ovr = OneVsRestSVM(kernel="linear", C=1.0, max_passes=50)
        ovr.fit(X, y)

        assert len(ovr.classifiers) == 3

    def test_predict_before_fit(self):
        """测试训练前预测"""
        ovr = OneVsRestSVM(kernel="linear")
        X = np.array([[1.0, 1.0]])
        with pytest.raises(RuntimeError):
            ovr.predict(X)


class TestOneVsOne:
    """One-vs-One 多分类测试"""

    def test_initialization(self):
        """测试初始化"""
        ovo = OneVsOneSVM(kernel="rbf", C=1.0)
        assert ovo.kernel == "rbf"
        assert ovo.C == 1.0

    def test_fit_predict_3_classes(self):
        """测试三分类"""
        np.random.seed(42)
        X = np.vstack([
            np.random.randn(20, 2) + [3, 3],
            np.random.randn(20, 2) + [-3, -3],
            np.random.randn(20, 2) + [3, -3],
        ])
        y = np.array([0] * 20 + [1] * 20 + [2] * 20)

        ovo = OneVsOneSVM(kernel="rbf", C=1.0, gamma=0.5, max_passes=50)
        ovo.fit(X, y)

        predictions = ovo.predict(X)
        accuracy = np.mean(predictions == y)
        assert accuracy > 0.8

    def test_n_classifiers(self):
        """测试分类器数量等于 C(n_classes, 2)"""
        np.random.seed(42)
        X = np.vstack([
            np.random.randn(10, 2) + [3, 3],
            np.random.randn(10, 2) + [-3, -3],
            np.random.randn(10, 2) + [3, -3],
        ])
        y = np.array([0] * 10 + [1] * 10 + [2] * 10)

        ovo = OneVsOneSVM(kernel="linear", C=1.0, max_passes=50)
        ovo.fit(X, y)

        # 3 类 -> C(3,2) = 3 个分类器
        assert len(ovo.classifiers) == 3

    def test_predict_before_fit(self):
        """测试训练前预测"""
        ovo = OneVsOneSVM(kernel="linear")
        X = np.array([[1.0, 1.0]])
        with pytest.raises(RuntimeError):
            ovo.predict(X)


# =============================================================================
# 模型评估指标测试
# =============================================================================

class TestMetrics:
    """模型评估指标测试"""

    def test_accuracy_perfect(self):
        """测试完美预测的准确率"""
        y_true = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 0])
        assert accuracy_score(y_true, y_pred) == 1.0

    def test_accuracy_zero(self):
        """测试完全错误的准确率"""
        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 0, 0])
        assert accuracy_score(y_true, y_pred) == 0.0

    def test_accuracy_partial(self):
        """测试部分正确的准确率"""
        y_true = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 1, 0, 0])
        assert accuracy_score(y_true, y_pred) == 0.5

    def test_precision_binary(self):
        """测试二分类精确率"""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 0, 1, 0])
        # TP=1, FP=1 -> precision = 0.5
        assert precision_score(y_true, y_pred) == 0.5

    def test_recall_binary(self):
        """测试二分类召回率"""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 0, 1, 0])
        # TP=1, FN=1 -> recall = 0.5
        assert recall_score(y_true, y_pred) == 0.5

    def test_f1_binary(self):
        """测试二分类 F1"""
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 0, 1, 0])
        # precision=0.5, recall=0.5 -> f1 = 0.5
        assert f1_score(y_true, y_pred) == 0.5

    def test_precision_macro(self):
        """测试宏平均精确率"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 2, 1])
        p = precision_score(y_true, y_pred, average='macro')
        assert 0 <= p <= 1

    def test_recall_macro(self):
        """测试宏平均召回率"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 2, 1])
        r = recall_score(y_true, y_pred, average='macro')
        assert 0 <= r <= 1

    def test_f1_macro(self):
        """测试宏平均 F1"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 2, 1])
        f = f1_score(y_true, y_pred, average='macro')
        assert 0 <= f <= 1

    def test_confusion_matrix(self):
        """测试混淆矩阵"""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 1, 0, 1])
        cm = confusion_matrix(y_true, y_pred)
        assert cm.shape == (2, 2)
        assert cm[0, 0] == 1  # TN
        assert cm[0, 1] == 1  # FP
        assert cm[1, 0] == 1  # FN
        assert cm[1, 1] == 1  # TP

    def test_confusion_matrix_multiclass(self):
        """测试多分类混淆矩阵"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 2, 1])
        cm = confusion_matrix(y_true, y_pred)
        assert cm.shape == (3, 3)
        assert cm[0, 0] == 2  # 类别 0 全对
        assert cm[1, 1] == 1  # 类别 1 对 1 个
        assert cm[2, 2] == 1  # 类别 2 对 1 个

    def test_mse_perfect(self):
        """测试完美预测的 MSE"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert mean_squared_error(y_true, y_pred) == 0.0

    def test_mse_calculation(self):
        """测试 MSE 计算"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        expected = 0.25  # (0.5^2 + 0.5^2 + 0.5^2) / 3
        assert abs(mean_squared_error(y_true, y_pred) - expected) < 1e-10

    def test_r2_perfect(self):
        """测试完美预测的 R2"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert abs(r2_score(y_true, y_pred) - 1.0) < 1e-10

    def test_r2_mean_prediction(self):
        """测试预测均值时 R2 为 0"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 2.0, 2.0])
        assert abs(r2_score(y_true, y_pred)) < 1e-10

    def test_mae_perfect(self):
        """测试完美预测的 MAE"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert mean_absolute_error(y_true, y_pred) == 0.0

    def test_mae_calculation(self):
        """测试 MAE 计算"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 3.0, 4.0])
        assert mean_absolute_error(y_true, y_pred) == 1.0


# =============================================================================
# 集成测试
# =============================================================================

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

    def test_different_kernels(self):
        """测试不同的核函数"""
        X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
        y = np.array([1, 1, -1, -1])

        for kernel in ["linear", "rbf", "polynomial", "sigmoid"]:
            svm = SVM(kernel=kernel, C=1.0, gamma=0.5, coef0=1.0, max_passes=50)
            svm.fit(X, y)
            assert svm.score(X, y) == 1.0

    def test_multiclass_with_metrics(self):
        """测试多分类与评估指标的集成"""
        np.random.seed(42)
        X = np.vstack([
            np.random.randn(20, 2) + [3, 3],
            np.random.randn(20, 2) + [-3, -3],
            np.random.randn(20, 2) + [3, -3],
        ])
        y = np.array([0] * 20 + [1] * 20 + [2] * 20)

        ovr = OneVsRestSVM(kernel="rbf", C=1.0, gamma=0.5, max_passes=50)
        ovr.fit(X, y)

        y_pred = ovr.predict(X)
        acc = accuracy_score(y, y_pred)
        f1 = f1_score(y, y_pred, average='macro')
        cm = confusion_matrix(y, y_pred)

        assert acc > 0.8
        assert f1 > 0.8
        assert cm.shape == (3, 3)

    def test_svr_with_metrics(self):
        """测试 SVR 与回归指标的集成"""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = 2 * X.flatten() + 1 + np.random.randn(50) * 0.5

        svr = SVR(kernel="linear", C=10.0, epsilon=0.1, max_passes=50)
        svr.fit(X, y)

        y_pred = svr.predict(X)
        mse = mean_squared_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        assert mse < 5.0
        assert r2 > 0.8
        assert mae < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
