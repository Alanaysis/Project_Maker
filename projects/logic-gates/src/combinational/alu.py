"""
算术逻辑单元(ALU)模块

实现简单的ALU，支持基本算术和逻辑运算。
"""

from typing import List, Dict, Tuple
from ..gates import AndGate, OrGate, XorGate, NotGate
from .adder import RippleCarryAdder
from .comparator import Comparator


class ALU:
    """算术逻辑单元

    支持的操作：
    - 0000: ADD (加法)
    - 0001: SUB (减法)
    - 0010: AND (按位与)
    - 0011: OR  (按位或)
    - 0100: XOR (按位异或)
    - 0101: NOT (按位取反)
    - 0110: SHL (左移)
    - 0111: SHR (右移)
    - 1000: CMP (比较)

    Examples:
        >>> alu = ALU(4)  # 4位ALU
        >>> result = alu.evaluate([0, 1, 0, 1], [0, 0, 1, 1], [0, 0, 0, 0])
        >>> result['result']
        [1, 0, 0, 0]  # 5 + 3 = 8
    """

    # 操作码定义
    OP_ADD = [0, 0, 0, 0]
    OP_SUB = [0, 0, 0, 1]
    OP_AND = [0, 0, 1, 0]
    OP_OR  = [0, 0, 1, 1]
    OP_XOR = [0, 1, 0, 0]
    OP_NOT = [0, 1, 0, 1]
    OP_SHL = [0, 1, 1, 0]
    OP_SHR = [0, 1, 1, 1]
    OP_CMP = [1, 0, 0, 0]

    def __init__(self, num_bits: int):
        """初始化ALU

        Args:
            num_bits: 数据位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._adder = RippleCarryAdder(num_bits)
        self._comparator = Comparator(num_bits)

    def evaluate(self, a: List[int], b: List[int], op: List[int]) -> Dict:
        """执行ALU操作

        Args:
            a: 第一个操作数（二进制列表，高位在前）
            b: 第二个操作数（二进制列表，高位在前）
            op: 操作码（4位）

        Returns:
            Dict: {
                'result': 计算结果,
                'zero': 零标志,
                'carry': 进位标志,
                'negative': 负数标志,
                'overflow': 溢出标志
            }
        """
        if len(a) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for a, got {len(a)}")
        if len(b) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for b, got {len(b)}")
        if len(op) != 4:
            raise ValueError("Opcode must be 4 bits")

        # 转换操作码为整数
        op_int = 0
        for i, bit in enumerate(op):
            op_int |= bit << (3 - i)

        # 执行操作
        result = [0] * self.num_bits
        carry = 0
        overflow = 0

        if op_int == 0:  # ADD
            # 转换为低位在前的格式
            a_rev = list(reversed(a))
            b_rev = list(reversed(b))
            result_rev, carry = self._adder.evaluate(a_rev, b_rev)
            result = list(reversed(result_rev))

        elif op_int == 1:  # SUB
            # A - B = A + NOT(B) + 1
            b_not = [1 - bit for bit in b]
            a_rev = list(reversed(a))
            b_not_rev = list(reversed(b_not))
            result_rev, carry = self._adder.evaluate(a_rev, b_not_rev, 1)
            result = list(reversed(result_rev))

        elif op_int == 2:  # AND
            result = [a[i] and b[i] for i in range(self.num_bits)]

        elif op_int == 3:  # OR
            result = [a[i] or b[i] for i in range(self.num_bits)]

        elif op_int == 4:  # XOR
            result = [a[i] ^ b[i] for i in range(self.num_bits)]

        elif op_int == 5:  # NOT
            result = [1 - bit for bit in a]

        elif op_int == 6:  # SHL
            # 左移 B 位
            shift_amount = self._bits_to_int(b)
            shift_amount = min(shift_amount, self.num_bits)
            result = a[shift_amount:] + [0] * shift_amount

        elif op_int == 7:  # SHR
            # 右移 B 位
            shift_amount = self._bits_to_int(b)
            shift_amount = min(shift_amount, self.num_bits)
            result = [0] * shift_amount + a[:self.num_bits - shift_amount]

        elif op_int == 8:  # CMP
            cmp_result = self._comparator.evaluate(a, b)
            # 将比较结果编码为单个值
            if cmp_result['gt']:
                result = [0] * (self.num_bits - 1) + [1]
            elif cmp_result['eq']:
                result = [0] * self.num_bits
            else:
                result = [1] + [0] * (self.num_bits - 1)

        # 计算标志位
        zero = int(all(bit == 0 for bit in result))
        negative = result[0] if self.num_bits > 0 else 0

        return {
            'result': result,
            'zero': zero,
            'carry': carry,
            'negative': negative,
            'overflow': overflow
        }

    def _bits_to_int(self, bits: List[int]) -> int:
        """将二进制列表转换为整数

        Args:
            bits: 二进制列表（高位在前）

        Returns:
            int: 整数值
        """
        result = 0
        for i, bit in enumerate(bits):
            result |= bit << (len(bits) - 1 - i)
        return result

    def add(self, a: int, b: int) -> Dict:
        """执行加法

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict: 包含结果和标志位
        """
        a_bits = self._int_to_bits(a)
        b_bits = self._int_to_bits(b)
        return self.evaluate(a_bits, b_bits, self.OP_ADD)

    def sub(self, a: int, b: int) -> Dict:
        """执行减法

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict: 包含结果和标志位
        """
        a_bits = self._int_to_bits(a)
        b_bits = self._int_to_bits(b)
        return self.evaluate(a_bits, b_bits, self.OP_SUB)

    def and_op(self, a: int, b: int) -> Dict:
        """执行按位与

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict: 包含结果和标志位
        """
        a_bits = self._int_to_bits(a)
        b_bits = self._int_to_bits(b)
        return self.evaluate(a_bits, b_bits, self.OP_AND)

    def or_op(self, a: int, b: int) -> Dict:
        """执行按位或

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict: 包含结果和标志位
        """
        a_bits = self._int_to_bits(a)
        b_bits = self._int_to_bits(b)
        return self.evaluate(a_bits, b_bits, self.OP_OR)

    def xor_op(self, a: int, b: int) -> Dict:
        """执行按位异或

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict: 包含结果和标志位
        """
        a_bits = self._int_to_bits(a)
        b_bits = self._int_to_bits(b)
        return self.evaluate(a_bits, b_bits, self.OP_XOR)

    def _int_to_bits(self, value: int) -> List[int]:
        """将整数转换为二进制列表

        Args:
            value: 整数值

        Returns:
            List[int]: 二进制列表（高位在前）
        """
        # 处理负数（补码）
        if value < 0:
            value = (1 << self.num_bits) + value

        bits = []
        for i in range(self.num_bits - 1, -1, -1):
            bits.append((value >> i) & 1)
        return bits
