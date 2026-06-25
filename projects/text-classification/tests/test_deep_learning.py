"""
Tests for Deep Learning Models.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.deep_learning import (
    ActivationFunctions,
    EmbeddingLayer,
    TextCNN,
    LSTMModel,
    BiLSTMAttention,
)


class TestActivationFunctions:
    """Test activation functions."""

    def test_sigmoid(self):
        """Test sigmoid function."""
        assert abs(ActivationFunctions.sigmoid(np.array([0.0]))[0] - 0.5) < 1e-6
        assert ActivationFunctions.sigmoid(np.array([100.0]))[0] > 0.99
        assert ActivationFunctions.sigmoid(np.array([-100.0]))[0] < 0.01

    def test_tanh(self):
        """Test tanh function."""
        assert abs(ActivationFunctions.tanh(np.array([0.0]))[0]) < 1e-6
        assert ActivationFunctions.tanh(np.array([100.0]))[0] > 0.99
        assert ActivationFunctions.tanh(np.array([-100.0]))[0] < -0.99

    def test_relu(self):
        """Test ReLU function."""
        assert ActivationFunctions.relu(np.array([1.0]))[0] == 1.0
        assert ActivationFunctions.relu(np.array([-1.0]))[0] == 0.0
        assert ActivationFunctions.relu(np.array([0.0]))[0] == 0.0

    def test_softmax(self):
        """Test softmax function."""
        x = np.array([1.0, 2.0, 3.0])
        result = ActivationFunctions.softmax(x)

        assert abs(sum(result) - 1.0) < 1e-6
        assert result[2] > result[1] > result[0]  # Preserves order


class TestEmbeddingLayer:
    """Test EmbeddingLayer functionality."""

    def test_init(self):
        """Test embedding layer initialization."""
        layer = EmbeddingLayer(vocab_size=100, embedding_dim=50)
        assert layer.vocab_size == 100
        assert layer.embedding_dim == 50
        assert layer.embeddings.shape == (100, 50)

    def test_forward(self):
        """Test forward pass."""
        layer = EmbeddingLayer(vocab_size=10, embedding_dim=5)
        indices = np.array([[0, 1, 2], [3, 4, 5]])

        result = layer.forward(indices)
        assert result.shape == (2, 3, 5)

    def test_embedding_lookup(self):
        """Test that embeddings are correctly looked up."""
        layer = EmbeddingLayer(vocab_size=10, embedding_dim=5)
        indices = np.array([[0]])

        result = layer.forward(indices)
        np.testing.assert_array_equal(result[0, 0], layer.embeddings[0])


class TestTextCNN:
    """Test TextCNN functionality."""

    def test_init(self):
        """Test TextCNN initialization."""
        model = TextCNN(
            vocab_size=100,
            embedding_dim=50,
            num_classes=3,
            filter_sizes=[2, 3, 4],
            num_filters=10,
        )
        assert model.vocab_size == 100
        assert model.embedding_dim == 50
        assert model.num_classes == 3
        assert model.num_filters == 10

    def test_forward(self):
        """Test forward pass."""
        model = TextCNN(
            vocab_size=100,
            embedding_dim=50,
            num_classes=3,
            filter_sizes=[2, 3],
            num_filters=10,
        )

        x = np.array([0, 1, 2, 3, 4])
        logits = model.forward(x)

        assert logits.shape == (3,)

    def test_predict(self):
        """Test prediction."""
        model = TextCNN(
            vocab_size=100,
            embedding_dim=50,
            num_classes=3,
            filter_sizes=[2, 3],
            num_filters=10,
        )

        x = np.array([0, 1, 2, 3, 4])
        pred = model.predict(x)

        assert 0 <= pred < 3

    def test_predict_proba(self):
        """Test probability prediction."""
        model = TextCNN(
            vocab_size=100,
            embedding_dim=50,
            num_classes=3,
            filter_sizes=[2, 3],
            num_filters=10,
        )

        x = np.array([0, 1, 2, 3, 4])
        proba = model.predict_proba(x)

        assert abs(sum(proba) - 1.0) < 1e-6
        assert all(p >= 0 for p in proba)

    def test_conv1d(self):
        """Test 1D convolution."""
        model = TextCNN(vocab_size=10, embedding_dim=5, num_classes=2, num_filters=3)

        x = np.random.randn(10, 5)
        filters = np.random.randn(3, 2, 5)

        result = model._conv1d(x, filters)
        assert result.shape == (3, 9)

    def test_max_pool(self):
        """Test max pooling."""
        model = TextCNN(vocab_size=10, embedding_dim=5, num_classes=2, num_filters=3)

        x = np.random.randn(3, 10)
        result = model._max_pool(x)

        assert result.shape == (3,)


class TestLSTMModel:
    """Test LSTMModel functionality."""

    def test_init(self):
        """Test LSTM model initialization."""
        model = LSTMModel(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )
        assert model.vocab_size == 100
        assert model.embedding_dim == 50
        assert model.hidden_dim == 64
        assert model.num_classes == 3

    def test_forward(self):
        """Test forward pass."""
        model = LSTMModel(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        logits = model.forward(x)

        assert logits.shape == (3,)

    def test_predict(self):
        """Test prediction."""
        model = LSTMModel(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        pred = model.predict(x)

        assert 0 <= pred < 3

    def test_predict_proba(self):
        """Test probability prediction."""
        model = LSTMModel(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        proba = model.predict_proba(x)

        assert abs(sum(proba) - 1.0) < 1e-6


class TestBiLSTMAttention:
    """Test BiLSTMAttention functionality."""

    def test_init(self):
        """Test BiLSTMAttention initialization."""
        model = BiLSTMAttention(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )
        assert model.vocab_size == 100
        assert model.embedding_dim == 50
        assert model.hidden_dim == 64
        assert model.num_classes == 3

    def test_forward(self):
        """Test forward pass."""
        model = BiLSTMAttention(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        logits = model.forward(x)

        assert logits.shape == (3,)

    def test_predict(self):
        """Test prediction."""
        model = BiLSTMAttention(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        pred = model.predict(x)

        assert 0 <= pred < 3

    def test_predict_proba(self):
        """Test probability prediction."""
        model = BiLSTMAttention(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        proba = model.predict_proba(x)

        assert abs(sum(proba) - 1.0) < 1e-6

    def test_get_attention_weights(self):
        """Test attention weight extraction."""
        model = BiLSTMAttention(
            vocab_size=100,
            embedding_dim=50,
            hidden_dim=64,
            num_classes=3,
        )

        x = np.array([0, 1, 2, 3, 4])
        weights = model.get_attention_weights(x)

        assert len(weights) == 5
        assert abs(sum(weights) - 1.0) < 1e-6
        assert all(w >= 0 for w in weights)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
