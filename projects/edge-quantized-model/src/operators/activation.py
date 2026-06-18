"""
激活函数模块

提供各种激活函数的实现
"""

import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ReLUOperator:
    """
    ReLU 激活函数

    f(x) = max(0, x)
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 ReLU

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        return {'output': self.relu(x)}

    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU 计算"""
        return np.maximum(0, x)


class LeakyReLUOperator:
    """
    LeakyReLU 激活函数

    f(x) = x if x > 0 else alpha * x
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 LeakyReLU

        Args:
            inputs: 输入字典
            params: 参数字典，包含 'alpha' 参数

        Returns:
            输出字典
        """
        x = inputs['input']
        alpha = params.get('alpha', 0.01)
        return {'output': self.leaky_relu(x, alpha)}

    def leaky_relu(self, x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
        """LeakyReLU 计算"""
        return np.where(x > 0, x, alpha * x)


class SigmoidOperator:
    """
    Sigmoid 激活函数

    f(x) = 1 / (1 + exp(-x))
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 Sigmoid

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        return {'output': self.sigmoid(x)}

    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid 计算"""
        # 数值稳定的实现
        return np.where(
            x >= 0,
            1 / (1 + np.exp(-x)),
            np.exp(x) / (1 + np.exp(x)),
        )


class TanhOperator:
    """
    Tanh 激活函数

    f(x) = tanh(x)
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 Tanh

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        return {'output': self.tanh(x)}

    def tanh(self, x: np.ndarray) -> np.ndarray:
        """Tanh 计算"""
        return np.tanh(x)


class SoftmaxOperator:
    """
    Softmax 激活函数

    f(x_i) = exp(x_i) / sum(exp(x_j))
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 Softmax

        Args:
            inputs: 输入字典
            params: 参数字典，包含 'axis' 参数

        Returns:
            输出字典
        """
        x = inputs['input']
        axis = params.get('axis', -1)
        return {'output': self.softmax(x, axis)}

    def softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Softmax 计算"""
        # 数值稳定的实现
        x_max = np.max(x, axis=axis, keepdims=True)
        exp_x = np.exp(x - x_max)
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class GELUOperator:
    """
    GELU 激活函数

    f(x) = x * Φ(x)
    其中 Φ(x) 是标准正态分布的累积分布函数
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 GELU

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        return {'output': self.gelu(x)}

    def gelu(self, x: np.ndarray) -> np.ndarray:
        """GELU 计算"""
        # 近似实现
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))


class SwishOperator:
    """
    Swish 激活函数

    f(x) = x * sigmoid(x)
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行 Swish

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        return {'output': self.swish(x)}

    def swish(self, x: np.ndarray) -> np.ndarray:
        """Swish 计算"""
        return x * (1 / (1 + np.exp(-x)))


# 量化激活函数
class QuantizedReLU:
    """量化 ReLU"""

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        x = inputs['input']
        scale = params.get('scale', 1.0)
        zero_point = params.get('zero_point', 0)

        # 量化 ReLU
        x_q = np.clip(np.round(x / scale) + zero_point, 0, 127).astype(np.uint8)

        return {'output': x_q}


class QuantizedSigmoid:
    """量化 Sigmoid"""

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        x = inputs['input']
        scale = params.get('scale', 1.0)
        zero_point = params.get('zero_point', 0)

        # 使用查找表实现量化 Sigmoid
        # 简化实现：直接计算后量化
        sigmoid_x = 1 / (1 + np.exp(-x))
        x_q = np.clip(np.round(sigmoid_x / scale) + zero_point, 0, 255).astype(np.uint8)

        return {'output': x_q}
