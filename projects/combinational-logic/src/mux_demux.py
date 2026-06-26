"""
多路选择器和解复用器模块
Multiplexer and Demultiplexer Module

多路选择器（MUX）：从多个输入中选择一个输出
- 2:1 MUX: 2个输入，1个选择线
- 4:1 MUX: 4个输入，2个选择线
- 8:1 MUX: 8个输入，3个选择线

解复用器（DEMUX）：将单个输入路由到一个输出
- 与MUX功能相反
"""

from src.gates import AND, OR, NOT


class Multiplexer2to1:
    """
    2:1多路选择器
    2:1 Multiplexer

    真值表:
    S | Y
    0 | I0
    1 | I1

    Y = (I0 AND NOT(S)) OR (I1 AND S)
    """

    def __init__(self):
        self.sel_not = NOT()
        self.and0 = AND()
        self.and1 = AND()
        self.or_gate = OR()

    def select(self, i0: int, i1: int, s: int) -> int:
        """
        Args:
            i0: 输入0
            i1: 输入1
            s: 选择线

        Returns:
            选中的输出
        """
        if s not in (0, 1):
            raise ValueError("Select line must be 0 or 1")
        if i0 not in (0, 1) or i1 not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        # Y = (I0 AND NOT(S)) OR (I1 AND S)
        term0 = self.and0.evaluate(i0, self.sel_not.evaluate(s))
        term1 = self.and1.evaluate(i1, s)
        return self.or_gate.evaluate(term0, term1)


class Multiplexer4to1:
    """
    4:1多路选择器
    4:1 Multiplexer

    真值表:
    S1 S0 | Y
    0  0  | I0
    0  1  | I1
    1  0  | I2
    1  1  | I3

    Y = I0·S1'·S0' + I1·S1'·S0 + I2·S1·S0' + I3·S1·S0
    """

    def __init__(self):
        self.s0_not = NOT()
        self.s1_not = NOT()
        self.gates_and = [AND() for _ in range(4)]
        self.or_gate = OR()

    def select(self, i0: int, i1: int, i2: int, i3: int, s1: int, s0: int) -> int:
        """
        Args:
            i0-i3: 四个输入
            s1, s0: 选择线

        Returns:
            选中的输出
        """
        if s1 not in (0, 1) or s0 not in (0, 1):
            raise ValueError("Select lines must be 0 or 1")
        for val in [i0, i1, i2, i3]:
            if val not in (0, 1):
                raise ValueError("Inputs must be 0 or 1")

        # 解码选择线
        term0 = self.gates_and[0].evaluate(i0, self.s0_not.evaluate(s0), self.s1_not.evaluate(s1))
        term1 = self.gates_and[1].evaluate(i1, self.s0.evaluate(s0), self.s1_not.evaluate(s1))
        term2 = self.gates_and[2].evaluate(i2, self.s0_not.evaluate(s0), self.s1.evaluate(s1))
        term3 = self.gates_and[3].evaluate(i3, self.s0.evaluate(s0), self.s1.evaluate(s1))

        return self.or_gate.evaluate(term0, term1, term2, term3)

    @property
    def s0(self):
        return self.gates_and[1]  # reference for property access

    @property
    def s1(self):
        return self.gates_and[2]  # reference for property access


class Multiplexer8to1:
    """
    8:1多路选择器
    8:1 Multiplexer

    使用3个选择线从8个输入中选择一个。
    可以通过级联两个4:1 MUX和一个2:1 MUX构建。

    Uses 3 select lines to choose from 8 inputs.
    Can be built by cascading two 4:1 MUXes and one 2:1 MUX.
    """

    def __init__(self):
        self.sel_gates = [NOT() for _ in range(3)]
        self.and_gates = [AND() for _ in range(8)]
        self.or_gate = OR()

    def select(self, inputs: list, s2: int, s1: int, s0: int) -> int:
        """
        Args:
            inputs: 8个输入列表
            s2, s1, s0: 选择线

        Returns:
            选中的输出
        """
        if len(inputs) != 8:
            raise ValueError("Must have exactly 8 inputs")
        for val in inputs:
            if val not in (0, 1):
                raise ValueError("Inputs must be 0 or 1")
        if s2 not in (0, 1) or s1 not in (0, 1) or s0 not in (0, 1):
            raise ValueError("Select lines must be 0 or 1")

        # 解码选择线并生成输出
        # 将选择线组合成索引
        index = (s2 << 2) | (s1 << 1) | s0
        return inputs[index]


class Demultiplexer1to2:
    """
    1:2解复用器
    1:1 Demultiplexer

    将单个输入路由到8个输出之一。
    EN为使能端，低电平有效。

    Routes single input to one of 8 outputs.
    EN is enable pin, active low.
    """

    def __init__(self):
        self.en_not = NOT()

    def distribute(self, data: int, en: int, sel: int) -> int:
        """
        Args:
            data: 输入数据
            en: 使能信号 (0=使能, 1=禁用)
            sel: 选择线

        Returns:
            选中的输出（其他输出为0）
        """
        if data not in (0, 1) or en not in (0, 1) or sel not in (0, 1):
            raise ValueError("All inputs must be 0 or 1")

        # 如果使能为高，所有输出为0
        if en == 1:
            return 0

        # 根据选择线输出数据
        return data if sel == 1 else 0


class Demultiplexer1to8:
    """
    1:8解复用器
    1:8 Demultiplexer

    将单个输入路由到8个输出之一。
    Sel选择哪个输出线接收数据。

    Routes single input to one of 8 outputs.
    Sel determines which output line receives the data.
    """

    def __init__(self):
        self.sel_not = [NOT() for _ in range(3)]

    def distribute(self, data: int, en: int, sel: int) -> list:
        """
        Args:
            data: 输入数据 (0或1)
            en: 使能信号 (0=使能, 1=禁用)
            sel: 3位选择线 (0-7)

        Returns:
            8位输出列表
        """
        if data not in (0, 1) or en not in (0, 1):
            raise ValueError("Data and enable must be 0 or 1")
        if not (0 <= sel <= 7):
            raise ValueError("Select must be 0-7")

        # 如果使能为高，所有输出为0
        if en == 1:
            return [0] * 8

        # 初始化所有输出为0
        outputs = [0] * 8
        # 将数据放到选中的输出线
        outputs[sel] = data

        return outputs
