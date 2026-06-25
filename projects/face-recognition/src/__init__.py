"""
面部识别系统

实现人脸检测、特征提取和身份识别功能。
"""

from .face_detector import FaceDetector
from .feature_extractor import FeatureExtractor
from .face_recognizer import FaceRecognizer
from .utils import preprocess_image, draw_faces, cosine_similarity, create_test_image, normalize_feature

__version__ = "1.0.0"
__all__ = [
    "FaceDetector",
    "FeatureExtractor",
    "FaceRecognizer",
    "preprocess_image",
    "draw_faces",
    "cosine_similarity",
    "create_test_image",
    "normalize_feature",
]
