"""神经语言模型模块 - 基于神经网络的语言模型"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple


class ActivationFunction:
    """激活函数集合"""

    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid 激活函数"""
        x = np.clip(x, -500, 500)
        return 1.0 / (1.0 + np.exp(-x))

    @staticmethod
    def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
        """Sigmoid 导数"""
        s = ActivationFunction.sigmoid(x)
        return s * (1 - s)

    @staticmethod
    def tanh(x: np.ndarray) -> np.ndarray:
        """Tanh 激活函数"""
        return np.tanh(x)

    @staticmethod
    def tanh_derivative(x: np.ndarray) -> np.ndarray:
        """Tanh 导数"""
        t = np.tanh(x)
        return 1 - t * t

    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        """Softmax 激活函数"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    @staticmethod
    def relu(x: np.ndarray) -> np.ndarray:
        """ReLU 激活函数"""
        return np.maximum(0, x)

    @staticmethod
    def relu_derivative(x: np.ndarray) -> np.ndarray:
        """ReLU 导数"""
        return (x > 0).astype(float)


class FeedforwardNeuralLM:
    """
    前馈神经网络语言模型 (FFNN LM)

    基于 Bengio et al. (2003) 的经典神经语言模型。

    架构:
        输入层 (N-1 个词的 embedding 拼接)
        → 隐藏层 (tanh)
        → 输出层 (softmax)

    特点:
    - 使用词嵌入 (word embedding) 表示词
    - 通过前 N-1 个词预测下一个词
    - 自动学习词之间的语义关系
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 32,
        hidden_dim: int = 64,
        context_size: int = 2,
        learning_rate: float = 0.01,
    ):
        """
        Args:
            vocab_size: 词汇表大小
            embedding_dim: 词嵌入维度
            hidden_dim: 隐藏层维度
            context_size: 上下文大小 (使用前几个词)
            learning_rate: 学习率
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.context_size = context_size
        self.learning_rate = learning_rate

        # 输入维度 = 上下文大小 * 嵌入维度
        input_dim = context_size * embedding_dim

        # 初始化权重
        scale_emb = np.sqrt(2.0 / vocab_size)
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * scale_emb

        scale_h = np.sqrt(2.0 / input_dim)
        self.W_hidden = np.random.randn(input_dim, hidden_dim) * scale_h
        self.b_hidden = np.zeros(hidden_dim)

        scale_o = np.sqrt(2.0 / hidden_dim)
        self.W_output = np.random.randn(hidden_dim, vocab_size) * scale_o
        self.b_output = np.zeros(vocab_size)

        self._trained = False

    def _forward(self, context_ids: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        前向传播

        Args:
            context_ids: 上下文词 ID 数组，shape (batch_size, context_size)

        Returns:
            (softmax 输出, 中间状态字典)
        """
        batch_size = context_ids.shape[0]

        # 查找嵌入并拼接
        embeddings = self.embeddings[context_ids]  # (batch, context_size, emb_dim)
        x = embeddings.reshape(batch_size, -1)  # (batch, input_dim)

        # 隐藏层
        z_hidden = x @ self.W_hidden + self.b_hidden  # (batch, hidden_dim)
        a_hidden = ActivationFunction.tanh(z_hidden)

        # 输出层
        z_output = a_hidden @ self.W_output + self.b_output  # (batch, vocab_size)
        probs = ActivationFunction.softmax(z_output)

        cache = {
            'x': x,
            'z_hidden': z_hidden,
            'a_hidden': a_hidden,
            'z_output': z_output,
            'probs': probs,
            'context_ids': context_ids,
            'batch_size': batch_size,
        }

        return probs, cache

    def _backward(self, cache: dict, target_ids: np.ndarray) -> float:
        """
        反向传播

        Args:
            cache: 前向传播的中间状态
            target_ids: 目标词 ID，shape (batch_size,)

        Returns:
            损失值 (交叉熵)
        """
        probs = cache['probs']
        a_hidden = cache['a_hidden']
        z_hidden = cache['z_hidden']
        x = cache['x']
        context_ids = cache['context_ids']
        batch_size = cache['batch_size']

        # 交叉熵损失
        eps = 1e-10
        loss = -np.mean(np.log(probs[np.arange(batch_size), target_ids] + eps))

        # 输出层梯度
        d_z_output = probs.copy()
        d_z_output[np.arange(batch_size), target_ids] -= 1
        d_z_output /= batch_size

        d_W_output = a_hidden.T @ d_z_output
        d_b_output = np.sum(d_z_output, axis=0)

        # 隐藏层梯度
        d_a_hidden = d_z_output @ self.W_output.T
        d_z_hidden = d_a_hidden * ActivationFunction.tanh_derivative(z_hidden)

        d_W_hidden = x.T @ d_z_hidden
        d_b_hidden = np.sum(d_z_hidden, axis=0)

        # 嵌入梯度
        d_x = d_z_hidden @ self.W_hidden.T
        d_embeddings = d_x.reshape(batch_size, self.context_size, self.embedding_dim)

        # 更新权重
        self.W_output -= self.learning_rate * d_W_output
        self.b_output -= self.learning_rate * d_b_output
        self.W_hidden -= self.learning_rate * d_W_hidden
        self.b_hidden -= self.learning_rate * d_b_hidden

        # 更新嵌入
        for i in range(batch_size):
            for j in range(self.context_size):
                idx = context_ids[i, j]
                self.embeddings[idx] -= self.learning_rate * d_embeddings[i, j]

        return loss

    def train_step(self, context_ids: np.ndarray, target_ids: np.ndarray) -> float:
        """
        单步训练

        Args:
            context_ids: 上下文词 ID，shape (batch_size, context_size)
            target_ids: 目标词 ID，shape (batch_size,)

        Returns:
            损失值
        """
        probs, cache = self._forward(context_ids)
        loss = self._backward(cache, target_ids)
        self._trained = True
        return loss

    def predict_proba(self, context_ids: np.ndarray) -> np.ndarray:
        """
        预测下一个词的概率分布

        Args:
            context_ids: 上下文词 ID，shape (context_size,) 或 (batch, context_size)

        Returns:
            概率分布，shape (vocab_size,) 或 (batch, vocab_size)
        """
        if context_ids.ndim == 1:
            context_ids = context_ids.reshape(1, -1)
        probs, _ = self._forward(context_ids)
        if probs.shape[0] == 1:
            return probs[0]
        return probs

    def perplexity(self, test_contexts: np.ndarray, test_targets: np.ndarray) -> float:
        """
        计算困惑度

        Args:
            test_contexts: 测试上下文，shape (N, context_size)
            test_targets: 测试目标，shape (N,)

        Returns:
            困惑度
        """
        probs, _ = self._forward(test_contexts)
        eps = 1e-10
        log_probs = np.log(probs[np.arange(len(test_targets)), test_targets] + eps)
        avg_log_prob = np.mean(log_probs)
        return math.exp(-avg_log_prob)

    def get_embedding(self, word_id: int) -> np.ndarray:
        """获取词嵌入向量"""
        return self.embeddings[word_id].copy()

    def __repr__(self) -> str:
        return (
            f"FeedforwardNeuralLM(vocab_size={self.vocab_size}, "
            f"embedding_dim={self.embedding_dim}, "
            f"hidden_dim={self.hidden_dim}, "
            f"context_size={self.context_size})"
        )


