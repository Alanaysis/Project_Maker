"""
LSTM Decoder - LSTM 文本解码器

使用 LSTM 循环神经网络作为文本解码器，在注意力机制的辅助下，
逐词生成图像描述。

解码流程（每个时间步）：
1. 当前词嵌入 + 上一步的上下文向量 -> LSTM 输入
2. LSTM 更新隐藏状态
3. 利用注意力机制计算新的上下文向量
4. 隐藏状态 + 上下文向量 -> 预测下一个词的概率分布

数学表示：
    input_t = [embedding(word_t), context_{t-1}]
    h_t, c_t = LSTM(input_t, (h_{t-1}, c_{t-1}))
    context_t, alpha_t = Attention(encoder_out, h_t)
    prediction = fc(h_t + context_t)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .attention import Attention


class LSTMDecoder(nn.Module):
    """LSTM 解码器，结合注意力机制生成图像描述。

    使用 LSTM 作为序列生成器，在每个时间步：
    - 接收词嵌入和上下文向量
    - 更新隐藏状态
    - 通过注意力机制关注图像不同区域
    - 输出下一个词的概率分布
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 256,
        hidden_dim: int = 512,
        encoder_dim: int = 256,
        attention_dim: int = 256,
        num_layers: int = 1,
        dropout: float = 0.5,
        attention_type: str = "bahdanau",
    ):
        """初始化 LSTM 解码器。

        Args:
            vocab_size: 词汇表大小
            embed_dim: 词嵌入维度
            hidden_dim: LSTM 隐藏状态维度
            encoder_dim: 编码器输出特征维度
            attention_dim: 注意力计算维度
            num_layers: LSTM 层数
            dropout: Dropout 比率
            attention_type: 注意力类型，"bahdanau" 或 "scaled_dot"
        """
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.encoder_dim = encoder_dim
        self.num_layers = num_layers

        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # 注意力机制
        if attention_type == "scaled_dot":
            from .attention import ScaledDotProductAttention
            self.attention = ScaledDotProductAttention(encoder_dim, hidden_dim, attention_dim)
        else:
            self.attention = Attention(encoder_dim, hidden_dim, attention_dim)

        # LSTM 单元
        # 输入维度 = embed_dim + encoder_dim（嵌入 + 上下文向量）
        self.lstm = nn.LSTMCell(
            embed_dim + encoder_dim, hidden_dim, bias=True
        )

        # 初始化 LSTM 隐藏状态的线性层
        # 从编码器特征的平均值映射到 LSTM 初始隐藏状态
        self.init_h = nn.Linear(encoder_dim, hidden_dim)
        self.init_c = nn.Linear(encoder_dim, hidden_dim)

        # 输出层：将 LSTM 状态和上下文向量映射到词汇表概率
        self.f_beta = nn.Linear(hidden_dim, encoder_dim)  # 门控机制
        self.fc_out = nn.Linear(hidden_dim + encoder_dim, vocab_size)

        self.dropout = nn.Dropout(dropout)
        self.sigmoid = nn.Sigmoid()
        self.relu = nn.ReLU()

    def init_hidden_state(self, encoder_out: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """从编码器特征初始化 LSTM 隐藏状态。

        使用编码器输出的平均值来初始化 h_0 和 c_0。

        Args:
            encoder_out: 编码器输出 (batch_size, num_pixels, encoder_dim)

        Returns:
            h_0: 初始隐藏状态 (batch_size, hidden_dim)
            c_0: 初始细胞状态 (batch_size, hidden_dim)
        """
        # 对编码器输出取平均: (batch_size, encoder_dim)
        mean_encoder_out = encoder_out.mean(dim=1)
        h = self.init_h(mean_encoder_out)  # (batch_size, hidden_dim)
        c = self.init_c(mean_encoder_out)  # (batch_size, hidden_dim)
        return self.relu(h), self.relu(c)

    def forward(
        self,
        encoder_out: torch.Tensor,
        captions: torch.Tensor,
        caption_lengths: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """训练阶段前向传播：使用 Teacher Forcing 生成描述。

        Args:
            encoder_out: 编码器输出特征 (batch_size, num_pixels, encoder_dim)
            captions: 目标描述序列 (batch_size, max_caption_length)
            caption_lengths: 每个描述的实际长度 (batch_size,)

        Returns:
            predictions: 预测的词概率分布 (batch_size, max_caption_length, vocab_size)
            attention_weights: 注意力权重 (batch_size, max_caption_length, num_pixels)
        """
        batch_size = encoder_out.size(0)
        num_pixels = encoder_out.size(1)
        vocab_size = self.vocab_size

        # 初始化隐藏状态
        h, c = self.init_hidden_state(encoder_out)

        # 不需要预测 <end> 之后的词，所以序列长度减1
        decode_lengths = (caption_lengths - 1).tolist()

        # 创建输出张量
        predictions = torch.zeros(batch_size, max(decode_lengths), vocab_size).to(encoder_out.device)
        attention_weights = torch.zeros(batch_size, max(decode_lengths), num_pixels).to(encoder_out.device)

        # Teacher Forcing：依次输入每个时间步的真实词
        for t in range(max(decode_lengths)):
            # 当前时间步需要处理的样本（长度 >= t+1 的）
            batch_size_t = sum([l > t for l in decode_lengths])

            # 当前词的嵌入 + 上一步的上下文向量
            if t == 0:
                # 第一步没有上下文，用零向量
                context = torch.zeros(batch_size_t, self.encoder_dim).to(encoder_out.device)
            else:
                context = prev_context[:batch_size_t]

            # 词嵌入
            embeddings = self.embedding(captions[:batch_size_t, t])  # (batch_t, embed_dim)

            # 拼接嵌入和上下文作为 LSTM 输入
            lstm_input = torch.cat([embeddings, context], dim=1)  # (batch_t, embed_dim + encoder_dim)

            # LSTM 更新
            h, c = self.lstm(
                lstm_input,
                (h[:batch_size_t], c[:batch_size_t])
            )

            # 注意力计算
            context, attn_weights = self.attention(
                encoder_out[:batch_size_t], h
            )

            # 门控机制：选择性地使用上下文信息
            gate = self.sigmoid(self.f_beta(h))
            context = gate * context

            # 预测下一个词（拼接隐藏状态和上下文）
            preds = self.fc_out(self.dropout(torch.cat([h, context], dim=1)))  # (batch_t, vocab_size)

            predictions[:batch_size_t, t] = preds
            attention_weights[:batch_size_t, t, :attn_weights.size(-1)] = attn_weights

            prev_context = context

        return predictions, attention_weights

    def generate(
        self,
        encoder_out: torch.Tensor,
        max_length: int = 50,
        start_idx: int = 1,
        end_idx: int = 2,
        temperature: float = 1.0,
        beam_size: int = 1,
    ) -> list[list[int]]:
        """推理阶段：使用贪心搜索或束搜索生成描述。

        Args:
            encoder_out: 编码器输出特征 (batch_size, num_pixels, encoder_dim)
            max_length: 最大生成长度
            start_idx: 起始标记索引
            end_idx: 结束标记索引
            temperature: 温度参数，控制生成多样性
            beam_size: 束搜索宽度，1 表示贪心搜索

        Returns:
            每个样本生成的词索引列表
        """
        batch_size = encoder_out.size(0)

        if beam_size > 1:
            return self._beam_search(encoder_out, max_length, start_idx, end_idx, beam_size)

        # 贪心搜索
        h, c = self.init_hidden_state(encoder_out)
        context = torch.zeros(batch_size, self.encoder_dim).to(encoder_out.device)

        # 起始标记
        input_word = torch.full((batch_size,), start_idx, dtype=torch.long).to(encoder_out.device)

        generated = [[] for _ in range(batch_size)]
        finished = [False] * batch_size

        for _ in range(max_length):
            embeddings = self.embedding(input_word)
            lstm_input = torch.cat([embeddings, context], dim=1)

            h, c = self.lstm(lstm_input, (h, c))
            context, _ = self.attention(encoder_out, h)

            gate = self.sigmoid(self.f_beta(h))
            context = gate * context

            preds = self.fc_out(torch.cat([h, context], dim=1))

            if temperature != 1.0:
                preds = preds / temperature

            # 贪心选择
            predicted = preds.argmax(dim=-1)  # (batch_size,)

            for i in range(batch_size):
                if not finished[i]:
                    word_idx = predicted[i].item()
                    if word_idx == end_idx:
                        finished[i] = True
                    else:
                        generated[i].append(word_idx)

            if all(finished):
                break

            input_word = predicted

        return generated

    def _beam_search(
        self,
        encoder_out: torch.Tensor,
        max_length: int,
        start_idx: int,
        end_idx: int,
        beam_size: int,
    ) -> list[list[int]]:
        """束搜索解码。

        Args:
            encoder_out: 编码器输出 (1, num_pixels, encoder_dim) - 束搜索通常处理单个样本
            max_length: 最大生成长度
            start_idx: 起始标记索引
            end_idx: 结束标记索引
            beam_size: 束宽度

        Returns:
            最佳生成序列
        """
        # 束搜索只处理单个样本
        encoder_out = encoder_out[:1]  # (1, num_pixels, encoder_dim)

        h, c = self.init_hidden_state(encoder_out)
        context = torch.zeros(1, self.encoder_dim).to(encoder_out.device)

        # 扩展为 beam_size 个候选
        h = h.expand(beam_size, -1)
        c = c.expand(beam_size, -1)
        context = context.expand(beam_size, -1)
        encoder_out = encoder_out.expand(beam_size, -1, -1)

        # 初始化：每个 beam 都从 <start> 开始
        input_word = torch.full((beam_size,), start_idx, dtype=torch.long).to(encoder_out.device)

        # 存储：(累积对数概率, 序列, 是否结束)
        sequences = [([start_idx], 0.0, False)]

        for _ in range(max_length):
            all_candidates = []

            for seq_idx, (seq, score, done) in enumerate(sequences):
                if done:
                    all_candidates.append((seq, score, True))
                    continue

                embeddings = self.embedding(
                    torch.tensor([seq[-1]], dtype=torch.long).to(encoder_out.device)
                )
                context_i = context[seq_idx:seq_idx+1]
                h_i = h[seq_idx:seq_idx+1]
                c_i = c[seq_idx:seq_idx+1]

                lstm_input = torch.cat([embeddings, context_i], dim=1)
                h_new, c_new = self.lstm(lstm_input, (h_i, c_i))
                context_new, _ = self.attention(encoder_out[:1], h_new)
                gate = self.sigmoid(self.f_beta(h_new))
                context_new = gate * context_new

                preds = F.log_softmax(self.fc_out(torch.cat([h_new, context_new], dim=1)), dim=-1)
                topk_scores, topk_indices = preds.topk(beam_size, dim=-1)

                for k in range(beam_size):
                    word_idx = topk_indices[0, k].item()
                    new_score = score + topk_scores[0, k].item()
                    new_seq = seq + [word_idx]
                    new_done = word_idx == end_idx
                    all_candidates.append((new_seq, new_score, new_done))

            # 选择得分最高的 beam_size 个候选
            all_candidates.sort(key=lambda x: x[1], reverse=True)
            sequences = all_candidates[:beam_size]

            # 更新 h, c, context for the selected beams
            if not all(done for _, _, done in sequences):
                # 简化处理：仅返回最佳序列
                break

        # 返回最佳序列（去除 <start> 标记）
        best_seq = sequences[0][0][1:]  # 去掉 <start>
        # 去除 <end> 标记
        if end_idx in best_seq:
            best_seq = best_seq[:best_seq.index(end_idx)]
        return [best_seq]
