"""
Gesture Recognition - Hand gesture recognition using keypoint detection and classification.

Core pipeline: 图像输入 → 手部检测 → 关键点提取 → 手势分类 → 输出
"""

__version__ = "1.0.0"

from gesture_recognition.models.hand_detector import HandDetector
from gesture_recognition.models.keypoint_extractor import KeypointExtractor
from gesture_recognition.models.gesture_classifier import GestureClassifier
from gesture_recognition.models.gesture_recognizer import GestureRecognizer
from gesture_recognition.data.hand_dataset import HandDataset
from gesture_recognition.utils.visualization import draw_hand_landmarks, draw_gesture_result

__all__ = [
    "HandDetector",
    "KeypointExtractor",
    "GestureClassifier",
    "GestureRecognizer",
    "HandDataset",
    "draw_hand_landmarks",
    "draw_gesture_result",
]
