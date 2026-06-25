"""
特征选择测试
"""

import numpy as np
import pytest
from src.feature_selection import (
    BinaryPSO,
    FeatureSelector,
    FeatureSelectionConfig,
    simple_cross_validation_accuracy,
    create_sample_dataset,
)


class TestFeatureSelectionConfig:
    """特征选择配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = FeatureSelectionConfig(n_features=10)

        assert config.n_features == 10
        assert config.n_particles == 30
        assert config.accuracy_weight == 0.9
        assert config.feature_weight == 0.1

    def test_custom_config(self):
        """测试自定义配置"""
        config = FeatureSelectionConfig(
            n_features=20,
            n_particles=50,
            min_features=3,
            max_features=15,
        )

        assert config.n_features == 20
        assert config.n_particles == 50
        assert config.min_features == 3
        assert config.max_features == 15


class TestBinaryPSO:
    """二进制 PSO 测试"""

    def test_initialization(self):
        """测试初始化"""
        config = FeatureSelectionConfig(n_features=10, n_particles=20)
        pso = BinaryPSO(config)

        assert pso.positions.shape == (20, 10)
        assert pso.velocities.shape == (20, 10)

    def test_sigmoid(self):
        """测试 sigmoid 函数"""
        config = FeatureSelectionConfig(n_features=5)
        pso = BinaryPSO(config)

        x = np.array([-100, 0, 100])
        result = pso._sigmoid(x)

        assert result[0] < 0.01
        assert result[1] == pytest.approx(0.5)
        assert result[2] > 0.99

    def test_to_binary(self):
        """测试二进制转换"""
        config = FeatureSelectionConfig(n_features=5, random_seed=42)
        pso = BinaryPSO(config)

        # 大值应该更可能为 1
        positions = np.array([[10, 10, 10, 10, 10]])
        binary = pso._to_binary(positions)

        assert binary.shape == (1, 5)
        assert np.all(np.isin(binary, [0, 1]))

    def test_optimize(self):
        """测试优化"""
        config = FeatureSelectionConfig(
            n_features=10,
            n_particles=20,
            max_iterations=20,
            random_seed=42,
        )
        pso = BinaryPSO(config)

        # 简单的适应度函数
        def fitness_function(binary_mask):
            return np.sum(binary_mask)

        result = pso.optimize(fitness_function, verbose=False)

        assert "best_position" in result
        assert "best_fitness" in result
        assert "n_selected_features" in result
        assert "selected_feature_indices" in result

    def test_feature_constraints(self):
        """测试特征数量约束"""
        config = FeatureSelectionConfig(
            n_features=10,
            n_particles=20,
            max_iterations=20,
            min_features=2,
            max_features=5,
            random_seed=42,
        )
        pso = BinaryPSO(config)

        def fitness_function(binary_mask):
            n_selected = np.sum(binary_mask)
            if n_selected < 2 or n_selected > 5:
                return float("inf")
            return -np.sum(binary_mask)

        result = pso.optimize(fitness_function, verbose=False)

        # 选择的特征数应该在约束范围内
        assert result["n_selected_features"] >= 2
        assert result["n_selected_features"] <= 5

    def test_callback(self):
        """测试回调函数"""
        config = FeatureSelectionConfig(
            n_features=5,
            n_particles=10,
            max_iterations=10,
            random_seed=42,
        )
        pso = BinaryPSO(config)

        callback_data = []

        def my_callback(iteration, fitness, position):
            callback_data.append((iteration, fitness))

        def fitness_function(binary_mask):
            return np.sum(binary_mask)

        pso.optimize(fitness_function, callback=my_callback)

        assert len(callback_data) > 0


class TestFeatureSelector:
    """特征选择器测试"""

    def test_initialization(self):
        """测试初始化"""
        config = FeatureSelectionConfig(n_features=10)
        selector = FeatureSelector(config)

        assert selector.config == config

    def test_select(self):
        """测试特征选择"""
        config = FeatureSelectionConfig(
            n_features=10,
            n_particles=20,
            max_iterations=20,
            random_seed=42,
        )
        selector = FeatureSelector(config)

        # 创建简单数据集
        X = np.random.randn(50, 10)
        y = (X[:, 0] > 0).astype(int).reshape(-1, 1)

        def evaluator(X_selected, y):
            return simple_cross_validation_accuracy(X_selected, y, n_folds=2)

        result = selector.select(X, y, evaluator, verbose=False)

        assert "best_position" in result
        assert "final_accuracy" in result
        assert "X_selected" in result


class TestHelperFunctions:
    """辅助函数测试"""

    def test_simple_cross_validation_accuracy(self):
        """测试简单交叉验证准确率"""
        X = np.random.randn(100, 5)
        y = (X[:, 0] > 0).astype(int).reshape(-1, 1)

        accuracy = simple_cross_validation_accuracy(X, y, n_folds=5)

        assert 0 <= accuracy <= 1

    def test_create_sample_dataset(self):
        """测试示例数据集创建"""
        X, y = create_sample_dataset(
            n_samples=100,
            n_features=10,
            n_informative=5,
        )

        assert X.shape == (100, 10)
        assert y.shape == (100, 1)
        assert np.all(np.isin(y, [0, 1]))