class RNNLanguageModel:
    """
    RNN 语言模型

    使用循环神经网络建模序列概率。

    架构:
        输入词嵌入 → RNN 隐藏层 → 输出层 (softmax)

    特点:
    - 理论上可以捕捉任意长度的上下文
    - 参数在时间步之间共享
    - 使用 BPTT (Backpropagation Through Time) 训练
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 32,
        hidden_dim: int = 64,
        learning_rate: float = 0.001,
    ):
        """
        Args:
            vocab_size: 词汇表大小
            embedding_dim: 词嵌入维度
            hidden_dim: RNN 隐藏层维度
            learning_rate: 学习率
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate

        # 词嵌入
        scale_emb = np.sqrt(2.0 / vocab_size)
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * scale_emb

        # RNN 权重
        scale_r = np.sqrt(2.0 / (embedding_dim + hidden_dim))
        self.W_xh = np.random.randn(embedding_dim, hidden_dim) * scale_r
        self.W_hh = np.random.randn(hidden_dim, hidden_dim) * scale_r
        self.b_h = np.zeros(hidden_dim)

        # 输出层
        scale_o = np.sqrt(2.0 / hidden_dim)
        self.W_hy = np.random.randn(hidden_dim, vocab_size) * scale_o
        self.b_y = np.zeros(vocab_size)

        self._trained = False

    def _forward(self, word_ids: List[int], h_prev: np.ndarray) -> Tuple[List, np.ndarray, List]:
        """
        前向传播

        Args:
            word_ids: 输入词 ID 序列
            h_prev: 初始隐藏状态

        Returns:
            (隐藏状态列表, 最终隐藏状态, 输出概率列表)
        """
        hiddens = [h_prev]
        outputs = []
        caches = []

        h = h_prev
        for t, wid in enumerate(word_ids):
            x = self.embeddings[wid]

            # RNN 更新
            z = x @ self.W_xh + h @ self.W_hh + self.b_h
            h = ActivationFunction.tanh(z)

            # 输出层
            y = h @ self.W_hy + self.b_y
            prob = ActivationFunction.softmax(y.reshape(1, -1))[0]

            hiddens.append(h)
            outputs.append(prob)
            caches.append({'x': x, 'z': z, 'h_prev': hiddens[t], 'h': h})

        return caches, h, outputs

    def train_step(
        self,
        word_ids: List[int],
        target_ids: List[int],
        h_prev: Optional[np.ndarray] = None,
    ) -> Tuple[float, np.ndarray]:
        """
        单步训练 (BPTT)

        Args:
            word_ids: 输入词 ID 序列
            target_ids: 目标词 ID 序列
            h_prev: 初始隐藏状态

        Returns:
            (损失值, 最终隐藏状态)
        """
        if h_prev is None:
            h_prev = np.zeros(self.hidden_dim)

        seq_len = len(word_ids)

        # 前向传播
        caches, h_final, outputs = self._forward(word_ids, h_prev)

        # 计算损失
        eps = 1e-10
        loss = 0.0
        for t in range(seq_len):
            loss -= np.log(outputs[t][target_ids[t]] + eps)
        loss /= seq_len

        # 反向传播 (BPTT)
        d_W_xh = np.zeros_like(self.W_xh)
        d_W_hh = np.zeros_like(self.W_hh)
        d_b_h = np.zeros_like(self.b_h)
        d_W_hy = np.zeros_like(self.W_hy)
        d_b_y = np.zeros_like(self.b_y)

        d_h_next = np.zeros(self.hidden_dim)

        for t in reversed(range(seq_len)):
            # 输出层梯度
            d_y = outputs[t].copy()
            d_y[target_ids[t]] -= 1

            d_W_hy += np.outer(caches[t]['h'], d_y)
            d_b_y += d_y

            # 隐藏层梯度
            d_h = d_y @ self.W_hy.T + d_h_next
            d_z = d_h * ActivationFunction.tanh_derivative(caches[t]['z'])

            d_W_xh += np.outer(caches[t]['x'], d_z)
            d_W_hh += np.outer(caches[t]['h_prev'], d_z)
            d_b_h += d_z

            d_h_next = d_z @ self.W_hh.T

        # 梯度裁剪
        for grad in [d_W_xh, d_W_hh, d_W_hy]:
            np.clip(grad, -5, 5, out=grad)

        # 更新权重
        self.W_xh -= self.learning_rate * d_W_xh
        self.W_hh -= self.learning_rate * d_W_hh
        self.b_h -= self.learning_rate * d_b_h
        self.W_hy -= self.learning_rate * d_W_hy
        self.b_y -= self.learning_rate * d_b_y

        # 更新嵌入 (简化版，只更新输入词)
        for t, wid in enumerate(word_ids):
            d_x = (d_W_xh @ self.W_xh.T)[t] if t < len(word_ids) else np.zeros(self.embedding_dim)
            # 简化嵌入更新
            d_emb = np.zeros(self.embedding_dim)
            d_z_t = (self.embeddings[wid] @ self.W_xh + caches[t]['h_prev'] @ self.W_hh + self.b_h)
            d_z_actual = np.tanh(d_z_t)
            # 使用输出梯度的反向传播链
            pass  # 嵌入更新在简化版本中跳过以保持稳定

        self._trained = True
        return loss, h_final

    def predict_proba(
        self,
        word_ids: List[int],
        h_prev: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测序列中每个位置的下一个词概率

        Args:
            word_ids: 输入词 ID 序列
            h_prev: 初始隐藏状态

        Returns:
            (最终位置的输出概率, 最终隐藏状态)
        """
        if h_prev is None:
            h_prev = np.zeros(self.hidden_dim)

        _, h_final, outputs = self._forward(word_ids, h_prev)
        return outputs[-1], h_final

    def __repr__(self) -> str:
        return (
            f"RNNLanguageModel(vocab_size={self.vocab_size}, "
            f"embedding_dim={self.embedding_dim}, "
            f"hidden_dim={self.hidden_dim})"
        )


class LSTMLanguageModel:
    """
    LSTM 语言模型

    使用长短时记忆网络 (LSTM) 建模序列概率。

    架构:
        输入词嵌入 → LSTM 层 → 输出层 (softmax)

    特点:
    - 通过门控机制解决 RNN 的梯度消失问题
    - 能更好地捕捉长距离依赖
    - 有独立的记忆单元 (cell state)
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 32,
        hidden_dim: int = 64,
        learning_rate: float = 0.001,
    ):
        """
        Args:
            vocab_size: 词汇表大小
            embedding_dim: 词嵌入维度
            hidden_dim: LSTM 隐藏层维度
            learning_rate: 学习率
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate

        # 词嵌入
        scale_emb = np.sqrt(2.0 / vocab_size)
        self.embeddings = np.random.randn(vocab_size, embedding_dim) * scale_emb

        # LSTM 权重 (4 个门: 遗忘门 f, 输入门 i, 候选门 g, 输出门 o)
        concat_dim = embedding_dim + hidden_dim
        scale = np.sqrt(2.0 / concat_dim)

        self.W = np.random.randn(concat_dim, 4 * hidden_dim) * scale
        self.b = np.zeros(4 * hidden_dim)
        # 将偏置的遗忘门部分初始化为 1，帮助学习长期依赖
        self.b[hidden_dim:2 * hidden_dim] = 1.0

        # 输出层
        scale_o = np.sqrt(2.0 / hidden_dim)
        self.W_hy = np.random.randn(hidden_dim, vocab_size) * scale_o
        self.b_y = np.zeros(vocab_size)

        self._trained = False

    def _lstm_step(
        self,
        x: np.ndarray,
        h_prev: np.ndarray,
        c_prev: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        单步 LSTM 计算

        Args:
            x: 输入向量 (embedding_dim,)
            h_prev: 上一步隐藏状态 (hidden_dim,)
            c_prev: 上一步记忆状态 (hidden_dim,)

        Returns:
            (新的隐藏状态, 新的记忆状态, 缓存)
        """
        # 拼接输入和上一步隐藏状态
        concat = np.concatenate([x, h_prev])

        # 计算 4 个门
        gates = concat @ self.W + self.b
        h = self.hidden_dim

        f_gate = ActivationFunction.sigmoid(gates[:h])         # 遗忘门
        i_gate = ActivationFunction.sigmoid(gates[h:2*h])      # 输入门
        g_gate = ActivationFunction.tanh(gates[2*h:3*h])       # 候选值
        o_gate = ActivationFunction.sigmoid(gates[3*h:4*h])    # 输出门

        # 更新记忆状态
        c_new = f_gate * c_prev + i_gate * g_gate

        # 计算隐藏状态
        h_new = o_gate * ActivationFunction.tanh(c_new)

        cache = {
            'x': x, 'h_prev': h_prev, 'c_prev': c_prev,
            'concat': concat, 'gates': gates,
            'f_gate': f_gate, 'i_gate': i_gate,
            'g_gate': g_gate, 'o_gate': o_gate,
            'c_new': c_new, 'h_new': h_new,
        }

        return h_new, c_new, cache

    def _forward(
        self,
        word_ids: List[int],
        h_prev: np.ndarray,
        c_prev: np.ndarray,
    ) -> Tuple[List[dict], np.ndarray, np.ndarray, List[np.ndarray]]:
        """
        前向传播

        Args:
            word_ids: 输入词 ID 序列
            h_prev: 初始隐藏状态
            c_prev: 初始记忆状态

        Returns:
            (缓存列表, 最终隐藏状态, 最终记忆状态, 输出概率列表)
        """
        caches = []
        outputs = []

        h = h_prev
        c = c_prev

        for wid in word_ids:
            x = self.embeddings[wid]
            h, c, cache = self._lstm_step(x, h, c)

            # 输出层
            y = h @ self.W_hy + self.b_y
            prob = ActivationFunction.softmax(y.reshape(1, -1))[0]

            caches.append(cache)
            outputs.append(prob)

        return caches, h, c, outputs

    def train_step(
        self,
        word_ids: List[int],
        target_ids: List[int],
        h_prev: Optional[np.ndarray] = None,
        c_prev: Optional[np.ndarray] = None,
    ) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        单步训练 (BPTT for LSTM)

        Args:
            word_ids: 输入词 ID 序列
            target_ids: 目标词 ID 序列
            h_prev: 初始隐藏状态
            c_prev: 初始记忆状态

        Returns:
            (损失值, 最终隐藏状态, 最终记忆状态)
        """
        if h_prev is None:
            h_prev = np.zeros(self.hidden_dim)
        if c_prev is None:
            c_prev = np.zeros(self.hidden_dim)

        seq_len = len(word_ids)

        # 前向传播
        caches, h_final, c_final, outputs = self._forward(word_ids, h_prev, c_prev)

        # 计算损失
        eps = 1e-10
        loss = 0.0
        for t in range(seq_len):
            loss -= np.log(outputs[t][target_ids[t]] + eps)
        loss /= seq_len

        # 反向传播
        d_W = np.zeros_like(self.W)
        d_b = np.zeros_like(self.b)
        d_W_hy = np.zeros_like(self.W_hy)
        d_b_y = np.zeros_like(self.b_y)

        d_h_next = np.zeros(self.hidden_dim)
        d_c_next = np.zeros(self.hidden_dim)

        h_dim = self.hidden_dim

        for t in reversed(range(seq_len)):
            cache = caches[t]

            # 输出层梯度
            d_y = outputs[t].copy()
            d_y[target_ids[t]] -= 1

            d_W_hy += np.outer(cache['h_new'], d_y)
            d_b_y += d_y

            # 隐藏状态梯度
            d_h = d_y @ self.W_hy.T + d_h_next

            # 记忆状态梯度
            d_c = d_h * cache['o_gate'] * ActivationFunction.tanh_derivative(
                ActivationFunction.tanh(cache['c_new'])
            ) + d_c_next

            # 各门梯度
            d_o = d_h * ActivationFunction.tanh(cache['c_new'])
            d_f = d_c * cache['c_prev']
            d_i = d_c * cache['g_gate']
            d_g = d_c * cache['i_gate']

            # 门的输入梯度
            d_gates = np.zeros(4 * h_dim)
            d_gates[:h_dim] = d_f * ActivationFunction.sigmoid_derivative(
                cache['gates'][:h_dim])
            d_gates[h_dim:2*h_dim] = d_i * ActivationFunction.sigmoid_derivative(
                cache['gates'][h_dim:2*h_dim])
            d_gates[2*h_dim:3*h_dim] = d_g * ActivationFunction.tanh_derivative(
                cache['gates'][2*h_dim:3*h_dim])
            d_gates[3*h_dim:4*h_dim] = d_o * ActivationFunction.sigmoid_derivative(
                cache['gates'][3*h_dim:4*h_dim])

            # 权重梯度
            d_W += np.outer(cache['concat'], d_gates)
            d_b += d_gates

            # 传递到上一步
            # d_concat = [d_x, d_h_prev] where d_x has embedding_dim, d_h_prev has hidden_dim
            d_concat = d_gates @ self.W.T
            d_h_next = d_concat[self.embedding_dim:]
            d_c_next = d_c * cache['f_gate']

        # 梯度裁剪
        for grad in [d_W, d_W_hy]:
            np.clip(grad, -5, 5, out=grad)

        # 更新权重
        self.W -= self.learning_rate * d_W
        self.b -= self.learning_rate * d_b
        self.W_hy -= self.learning_rate * d_W_hy
        self.b_y -= self.learning_rate * d_b_y

        self._trained = True
        return loss, h_final, c_final

    def predict_proba(
        self,
        word_ids: List[int],
        h_prev: Optional[np.ndarray] = None,
        c_prev: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        预测序列中每个位置的下一个词概率

        Args:
            word_ids: 输入词 ID 序列
            h_prev: 初始隐藏状态
            c_prev: 初始记忆状态

        Returns:
            (最终位置的输出概率, 最终隐藏状态, 最终记忆状态)
        """
        if h_prev is None:
            h_prev = np.zeros(self.hidden_dim)
        if c_prev is None:
            c_prev = np.zeros(self.hidden_dim)

        _, h_final, c_final, outputs = self._forward(word_ids, h_prev, c_prev)
        return outputs[-1], h_final, c_final

    def perplexity(
        self,
        test_sequences: List[Tuple[List[int], List[int]]],
    ) -> float:
        """
        计算困惑度

        Args:
            test_sequences: [(word_ids, target_ids), ...] 测试序列

        Returns:
            困惑度
        """
        total_log_prob = 0.0
        total_words = 0

        for word_ids, target_ids in test_sequences:
            h = np.zeros(self.hidden_dim)
            c = np.zeros(self.hidden_dim)

            _, _, _, outputs = self._forward(word_ids, h, c)

            for t, tid in enumerate(target_ids):
                prob = outputs[t][tid]
                if prob <= 0:
                    return float('inf')
                total_log_prob += math.log(prob)
                total_words += 1

        if total_words == 0:
            return float('inf')

        return math.exp(-total_log_prob / total_words)

    def __repr__(self) -> str:
        return (
            f"LSTMLanguageModel(vocab_size={self.vocab_size}, "
            f"embedding_dim={self.embedding_dim}, "
            f"hidden_dim={self.hidden_dim})"
        )
