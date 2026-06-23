"""
特征匹配 SIFT/ORB

实现图像特征点检测和匹配，理解计算机视觉中的特征提取与匹配技术。
"""

from .detector import FeatureDetector
from .descriptor import DescriptorExtractor
from .matcher import FeatureMatcher
from .visualizer import Visualizer

__version__ = '1.0.0'
__all__ = ['FeatureDetector', 'DescriptorExtractor', 'FeatureMatcher', 'Visualizer']
