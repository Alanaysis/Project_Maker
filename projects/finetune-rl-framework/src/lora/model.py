"""
LoRA 模型包装器

本模块提供将 LoRA 应用到 Hugging Face Transformers 模型的高级接口。

💡 设计思路:
    - 自动检测模型的注意力层并注入 LoRA
    - 提供简洁的 API 用于训练和推理
    - 支持权重的保存、加载和合并
"""

from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .layer import LoRALinear, inject_lora_layers, count_lora_parameters


class LoRAModel:
    """
    LoRA 模型包装器

    提供将 LoRA 应用到预训练模型的便捷接口

    使用示例:
        model = LoRAModel.from_pretrained(
            "gpt2",
            target_modules=["c_attn", "c_proj"],
            rank=8,
            alpha=16
        )
        # 现在可以像普通模型一样训练
    """

    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        target_modules: list[str],
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0,
    ):
        self.base_model = model
        self.tokenizer = tokenizer
        self.target_modules = target_modules
        self.rank = rank
        self.alpha = alpha
        self.dropout = dropout

        # 注入 LoRA 层
        self.model = inject_lora_layers(
            model, target_modules, rank, alpha, dropout
        )

        # 冻结非 LoRA 参数
        self._setup_training()

    def _setup_training(self):
        """
        设置训练模式

        ⭐ 关键步骤:
        1. 冻结所有参数
        2. 解冻 LoRA 参数
        3. 设置梯度检查点（可选，节省内存）
        """
        # 先冻结所有参数
        for param in self.model.parameters():
            param.requires_grad = False

        # 只解冻 LoRA 参数
        for name, param in self.model.named_parameters():
            if "lora_A" in name or "lora_B" in name:
                param.requires_grad = True

        # 统计参数量
        lora_params, total_params = count_lora_parameters(self.model)
        print(f"LoRA 参数量: {lora_params:,}")
        print(f"总参数量: {total_params:,}")
        print(f"LoRA 参数占比: {lora_params/total_params*100:.2f}%")

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        target_modules: list[str],
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0,
        device: str = "auto",
    ) -> "LoRAModel":
        """
        从预训练模型创建 LoRA 模型

        Args:
            model_name: Hugging Face 模型名称或路径
            target_modules: 要注入 LoRA 的模块名称列表
            rank: LoRA 秩
            alpha: LoRA 缩放因子
            dropout: Dropout 概率
            device: 设备 ("auto", "cpu", "cuda")

        Returns:
            LoRAModel 实例
        """
        # 加载分词器
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # 加载模型
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # 设备设置
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)

        return cls(model, tokenizer, target_modules, rank, alpha, dropout)

    def forward(self, **kwargs):
        """前向传播"""
        return self.model(**kwargs)

    def generate(self, **kwargs):
        """生成文本"""
        return self.model.generate(**kwargs)

    def parameters(self):
        """获取可训练参数（仅 LoRA 参数）"""
        return [p for p in self.model.parameters() if p.requires_grad]

    def named_parameters(self):
        """获取可训练参数名称和值"""
        return [
            (n, p) for n, p in self.model.named_parameters()
            if p.requires_grad
        ]

    def save_lora_weights(self, path: str):
        """
        保存 LoRA 权重

        只保存 LoRA 的 A 和 B 矩阵，不保存基础模型权重
        这使得保存的文件很小（通常几 MB）
        """
        lora_state_dict = {}
        for name, param in self.model.named_parameters():
            if "lora_A" in name or "lora_B" in name:
                lora_state_dict[name] = param.data.clone()

        torch.save({
            "lora_state_dict": lora_state_dict,
            "rank": self.rank,
            "alpha": self.alpha,
            "target_modules": self.target_modules,
        }, path)
        print(f"LoRA 权重已保存到: {path}")

    def load_lora_weights(self, path: str):
        """
        加载 LoRA 权重

        从文件加载 LoRA 的 A 和 B 矩阵
        """
        checkpoint = torch.load(path, map_location="cpu")
        lora_state_dict = checkpoint["lora_state_dict"]

        model_state_dict = self.model.state_dict()
        model_state_dict.update(lora_state_dict)
        self.model.load_state_dict(model_state_dict)

        print(f"LoRA 权重已从 {path} 加载")

    def merge_and_save(self, path: str):
        """
        合并 LoRA 权重到基础模型并保存

        合并后的模型可以像普通模型一样加载和推理
        不需要额外的 LoRA 计算
        """
        # 合并所有 LoRA 层
        for module in self.model.modules():
            if isinstance(module, LoRALinear):
                module.merge()

        # 保存完整模型
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        print(f"合并后的模型已保存到: {path}")
