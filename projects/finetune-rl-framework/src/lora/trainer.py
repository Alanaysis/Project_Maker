"""
LoRA 训练器

本模块实现 LoRA 微调的训练循环。

⭐ 训练流程:
    1. 加载预训练模型并注入 LoRA 层
    2. 冻结基础模型参数，只训练 LoRA 参数
    3. 使用标准的交叉熵损失进行训练
    4. 保存训练后的 LoRA 权重

💡 与全参数微调的区别:
    - 只有 LoRA 的 A 和 B 矩阵参与梯度更新
    - 梯度计算量大幅减少
    - 优化器状态也相应减少
"""

import os
from typing import Optional, Dict, List
from dataclasses import dataclass, field

import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

from .model import LoRAModel


@dataclass
class LoRAConfig:
    """LoRA 训练配置"""

    # LoRA 参数
    rank: int = 8                           # 低秩维度
    alpha: float = 16.0                     # 缩放因子
    dropout: float = 0.05                   # Dropout 概率
    target_modules: List[str] = field(      # 目标模块
        default_factory=lambda: ["c_attn", "c_proj"]
    )

    # 训练参数
    learning_rate: float = 2e-4             # 学习率
    num_epochs: int = 3                     # 训练轮数
    batch_size: int = 4                     # 批大小
    gradient_accumulation_steps: int = 1    # 梯度累积步数
    max_grad_norm: float = 1.0             # 梯度裁剪
    warmup_steps: int = 100                # 预热步数
    weight_decay: float = 0.01             # 权重衰减

    # 其他
    output_dir: str = "./lora_output"      # 输出目录
    logging_steps: int = 10                # 日志间隔
    eval_steps: int = 100                  # 评估间隔
    save_steps: int = 500                  # 保存间隔
    use_amp: bool = True                   # 混合精度训练
    device: str = "auto"                   # 设备


