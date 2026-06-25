"""
模型选择测试用例
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model_selection import (
    KFold, CrossValidator, train_test_split,
    accuracy_score, mean_squared_error, r2_score
)
from src.knn_classifier import KNNClassifier
from src.knn_regressor import KNNRegressor


class TestKFold:
    """K-Fold 交叉验证测试类"""

    def test_initialization(self):
        """测试初始化"""
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        assert kfold.n_splits == 5
        assert kfold.shuffle is True
        assert kfold.random_state == 42

    def test_initialization_invalid(self):
        """测试无效初始化"""
        with pytest.raises(ValueError):
            KFold(n_splits=1)

    def test_split_basic(self):
        """测试基本分割功能"""
        X = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]])
        kfold = KFold(n_splits=5, shuffle=False)

        splits = kfold.split(X)

        assert len(splits) == 5

        for train_idx, val_idx in splits:
            # 验证没有重叠
            assert len(set(train_idx) & set(val_idx)) == 0
            # 验证覆盖所有样本
            assert len(train_idx) + len(val_idx) == 10

    def test_split_shuffle(self):
        """测试打乱分割"""
        X = np.arange(20).reshape(-1, 1)

        kfold_no_shuffle = KFold(n_splits=5, shuffle=False)
        kfold_shuffle = KFold(n_splits=5, shuffle=True, random_state=42)

        splits_no_shuffle = kfold_no_shuffle.split(X)
        splits_shuffle = kfold_shuffle.split(X)

        # 验证都能生成正确的分割
        assert len(splits_no_shuffle) == 5
        assert len(splits_shuffle) == 5

    def test_split_reproducible(self):
        """测试可复现性"""
        X = np.arange(20).reshape(-1, 1)

        kfold1 = KFold(n_splits=5, shuffle=True, random_state=42)
        kfold2 = KFold(n_splits=5, shuffle=True, random_state=42)

        splits1 = kfold1.split(X)
        splits2 = kfold2.split(X)

        for (train1, val1), (train2, val2) in zip(splits1, splits2):
            np.testing.assert_array_equal(train1, train2)
            np.testing.assert_array_equal(val1, val2)

    def test_split_uneven(self):
        """测试不均匀分割"""
        X = np.arange(11).reshape(-1, 1)  # 11 个样本，5 折

        kfold = KFold(n_splits=5, shuffle=False)
        splits = kfold.split(X)

        assert len(splits) == 5

        # 验证每折大小差异不超过 1
        val_sizes = [len(val_idx) for _, val_idx in splits]
        assert max(val_sizes) - min(val_sizes) <= 1

    def test_split_too_few_samples(self):
        """测试样本数少于折数"""
        X = np.array([[1], [2]])

        kfold = KFold(n_splits=5)

        with pytest.raises(ValueError):
            kfold.split(X)


class TestCrossValidator:
    """交叉验证器测试类"""

    def test_initialization(self):
        """测试初始化"""
        cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)
        assert cv.n_folds == 5
        assert cv.shuffle is True
        assert cv.random_state == 42

    def test_cross_val_score_classification(self):
        """测试分类交叉验证评分"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = np.random.randint(0, 3, 100)

        cv = CrossValidator(n_folds=5, random_state=42)
        knn = KNNClassifier(k=5)
        results = cv.cross_val_score(knn, X, y)

        assert 'scores' in results
        assert 'mean_score' in results
        assert 'std_score' in results
        assert 'train_scores' in results

        assert len(results['scores']) == 5
        assert 0 <= results['mean_score'] <= 1
        assert results['std_score'] >= 0

    def test_cross_val_score_regression(self):
        """测试回归交叉验证评分"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = np.random.randn(100)

        cv = CrossValidator(n_folds=5, random_state=42)
        reg = KNNRegressor(k=5)
        results = cv.cross_val_score(reg, X, y)

        assert 'scores' in results
        assert 'mean_score' in results
        assert len(results['scores']) == 5

    def test_cross_val_score_custom_scoring(self):
        """测试自定义评分函数"""
        np.random.seed(42)
        X = np.random.randn(50, 2)
        y = np.random.randint(0, 2, 50)

        cv = CrossValidator(n_folds=3, random_state=42)
        knn = KNNClassifier(k=3)

        def custom_score(y_true, y_pred):
            return np.mean(y_true == y_pred)

        results = cv.cross_val_score(knn, X, y, scoring=custom_score)

        assert 'scores' in results
        assert len(results['scores']) == 3

    def test_select_k_classification(self):
        """测试分类 K 值选择"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = np.random.randint(0, 3, 100)

        cv = CrossValidator(n_folds=5, random_state=42)
        results = cv.select_k(X, y, k_range=[1, 3, 5], task='classification')

        assert 'best_k' in results
        assert 'best_score' in results
        assert 'k_scores' in results
        assert 'k_std' in results

        assert results['best_k'] in [1, 3, 5]
        assert 0 <= results['best_score'] <= 1

    def test_select_k_regression(self):
        """测试回归 K 值选择"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = np.random.randn(100)

        cv = CrossValidator(n_folds=5, random_state=42)
        results = cv.select_k(
            X, y, k_range=[1, 3, 5], task='regression', weights='distance'
        )

        assert 'best_k' in results
        assert 'best_score' in results

    def test_select_k_k_too_large(self):
        """测试 K 值过大"""
        np.random.seed(42)
        X = np.random.randn(20, 2)
        y = np.random.randint(0, 2, 20)

        cv = CrossValidator(n_folds=5, random_state=42)

        with pytest.raises(ValueError):
            cv.select_k(X, y, k_range=[50], task='classification')


class TestTrainTestSplit:
    """训练测试划分测试类"""

    def test_split_basic(self):
        """测试基本划分功能"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        assert len(X_train) == 16
        assert len(X_test) == 4
        assert len(y_train) == 16
        assert len(y_test) == 4

    def test_split_no_overlap(self):
        """测试划分无重叠"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        # 验证没有重复样本
        all_X = np.vstack([X_train, X_test])
        assert len(np.unique(all_X, axis=0)) == len(all_X)

    def test_split_reproducible(self):
        """测试可复现性"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train1, X_test1, y_train1, y_test1 = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
        X_train2, X_test2, y_train2, y_test2 = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        np.testing.assert_array_equal(X_train1, X_train2)
        np.testing.assert_array_equal(X_test1, X_test2)

    def test_split_preserves_correspondence(self):
        """测试划分保持对应关系"""
        X = np.array([[1, 10], [2, 20], [3, 30], [4, 40], [5, 50]])
        y = np.array([100, 200, 300, 400, 500])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.4, random_state=42
        )

        # 验证 X 和 y 的对应关系
        for i in range(len(X_train)):
            assert y_train[i] == X_train[i, 0] * 100

    def test_split_small_test_size(self):
        """测试小测试集"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.1, random_state=42
        )

        assert len(X_test) == 2  # 10% of 20

    def test_split_large_test_size(self):
        """测试大测试集"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.5, random_state=42
        )

        assert len(X_test) == 10


