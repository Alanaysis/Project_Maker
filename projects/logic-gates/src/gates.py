# 逻辑门实现

"""
逻辑门模块

本模块实现了所有基本逻辑门，包括：
- AND（与门）
- OR（或门）
- NOT（非门）
- XOR（异或门）
- NAND（与非门）
- NOR（或非门）
- CustomGate（自定义门）

所有逻辑门都继承自Gate抽象基类，提供统一的接口。
"""

from abc import ABC, abstractmethod
from itertools import product
from typing import List, Tuple, Callable

from .signal import Signal
from .exceptions import InvalidInputError


class Gate(ABC):
    """逻辑门抽象基类

    所有逻辑门都必须继承此类并实现evaluate方法。

    Examples:
        >>> from logic_gates import AndGate
        >>> gate = AndGate()
        >>> gate.evaluate(1, 1)
        1
        >>> gate(1, 1)  # 可调用
        1
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """获取门名称

        Returns:
            str: 门的名称
        """
        pass

    @property
    @abstractmethod
    def num_inputs(self) -> int:
        """获取输入数量

        Returns:
            int: 输入数量
        """
        pass

    @abstractmethod
    def evaluate(self, *inputs: int) -> int:
        """计算输出

        Args:
            *inputs: 输入信号，每个为0或1

        Returns:
            int: 输出信号，0或1

        Raises:
            InvalidInputError: 输入信号无效
        """
        pass

    def truth_table(self) -> List[Tuple[List[int], int]]:
        """生成真值表

        Returns:
            真值表，每个元素为([输入组合], 输出)

        Examples:
            >>> gate = AndGate()
            >>> table = gate.truth_table()
            >>> len(table)
            4
        """
        table = []
        for inputs in product([0, 1], repeat=self.num_inputs):
            output = self.evaluate(*inputs)
            table.append((list(inputs), output))
        return table

    def __call__(self, *inputs: int) -> int:
        """使门可调用

        Args:
            *inputs: 输入信号

        Returns:
            int: 输出信号
        """
        return self.evaluate(*inputs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(inputs={self.num_inputs})"

    def __str__(self) -> str:
        return f"{self.name} Gate ({self.num_inputs} inputs)"

    def _validate_inputs(self, inputs: tuple):
        """验证输入

        Args:
            inputs: 输入元组

        Raises:
            InvalidInputError: 输入无效
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"{self.name} gate requires {self.num_inputs} input(s), "
                f"got {len(inputs)}"
            )

        for i, inp in enumerate(inputs):
            if inp not in (0, 1):
                raise InvalidInputError(
                    f"Invalid input at position {i}: {inp}. Must be 0 or 1"
                )


class AndGate(Gate):
    """与门

    所有输入为1时输出1。

    Truth Table:
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 1

    Examples:
        >>> gate = AndGate()
        >>> gate.evaluate(0, 0)
        0
        >>> gate.evaluate(1, 1)
        1
    """

    @property
    def name(self) -> str:
        return "AND"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算AND门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(all(inputs))


class OrGate(Gate):
    """或门

    任一输入为1时输出1。

    Truth Table:
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 1

    Examples:
        >>> gate = OrGate()
        >>> gate.evaluate(0, 0)
        0
        >>> gate.evaluate(0, 1)
        1
    """

    @property
    def name(self) -> str:
        return "OR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算OR门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(any(inputs))


class NotGate(Gate):
    """非门

    输入取反。

    Truth Table:
        A | OUT
        0 | 1
        1 | 0

    Examples:
        >>> gate = NotGate()
        >>> gate.evaluate(0)
        1
        >>> gate.evaluate(1)
        0
    """

    @property
    def name(self) -> str:
        return "NOT"

    @property
    def num_inputs(self) -> int:
        return 1

    def evaluate(self, *inputs: int) -> int:
        """计算NOT门输出

        Args:
            *inputs: 一个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(not inputs[0])


class XorGate(Gate):
    """异或门

    输入不同时输出1。

    Truth Table:
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 0

    Examples:
        >>> gate = XorGate()
        >>> gate.evaluate(0, 0)
        0
        >>> gate.evaluate(0, 1)
        1
        >>> gate.evaluate(1, 1)
        0
    """

    @property
    def name(self) -> str:
        return "XOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算XOR门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(sum(inputs) % 2 == 1)


class NandGate(Gate):
    """与非门

    AND门取反。

    Truth Table:
        A | B | OUT
        0 | 0 | 1
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 0

    Examples:
        >>> gate = NandGate()
        >>> gate.evaluate(0, 0)
        1
        >>> gate.evaluate(1, 1)
        0
    """

    @property
    def name(self) -> str:
        return "NAND"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算NAND门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(not all(inputs))


class NorGate(Gate):
    """或非门

    OR门取反。

    Truth Table:
        A | B | OUT
        0 | 0 | 1
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 0

    Examples:
        >>> gate = NorGate()
        >>> gate.evaluate(0, 0)
        1
        >>> gate.evaluate(1, 1)
        0
    """

    @property
    def name(self) -> str:
        return "NOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算NOR门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(not any(inputs))


class XnorGate(Gate):
    """同或门

    输入相同时输出1。

    Truth Table:
        A | B | OUT
        0 | 0 | 1
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 1

    Examples:
        >>> gate = XnorGate()
        >>> gate.evaluate(0, 0)
        1
        >>> gate.evaluate(0, 1)
        0
        >>> gate.evaluate(1, 1)
        1
    """

    @property
    def name(self) -> str:
        return "XNOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算XNOR门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return int(sum(inputs) % 2 == 0)


class Buffer(Gate):
    """缓冲器

    输入直通输出，用于信号驱动。

    Truth Table:
        A | OUT
        0 | 0
        1 | 1

    Examples:
        >>> gate = Buffer()
        >>> gate.evaluate(0)
        0
        >>> gate.evaluate(1)
        1
    """

    @property
    def name(self) -> str:
        return "BUF"

    @property
    def num_inputs(self) -> int:
        return 1

    def evaluate(self, *inputs: int) -> int:
        """计算缓冲器输出

        Args:
            *inputs: 一个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        return inputs[0]


class CustomGate(Gate):
    """自定义逻辑门

    允许用户定义自己的逻辑门。

    Args:
        name: 门名称
        num_inputs: 输入数量
        logic_func: 逻辑函数，接收输入参数，返回0或1

    Examples:
        >>> def majority(*inputs):
        ...     return int(sum(inputs) > len(inputs) / 2)
        >>> gate = CustomGate("MAJ", 3, majority)
        >>> gate.evaluate(1, 1, 0)
        1
        >>> gate.evaluate(0, 0, 1)
        0
    """

    def __init__(self, name: str, num_inputs: int, logic_func: Callable):
        self._name = name
        self._num_inputs = num_inputs
        self._logic_func = logic_func

    @property
    def name(self) -> str:
        return self._name

    @property
    def num_inputs(self) -> int:
        return self._num_inputs

    def evaluate(self, *inputs: int) -> int:
        """计算自定义门输出

        Args:
            *inputs: 输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        self._validate_inputs(inputs)
        result = self._logic_func(*inputs)

        # 验证输出
        if result not in (0, 1):
            raise InvalidInputError(
                f"Custom gate function must return 0 or 1, got {result}"
            )

        return result
