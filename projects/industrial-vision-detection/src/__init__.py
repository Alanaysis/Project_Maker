"""
Industrial Vision Detection - 工业视觉检测神经网络

一个用于学习工业级视觉缺陷检测系统的学习项目
"""

__version__ = '0.1.0'
__author__ = 'Industrial Vision Detection Team'

from .models import YOLOModel, YOLOv8Tiny
from .data import DefectDataset
from .utils import compute_iou, compute_map
