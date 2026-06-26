"""
组合逻辑电路模拟 - 组合逻辑基础模块
Combinational Logic Circuit Simulation - Core Module

组合逻辑电路的特点：
- 输出仅取决于当前输入
- 没有记忆功能（无反馈）
- 由基本逻辑门（与、或、非、异或）构成
- 关键特性：传播延迟、无时钟依赖

Combinational logic circuits:
- Output depends only on current inputs
- No memory (no feedback)
- Built from basic gates (AND, OR, NOT, XOR)
- Key characteristics: propagation delay, no clock dependency
"""


class Gate:
    """
    基本逻辑门基类
    Base logic gate class

    所有逻辑门都继承此类，实现基本的布尔运算。
    """

    def __init__(self, name: str = "Gate", propagation_delay: float = 1.0):
        """
        Args:
            name: 门电路名称
            propagation_delay: 传播延迟（纳秒）
        """
        self.name = name
        self.propagation_delay = propagation_delay

    def evaluate(self, *inputs: int) -> int:
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"


class AND(Gate):
    """
    与门 - 所有输入为1时输出为1
    AND gate - output is 1 only when all inputs are 1
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("AND", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        return 1 if all(i == 1 for i in inputs) else 0


class OR(Gate):
    """
    或门 - 任一输入为1时输出为1
    OR gate - output is 1 when any input is 1
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("OR", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        return 1 if any(i == 1 for i in inputs) else 0


class NOT(Gate):
    """
    非门 - 输入取反
    NOT gate - inverts the input
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("NOT", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        if not inputs:
            raise ValueError("NOT gate requires exactly 1 input")
        return 0 if inputs[0] == 1 else 1


class XOR(Gate):
    """
    异或门 - 输入不同则输出为1
    XOR gate - output is 1 when inputs differ
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("XOR", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        if len(inputs) != 2:
            raise ValueError("XOR gate requires exactly 2 inputs")
        return 1 if inputs[0] != inputs[1] else 0


class NAND(Gate):
    """
    与非门 - 与门的反相输出
    NAND gate - inverted AND output
    通用门：可以用NAND门构建所有其他逻辑门
    Universal gate: all other gates can be built from NAND
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("NAND", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        and_result = AND().evaluate(*inputs)
        return NOT().evaluate(and_result)


class NOR(Gate):
    """
    或非门 - 或门的反相输出
    NOR gate - inverted OR output
    通用门：可以用NOR门构建所有其他逻辑门
    Universal gate: all other gates can be built from NOR
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("NOR", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        or_result = OR().evaluate(*inputs)
        return NOT().evaluate(or_result)


class XNOR(Gate):
    """
    同或门 - 输入相同时输出为1
    XNOR gate - output is 1 when inputs are equal
    """

    def __init__(self, propagation_delay: float = 1.0):
        super().__init__("XNOR", propagation_delay)

    def evaluate(self, *inputs: int) -> int:
        if len(inputs) != 2:
            raise ValueError("XNOR gate requires exactly 2 inputs")
        return 1 if inputs[0] == inputs[1] else 0
