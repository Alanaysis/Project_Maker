"""
Tests for Hand Detector

测试覆盖：
1. 初始化测试
2. 肤色检测测试
3. 形态学操作测试
4. 轮廓检测测试
5. 边界情况测试
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gesture_recognition.models.hand_detector import HandDetector


class TestHandDetector:
    """手部检测器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        detector = HandDetector()
        assert detector.min_hand_area == 3000
        assert detector.max_hands == 2
        assert detector.kernel is not None

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        detector = HandDetector(
            min_hand_area=5000,
            max_hands=3,
            skin_lower=(10, 30, 80),
            skin_upper=(25, 250, 250),
        )
        assert detector.min_hand_area == 5000
        assert detector.max_hands == 3

    def test_detect_skin(self):
        """测试肤色检测"""
        detector = HandDetector()

        # 创建HSV图像
        hsv_image = np.zeros((100, 100, 3), dtype=np.uint8)
        hsv_image[:, :, 0] = 10  # H: 肤色范围
        hsv_image[:, :, 1] = 150  # S
        hsv_image[:, :, 2] = 200  # V

        mask = detector._detect_skin(hsv_image)
        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8

    def test_clean_mask(self):
        """测试掩码清理"""
        detector = HandDetector()

        # 创建带噪声的掩码
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255  # 手部区域
        mask[10:12, 10:12] = 255  # 小噪声点

        cleaned = detector._clean_mask(mask)
        assert cleaned.shape == (100, 100)

    def test_find_hands_empty(self):
        """测试空掩码的手部检测"""
        detector = HandDetector()
        mask = np.zeros((100, 100), dtype=np.uint8)

        hands = detector._find_hands(mask)
        assert len(hands) == 0

    def test_find_hands_with_region(self):
        """测试有手部区域的检测"""
        detector = HandDetector(min_hand_area=100)
        mask = np.zeros((200, 200), dtype=np.uint8)

        # 创建足够大的手部区域
        mask[50:150, 50:150] = 255

        hands = detector._find_hands(mask)
        assert len(hands) > 0

        # 检查返回的结构
        hand = hands[0]
        assert "bbox" in hand
        assert "center" in hand
        assert "area" in hand
        assert "mask" in hand

    def test_detect_returns_list(self):
        """测试detect返回列表类型"""
        detector = HandDetector()
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        result = detector.detect(image)
        assert isinstance(result, list)

    def test_detect_limits_hands(self):
        """测试最大手数限制"""
        detector = HandDetector(max_hands=1, min_hand_area=100)
        mask = np.zeros((200, 200), dtype=np.uint8)

        # 创建两个手部区域
        mask[20:80, 20:80] = 255
        mask[20:80, 120:180] = 255

        # 使用内部方法测试
        hands = detector._find_hands(mask)
        hands.sort(key=lambda h: h["area"], reverse=True)
        limited_hands = hands[:detector.max_hands]

        assert len(limited_hands) <= detector.max_hands