class LoRATrainer:
    """
    LoRA 训练器

    实现标准的监督微调（SFT）训练循环

    使用示例:
        config = LoRAConfig(
            rank=8,
            learning_rate=2e-4,
            num_epochs=3
        )
        trainer = LoRATrainer(config)
        trainer.train(train_dataset, eval_dataset)
    """

    def __init__(self, config: LoRAConfig):
        self.config = config

        # 设备设置
        if config.device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        else:
            self.device = torch.device(config.device)

        # 模型和优化器（延迟初始化）
        self.model = None
        self.optimizer = None
        self.scaler = GradScaler(enabled=config.use_amp)

        # 训练状态
        self.global_step = 0
        self.best_eval_loss = float("inf")

    def setup_model(self, model_name: str):
        """
        设置模型

        Args:
            model_name: 预训练模型名称或路径
        """
        print(f"加载模型: {model_name}")

        self.model = LoRAModel.from_pretrained(
            model_name=model_name,
            target_modules=self.config.target_modules,
            rank=self.config.rank,
            alpha=self.config.alpha,
            dropout=self.config.dropout,
            device=str(self.device),
        )

        # 设置优化器
        # ⭐ 只对 LoRA 参数进行优化
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

        print("模型设置完成")

    def train(
        self,
        train_dataset,
        eval_dataset=None,
        model_name: str = "gpt2",
    ) -> Dict[str, list]:
        """
        执行训练

        Args:
            train_dataset: 训练数据集
            eval_dataset: 评估数据集（可选）
            model_name: 预训练模型名称

        Returns:
            训练历史记录
        """
        # 初始化模型
        if self.model is None:
            self.setup_model(model_name)

        # 创建数据加载器
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            collate_fn=self._collate_fn,
        )

        # 训练历史
        history = {
            "train_loss": [],
            "eval_loss": [],
            "learning_rate": [],
        }

        # 训练循环
        print(f"\n开始训练，共 {self.config.num_epochs} 个 epoch")
        print("=" * 60)

        for epoch in range(self.config.num_epochs):
            print(f"\nEpoch {epoch + 1}/{self.config.num_epochs}")
            print("-" * 40)

            # 训练一个 epoch
            epoch_loss = self._train_epoch(train_loader, epoch)
            history["train_loss"].append(epoch_loss)

            # 评估
            if eval_dataset is not None:
                eval_loss = self.evaluate(eval_dataset)
                history["eval_loss"].append(eval_loss)
                print(f"  评估损失: {eval_loss:.4f}")

                # 保存最佳模型
                if eval_loss < self.best_eval_loss:
                    self.best_eval_loss = eval_loss
                    self.save(os.path.join(self.config.output_dir, "best"))

        print("\n" + "=" * 60)
        print("训练完成!")

        return history

    def _train_epoch(self, train_loader: DataLoader, epoch: int) -> float:
        """
        训练一个 epoch

        ⭐ 训练步骤:
            1. 前向传播
            2. 计算损失
            3. 反向传播
            4. 梯度裁剪
            5. 参数更新
        """
        self.model.model.train()
        total_loss = 0
        num_steps = 0

        progress_bar = tqdm(
            train_loader,
            desc=f"Training Epoch {epoch + 1}",
            leave=False,
        )

        for step, batch in enumerate(progress_bar):
            # 将数据移到设备
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # 混合精度训练
            with autocast(enabled=self.config.use_amp):
                # 前向传播
                outputs = self.model.forward(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                )
                loss = outputs.loss

                # 梯度累积
                loss = loss / self.config.gradient_accumulation_steps

            # 反向传播
            self.scaler.scale(loss).backward()

            # 梯度累积
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                # 梯度裁剪
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config.max_grad_norm,
                )

                # 参数更新
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.optimizer.zero_grad()

                self.global_step += 1

            # 记录损失
            total_loss += loss.item() * self.config.gradient_accumulation_steps
            num_steps += 1

            # 更新进度条
            progress_bar.set_postfix({
                "loss": f"{loss.item():.4f}",
                "lr": f"{self.optimizer.param_groups[0]['lr']:.2e}",
            })

            # 日志
            if self.global_step % self.config.logging_steps == 0:
                avg_loss = total_loss / num_steps
                print(f"  Step {self.global_step}: loss = {avg_loss:.4f}")

        return total_loss / num_steps

    def evaluate(self, dataset) -> float:
        """
        评估模型

        Args:
            dataset: 评估数据集

        Returns:
            评估损失
        """
        eval_loader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            collate_fn=self._collate_fn,
        )

        self.model.model.eval()
        total_loss = 0
        num_steps = 0

        with torch.no_grad():
            for batch in tqdm(eval_loader, desc="Evaluating", leave=False):
                batch = {k: v.to(self.device) for k, v in batch.items()}

                outputs = self.model.forward(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                )

                total_loss += outputs.loss.item()
                num_steps += 1

        return total_loss / num_steps

    def save(self, path: str):
        """保存 LoRA 权重"""
        os.makedirs(path, exist_ok=True)
        self.model.save_lora_weights(os.path.join(path, "lora_weights.pt"))

    def load(self, path: str):
        """加载 LoRA 权重"""
        self.model.load_lora_weights(os.path.join(path, "lora_weights.pt"))

    def _collate_fn(self, batch):
        """
        数据批处理函数

        处理不同长度的序列，进行 padding
        """
        # 获取最大长度
        max_length = max(item["input_ids"].size(0) for item in batch)

        # Padding
        input_ids = []
        attention_mask = []
        labels = []

        for item in batch:
            seq_len = item["input_ids"].size(0)
            pad_len = max_length - seq_len

            # 左侧 padding
            input_ids.append(
                torch.cat([
                    torch.full((pad_len,), self.model.tokenizer.pad_token_id),
                    item["input_ids"],
                ])
            )
            attention_mask.append(
                torch.cat([
                    torch.zeros(pad_len),
                    item["attention_mask"],
                ])
            )
            labels.append(
                torch.cat([
                    torch.full((pad_len,), -100),  # -100 表示不计算损失
                    item["labels"],
                ])
            )

        return {
            "input_ids": torch.stack(input_ids),
            "attention_mask": torch.stack(attention_mask),
            "labels": torch.stack(labels),
        }
