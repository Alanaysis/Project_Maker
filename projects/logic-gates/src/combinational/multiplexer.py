"""
多路选择器模块

实现多路选择器(MUX)和多路分配器(DEMUX)。
"""

from typing import List, Dict
from ..gates import AndGate, OrGate, NotGate
from ..circuit import Circuit


class Multiplexer:
    """多路选择器

    根据选择信号从多个输入中选择一个输出。

    支持 2^n 个输入，n 个选择线。

    Examples:
        >>> mux = Multiplexer(2)  # 4选1
        >>> mux.evaluate([1, 0, 1, 0], [0, 1])
        0
        >>> mux.evaluate([1, 0, 1, 0], [1, 0])
        1
    """

    def __init__(self, num_select_lines: int):
        """初始化多路选择器

        Args:
            num_select_lines: 选择线数量，输入数量为 2^n

        Raises:
            ValueError: 选择线数量必须为正整数
        """
        if num_select_lines < 1:
            raise ValueError("Number of select lines must be positive")

        self.num_select = num_select_lines
        self.num_inputs = 2 ** num_select_lines

    def evaluate(self, data_inputs: List[int], select_inputs: List[int]) -> int:
        """计算多路选择器输出

        Args:
            data_inputs: 数据输入列表，长度必须为 2^n
            select_inputs: 选择输入列表，长度必须为 n

        Returns:
            int: 选中的输入值

        Raises:
            ValueError: 输入长度不正确
        """
        if len(data_inputs) != self.num_inputs:
            raise ValueError(f"Expected {self.num_inputs} data inputs, got {len(data_inputs)}")
        if len(select_inputs) != self.num_select:
            raise ValueError(f"Expected {self.num_select} select inputs, got {len(select_inputs)}")

        # 计算选择索引
        select_index = 0
        for i, s in enumerate(select_inputs):
            select_index |= s << i

        return data_inputs[select_index]

    def truth_table(self) -> List[Dict]:
        """生成真值表

        Returns:
            List[Dict]: 真值表
        """
        from itertools import product

        table = []
        for data in product([0, 1], repeat=self.num_inputs):
            for select in product([0, 1], repeat=self.num_select):
                output = self.evaluate(list(data), list(select))
                table.append({
                    "data_inputs": list(data),
                    "select_inputs": list(select),
                    "output": output
                })

        return table


class Demultiplexer:
    """多路分配器

    根据选择信号将输入分配到多个输出中的一个。

    Examples:
        >>> demux = Demultiplexer(2)  # 1:4
        >>> outputs = demux.evaluate(1, [0, 1])
        >>> outputs
        [0, 1, 0, 0]
    """

    def __init__(self, num_select_lines: int):
        """初始化多路分配器

        Args:
            num_select_lines: 选择线数量，输出数量为 2^n
        """
        if num_select_lines < 1:
            raise ValueError("Number of select lines must be positive")

        self.num_select = num_select_lines
        self.num_outputs = 2 ** num_select_lines

    def evaluate(self, data_input: int, select_inputs: List[int]) -> List[int]:
        """计算多路分配器输出

        Args:
            data_input: 数据输入
            select_inputs: 选择输入列表

        Returns:
            List[int]: 所有输出，被选中的输出等于输入值
        """
        if len(select_inputs) != self.num_select:
            raise ValueError(f"Expected {self.num_select} select inputs, got {len(select_inputs)}")

        # 计算选择索引
        select_index = 0
        for i, s in enumerate(select_inputs):
            select_index |= s << i

        # 生成输出
        outputs = [0] * self.num_outputs
        outputs[select_index] = data_input

        return outputs
