"""
算子模块

提供各种算子的实现和融合功能
"""

from .conv import Conv2dOperator, QuantizedConv2d
from .linear import LinearOperator, QuantizedLinear
from .activation import ReLUOperator, SigmoidOperator, TanhOperator
from .fusion import OperatorFusion, fuse_conv_bn, fuse_conv_bn_relu

__all__ = [
    "Conv2dOperator",
    "QuantizedConv2d",
    "LinearOperator",
    "QuantizedLinear",
    "ReLUOperator",
    "SigmoidOperator",
    "TanhOperator",
    "OperatorFusion",
    "fuse_conv_bn",
    "fuse_conv_bn_relu",
]