class TestScoringFunctions:
    """评分函数测试类"""

    def test_accuracy_score_perfect(self):
        """测试完美准确率"""
        y_true = np.array([0, 1, 2, 0, 1])
        y_pred = np.array([0, 1, 2, 0, 1])

        assert accuracy_score(y_true, y_pred) == 1.0

    def test_accuracy_score_zero(self):
        """测试零准确率"""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 1, 1])

        assert accuracy_score(y_true, y_pred) == 0.0

    def test_accuracy_score_partial(self):
        """测试部分准确率"""
        y_true = np.array([0, 1, 2, 0])
        y_pred = np.array([0, 1, 0, 0])

        assert accuracy_score(y_true, y_pred) == 0.75

    def test_mse_perfect(self):
        """测试完美预测的 MSE"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        assert mean_squared_error(y_true, y_pred) == 0.0

    def test_mse_calculation(self):
        """测试 MSE 计算"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])

        expected = np.mean([0.25, 0.25, 0.25])
        assert abs(mean_squared_error(y_true, y_pred) - expected) < 1e-10

    def test_r2_score_perfect(self):
        """测试完美 R²"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        assert abs(r2_score(y_true, y_pred) - 1.0) < 1e-10

    def test_r2_score_mean(self):
        """测试使用均值预测的 R²"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 2.0, 2.0])

        assert abs(r2_score(y_true, y_pred)) < 1e-10

    def test_r2_score_poor(self):
        """测试差预测的 R²"""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([10.0, 20.0, 30.0])

        assert r2_score(y_true, y_pred) < 0


class TestModelSelectionIntegration:
    """模型选择集成测试"""

    def test_full_workflow_classification(self):
        """测试完整的分类工作流程"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)

        # 1. 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        # 2. 交叉验证选择 K
        cv = CrossValidator(n_folds=5, random_state=42)
        cv_results = cv.select_k(
            X_train, y_train,
            k_range=[1, 3, 5, 7],
            task='classification'
        )

        # 3. 使用最优 K 训练模型
        best_knn = KNNClassifier(k=cv_results['best_k'])
        best_knn.fit(X_train, y_train)

        # 4. 评估模型
        accuracy = best_knn.score(X_test, y_test)

        assert accuracy > 0.5

    def test_full_workflow_regression(self):
        """测试完整的回归工作流程"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1

        # 1. 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        # 2. 交叉验证选择 K
        cv = CrossValidator(n_folds=5, random_state=42)
        cv_results = cv.select_k(
            X_train, y_train,
            k_range=[1, 3, 5, 7],
            task='regression',
            weights='distance'
        )

        # 3. 使用最优 K 训练模型
        best_reg = KNNRegressor(
            k=cv_results['best_k'], weights='distance'
        )
        best_reg.fit(X_train, y_train)

        # 4. 评估模型
        y_pred = best_reg.predict(X_test)
        r2 = r2_score(y_test, y_pred)

        assert r2 > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
