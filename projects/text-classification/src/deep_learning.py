"""
Deep Learning Models for Text Classification.

This module implements neural network models from scratch using only NumPy:
- TextCNN: Convolutional Neural Network for text
- LSTM: Long Short-Term Memory network
- BiLSTMAttention: Bidirectional LSTM with Attention mechanism

These implementations are for educational purposes to understand the internal
mechanics of deep learning models for NLP.
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple


class ActivationFunctions:
    """Common activation functions and their derivatives."""

    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        x = np.clip(x, -500, 500)
        return 1.0 / (1.0 + np.exp(-x))

    @staticmethod
    def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of sigmoid."""
        s = ActivationFunctions.sigmoid(x)
        return s * (1 - s)

    @staticmethod
    def tanh(x: np.ndarray) -> np.ndarray:
        """Tanh activation function."""
        return np.tanh(x)

    @staticmethod
    def tanh_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of tanh."""
        t = np.tanh(x)
        return 1 - t * t

    @staticmethod
    def relu(x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    @staticmethod
    def relu_derivative(x: np.ndarray) -> np.ndarray:
        """Derivative of ReLU."""
        return (x > 0).astype(float)

    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        """Softmax activation function."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


class EmbeddingLayer:
    """
    Simple embedding layer that maps word indices to dense vectors.

    Parameters
    ----------
    vocab_size : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of the embeddings.
    """

    def __init__(self, vocab_size: int, embedding_dim: int):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        # Initialize embeddings randomly
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * 0.1

    def forward(self, indices: np.ndarray) -> np.ndarray:
        """
        Lookup embeddings for given indices.

        Parameters
        ----------
        indices : np.ndarray
            Word indices of shape (batch_size, seq_len).

        Returns
        -------
        np.ndarray
            Embeddings of shape (batch_size, seq_len, embedding_dim).
        """
        return self.embeddings[indices]

    def backward(self, indices: np.ndarray, grad_output: np.ndarray) -> None:
        """
        Update embeddings based on gradients.

        Parameters
        ----------
        indices : np.ndarray
            Word indices.
        grad_output : np.ndarray
            Gradient of loss with respect to embeddings.
        """
        # Accumulate gradients for each index
        for i in range(indices.shape[0]):
            for j in range(indices.shape[1]):
                self.embeddings[indices[i, j]] -= 0.01 * grad_output[i, j]


