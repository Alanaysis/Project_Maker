"""
卷积算子模块

提供卷积算子的实现，包括：
- 普通卷积
- 量化卷积
- 深度可分离卷积
"""

import numpy as np
from typing import Dict, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class Conv2dOperator:
    """
    卷积算子

    实现 2D 卷积操作
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行卷积

        Args:
            inputs: 输入字典，包含 'input', 'weight', 'bias'（可选）
            params: 卷积参数

        Returns:
            输出字典
        """
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        stride = params.get('stride', 1)
        padding = params.get('padding', 0)
        groups = params.get('groups', 1)

        output = self.conv2d(x, weight, bias, stride, padding, groups)

        return {'output': output}

    def conv2d(
        self,
        x: np.ndarray,
        weight: np.ndarray,
        bias: Optional[np.ndarray],
        stride: int = 1,
        padding: int = 0,
        groups: int = 1,
    ) -> np.ndarray:
        """
        2D 卷积实现

        Args:
            x: 输入 [batch, in_channels, height, width]
            weight: 权重 [out_channels, in_channels, kernel_h, kernel_w]
            bias: 偏置 [out_channels]
            stride: 步长
            padding: 填充
            groups: 分组数

        Returns:
            输出 [batch, out_channels, out_height, out_width]
        """
        batch, in_channels, h, w = x.shape
        out_channels, _, kh, kw = weight.shape

        # 验证输入
        assert in_channels % groups == 0, "输入通道数必须能被分组数整除"
        assert out_channels % groups == 0, "输出通道数必须能被分组数整除"

        # 添加 padding
        if padding > 0:
            x = np.pad(
                x,
                ((0, 0), (0, 0), (padding, padding), (padding, padding)),
                mode='constant',
            )

        # 计算输出尺寸
        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        # 初始化输出
        output = np.zeros((batch, out_channels, out_h, out_w))

        # 分组卷积
        in_channels_per_group = in_channels // groups
        out_channels_per_group = out_channels // groups

        for g in range(groups):
            # 当前组的输入和权重
            x_group = x[:, g * in_channels_per_group:(g + 1) * in_channels_per_group]
            w_group = weight[g * out_channels_per_group:(g + 1) * out_channels_per_group]

            # 卷积计算
            for b in range(batch):
                for oc in range(out_channels_per_group):
                    for oh in range(out_h):
                        for ow in range(out_w):
                            h_start = oh * stride
                            w_start = ow * stride
                            receptive_field = x_group[
                                b, :, h_start:h_start + kh, w_start:w_start + kw
                            ]
                            output[b, g * out_channels_per_group + oc, oh, ow] = np.sum(
                                receptive_field * w_group[oc]
                            )

        # 添加偏置
        if bias is not None:
            output += bias.reshape(1, -1, 1, 1)

        return output

    def compute_output_shape(
        self,
        input_shape: Tuple[int, ...],
        weight_shape: Tuple[int, ...],
        stride: int = 1,
        padding: int = 0,
    ) -> Tuple[int, ...]:
        """
        计算输出形状

        Args:
            input_shape: 输入形状 (batch, in_channels, height, width)
            weight_shape: 权重形状 (out_channels, in_channels, kernel_h, kernel_w)
            stride: 步长
            padding: 填充

        Returns:
            输出形状
        """
        batch, in_channels, h, w = input_shape
        out_channels, _, kh, kw = weight_shape

        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        return (batch, out_channels, out_h, out_w)


class QuantizedConv2d:
    """
    量化卷积算子

    实现 INT8 量化卷积
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行量化卷积

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
        output_scale = params.get('output_scale', 1.0)
        output_zero_point = params.get('output_zero_point', 0)

        stride = params.get('stride', 1)
        padding = params.get('padding', 0)

        # 量化输入
        x_q = np.clip(
            np.round(x / x_scale) + x_zero_point, -128, 127
        ).astype(np.int8)

        # 量化权重
        w_q = np.clip(
            np.round(weight / w_scale) + w_zero_point, -128, 127
        ).astype(np.int8)

        # 整数卷积
        output_q = self._int8_conv2d(x_q, w_q, stride, padding)

        # 反量化
        output = (output_q.astype(np.float32) - x_zero_point * w_zero_point) * x_scale * w_scale

        if bias is not None:
            output += bias

        return {'output': output}

    def _int8_conv2d(
        self,
        x: np.ndarray,
        weight: np.ndarray,
        stride: int = 1,
        padding: int = 0,
    ) -> np.ndarray:
        """
        INT8 卷积实现

        Args:
            x: 量化输入 [batch, in_channels, height, width]
            weight: 量化权重 [out_channels, in_channels, kernel_h, kernel_w]
            stride: 步长
            padding: 填充

        Returns:
            量化输出
        """
        batch, in_channels, h, w = x.shape
        out_channels, _, kh, kw = weight.shape

        # 添加 padding
        if padding > 0:
            x = np.pad(
                x,
                ((0, 0), (0, 0), (padding, padding), (padding, padding)),
                mode='constant',
            )

        # 计算输出尺寸
        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        # 初始化输出（使用 INT32 累加）
        output = np.zeros((batch, out_channels, out_h, out_w), dtype=np.int32)

        # 卷积计算
        for b in range(batch):
            for oc in range(out_channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[
                            b, :, h_start:h_start + kh, w_start:w_start + kw
                        ]
                        output[b, oc, oh, ow] = np.sum(
                            receptive_field.astype(np.int32) * weight[oc].astype(np.int32)
                        )

        return output


class DepthwiseConv2d:
    """
    深度可分离卷积

    每个通道独立卷积
    """

    def execute(
        self,
        inputs: Dict[str, np.ndarray],
        params: Dict[str, Any],
    ) -> Dict[str, np.ndarray]:
        """
        执行深度可分离卷积

        Args:
            inputs: 输入字典
            params: 参数字典

        Returns:
            输出字典
        """
        x = inputs['input']
        weight = inputs['weight']
        bias = inputs.get('bias')

        stride = params.get('stride', 1)
        padding = params.get('padding', 0)

        output = self.depthwise_conv2d(x, weight, bias, stride, padding)

        return {'output': output}

    def depthwise_conv2d(
        self,
        x: np.ndarray,
        weight: np.ndarray,
        bias: Optional[np.ndarray],
        stride: int = 1,
        padding: int = 0,
    ) -> np.ndarray:
        """
        深度可分离卷积实现

        Args:
            x: 输入 [batch, channels, height, width]
            weight: 权重 [channels, 1, kernel_h, kernel_w]
            bias: 偏置 [channels]
            stride: 步长
            padding: 填充

        Returns:
            输出 [batch, channels, out_height, out_width]
        """
        batch, channels, h, w = x.shape
        _, _, kh, kw = weight.shape

        # 添加 padding
        if padding > 0:
            x = np.pad(
                x,
                ((0, 0), (0, 0), (padding, padding), (padding, padding)),
                mode='constant',
            )

        # 计算输出尺寸
        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        # 初始化输出
        output = np.zeros((batch, channels, out_h, out_w))

        # 深度卷积
        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, c, h_start:h_start + kh, w_start:w_start + kw]
                        output[b, c, oh, ow] = np.sum(receptive_field * weight[c, 0])

        # 添加偏置
        if bias is not None:
            output += bias.reshape(1, -1, 1, 1)

        return output
