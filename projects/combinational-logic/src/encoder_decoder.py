"""
编码器和译码器模块
Encoder and Decoder Module

编码器：将多个输入编码为较少位数的输出
- 二进制编码器：8线-3线编码
- BCD编码器：10线-4线编码（十进制）

译码器：将较少位数的输入解码为多个输出
- 二进制译码器：3线-8线译码（3-8 decoder）
- BCD译码器：4线-10线译码（4-10 decoder）
- 7段译码器：驱动7段数码管

Encoder: encodes multiple inputs into fewer output bits
- Binary encoder: 8-to-3 line encoder
- BCD encoder: 10-to-4 line encoder (decimal)

Decoder: decodes fewer input bits into multiple outputs
- Binary decoder: 3-to-8 line decoder
- BCD decoder: 4-to-10 line decoder
- 7-segment decoder: drives 7-segment displays
"""

from src.gates import AND, OR, NOT


class BinaryEncoder:
    """
    二进制编码器（优先编码器）
    Binary Encoder (Priority Encoder)

    8线-3线优先编码器：
    - 输入I7优先级最高，I0优先级最低
    - 输出为输入中最高优先级有效位的3位二进制编码

    8-to-3 Priority Encoder:
    - I7 has highest priority, I0 has lowest
    - Output is 3-bit binary code of highest priority active input
    """

    def __init__(self):
        self.out_gates = [OR() for _ in range(3)]

    def encode(self, inputs: list) -> int:
        """
        对8个输入进行编码

        Args:
            inputs: 8个输入列表（高优先在前）

        Returns:
            3位二进制编码 (0-7)
        """
        if len(inputs) != 8:
            raise ValueError("Must have exactly 8 inputs")
        for val in inputs:
            if val not in (0, 1):
                raise ValueError("Inputs must be 0 or 1")

        # 从最高优先级开始查找第一个有效输入
        # inputs[0] = I7 (最高优先级), inputs[7] = I0 (最低优先级)
        for priority in range(7, -1, -1):
            if inputs[7 - priority] == 1:
                return priority

        return 0  # 所有输入为0时


class BCDToBinaryEncoder:
    """
    BCD编码器：将十进制输入转换为4位二进制码
    BCD Encoder: converts decimal input to 4-bit binary code
    """

    def encode(self, decimal_input: int) -> int:
        """
        Args:
            decimal_input: 十进制输入 (0-9)

        Returns:
            4位BCD码
        """
        if not (0 <= decimal_input <= 9):
            raise ValueError("BCD input must be 0-9")
        return decimal_input


class BinaryDecoder:
    """
    二进制译码器（3线-8线）
    Binary Decoder (3-to-8 line)

    真值表:
    C B A | Y0 Y1 Y2 Y3 Y4 Y5 Y6 Y7
    0 0 0 | 1  0  0  0  0  0  0  0
    0 0 1 | 0  1  0  0  0  0  0  0
    0 1 0 | 0  0  1  0  0  0  0  0
    0 1 1 | 0  0  0  1  0  0  0  0
    1 0 0 | 0  0  0  0  1  0  0  0
    1 0 1 | 0  0  0  0  0  1  0  0
    1 1 0 | 0  0  0  0  0  0  1  0
    1 1 1 | 0  0  0  0  0  0  0  1

    输出：只有一个输出为1，其余为0
    Output: only one output is 1, rest are 0
    """

    def __init__(self):
        self.inverters = [NOT() for _ in range(3)]
        self.and_gates = [AND() for _ in range(8)]

    def decode(self, inputs: list) -> list:
        """
        将3位输入解码为8位输出

        Args:
            inputs: 3位输入 [C, B, A]

        Returns:
            8位输出列表
        """
        if len(inputs) != 3:
            raise ValueError("Must have exactly 3 inputs")
        for val in inputs:
            if val not in (0, 1):
                raise ValueError("Inputs must be 0 or 1")

        # 计算选中输出的索引
        index = (inputs[0] << 2) | (inputs[1] << 1) | inputs[2]

        # 初始化所有输出为0
        outputs = [0] * 8
        # 将选中输出设为1
        outputs[index] = 1

        return outputs


class BCDDecoder:
    """
    BCD译码器（4线-10线）
    BCD Decoder (4-to-10 line)

    将4位BCD码转换为10个十进制输出线。
    Converts 4-bit BCD code to 10 decimal output lines.
    """

    def decode(self, bcd_input: int) -> list:
        """
        Args:
            bcd_input: 4位BCD输入 (0-9)

        Returns:
            10位输出列表（十进制）
        """
        if not (0 <= bcd_input <= 9):
            raise ValueError("BCD input must be 0-9")

        outputs = [0] * 10
        outputs[bcd_input] = 1
        return outputs


class SevenSegmentDecoder:
    """
    7段译码器
    7-Segment Decoder

    将4位BCD码转换为7段数码管的驱动信号。
    段顺序：a, b, c, d, e, f, g

    Converts 4-bit BCD to 7-segment display drive signals.
    Segment order: a, b, c, d, e, f, g

    显示映射:
    0: 1111110  (a,b,c,d,e,f on)
    1: 0110000  (b,c on)
    2: 1101101  (a,b,d,e,g on)
    3: 1111001  (a,b,c,d,g on)
    4: 0110011  (b,c,f,g on)
    5: 1011011  (a,c,d,f,g on)
    6: 1011111  (a,c,d,e,f,g on)
    7: 1110000  (a,b,c on)
    8: 1111111  (all on)
    9: 1111011  (a,b,c,d,f,g on)
    """

    # 段映射: digit -> [a, b, c, d, e, f, g]
    SEGMENT_MAP = {
        0: [1, 1, 1, 1, 1, 1, 0],
        1: [0, 1, 1, 0, 0, 0, 0],
        2: [1, 1, 0, 1, 1, 0, 1],
        3: [1, 1, 1, 1, 0, 0, 1],
        4: [0, 1, 1, 0, 0, 1, 1],
        5: [1, 0, 1, 1, 0, 1, 1],
        6: [1, 0, 1, 1, 1, 1, 1],
        7: [1, 1, 1, 0, 0, 0, 0],
        8: [1, 1, 1, 1, 1, 1, 1],
        9: [1, 1, 1, 1, 0, 1, 1],
    }

    def decode(self, bcd_input: int, dp: int = 0) -> list:
        """
        Args:
            bcd_input: 4位BCD输入 (0-9)
            dp: 小数点 (0或1)

        Returns:
            8位输出 [a, b, c, d, e, f, g, dp]
        """
        if not (0 <= bcd_input <= 9):
            raise ValueError("BCD input must be 0-9")
        if dp not in (0, 1):
            raise ValueError("Decimal point must be 0 or 1")

        segments = self.SEGMENT_MAP[bcd_input].copy()
        segments.append(dp)
        return segments

    def display_char(self, bcd_input: int) -> str:
        """
        获取7段数码管显示的字符表示

        Returns:
            字符表示
        """
        # 使用ASCII字符模拟7段显示
        char_map = {
            0: "0", 1: "1", 2: "2", 3: "3", 4: "4",
            5: "5", 6: "6", 7: "7", 8: "8", 9: "9"
        }
        return char_map.get(bcd_input, "?")
