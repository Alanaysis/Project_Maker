"""
决策树模块

包含以下算法实现：
- ID3: 基于信息增益的决策树
- C4.5: 基于信息增益率的决策树
- CART分类: 基于基尼系数的决策树
- CART回归: 基于方差减少的决策树
- 剪枝: 预剪枝和后剪枝
"""

from .decision_tree import DecisionTreeClassifier
from .id3 import ID3DecisionTree
from .c45 import C45DecisionTree
from .cart_classifier import CARTClassifier
from .cart_regressor import CARTRegressor
from .pruning import PrePruningTree, PostPruningTree, ReducedErrorPruning
from .utils import train_test_split, accuracy_score, normalize, check_input
from .metrics import confusion_matrix, precision_score, recall_score, f1_score
from .visualization import (
    plot_tree, plot_decision_boundary, plot_feature_importance,
    plot_learning_curve, plot_confusion_matrix, print_tree_text
)

__version__ = "1.0.0"
__all__ = [
    # 决策树算法
    "DecisionTreeClassifier",
    "ID3DecisionTree",
    "C45DecisionTree",
    "CARTClassifier",
    "CARTRegressor",
    # 剪枝
    "PrePruningTree",
    "PostPruningTree",
    "ReducedErrorPruning",
    # 工具函数
    "train_test_split",
    "accuracy_score",
    "normalize",
    "check_input",
    # 评估指标
    "confusion_matrix",
    "precision_score",
    "recall_score",
    "f1_score",
    # 可视化
    "plot_tree",
    "plot_decision_boundary",
    "plot_feature_importance",
    "plot_learning_curve",
    "plot_confusion_matrix",
    "print_tree_text",
]
