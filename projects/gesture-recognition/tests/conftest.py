"""Test fixtures for gesture recognition tests."""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_keypoints():
    """
    生成样本关键点

    Returns:
        np.ndarray: (21, 2) 归一化关键点坐标
    """
    # 创建一个张开手掌的关键点
    keypoints = np.zeros((21, 2))
    keypoints[0] = [0.5, 0.8]  # 手腕

    # 拇指
    keypoints[1] = [0.35, 0.7]
    keypoints[2] = [0.3, 0.65]
    keypoints[3] = [0.25, 0.62]
    keypoints[4] = [0.2, 0.6]

    # 食指
    keypoints[5] = [0.45, 0.6]
    keypoints[6] = [0.45, 0.45]
    keypoints[7] = [0.45, 0.35]
    keypoints[8] = [0.45, 0.25]

    # 中指
    keypoints[9] = [0.5, 0.6]
    keypoints[10] = [0.5, 0.45]
    keypoints[11] = [0.5, 0.35]
    keypoints[12] = [0.5, 0.25]

    # 无名指
    keypoints[13] = [0.55, 0.6]
    keypoints[14] = [0.55, 0.45]
    keypoints[15] = [0.55, 0.35]
    keypoints[16] = [0.55, 0.25]

    # 小指
    keypoints[17] = [0.6, 0.6]
    keypoints[18] = [0.6, 0.45]
    keypoints[19] = [0.6, 0.35]
    keypoints[20] = [0.6, 0.25]

    return keypoints


@pytest.fixture
def fist_keypoints():
    """
    生成拳头关键点

    Returns:
        np.ndarray: (21, 2) 归一化关键点坐标
    """
    keypoints = np.zeros((21, 2))
    keypoints[0] = [0.5, 0.8]  # 手腕

    # 所有手指弯曲
    for i in range(1, 21):
        finger_idx = (i - 1) // 4
        keypoints[i] = [0.4 + finger_idx * 0.05, 0.75]

    return keypoints


@pytest.fixture
def sample_image():
    """
    生成样本图像

    Returns:
        np.ndarray: BGR格式的测试图像
    """
    # 创建带有肤色区域的测试图像
    image = np.ones((480, 640, 3), dtype=np.uint8) * 200

    # 添加"手部"区域（肤色）
    cv2 = pytest.importorskip("cv2")
    cv2.ellipse(image, (320, 240), (80, 100), 0, 0, 360, (150, 120, 100), -1)

    return image


@pytest.fixture
def synthetic_dataset():
    """
    创建合成数据集

    Returns:
        HandDataset: 测试用数据集
    """
    from gesture_recognition.data.hand_dataset import HandDataset

    return HandDataset(num_samples=70, num_classes=7)


@pytest.fixture
def gesture_classifier():
    """
    创建手势分类器

    Returns:
        GestureClassifier: 测试用分类器
    """
    from gesture_recognition.models.gesture_classifier import GestureClassifier

    return GestureClassifier(device="cpu")
