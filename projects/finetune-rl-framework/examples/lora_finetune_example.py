"""
LoRA 微调示例

⭐ 本示例展示如何使用 LoRA 微调 GPT-2 模型

运行方式:
    python examples/lora_finetune_example.py

💡 学习要点:
1. LoRA 如何注入到 Transformer 模型
2. LoRA 参数量远小于全参数量
3. 训练过程中只有 LoRA 参数被更新
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
from transformers import AutoTokenizer

from src.lora.layer import LoRALinear, inject_lora_layers, count_lora_parameters
from src.data.dataset import create_sample_dataset, SFTDataset


def main():
    """LoRA 微调示例"""

    print("=" * 60)
    print("LoRA 微调示例")
    print("=" * 60)

    # ========== 1. 创建简单模型 ==========
    print("\n1. 创建模型...")

    # 使用一个简单的模型（避免下载大模型）
    class SimpleTransformer(torch.nn.Module):
        def __init__(self, vocab_size=1000, hidden_size=128, num_layers=2):
            super().__init__()
            self.embedding = torch.nn.Embedding(vocab_size, hidden_size)
            self.layers = torch.nn.ModuleList([
                torch.nn.Linear(hidden_size, hidden_size)
                for _ in range(num_layers)
            ])
            self.output = torch.nn.Linear(hidden_size, vocab_size)

        def forward(self, input_ids, attention_mask=None, labels=None):
            x = self.embedding(input_ids)
            for layer in self.layers:
                x = torch.relu(layer(x))
            logits = self.output(x)

            loss = None
            if labels is not None:
                loss_fn = torch.nn.CrossEntropyLoss()
                loss = loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))

            return type('Output', (), {'logits': logits, 'loss': loss})()

    model = SimpleTransformer()

    # 统计原始参数量
    original_params = sum(p.numel() for p in model.parameters())
    print(f"原始模型参数量: {original_params:,}")

    # ========== 2. 注入 LoRA 层 ==========
    print("\n2. 注入 LoRA 层...")

    model = inject_lora_layers(
        model,
        target_modules=["layers"],  # 注入到所有线性层
        rank=8,
        alpha=16.0,
        dropout=0.05,
    )

    # 统计 LoRA 参数量
    lora_params, total_params = count_lora_parameters(model)
    print(f"LoRA 参数量: {lora_params:,}")
    print(f"总参数量: {total_params:,}")
    print(f"LoRA 参数占比: {lora_params/total_params*100:.2f}%")

    # ========== 3. 冻结非 LoRA 参数 ==========
    print("\n3. 设置训练参数...")

    # 冻结所有参数
    for param in model.parameters():
        param.requires_grad = False

    # 只解冻 LoRA 参数
    for name, param in model.named_parameters():
        if "lora_A" in name or "lora_B" in name:
            param.requires_grad = True

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"可训练参数量: {trainable_params:,}")

    # ========== 4. 准备数据 ==========
    print("\n4. 准备训练数据...")

    # 创建示例数据
    data = create_sample_dataset("sft", num_samples=20)
    print(f"训练样本数: {len(data)}")

    # 创建模拟的分词器
    class SimpleTokenizer:
        def __init__(self, vocab_size=1000, max_length=32):
            self.vocab_size = vocab_size
            self.max_length = max_length
            self.pad_token_id = 0

        def __call__(self, text, max_length=None, padding=None, truncation=None, return_tensors=None):
            tokens = [ord(c) % self.vocab_size for c in text[:max_length or self.max_length]]
            max_len = max_length or self.max_length
            tokens = tokens + [self.pad_token_id] * (max_len - len(tokens))
            input_ids = torch.tensor([tokens])
            attention_mask = torch.tensor([[1] * min(len(text), max_len) + [0] * max(0, max_len - len(text))])
            return {"input_ids": input_ids, "attention_mask": attention_mask}

    tokenizer = SimpleTokenizer()
    dataset = SFTDataset(data, tokenizer, max_length=32)

    # ========== 5. 训练循环 ==========
    print("\n5. 开始训练...")

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=2e-4,
    )

    num_epochs = 3
    batch_size = 4

    for epoch in range(num_epochs):
        total_loss = 0
        num_batches = 0

        for i in range(0, len(dataset), batch_size):
            batch = [dataset[j] for j in range(i, min(i + batch_size, len(dataset)))]

            # Stack batch
            input_ids = torch.stack([item["input_ids"] for item in batch])
            attention_mask = torch.stack([item["attention_mask"] for item in batch])
            labels = input_ids.clone()

            # 前向传播
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        print(f"  Epoch {epoch + 1}/{num_epochs}: loss = {avg_loss:.4f}")

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)

    # ========== 6. 保存 LoRA 权重 ==========
    print("\n6. 保存 LoRA 权重...")

    lora_state_dict = {}
    for name, param in model.named_parameters():
        if "lora_A" in name or "lora_B" in name:
            lora_state_dict[name] = param.data.clone()

    output_dir = "./lora_output"
    os.makedirs(output_dir, exist_ok=True)
    torch.save(lora_state_dict, os.path.join(output_dir, "lora_weights.pt"))
    print(f"LoRA 权重已保存到: {output_dir}/lora_weights.pt")

    # 显示保存的文件大小
    file_size = os.path.getsize(os.path.join(output_dir, "lora_weights.pt"))
    print(f"文件大小: {file_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()
