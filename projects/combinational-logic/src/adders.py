"""
半加器和全加器模块
Half Adder and Full Adder Module

加法器是组合逻辑电路中最核心的组件之一。
- 半加器：处理两个1位二进制数的加法
- 全加器：处理三个1位二进制数的加法（包含进位输入）
- 多位加法器：通过级联全加器实现

Adders are one of the most fundamental components in combinational logic.
- Half Adder: adds two 1-bit numbers
- Full Adder: adds three 1-bit numbers (includes carry-in)
- Multi-bit Adder: cascaded full adders
"""

from src.gates import XOR, AND, OR, NOT


class HalfAdder:
    """
    半加器 - 两个1位二进制数相加
    Half Adder - adds two 1-bit binary numbers

    真值表 (Truth Table):
    A | B | Sum | Carry
    0 | 0 |  0  |   0
    0 | 1 |  1  |   0
    1 | 0 |  1  |   0
    1 | 1 |  0  |   1

    Sum = A XOR B
    Carry = A AND B
    """

    def __init__(self):
        self.sum_gate = XOR()
        self.carry_gate = AND()

    def add(self, a: int, b: int) -> tuple:
        """
        执行半加运算

        Args:
            a: 第一个1位输入
            b: 第二个1位输入

        Returns:
            (sum, carry) 元组
        """
        if a not in (0, 1) or b not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")
        s = self.sum_gate.evaluate(a, b)
        c = self.carry_gate.evaluate(a, b)
        return s, c


class FullAdder:
    """
    全加器 - 三个1位二进制数相加（包含进位）
    Full Adder - adds three 1-bit binary numbers (with carry-in)

    真值表 (Truth Table):
    A | B | Cin | Sum | Cout
    0 | 0 |  0  |  0  |   0
    0 | 0 |  1  |  1  |   0
    0 | 1 |  0  |  1  |   0
    0 | 1 |  1  |  0  |   1
    1 | 0 |  0  |  1  |   0
    1 | 0 |  1  |  0  |   1
    1 | 1 |  0  |  0  |   1
    1 | 1 |  1  |  1  |   1

    Sum = A XOR B XOR Cin
    Cout = (A AND B) OR (Cin AND (A XOR B))
    """

    def __init__(self):
        # 使用两个半加器和一个或门构建全加器
        # Build full adder from two half adders and one OR gate
        self.ha1 = HalfAdder()
        self.ha2 = HalfAdder()
        self.carry_or = OR()

    def add(self, a: int, b: int, cin: int = 0) -> tuple:
        """
        执行全加运算

        Args:
            a: 第一个1位输入
            b: 第二个1位输入
            cin: 进位输入

        Returns:
            (sum, carry_out) 元组
        """
        if a not in (0, 1) or b not in (0, 1) or cin not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        # 第一级半加器：A + B
        sum1, carry1 = self.ha1.add(a, b)
        # 第二级半加器：sum1 + Cin
        sum_out, carry2 = self.ha2.add(sum1, cin)
        # 最终进位 = carry1 OR carry2
        cout = self.carry_or.evaluate(carry1, carry2)

        return sum_out, cout


