"""
LoRA (Low-Rank Adaptation) 层实现

⭐ 核心知识点:
LoRA 的核心思想是将权重更新 ΔW 分解为两个低秩矩阵的乘积:
    W' = W + ΔW = W + (α/r) * B @ A

其中:
    - W ∈ R^{d×k} 是原始权重（冻结）
    - A ∈ R^{r×k} 是降维矩阵（可训练）
    - B ∈ R^{d×r} 是升维矩阵（可训练）
    - r << min(d, k) 是低秩维度
    - α 是缩放因子

💡 为什么 LoRA 有效?
    - 预训练模型的权重更新矩阵通常具有低秩特性
    - 即微调时的有效更新集中在低秩子空间中
    - 这意味着我们可以用远少的参数来近似全参数更新

参考论文: "LoRA: Low-Rank Adaptation of Large Language Models" (Hu et al., 2021)
"""

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class LoRALinear(nn.Module):
    """
    LoRA 低秩适配线性层

    ⭐ 实现要点:
    1. 原始权重 W 被冻结，不参与梯度更新
    2. 添加两个可训练的低秩矩阵 A 和 B
    3. 前向传播: output = Wx + (α/r) * BAx
    4. 初始化: A 使用 Kaiming 均匀分布，B 使用零初始化
       - 零初始化 B 确保训练开始时 ΔW = BA = 0
       - 这意味着模型初始行为与原始模型完全一致

    Args:
        in_features: 输入维度
        out_features: 输出维度
        rank: 低秩维度 r，典型值 4/8/16/32/64
        alpha: 缩放因子 α，控制 LoRA 更新的幅度
        dropout: Dropout 概率
        merge_weights: 是否在推理时合并权重
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0,
        merge_weights: bool = False,
    ):
        super().__init__()

        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.merge_weights = merge_weights

        # ⭐ 缩放因子: scaling = α / r
        # 这个设计确保不同 rank 下 LoRA 更新的幅度大致一致
        # 当 rank 增大时，α/r 减小，避免更新过大
        self.scaling = alpha / rank

        # 原始线性层的权重（冻结）
        # 这是预训练模型的权重，不参与梯度更新
        self.linear = nn.Linear(in_features, out_features, bias=True)

        # LoRA 低秩矩阵 A: 降维矩阵
        # shape: (in_features, rank) -> 将输入从 d 维降到 r 维
        self.lora_A = nn.Parameter(torch.empty(in_features, rank))

        # LoRA 低秩矩阵 B: 升维矩阵
        # shape: (rank, out_features) -> 将 r 维映射回 k 维
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))

        # Dropout 层（可选）
        self.lora_dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # ⭐ 初始化策略
        # A 使用 Kaiming 均匀分布: 确保梯度在合理范围内
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        # B 使用零初始化: 确保初始时 ΔW = BA = 0
        nn.init.zeros_(self.lora_B)

        # 标记哪些参数需要梯度
        self._freeze_base_weights()

    def _freeze_base_weights(self):
        """冻结基础模型的权重"""
        # 基础权重不参与梯度更新
        self.linear.weight.requires_grad = False
        if self.linear.bias is not None:
            self.linear.bias.requires_grad = False

    def merge(self):
        """
        将 LoRA 权重合并到基础权重中

        合并后: W' = W + (α/r) * B @ A
        合并后模型可以像普通模型一样推理，无需额外计算
        """
        if not self.merged:
            # 计算 ΔW = (α/r) * B @ A
            delta_w = (self.lora_B @ self.lora_A.T) * self.scaling
            # 合并到基础权重
            self.linear.weight.data += delta_w.T
            self.merged = True

    def unmerge(self):
        """
        从基础权重中移除 LoRA 权重

        W = W' - (α/r) * B @ A
        """
        if self.merged:
            delta_w = (self.lora_B @ self.lora_A.T) * self.scaling
            self.linear.weight.data -= delta_w.T
            self.merged = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        ⭐ 数学公式:
            output = Wx + (α/r) * dropout(x) @ A @ B

        计算步骤:
            1. 基础线性变换: base = Wx
            2. LoRA 分支: lora = (α/r) * dropout(x) @ A @ B
            3. 最终输出: output = base + lora

        Args:
            x: 输入张量, shape (batch, seq_len, in_features)

        Returns:
            输出张量, shape (batch, seq_len, out_features)
        """
        # 基础线性变换 (权重冻结)
        base_output = self.linear(x)

        # LoRA 分支
        lora_output = self.lora_dropout(x)       # Dropout
        lora_output = lora_output @ self.lora_A  # 降维: (batch, seq, in) -> (batch, seq, rank)
        lora_output = lora_output @ self.lora_B  # 升维: (batch, seq, rank) -> (batch, seq, out)
        lora_output = lora_output * self.scaling # 缩放: 乘以 α/r

        return base_output + lora_output

    def extra_repr(self) -> str:
        return (
            f"in_features={self.in_features}, "
            f"out_features={self.out_features}, "
            f"rank={self.rank}, "
            f"alpha={self.alpha}, "
            f"scaling={self.scaling:.4f}"
        )


def inject_lora_layers(
    model: nn.Module,
    target_modules: list[str],
    rank: int = 8,
    alpha: float = 16.0,
    dropout: float = 0.0,
) -> nn.Module:
    """
    将 LoRA 层注入到模型的目标模块中

    ⭐ 这是 LoRA 应用到 Transformer 模型的关键步骤

    通常注入到注意力层的 Q/K/V/O 投影层:
    - q_proj: Query 投影
    - k_proj: Key 投影
    - v_proj: Value 投影
    - o_proj: 输出投影

    Args:
        model: 原始模型
        target_modules: 要注入 LoRA 的模块名称列表
        rank: LoRA 秩
        alpha: LoRA 缩放因子
        dropout: Dropout 概率

    Returns:
        注入 LoRA 后的模型
    """
    lora_layers = {}

    for name, module in model.named_modules():
        # 检查模块名称是否在目标列表中
        if any(target in name for target in target_modules):
            if isinstance(module, nn.Linear):
                # 创建 LoRA 层
                lora_layer = LoRALinear(
                    in_features=module.in_features,
                    out_features=module.out_features,
                    rank=rank,
                    alpha=alpha,
                    dropout=dropout,
                )
                # 复制原始权重
                lora_layer.linear.weight.data = module.weight.data.clone()
                if module.bias is not None:
                    lora_layer.linear.bias.data = module.bias.data.clone()

                lora_layers[name] = lora_layer

    # 替换模型中的模块
    for name, lora_layer in lora_layers.items():
        # 获取父模块和子模块名
        parts = name.split(".")
        parent = model
        for part in parts[:-1]:
            parent = getattr(parent, part)
        setattr(parent, parts[-1], lora_layer)

    return model


def count_lora_parameters(model: nn.Module) -> tuple[int, int]:
    """
    统计 LoRA 参数量和总参数量

    Args:
        model: 模型

    Returns:
        (lora_params, total_params): LoRA 参数量和总参数量
    """
    lora_params = 0
    total_params = 0

    for name, param in model.named_parameters():
        if "lora_A" in name or "lora_B" in name:
            lora_params += param.numel()
        total_params += param.numel()

    return lora_params, total_params
