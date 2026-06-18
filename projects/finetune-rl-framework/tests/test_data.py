"""
数据模块测试

⭐ 测试重点:
1. 数据集类的正确性
2. 数据格式化
3. 示例数据生成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import torch

from src.data.dataset import (
    SFTDataset,
    PPODataset,
    create_sample_dataset,
    save_dataset,
    load_jsonl,
)


class MockTokenizer:
    """模拟分词器"""

    def __init__(self, vocab_size=1000, max_length=10):
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.pad_token_id = 0
        self.eos_token_id = 1

    def __call__(self, text, max_length=None, padding=None, truncation=None, return_tensors=None):
        # 简单的 tokenization：将字符转换为 token id
        tokens = [ord(c) % self.vocab_size for c in text[:max_length or self.max_length]]

        # Padding
        if padding == "max_length":
            max_len = max_length or self.max_length
            tokens = tokens + [self.pad_token_id] * (max_len - len(tokens))

        input_ids = torch.tensor([tokens])
        attention_mask = torch.tensor([[1] * len(text[:max_length or self.max_length]) + [0] * max(0, (max_length or self.max_length) - len(text))])

        result = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        if return_tensors == "pt":
            return result
        return result


class TestSFTDataset:
    """SFT 数据集测试"""

    def test_init(self):
        """测试初始化"""
        data = [
            {"instruction": "test", "input": "", "output": "result"},
        ]
        tokenizer = MockTokenizer()

        dataset = SFTDataset(data, tokenizer, max_length=10)

        assert len(dataset) == 1

    def test_getitem(self):
        """测试获取数据项"""
        data = [
            {"instruction": "test", "input": "", "output": "result"},
        ]
        tokenizer = MockTokenizer(max_length=20)

        dataset = SFTDataset(data, tokenizer, max_length=20)

        item = dataset[0]

        assert "input_ids" in item
        assert "attention_mask" in item
        assert "labels" in item
        assert item["input_ids"].shape[0] == 20

    def test_labels(self):
        """测试标签"""
        data = [
            {"instruction": "test", "input": "", "output": "result"},
        ]
        tokenizer = MockTokenizer(max_length=20)

        dataset = SFTDataset(data, tokenizer, max_length=20)

        item = dataset[0]

        # 标签应该与 input_ids 相同
        assert torch.equal(item["input_ids"], item["labels"])

    def test_format_alpaca(self):
        """测试 Alpaca 格式化"""
        data = [
            {"instruction": "test instruction", "input": "test input", "output": "test output"},
        ]
        tokenizer = MockTokenizer(max_length=100)

        dataset = SFTDataset(data, tokenizer, max_length=100, format_template="alpaca")

        item = dataset[0]

        # 应该成功创建
        assert item["input_ids"].shape[0] == 100


class TestPPODataset:
    """PPO 数据集测试"""

    def test_init(self):
        """测试初始化"""
        prompts = ["test prompt 1", "test prompt 2"]
        tokenizer = MockTokenizer()

        dataset = PPODataset(prompts, tokenizer, max_length=10)

        assert len(dataset) == 2

    def test_getitem(self):
        """测试获取数据项"""
        prompts = ["test prompt"]
        tokenizer = MockTokenizer(max_length=10)

        dataset = PPODataset(prompts, tokenizer, max_length=10)

        item = dataset[0]

        assert "input_ids" in item
        assert "attention_mask" in item
        assert item["input_ids"].shape[0] == 10


class TestCreateSampleDataset:
    """示例数据集测试"""

    def test_create_sft_samples(self):
        """测试创建 SFT 示例"""
        data = create_sample_dataset("sft", num_samples=10)

        assert len(data) == 10

        for item in data:
            assert "instruction" in item
            assert "output" in item

    def test_create_ppo_samples(self):
        """测试创建 PPO 示例"""
        data = create_sample_dataset("ppo", num_samples=10)

        assert len(data) == 10

        for item in data:
            assert "prompt" in item

    def test_invalid_type(self):
        """测试无效类型"""
        with pytest.raises(ValueError):
            create_sample_dataset("invalid")


class TestSaveDataset:
    """数据集保存测试"""

    def test_save_jsonl(self, tmp_path):
        """测试保存为 JSONL 格式"""
        data = [{"text": "test"}]
        file_path = str(tmp_path / "test.jsonl")

        save_dataset(data, file_path, format="jsonl")

        # 读取并验证
        loaded = load_jsonl(file_path)
        assert len(loaded) == 1
        assert loaded[0]["text"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
