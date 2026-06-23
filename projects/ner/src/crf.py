"""
条件随机场 (CRF) 层
===================

实现 CRF 的核心算法:
1. 前向算法 (Forward Algorithm) - 计算配分函数 Z(x)
2. 维特比算法 (Viterbi Algorithm) - 解码最优标签序列
3. 损失计算 - 负对数似然

CRF 的核心思想:
- 在序列标注中，当前标签不仅依赖于输入特征，还依赖于相邻标签
- CRF 通过转移矩阵建模标签之间的依赖关系

数学公式:
- P(y|x) = exp(Score(x,y)) / Z(x)
- Score(x,y) = sum(emission_scores) + sum(transition_scores)
- Z(x) = sum over all possible y of exp(Score(x,y))
"""

import torch
import torch.nn as nn


class CRF(nn.Module):
    """
    条件随机场 (CRF) 层

    参数:
        num_tags: 标签数量
        batch_first: 输入是否为 batch_first 格式 (batch, seq_len, num_tags)
    """

    def __init__(self, num_tags: int, batch_first: bool = True):
        super().__init__()
        self.num_tags = num_tags
        self.batch_first = batch_first

        # 转移矩阵: transitions[i][j] 表示从标签 j 转移到标签 i 的分数
        # 注意: 这里使用 column-major 方式，transitions[i][j] = score(j -> i)
        self.transitions = nn.Parameter(torch.randn(num_tags, num_tags))

        # START 和 END 标签的转移分数
        self.start_transitions = nn.Parameter(torch.randn(num_tags))
        self.end_transitions = nn.Parameter(torch.randn(num_tags))

        self._initialize_parameters()

    def _initialize_parameters(self):
        """初始化参数，使用均匀分布"""
        nn.init.uniform_(self.transitions, -0.1, 0.1)
        nn.init.uniform_(self.start_transitions, -0.1, 0.1)
        nn.init.uniform_(self.end_transitions, -0.1, 0.1)

    def forward(self, emissions: torch.Tensor, tags: torch.Tensor,
                mask: torch.Tensor = None) -> torch.Tensor:
        """
        计算负对数似然损失

        参数:
            emissions: 发射分数 (batch, seq_len, num_tags)
            tags: 真实标签 (batch, seq_len)
            mask: 掩码 (batch, seq_len)，1 表示有效，0 表示填充

        返回:
            loss: 平均负对数似然损失
        """
        if not self.batch_first:
            emissions = emissions.transpose(0, 1)
            tags = tags.transpose(0, 1)
            if mask is not None:
                mask = mask.transpose(0, 1)

        if mask is None:
            mask = torch.ones_like(tags, dtype=torch.float32)

        # 计算真实路径的分数
        numerator = self._compute_score(emissions, tags, mask)
        # 计算配分函数 (所有路径的分数)
        denominator = self._compute_log_partition(emissions, mask)
        # 负对数似然损失
        loss = (denominator - numerator).mean()
        return loss

    def decode(self, emissions: torch.Tensor,
               mask: torch.Tensor = None) -> list:
        """
        维特比解码 - 找到最优标签序列

        参数:
            emissions: 发射分数 (batch, seq_len, num_tags)
            mask: 掩码 (batch, seq_len)

        返回:
            best_tags_list: 最优标签序列列表
        """
        if not self.batch_first:
            emissions = emissions.transpose(0, 1)
            if mask is not None:
                mask = mask.transpose(0, 1)

        if mask is None:
            mask = torch.ones(emissions.shape[:2], dtype=torch.float32,
                              device=emissions.device)

        return self._viterbi_decode(emissions, mask)

    def _compute_score(self, emissions: torch.Tensor, tags: torch.Tensor,
                       mask: torch.Tensor) -> torch.Tensor:
        """
        计算真实路径的分数

        Score(x, y) = start_transitions[y_0] +
                      sum(emission[i][y_i]) +
                      sum(transition[y_i][y_{i-1}]) +
                      end_transitions[y_last]
        """
        batch_size, seq_len, _ = emissions.shape

        # 起始转移分数
        score = self.start_transitions[tags[:, 0]]
        # 第一个位置的发射分数
        score += emissions[torch.arange(batch_size), 0, tags[:, 0]]

        for i in range(1, seq_len):
            # 发射分数
            score += emissions[torch.arange(batch_size), i, tags[:, i]] * mask[:, i]
            # 转移分数: from tags[:, i-1] to tags[:, i]
            score += self.transitions[tags[:, i], tags[:, i-1]] * mask[:, i]

        # 找到每个序列的最后一个有效位置
        seq_lengths = mask.sum(dim=1).long() - 1
        last_tags = tags[torch.arange(batch_size), seq_lengths]
        # 结束转移分数
        score += self.end_transitions[last_tags]

        return score

    def _compute_log_partition(self, emissions: torch.Tensor,
                               mask: torch.Tensor) -> torch.Tensor:
        """
        前向算法计算配分函数 Z(x)

        alpha[i][j] = log(sum over all paths ending in tag j at position i)
        """
        batch_size, seq_len, num_tags = emissions.shape

        # 初始化: alpha[j] = start_transitions[j] + emission[0][j]
        alpha = self.start_transitions + emissions[:, 0]  # (batch, num_tags)

        for i in range(1, seq_len):
            # alpha[b, j] = log(sum_i exp(alpha[b, i] + transitions[j, i] + emission[b, j]))
            # 使用 log-sum-exp 避免数值溢出
            emit_score = emissions[:, i].unsqueeze(2)  # (batch, num_tags, 1)
            trans_score = self.transitions.unsqueeze(0)  # (1, num_tags, num_tags)
            alpha_expand = alpha.unsqueeze(1)  # (batch, 1, num_tags)

            # (batch, num_tags, num_tags)
            scores = alpha_expand + trans_score + emit_score
            # log-sum-exp over previous tags (dim=2)
            new_alpha = torch.logsumexp(scores, dim=2)  # (batch, num_tags)

            # 应用掩码
            mask_i = mask[:, i].unsqueeze(1)
            alpha = new_alpha * mask_i + alpha * (1 - mask_i)

        # 加上结束转移分数
        alpha += self.end_transitions
        # log-sum-exp over all final tags
        return torch.logsumexp(alpha, dim=1)  # (batch,)

    def _viterbi_decode(self, emissions: torch.Tensor,
                        mask: torch.Tensor) -> list:
        """
        维特比算法解码最优路径

        维护:
        - score[b, j] = 到达位置 i 标签 j 的最优路径分数
        - history[b, i, j] = 位置 i 标签 j 的最优前驱标签
        """
        batch_size, seq_len, num_tags = emissions.shape

        # 初始化
        score = self.start_transitions + emissions[:, 0]  # (batch, num_tags)
        history = []

        for i in range(1, seq_len):
            # score[b, i] + transitions[j, i] + emission[b, j]
            broadcast_score = score.unsqueeze(2)  # (batch, num_tags, 1)
            broadcast_emit = emissions[:, i].unsqueeze(1)  # (batch, 1, num_tags)
            next_score = broadcast_score + self.transitions + broadcast_emit
            # (batch, num_tags, num_tags) -> 取最优前驱
            next_score, indices = next_score.max(dim=1)  # (batch, num_tags)

            mask_i = mask[:, i].unsqueeze(1)
            score = next_score * mask_i + score * (1 - mask_i)
            history.append(indices)

        # 加上结束转移分数
        score += self.end_transitions

        # 回溯
        seq_lengths = mask.sum(dim=1).long() - 1
        best_tags_list = []

        for b in range(batch_size):
            seq_len_b = seq_lengths[b].item()
            # 找到最后位置的最优标签
            _, best_last_tag = score[b].max(dim=0)
            best_tags = [best_last_tag.item()]

            # 回溯
            for hist in reversed(history[:seq_len_b]):
                best_last_tag = hist[b][best_last_tag]
                best_tags.append(best_last_tag.item())

            best_tags.reverse()
            best_tags_list.append(best_tags)

        return best_tags_list
