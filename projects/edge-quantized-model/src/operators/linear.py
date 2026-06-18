"""
全连接算子模块

提供全连接（Linear）算子的实现
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class LinearOperator:
    """
    全连接算子

    实现 y = xW^T + b
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行全连接

        Args:
            inputs: 输入字典，包含 'input', 'weight', 'bias'（可选）
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        output = self.linear(x, weight, bias)

        return {'output': output}

    def linear(
        self,
        x: np.ndarray,
        weight: np.ndarray,
        bias: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        全连接计算

        Args:
            x: 输入 [batch, in_features]
            weight: 权重 [out_features, in_features]
            bias: 偏置 [out_features]

        Returns:
            输出 [batch, out_features]
        """
        # 矩阵乘法
        output = np.dot(x, weight.T)

        # 添加偏置
        if bias is not None:
            output += bias

        return output

    def compute_output_shape(
        self,
        input_shape: tuple,
        weight_shape: tuple,
    ) -> tuple:
        """
        计算输出形状

        Args:
            input_shape: 输入形状 (batch, in_features)
            weight_shape: 权重形状 (out_features, in_features)

        Returns:
            输出形状
        """
        batch = input_shape[0]
        out_features = weight_shape[0]
        return (batch, out_features)


class QuantizedLinear:
    """
    量化全连接算子

    实现 INT8 量化全连接
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行量化全连接

        Args:
            inputs: 输入字典
            params: 参数字典，包含量化参数

        Returns:
            输出字典
        """
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        # 量化参数
        x_scale = params.get('x_scale', 1.0)
        x_zero_point = params.get('x_zero_point', 0)
        w_scale = params.get('w_scale', 1.0)
        w_zero_point = params.get('w_zero_point', 0)

        # 量化输入
        x_q = np.clip(
            np.round(x / x_scale) + x_zero_point, -128, 127
        ).astype(np.int8)

        # 量化权重
        w_q = np.clip(
            np.round(weight / w_scale) + w_zero_point, -128, 127
        ).astype(np.int8)

        # 整数矩阵乘法
        output_q = np.dot(x_q.astype(np.int32), w_q.astype(np.int32).T)

        # 反量化
        output = (output_q.astype(np.float32) - x_zero_point * w_zero_point) * x_scale * w_scale

        if bias is not None:
            output += bias

        return {'output': output}


class QuantizedLinearPerChannel:
    """
    逐通道量化全连接算子

    每个输出通道使用独立的量化参数
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行逐通道量化全连接

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        # 量化参数
        x_scale = params.get('x_scale', 1.0)
        x_zero_point = params.get('x_zero_point', 0)
        w_scales = params.get('w_scales')  # [out_channels]
        w_zero_points = params.get('w_zero_points')  # [out_channels]

        # 量化输入
        x_q = np.clip(
            np.round(x / x_scale) + x_zero_point, -128, 127
        ).astype(np.int8)

        out_features = weight.shape[0]
        output = np.zeros((x.shape[0], out_features), dtype=np.float32)

        # 逐通道量化矩阵乘法
        for oc in range(out_features):
            # 量化当前通道的权重
            w_q = np.clip(
                np.round(weight[oc] / w_scales[oc]) + w_zero_points[oc], -128, 127
            ).astype(np.int8)

            # 整数矩阵乘法
            output_q = np.dot(x_q.astype(np.int32), w_q.astype(np.int32))

            # 反量化
            output[:, oc] = (output_q.astype(np.float32) - x_zero_point * w_zero_points[oc]) * x_scale * w_scales[oc]

        if bias is not None:
            output += bias

        return {'output': output}
