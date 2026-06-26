"""
Android 基础应用学习项目 - Android Basic Application Learning Project

通过 Python 模拟 Android 核心概念，帮助学习者理解 Android 架构原理。
Simulates core Android concepts using Python to help learners understand Android architecture.
"""

from . import lifecycle
from . import view
from . import layout
from . import intent
from . import fragment
from . import shared_prefs
from . import compose
from . import data_binding
from . import network

__all__ = [
    "lifecycle",
    "view",
    "layout",
    "intent",
    "fragment",
    "shared_prefs",
    "compose",
    "data_binding",
    "network",
]
