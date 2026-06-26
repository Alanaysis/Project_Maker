"""
乘法器电路模块
Multiplier Circuit Module

乘法器是组合逻辑电路中的重要组件。
- 直接乘法器：使用部分积和加法器实现
- 原理：将乘法分解为移位和加法操作

Multiplier circuits are important combinational logic components.
- Direct multiplier: uses partial products and adders
- Principle: decompose multiplication into shifts and adds
"""

from src.adders import RippleCarryAdder, FullAdder


class DirectMultiplier:
    """
    直接乘法器 - 通过部分积实现
    Direct Multiplier - implements multiplication via partial products

    对于n位乘m位乘法器：
    - 产生n×m个部分积
    - 使用加法器树将部分积相加

    For n-bit × m-bit multiplication:
    - Generates n×m partial products
    - Uses adder tree to sum partial products
    """

    def __init__(self, a_bits: int = 4, b_bits: int = 4):
        """
        Args:
            a_bits: 被乘数位数
            b_bits: 乘数位数
        """
        self.a_bits = a_bits
        self.b_bits = b_bits
        self.result_bits = a_bits + b_bits

    def multiply(self, a: int, b: int) -> int:
        """
        执行二进制乘法

        Args:
            a: 被乘数
            b: 乘数

        Returns:
            乘积
        """
        if a < 0 or b < 0:
            raise ValueError("Inputs must be non-negative")
        if a >= (1 << self.a_bits) or b >= (1 << self.b_bits):
            raise ValueError(f"Input out of range")

        result = 0
        for i in range(self.b_bits):
            # 如果乘数的第i位为1，则将被乘数左移i位后加入结果
            if (b >> i) & 1:
                result += (a << i)

        return result

    def get_partial_products(self, a: int, b: int) -> list:
        """
        获取所有部分积（用于教学展示）

        Args:
            a: 被乘数
            b: 乘数

        Returns:
            部分积列表
        """
        partial_products = []
        for i in range(self.b_bits):
            if (b >> i) & 1:
                partial_products.append(a << i)
            else:
                partial_products.append(0)
        return partial_products


class WallaceTreeMultiplier:
    """
    Wallace树乘法器 - 使用压缩器树加速乘法
    Wallace Tree Multiplier - uses compressor tree to accelerate multiplication

    Wallace树的核心思想：
    1. 生成所有部分积
    2. 使用FA/HA压缩器将部分积层数逐步减少
    3. 最后用行波进位加法器求和

    Key idea:
    1. Generate all partial products
    2. Use FA/HA compressors to reduce layers progressively
    3. Final sum with ripple carry adder
    """

    def __init__(self, a_bits: int = 4, b_bits: int = 4):
        self.a_bits = a_bits
        self.b_bits = b_bits
        self.result_bits = a_bits + b_bits

    def multiply(self, a: int, b: int) -> int:
        """
        执行Wallace树乘法

        Args:
            a: 被乘数
            b: 乘数

        Returns:
            乘积
        """
        if a < 0 or b < 0:
            raise ValueError("Inputs must be non-negative")

        # 步骤1：生成部分积
        partial_products = []
        for i in range(self.b_bits):
            if (b >> i) & 1:
                partial_products.append((a << i) & ((1 << self.result_bits) - 1))
            else:
                partial_products.append(0)

        # 步骤2：使用Wallace树压缩
        # 简化实现：直接返回结果（完整Wallace树实现需要大量全加器）
        result = 0
        for i, pp in enumerate(partial_products):
            result += pp

        return result & ((1 << self.result_bits) - 1)

    def get_partial_products(self, a: int, b: int) -> list:
        """获取部分积"""
        partial_products = []
        for i in range(self.b_bits):
            if (b >> i) & 1:
                partial_products.append(a << i)
            else:
                partial_products.append(0)
        return partial_products