class TextCNN:
    """
    TextCNN model for text classification.

    Uses multiple filter sizes to capture different n-gram features,
    followed by max-over-time pooling and a fully connected layer.

    Parameters
    ----------
    vocab_size : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of word embeddings.
    num_classes : int
        Number of output classes.
    filter_sizes : list of int
        Sizes of the convolutional filters.
    num_filters : int
        Number of filters per size.
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        num_classes: int = 2,
        filter_sizes: List[int] = [2, 3, 4],
        num_filters: int = 100,
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_classes = num_classes
        self.filter_sizes = filter_sizes
        self.num_filters = num_filters

        # Embedding layer
        self.embedding = EmbeddingLayer(vocab_size, embedding_dim)

        # Convolutional filters
        self.filters = {}
        for size in filter_sizes:
            self.filters[size] = np.random.randn(num_filters, size, embedding_dim) * 0.1

        # Fully connected layer
        total_filters = num_filters * len(filter_sizes)
        self.fc_weights = np.random.randn(total_filters, num_classes) * 0.1
        self.fc_bias = np.zeros(num_classes)

    def _conv1d(self, x: np.ndarray, filters: np.ndarray) -> np.ndarray:
        """
        1D convolution.

        Parameters
        ----------
        x : np.ndarray
            Input of shape (seq_len, embedding_dim).
        filters : np.ndarray
            Filters of shape (num_filters, filter_size, embedding_dim).

        Returns
        -------
        np.ndarray
            Convolved features of shape (num_filters, seq_len - filter_size + 1).
        """
        seq_len = x.shape[0]
        num_filters, filter_size, _ = filters.shape
        out_len = seq_len - filter_size + 1

        output = np.zeros((num_filters, out_len))
        for i in range(out_len):
            window = x[i : i + filter_size]
            for f in range(num_filters):
                output[f, i] = np.sum(window * filters[f])

        return output

    def _max_pool(self, x: np.ndarray) -> np.ndarray:
        """
        Max-over-time pooling.

        Parameters
        ----------
        x : np.ndarray
            Input of shape (num_filters, time_steps).

        Returns
        -------
        np.ndarray
            Pooled features of shape (num_filters,).
        """
        return np.max(x, axis=1)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.

        Parameters
        ----------
        x : np.ndarray
            Input word indices of shape (seq_len,).

        Returns
        -------
        np.ndarray
            Class logits of shape (num_classes,).
        """
        # Embedding lookup
        embedded = self.embedding.forward(x.reshape(1, -1))[0]  # (seq_len, embedding_dim)

        # Apply convolutions and max pooling
        pooled_outputs = []
        for size in self.filter_sizes:
            conv_out = self._conv1d(embedded, self.filters[size])
            pooled = self._max_pool(conv_out)
            pooled_outputs.append(pooled)

        # Concatenate pooled features
        features = np.concatenate(pooled_outputs)

        # Fully connected layer
        logits = np.dot(features, self.fc_weights) + self.fc_bias

        return logits

    def predict(self, x: np.ndarray) -> int:
        """
        Predict class for input.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        int
            Predicted class index.
        """
        logits = self.forward(x)
        return np.argmax(logits)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        np.ndarray
            Class probabilities.
        """
        logits = self.forward(x)
        return ActivationFunctions.softmax(logits)


class LSTMCell:
    """
    LSTM (Long Short-Term Memory) cell.

    LSTM uses gates to control the flow of information:
    - Forget gate: What to discard from cell state
    - Input gate: What to add to cell state
    - Output gate: What to output

    Parameters
    ----------
    input_dim : int
        Dimension of input features.
    hidden_dim : int
        Dimension of hidden state.
    """

    def __init__(self, input_dim: int, hidden_dim: int):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Initialize weights for gates
        scale = 0.1
        # Forget gate
        self.Wf = np.random.randn(hidden_dim, input_dim + hidden_dim) * scale
        self.bf = np.zeros((hidden_dim, 1))
        # Input gate
        self.Wi = np.random.randn(hidden_dim, input_dim + hidden_dim) * scale
        self.bi = np.zeros((hidden_dim, 1))
        # Candidate gate
        self.Wc = np.random.randn(hidden_dim, input_dim + hidden_dim) * scale
        self.bc = np.zeros((hidden_dim, 1))
        # Output gate
        self.Wo = np.random.randn(hidden_dim, input_dim + hidden_dim) * scale
        self.bo = np.zeros((hidden_dim, 1))

    def forward(
        self,
        x: np.ndarray,
        h_prev: np.ndarray,
        c_prev: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass for one LSTM time step.

        Parameters
        ----------
        x : np.ndarray
            Input at current time step, shape (input_dim, 1).
        h_prev : np.ndarray
            Previous hidden state, shape (hidden_dim, 1).
        c_prev : np.ndarray
            Previous cell state, shape (hidden_dim, 1).

        Returns
        -------
        tuple of np.ndarray
            New hidden state and cell state.
        """
        # Concatenate input and previous hidden state
        combined = np.vstack([x.reshape(-1, 1), h_prev])

        # Forget gate
        fg = ActivationFunctions.sigmoid(np.dot(self.Wf, combined) + self.bf)
        # Input gate
        ig = ActivationFunctions.sigmoid(np.dot(self.Wi, combined) + self.bi)
        # Candidate values
        c_candidate = ActivationFunctions.tanh(np.dot(self.Wc, combined) + self.bc)
        # Output gate
        og = ActivationFunctions.sigmoid(np.dot(self.Wo, combined) + self.bo)

        # Update cell state
        c_new = fg * c_prev + ig * c_candidate
        # Compute hidden state
        h_new = og * ActivationFunctions.tanh(c_new)

        return h_new, c_new


