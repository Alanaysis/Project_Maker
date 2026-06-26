"""
贝塞尔曲线引擎 (Bezier Curve Engine)
=====================================

核心模块：实现贝塞尔曲线的数学计算和渲染
"""

from . import linear_bezier
from . import quadratic_bezier
from . import cubic_bezier
from . import de_casteljau
from . import subdivision
from . import curve_intersection
from . import tangent_normal
from . import curve_length

__version__ = "0.1.0"
__all__ = [
    "linear_bezier",
    "quadratic_bezier",
    "cubic_bezier",
    "de_casteljau",
    "subdivision",
    "curve_intersection",
    "tangent_normal",
    "curve_length",
]