class RippleCarryAdder:
    """
    行波进位加法器 - 多位二进制数加法
    Ripple Carry Adder - multi-bit binary addition

    通过将多个全加器级联来实现多位加法。
    最低位的进位输入接地（为0），最高位的进位输出为溢出标志。

    Key concept: The carry ripples through each stage,
    which limits speed for large adders.
    """

    def __init__(self, num_bits: int = 4):
        """
        Args:
            num_bits: 加法器的位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be at least 1")
        self.num_bits = num_bits
        self.full_adders = [FullAdder() for _ in range(num_bits)]

    def add(self, a: int, b: int) -> tuple:
        """
        执行多位二进制加法

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            (result, carry_out) 元组
            result: 加法结果的整数值
            carry_out: 最终进位输出
        """
        if a < 0 or b < 0:
            raise ValueError("Inputs must be non-negative")

        carry = 0
        result = 0

        for i in range(self.num_bits):
            # 提取第i位
            bit_a = (a >> i) & 1
            bit_b = (b >> i) & 1

            # 当前位的全加
            sum_bit, carry = self.full_adders[i].add(bit_a, bit_b, carry)

            # 累加结果
            result |= (sum_bit << i)

        return result, carry

    def add_signed(self, a: int, b: int) -> tuple:
        """
        执行有符号数加法（补码表示）

        Args:
            a: 第一个有符号数
            b: 第二个有符号数

        Returns:
            (result, carry_out, overflow) 元组
        """
        # 将负数转换为补码表示
        max_val = (1 << (self.num_bits - 1)) - 1
        min_val = -(1 << (self.num_bits - 1))

        if not (min_val <= a <= max_val) or not (min_val <= b <= max_val):
            raise ValueError(f"Input out of range [{min_val}, {max_val}]")

        # 将负数转换为num_bits位补码
        a_unsigned = a & ((1 << self.num_bits) - 1)
        b_unsigned = b & ((1 << self.num_bits) - 1)

        result_unsigned, carry = self.add(a_unsigned, b_unsigned)
        result_signed = result_unsigned & ((1 << self.num_bits) - 1)

        # 检测溢出：两个正数相加得到负数，或两个负数相加得到正数
        # 使用原始输入的符号位
        a_sign = 0 if a >= 0 else 1
        b_sign = 0 if b >= 0 else 1
        result_sign = (result_signed >> (self.num_bits - 1)) & 1

        overflow = (a_sign == b_sign) and (a_sign != result_sign)

        # 如果未溢出，将结果转换回有符号数
        if result_sign and not overflow:
            result_signed = result_signed - (1 << self.num_bits)

        return result_signed, carry, overflow


class Subtracter:
    """
    减法器 - 利用加法器实现减法
    Subtracter - subtraction using adder

    减法可以通过补码转换为加法：A - B = A + (~B + 1)
    即：A - B = A + (B的补码)
    """

    def __init__(self, num_bits: int = 4):
        """
        Args:
            num_bits: 减法器位数
        """
        self.num_bits = num_bits
        self.adder = RippleCarryAdder(num_bits)
        self.inverters = [NOT() for _ in range(num_bits)]

    def subtract(self, a: int, b: int) -> int:
        """
        执行无符号数减法

        Args:
            a: 被减数
            b: 减数

        Returns:
            差值
        """
        if a < b:
            raise ValueError("Result would be negative for unsigned subtraction")

        # 计算B的补码：~B + 1
        b_inverted = 0
        for i in range(self.num_bits):
            bit_b = (b >> i) & 1
            b_inverted |= ((NOT().evaluate(bit_b)) << i)

        # A + (~B + 1)
        result, _ = self.adder.add(a, b_inverted + 1)
        return result

    def subtract_signed(self, a: int, b: int) -> int:
        """
        执行有符号数减法

        Args:
            a: 被减数
            b: 减数

        Returns:
            差值
        """
        # A - B = A + (-B)
        max_val = (1 << (self.num_bits - 1)) - 1
        min_val = -(1 << (self.num_bits - 1))

        if not (min_val <= a <= max_val) or not (min_val <= b <= max_val):
            raise ValueError(f"Input out of range [{min_val}, {max_val}]")

        # 对B取负：按位取反加1
        b_neg = ((~b) + 1) & ((1 << self.num_bits) - 1)

        # 使用无符号加法
        result_unsigned, _ = self.adder.add(a & ((1 << self.num_bits) - 1), b_neg)
        result_signed = result_unsigned & ((1 << self.num_bits) - 1)

        # 转换回有符号数
        if result_signed >= (1 << (self.num_bits - 1)):
            result_signed = result_signed - (1 << self.num_bits)

        return result_signed
