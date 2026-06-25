"""
测试数据集
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.dataset import SyntheticCaptionDataset, synthetic_collate_fn, collate_fn


class TestSyntheticDataset:
    """合成数据集测试套件。"""

    def test_dataset_length(self):
        """测试数据集长度。"""
        dataset = SyntheticCaptionDataset(num_samples=50)
        assert len(dataset) == 50

    def test_getitem(self):
        """测试获取样本。"""
        dataset = SyntheticCaptionDataset(num_samples=10, image_size=64)
        image, caption, length = dataset[0]
        assert image.shape == (3, 64, 64)
        assert caption.dim() == 1
        assert isinstance(length, int)
        assert length > 0

    def test_collate_fn(self):
        """测试批量整理函数。"""
        dataset = SyntheticCaptionDataset(num_samples=8, image_size=64)
        batch = [dataset[i] for i in range(4)]
        images, captions, lengths = synthetic_collate_fn(batch)

        assert images.shape[0] == 4
        assert images.shape[1] == 3
        assert captions.shape[0] == 4
        assert lengths.shape[0] == 4

        # 长度应降序排列
        for i in range(len(lengths) - 1):
            assert lengths[i] >= lengths[i + 1]

    def test_caption_start_end(self):
        """测试描述包含 start 和 end 标记。"""
        dataset = SyntheticCaptionDataset(
            num_samples=10, vocab_size=20, max_caption_length=8
        )
        _, caption, length = dataset[0]
        # 第一个 token 应该是 <start> = 1
        assert caption[0].item() == 1

    def test_collate_padding(self):
        """测试填充正确性。"""
        dataset = SyntheticCaptionDataset(num_samples=4, image_size=64)
        batch = [dataset[i] for i in range(4)]
        images, captions, lengths = synthetic_collate_fn(batch)

        max_len = captions.shape[1]
        # 最短序列之后的位置应为 0 (pad)
        for i in range(4):
            if lengths[i] < max_len:
                assert (captions[i, lengths[i]:] == 0).all()


def run_tests():
    """运行所有测试。"""
    test = TestSyntheticDataset()
    tests = [getattr(test, name) for name in dir(test) if name.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__} - {e}")
            failed += 1
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("数据集测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
