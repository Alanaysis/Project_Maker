"""
基于多路选择器的逻辑综合模块
Multiplexer-based Logic Synthesis Module

多路选择器可以作为通用逻辑函数实现器。
任何布尔函数都可以用一个足够大的MUX实现。

Key insight: A 2^n:1 MUX can implement any n-variable boolean function.

原理：
1. 列出函数的真值表
2. 将选择线连接到输入变量
3. 根据真值表设置数据输入
"""

from src.mux_demux import Multiplexer4to1, Multiplexer8to1


class MuxLogicSynthesizer:
    """
    基于MUX的逻辑综合器

    使用多路选择器实现任意布尔函数。
    Implements arbitrary boolean functions using multiplexers.
    """

    def __init__(self):
        self.mux4 = Multiplexer4to1()
        self.mux8 = Multiplexer8to1()

    def implement_2var(self, truth_table: list) -> int:
        """
        使用4:1 MUX实现2变量布尔函数

        Args:
            truth_table: 真值表 [f(0,0), f(0,1), f(1,0), f(1,1)]

        Returns:
            函数输出
        """
        if len(truth_table) != 4:
            raise ValueError("Truth table must have 4 entries")

        # 将真值表存储为类属性供MUX访问
        self._truth_table_2var = truth_table
        return self._eval_2var

    def _eval_2var(self, a: int = None, b: int = None) -> int:
        """
        评估2变量函数

        Args:
            a: 变量A (MSB)
            b: 变量B (LSB)

        Returns:
            函数输出
        """
        if a is None or b is None:
            raise ValueError("Both variables must be provided")

        # 将输入组合成索引
        index = (a << 1) | b
        return self._truth_table_2var[index]

    def implement_from_truth_table(self, num_vars: int, truth_table: list) -> callable:
        """
        从真值表生成可调用函数

        Args:
            num_vars: 变量数量
            truth_table: 真值表列表

        Returns:
            可调用函数
        """
        if num_vars not in (2, 3):
            raise ValueError("Supported: 2 or 3 variables")
        expected_size = 1 << num_vars
        if len(truth_table) != expected_size:
            raise ValueError(f"Truth table must have {expected_size} entries")

        def evaluate(*inputs: int) -> int:
            if len(inputs) != num_vars:
                raise ValueError(f"Expected {num_vars} inputs")

            # 将输入组合成索引
            index = 0
            for i, inp in enumerate(reversed(inputs)):
                index |= (inp << i)

            return truth_table[index]

        return evaluate

    def get_truth_table(self, func, num_vars: int) -> list:
        """
        从函数获取真值表

        Args:
            func: 布尔函数
            num_vars: 变量数量

        Returns:
            真值表列表
        """
        truth_table = []
        for i in range(1 << num_vars):
            inputs = [(i >> j) & 1 for j in range(num_vars)]
            truth_table.append(func(*inputs))
        return truth_table

    def simplify_with_mux(self, func, num_vars: int) -> dict:
        """
        使用MUX简化逻辑综合

        Args:
            func: 布尔函数
            num_vars: 变量数量

        Returns:
            MUX配置信息
        """
        truth_table = self.get_truth_table(func, num_vars)
        mux_size = 1 << num_vars

        return {
            "num_variables": num_vars,
            "mux_type": f"{mux_size}:1",
            "truth_table": truth_table,
            "inputs": [f"x{i}" for i in range(num_vars)],
            "outputs": [f"f({','.join(['{0}' for _ in range(num_vars)])})"]
        }