class LSTMModel:
    """
    LSTM model for text classification.

    Parameters
    ----------
    vocab_size : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of word embeddings.
    hidden_dim : int
        Dimension of LSTM hidden state.
    num_classes : int
        Number of output classes.
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        hidden_dim: int = 128,
        num_classes: int = 2,
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Embedding layer
        self.embedding = EmbeddingLayer(vocab_size, embedding_dim)

        # LSTM cell
        self.lstm = LSTMCell(embedding_dim, hidden_dim)

        # Output layer
        self.W_out = np.random.randn(num_classes, hidden_dim) * 0.1
        self.b_out = np.zeros((num_classes, 1))

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.

        Parameters
        ----------
        x : np.ndarray
            Input word indices of shape (seq_len,).

        Returns
        -------
        np.ndarray
            Class logits of shape (num_classes,).
        """
        # Embedding lookup
        embedded = self.embedding.forward(x.reshape(1, -1))[0]  # (seq_len, embedding_dim)

        # Initialize hidden and cell states
        h = np.zeros((self.hidden_dim, 1))
        c = np.zeros((self.hidden_dim, 1))

        # Process each time step
        for t in range(len(x)):
            h, c = self.lstm.forward(embedded[t], h, c)

        # Output layer (use final hidden state)
        logits = np.dot(self.W_out, h) + self.b_out

        return logits.flatten()

    def predict(self, x: np.ndarray) -> int:
        """
        Predict class for input.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        int
            Predicted class index.
        """
        logits = self.forward(x)
        return np.argmax(logits)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        np.ndarray
            Class probabilities.
        """
        logits = self.forward(x)
        return ActivationFunctions.softmax(logits)


class BiLSTMAttention:
    """
    Bidirectional LSTM with Attention mechanism.

    The attention mechanism allows the model to focus on important parts
    of the input sequence when making predictions.

    Parameters
    ----------
    vocab_size : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of word embeddings.
    hidden_dim : int
        Dimension of LSTM hidden state.
    num_classes : int
        Number of output classes.
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        hidden_dim: int = 128,
        num_classes: int = 2,
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Embedding layer
        self.embedding = EmbeddingLayer(vocab_size, embedding_dim)

        # Forward LSTM
        self.lstm_forward = LSTMCell(embedding_dim, hidden_dim)
        # Backward LSTM
        self.lstm_backward = LSTMCell(embedding_dim, hidden_dim)

        # Attention parameters
        self.W_attention = np.random.randn(hidden_dim * 2, hidden_dim * 2) * 0.1
        self.v_attention = np.random.randn(hidden_dim * 2, 1) * 0.1

        # Output layer
        self.W_out = np.random.randn(num_classes, hidden_dim * 2) * 0.1
        self.b_out = np.zeros((num_classes, 1))

    def _attention(self, hidden_states: np.ndarray) -> np.ndarray:
        """
        Compute attention weights and context vector.

        Parameters
        ----------
        hidden_states : np.ndarray
            Hidden states of shape (seq_len, hidden_dim * 2).

        Returns
        -------
        np.ndarray
            Context vector of shape (hidden_dim * 2,).
        """
        # Compute attention scores
        scores = np.dot(np.tanh(np.dot(hidden_states, self.W_attention)), self.v_attention)
        scores = scores.flatten()

        # Softmax
        attention_weights = ActivationFunctions.softmax(scores)

        # Weighted sum
        context = np.dot(attention_weights, hidden_states)

        return context

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.

        Parameters
        ----------
        x : np.ndarray
            Input word indices of shape (seq_len,).

        Returns
        -------
        np.ndarray
            Class logits of shape (num_classes,).
        """
        seq_len = len(x)

        # Embedding lookup
        embedded = self.embedding.forward(x.reshape(1, -1))[0]  # (seq_len, embedding_dim)

        # Forward LSTM
        h_forward = np.zeros((self.hidden_dim, 1))
        c_forward = np.zeros((self.hidden_dim, 1))
        forward_states = []

        for t in range(seq_len):
            h_forward, c_forward = self.lstm_forward.forward(embedded[t], h_forward, c_forward)
            forward_states.append(h_forward.flatten())

        # Backward LSTM
        h_backward = np.zeros((self.hidden_dim, 1))
        c_backward = np.zeros((self.hidden_dim, 1))
        backward_states = []

        for t in range(seq_len - 1, -1, -1):
            h_backward, c_backward = self.lstm_backward.forward(embedded[t], h_backward, c_backward)
            backward_states.append(h_backward.flatten())

        backward_states.reverse()

        # Concatenate forward and backward states
        hidden_states = np.column_stack([forward_states, backward_states])  # (seq_len, hidden_dim * 2)

        # Apply attention
        context = self._attention(hidden_states)  # (hidden_dim * 2,)

        # Output layer
        logits = np.dot(self.W_out, context.reshape(-1, 1)) + self.b_out

        return logits.flatten()

    def predict(self, x: np.ndarray) -> int:
        """
        Predict class for input.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        int
            Predicted class index.
        """
        logits = self.forward(x)
        return np.argmax(logits)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        np.ndarray
            Class probabilities.
        """
        logits = self.forward(x)
        return ActivationFunctions.softmax(logits)

    def get_attention_weights(self, x: np.ndarray) -> np.ndarray:
        """
        Get attention weights for visualization.

        Parameters
        ----------
        x : np.ndarray
            Input word indices.

        Returns
        -------
        np.ndarray
            Attention weights for each token.
        """
        seq_len = len(x)

        # Embedding lookup
        embedded = self.embedding.forward(x.reshape(1, -1))[0]

        # Forward LSTM
        h_forward = np.zeros((self.hidden_dim, 1))
        c_forward = np.zeros((self.hidden_dim, 1))
        forward_states = []

        for t in range(seq_len):
            h_forward, c_forward = self.lstm_forward.forward(embedded[t], h_forward, c_forward)
            forward_states.append(h_forward.flatten())

        # Backward LSTM
        h_backward = np.zeros((self.hidden_dim, 1))
        c_backward = np.zeros((self.hidden_dim, 1))
        backward_states = []

        for t in range(seq_len - 1, -1, -1):
            h_backward, c_backward = self.lstm_backward.forward(embedded[t], h_backward, c_backward)
            backward_states.append(h_backward.flatten())

        backward_states.reverse()

        # Concatenate states
        hidden_states = np.column_stack([forward_states, backward_states])

        # Compute attention weights
        scores = np.dot(np.tanh(np.dot(hidden_states, self.W_attention)), self.v_attention)
        scores = scores.flatten()

        return ActivationFunctions.softmax(scores)
