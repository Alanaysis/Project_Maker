"""测试文字识别器"""

import pytest
import torch
import numpy as np
import cv2
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.recognizer import CRNN, CTCDecoder, TextRecognizer, create_recognizer


class TestCRNN:
    """测试 CRNN 模型"""

    @pytest.fixture
    def model(self):
        return CRNN(num_classes=63)

    def test_forward(self, model):
        """前向传播"""
        x = torch.randn(2, 1, 32, 100)
        output = model(x)
        # 输出形状: (T, B, num_classes)
        assert output.shape[1] == 2
        assert output.shape[2] == 63

    def test_output_sequence(self, model):
        """输出序列长度"""
        x = torch.randn(1, 1, 32, 100)
        output = model(x)
        # 序列长度应大于0
        assert output.shape[0] > 0

    def test_gradient(self, model):
        """梯度计算"""
        x = torch.randn(2, 1, 32, 100)
        output = model(x)
        loss = output.sum()
        loss.backward()

        for param in model.parameters():
            assert param.grad is not None

    def test_different_input_sizes(self, model):
        """不同输入大小"""
        for width in [50, 100, 200]:
            x = torch.randn(1, 1, 32, width)
            output = model(x)
            assert output.shape[1] == 1
            assert output.shape[2] == 63

    def test_batch_processing(self, model):
        """批量处理"""
        x = torch.randn(4, 1, 32, 100)
        output = model(x)
        assert output.shape[1] == 4


class TestCTCDecoder:
    """测试 CTC 解码器"""

    @pytest.fixture
    def decoder(self):
        charset = "0123456789abcdefghijklmnopqrstuvwxyz"
        return CTCDecoder(charset)

    def test_greedy_decode(self, decoder):
        """贪心解码"""
        # 模拟输出: 3个时间步, 63个类别
        logits = torch.randn(3, 63)
        text = decoder.greedy_decode(logits)
        assert isinstance(text, str)

    def test_decode_no_repeat(self, decoder):
        """去重测试"""
        # 创建有重复的输出
        logits = torch.zeros(5, 63)
        logits[0, 1] = 1  # 字符 '0'
        logits[1, 1] = 1  # 重复
        logits[2, 2] = 1  # 字符 '1'

        text = decoder.greedy_decode(logits)
        # 应该去重
        assert len(text) <= 3

    def test_decode_blank(self, decoder):
        """blank 处理"""
        logits = torch.zeros(3, 63)
        logits[0, 0] = 1  # blank
        logits[1, 1] = 1  # 字符 '0'
        logits[2, 0] = 1  # blank

        text = decoder.greedy_decode(logits)
        assert len(text) <= 1

    def test_beam_search(self, decoder):
        """Beam Search 解码"""
        logits = torch.randn(3, 63)
        text = decoder.beam_search_decode(logits, beam_size=5)
        assert isinstance(text, str)


class TestTextRecognizer:
    """测试文字识别器"""

    @pytest.fixture
    def recognizer(self):
        return TextRecognizer()

    @pytest.fixture
    def digit_image(self):
        """创建数字图像"""
        image = np.zeros((32, 100), dtype=np.uint8)
        cv2.putText(image, "123", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)
        return image

    def test_preprocess(self, recognizer, digit_image):
        """预处理"""
        tensor = recognizer.preprocess(digit_image)
        assert tensor.shape == (1, 1, 32, 100)

    def test_preprocess_color(self, recognizer):
        """彩色图像预处理"""
        image = np.zeros((32, 100, 3), dtype=np.uint8)
        tensor = recognizer.preprocess(image)
        assert tensor.shape == (1, 1, 32, 100)

    def test_recognize(self, recognizer, digit_image):
        """识别"""
        text, confidence = recognizer.recognize(digit_image)
        assert isinstance(text, str)
        assert 0 <= confidence <= 1

    def test_recognize_batch(self, recognizer):
        """批量识别"""
        images = [
            np.zeros((32, 100), dtype=np.uint8),
            np.zeros((32, 100), dtype=np.uint8)
        ]
        results = recognizer.recognize_batch(images)
        assert len(results) == 2
        for text, conf in results:
            assert isinstance(text, str)
            assert 0 <= conf <= 1

    def test_device(self):
        """设备测试"""
        recognizer = TextRecognizer(device="cpu")
        assert recognizer.device == "cpu"

    def test_charset(self):
        """字符集测试"""
        charset = "abc"
        recognizer = TextRecognizer(charset=charset)
        assert recognizer.charset == charset


class TestCreateRecognizer:
    """测试识别器工厂函数"""

    def test_create_default(self):
        """默认创建"""
        recognizer = create_recognizer()
        assert isinstance(recognizer, TextRecognizer)

    def test_create_with_charset(self):
        """带字符集创建"""
        charset = "0123456789"
        recognizer = create_recognizer(charset=charset)
        assert recognizer.charset == charset

    def test_create_device(self):
        """设备创建"""
        recognizer = create_recognizer(device="cpu")
        assert recognizer.device == "cpu"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])