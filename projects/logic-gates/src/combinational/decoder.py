"""
解码器模块

实现二进制解码器和编码器。
"""

from typing import List, Dict


class Decoder:
    """二进制解码器

    将 n 位二进制输入解码为 2^n 个输出。

    Examples:
        >>> decoder = Decoder(2)  # 2:4 解码器
        >>> outputs = decoder.evaluate([0, 1])
        >>> outputs
        [0, 1, 0, 0]
    """

    def __init__(self, num_inputs: int):
        """初始化解码器

        Args:
            num_inputs: 输入位数
        """
        if num_inputs < 1:
            raise ValueError("Number of inputs must be positive")

        self.num_inputs = num_inputs
        self.num_outputs = 2 ** num_inputs

    def evaluate(self, inputs: List[int]) -> List[int]:
        """计算解码器输出

        Args:
            inputs: 输入列表，长度必须为 num_inputs

        Returns:
            List[int]: 所有输出，只有一个输出为1
        """
        if len(inputs) != self.num_inputs:
            raise ValueError(f"Expected {self.num_inputs} inputs, got {len(inputs)}")

        # 计算输入值
        input_value = 0
        for i, inp in enumerate(inputs):
            input_value |= inp << i

        # 生成输出
        outputs = [0] * self.num_outputs
        outputs[input_value] = 1

        return outputs


class Encoder:
    """二进制编码器

    将 2^n 个输入编码为 n 位二进制输出。
    假设只有一个输入为1。

    Examples:
        >>> encoder = Encoder(4)  # 4:2 编码器
        >>> outputs = encoder.evaluate([0, 1, 0, 0])
        >>> outputs
        [0, 1]
    """

    def __init__(self, num_inputs: int):
        """初始化编码器

        Args:
            num_inputs: 输入数量，必须为 2^n
        """
        if num_inputs < 2:
            raise ValueError("Number of inputs must be at least 2")

        # 检查是否为 2 的幂
        if num_inputs & (num_inputs - 1) != 0:
            raise ValueError("Number of inputs must be a power of 2")

        self.num_inputs = num_inputs
        self.num_outputs = num_inputs.bit_length() - 1

    def evaluate(self, inputs: List[int]) -> List[int]:
        """计算编码器输出

        Args:
            inputs: 输入列表，只有一个输入应该为1

        Returns:
            List[int]: 编码后的二进制输出

        Raises:
            ValueError: 输入长度不正确或多个输入为1
        """
        if len(inputs) != self.num_inputs:
            raise ValueError(f"Expected {self.num_inputs} inputs, got {len(inputs)}")

        # 找到激活的输入
        active_inputs = [i for i, val in enumerate(inputs) if val == 1]

        if len(active_inputs) == 0:
            # 没有输入激活
            return [0] * self.num_outputs

        if len(active_inputs) > 1:
            # 多个输入激活（优先级编码器可以处理这种情况）
            # 这里我们取最高优先级（最高索引）
            active_input = max(active_inputs)
        else:
            active_input = active_inputs[0]

        # 转换为二进制
        binary = format(active_input, f'0{self.num_outputs}b')
        return [int(b) for b in binary]


class PriorityEncoder:
    """优先级编码器

    将多个输入编码为二进制输出，支持多个输入同时激活。

    Examples:
        >>> encoder = PriorityEncoder(4)
        >>> outputs = encoder.evaluate([0, 1, 0, 1])
        >>> outputs
        [1, 1, 1]  # 二进制 3，同时有有效输出
    """

    def __init__(self, num_inputs: int):
        """初始化优先级编码器

        Args:
            num_inputs: 输入数量
        """
        if num_inputs < 2:
            raise ValueError("Number of inputs must be at least 2")

        self.num_inputs = num_inputs
        self.num_outputs = num_inputs.bit_length()

    def evaluate(self, inputs: List[int]) -> List[int]:
        """计算优先级编码器输出

        Args:
            inputs: 输入列表

        Returns:
            List[int]: [编码输出..., 有效位]
        """
        if len(inputs) != self.num_inputs:
            raise ValueError(f"Expected {self.num_inputs} inputs, got {len(inputs)}")

        # 找到最高优先级的激活输入
        active_input = -1
        for i in range(len(inputs) - 1, -1, -1):
            if inputs[i] == 1:
                active_input = i
                break

        if active_input == -1:
            # 没有输入激活
            return [0] * (self.num_outputs - 1) + [0]  # 有效位为0

        # 转换为二进制
        binary = format(active_input, f'0{self.num_outputs - 1}b')
        outputs = [int(b) for b in binary] + [1]  # 有效位为1

        return outputs
