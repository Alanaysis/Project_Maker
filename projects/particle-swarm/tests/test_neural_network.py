"""
神经网络训练测试
"""

import numpy as np
import pytest
from src.neural_network import (
    NeuralNetwork,
    NeuralNetworkTrainer,
    NeuralNetworkConfig,
    create_xor_dataset,
    create_spiral_dataset,
)


class TestNeuralNetworkConfig:
    """神经网络配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])

        assert config.layer_sizes == [2, 10, 1]
        assert config.hidden_activation == "relu"
        assert config.output_activation == "sigmoid"

    def test_custom_config(self):
        """测试自定义配置"""
        config = NeuralNetworkConfig(
            layer_sizes=[2, 20, 10, 1],
            hidden_activation="tanh",
            output_activation="sigmoid",
        )

        assert config.layer_sizes == [2, 20, 10, 1]
        assert config.hidden_activation == "tanh"


class TestNeuralNetwork:
    """神经网络测试"""

    def test_initialization(self):
        """测试初始化"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        network = NeuralNetwork(config)

        assert network.layer_sizes == [2, 10, 1]
        assert network.n_layers == 2

    def test_weight_count(self):
        """测试权重数量计算"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        network = NeuralNetwork(config)

        # 第一层: (2+1) * 10 = 30
        # 第二层: (10+1) * 1 = 11
        # 总计: 41
        assert network.n_weights == 41

    def test_unpack_weights(self):
        """测试权重解包"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        network = NeuralNetwork(config)

        weights = np.random.randn(network.n_weights)
        layers = network._unpack_weights(weights)

        assert len(layers) == 2

        # 第一层
        W1, b1 = layers[0]
        assert W1.shape == (2, 10)
        assert b1.shape == (10,)

        # 第二层
        W2, b2 = layers[1]
        assert W2.shape == (10, 1)
        assert b2.shape == (1,)

    def test_forward(self):
        """测试前向传播"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        network = NeuralNetwork(config)

        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        weights = np.random.randn(network.n_weights)

        output = network.forward(X, weights)

        assert output.shape == (4, 1)
        assert np.all(output >= 0)
        assert np.all(output <= 1)

    def test_relu_activation(self):
        """测试 ReLU 激活函数"""
        config = NeuralNetworkConfig(
            layer_sizes=[2, 10, 1],
            hidden_activation="relu",
        )
        network = NeuralNetwork(config)

        x = np.array([-2, -1, 0, 1, 2])
        result = network._relu(x)

        np.testing.assert_array_equal(result, [0, 0, 0, 1, 2])

    def test_sigmoid_activation(self):
        """测试 Sigmoid 激活函数"""
        config = NeuralNetworkConfig(
            layer_sizes=[2, 10, 1],
            output_activation="sigmoid",
        )
        network = NeuralNetwork(config)

        x = np.array([-100, 0, 100])
        result = network._sigmoid(x)

        assert result[0] < 0.01
        assert result[1] == pytest.approx(0.5)
        assert result[2] > 0.99


class TestNeuralNetworkTrainer:
    """神经网络训练器测试"""

    def test_initialization(self):
        """测试初始化"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        trainer = NeuralNetworkTrainer(config)

        assert trainer.config == config
        assert trainer.network is not None

    def test_create_xor_dataset(self):
        """测试 XOR 数据集创建"""
        X, y = create_xor_dataset()

        assert X.shape == (4, 2)
        assert y.shape == (4, 1)
        assert np.all(np.isin(y, [0, 1]))

    def test_create_spiral_dataset(self):
        """测试螺旋数据集创建"""
        X, y = create_spiral_dataset(n_points=50)

        assert X.shape == (100, 2)
        assert y.shape == (100, 1)

    def test_train_xor(self):
        """测试训练 XOR 问题"""
        config = NeuralNetworkConfig(
            layer_sizes=[2, 10, 1],
            n_particles=20,
            max_iterations=50,
            random_seed=42,
        )
        trainer = NeuralNetworkTrainer(config)

        X, y = create_xor_dataset()
        result = trainer.train(X, y, loss_type="binary_crossentropy", verbose=False)

        assert "best_weights" in result
        assert "best_loss" in result
        assert result["best_loss"] < 1.0

    def test_predict(self):
        """测试预测"""
        config = NeuralNetworkConfig(layer_sizes=[2, 10, 1])
        trainer = NeuralNetworkTrainer(config)

        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        weights = np.random.randn(trainer.network.n_weights)

        predictions = trainer.predict(X, weights)

        assert predictions.shape == (4, 1)
