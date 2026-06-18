"""
数据集处理模块

本模块提供 LoRA 微调和 PPO 训练所需的数据集类。

💡 数据格式:
    - SFT 数据: {"instruction": "...", "input": "...", "output": "..."}
    - PPO 数据: {"prompt": "..."}

⭐ 数据处理流程:
    1. 加载原始数据（JSON/JSONL 格式）
    2. 格式化为模型输入（instruction + input + output）
    3. Tokenization
    4. 创建 PyTorch Dataset
"""

import json
import os
from typing import Dict, List, Optional, Union

import torch
from torch.utils.data import Dataset


class SFTDataset(Dataset):
    """
    监督微调（SFT）数据集

    ⭐ 数据格式:
    {
        "instruction": "将以下英文翻译成中文",
        "input": "Hello, how are you?",
        "output": "你好，你好吗？"
    }

    或者简化的格式:
    {
        "text": "问题：xxx\n回答：xxx"
    }

    Args:
        data: 数据列表
        tokenizer: 分词器
        max_length: 最大序列长度
        format_template: 格式化模板
    """

    def __init__(
        self,
        data: List[Dict],
        tokenizer,
        max_length: int = 512,
        format_template: str = "default",
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.format_template = format_template

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # 格式化文本
        text = self._format_text(item)

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].squeeze(0)
        attention_mask = encoding["attention_mask"].squeeze(0)

        # 创建标签（与 input_ids 相同，用于因果语言建模）
        labels = input_ids.clone()

        # 将 padding token 的标签设为 -100（不计算损失）
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    def _format_text(self, item: Dict) -> str:
        """
        格式化文本

        💡 不同的格式化方式会影响模型的学习效果
        """
        if "text" in item:
            return item["text"]

        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output = item.get("output", "")

        if self.format_template == "alpaca":
            # Alpaca 格式
            if input_text:
                return (
                    f"Below is an instruction that describes a task, "
                    f"paired with an input that provides further context. "
                    f"Write a response that appropriately completes the request.\n\n"
                    f"### Instruction:\n{instruction}\n\n"
                    f"### Input:\n{input_text}\n\n"
                    f"### Response:\n{output}"
                )
            else:
                return (
                    f"Below is an instruction that describes a task. "
                    f"Write a response that appropriately completes the request.\n\n"
                    f"### Instruction:\n{instruction}\n\n"
                    f"### Response:\n{output}"
                )
        else:
            # 默认格式
            if input_text:
                return f"指令：{instruction}\n输入：{input_text}\n输出：{output}"
            else:
                return f"指令：{instruction}\n输出：{output}"


class PPODataset(Dataset):
    """
    PPO 训练数据集

    ⭐ PPO 只需要提示词（prompt），不需要回答
    因为回答是由策略模型在线生成的

    Args:
        prompts: 提示词列表
        tokenizer: 分词器
        max_length: 最大序列长度
    """

    def __init__(
        self,
        prompts: List[str],
        tokenizer,
        max_length: int = 256,
    ):
        self.prompts = prompts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        prompt = self.prompts[idx]

        encoding = self.tokenizer(
            prompt,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
        }


def load_jsonl(file_path: str) -> List[Dict]:
    """
    加载 JSONL 格式数据

    Args:
        file_path: 文件路径

    Returns:
        数据列表
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def load_json(file_path: str) -> List[Dict]:
    """
    加载 JSON 格式数据

    Args:
        file_path: 文件路径

    Returns:
        数据列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("data", [data])
    return data


def load_dataset(
    file_path: str,
    tokenizer,
    max_length: int = 512,
    format_template: str = "default",
    dataset_type: str = "sft",
) -> Dataset:
    """
    加载数据集

    Args:
        file_path: 数据文件路径
        tokenizer: 分词器
        max_length: 最大序列长度
        format_template: 格式化模板
        dataset_type: 数据集类型 ("sft" 或 "ppo")

    Returns:
        Dataset 实例
    """
    # 根据文件扩展名选择加载方式
    if file_path.endswith(".jsonl"):
        data = load_jsonl(file_path)
    else:
        data = load_json(file_path)

    if dataset_type == "sft":
        return SFTDataset(data, tokenizer, max_length, format_template)
    elif dataset_type == "ppo":
        prompts = [item.get("prompt", item.get("text", "")) for item in data]
        return PPODataset(prompts, tokenizer, max_length)
    else:
        raise ValueError(f"不支持的数据集类型: {dataset_type}")


def create_sample_dataset(
    dataset_type: str = "sft",
    num_samples: int = 100,
) -> List[Dict]:
    """
    创建示例数据集

    💡 用于快速测试和验证

    Args:
        dataset_type: 数据集类型 ("sft" 或 "ppo")
        num_samples: 样本数量

    Returns:
        数据列表
    """
    if dataset_type == "sft":
        return _create_sft_samples(num_samples)
    elif dataset_type == "ppo":
        return _create_ppo_samples(num_samples)
    else:
        raise ValueError(f"不支持的数据集类型: {dataset_type}")


def _create_sft_samples(num_samples: int) -> List[Dict]:
    """创建 SFT 示例数据"""
    templates = [
        {
            "instruction": "将以下英文翻译成中文",
            "input": "Hello, how are you?",
            "output": "你好，你好吗？",
        },
        {
            "instruction": "总结以下文本",
            "input": "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
            "output": "人工智能是计算机科学的分支，旨在创造能模拟人类智能的机器。",
        },
        {
            "instruction": "解释什么是机器学习",
            "input": "",
            "output": "机器学习是人工智能的一个子领域，它使计算机系统能够从数据中学习和改进，而无需显式编程。",
        },
        {
            "instruction": "写一首关于春天的诗",
            "input": "",
            "output": "春风拂面暖，花开满园香。燕子归来早，万物复苏忙。",
        },
        {
            "instruction": "给出以下问题的答案",
            "input": "什么是深度学习？",
            "output": "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的层次化表示。",
        },
    ]

    data = []
    for i in range(num_samples):
        template = templates[i % len(templates)]
        data.append(template.copy())

    return data


def _create_ppo_samples(num_samples: int) -> List[Dict]:
    """创建 PPO 示例数据（提示词）"""
    prompts = [
        "请解释什么是人工智能",
        "写一个Python函数来计算斐波那契数列",
        "什么是量子计算？",
        "请推荐几本关于机器学习的书",
        "解释一下区块链技术的原理",
        "如何提高代码的可读性？",
        "什么是微服务架构？",
        "请描述一下你的理想工作",
        "如何保持健康的生活方式？",
        "解释一下什么是API",
    ]

    data = []
    for i in range(num_samples):
        data.append({"prompt": prompts[i % len(prompts)]})

    return data


def save_dataset(data: List[Dict], file_path: str, format: str = "jsonl"):
    """
    保存数据集

    Args:
        data: 数据列表
        file_path: 文件路径
        format: 保存格式 ("json" 或 "jsonl")
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if format == "jsonl":
        with open(file_path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"数据集已保存到: {file_path} ({len(data)} 条)")
