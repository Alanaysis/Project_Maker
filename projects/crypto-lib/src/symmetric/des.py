"""
DES (Data Encryption Standard) 对称加密算法实现

DES是一种分组密码，分组大小为64位（8字节），密钥长度为56位（实际使用64位，其中8位用于奇偶校验）。

算法流程：
1. 初始置换（IP）
2. 16轮Feistel网络
3. 逆初始置换（IP^-1）

每轮操作：
1. 扩展置换（E）
2. 与轮密钥异或
3. S-Box替换
4. P-Box置换

注意：DES已被认为不安全，仅用于学习目的。
"""

import os
from typing import Tuple
from .modes import ECB, CBC, CTR


class DES:
    """DES加密算法实现类"""

    # 初始置换表
    IP = [
        58, 50, 42, 34, 26, 18, 10, 2,
        60, 52, 44, 36, 28, 20, 12, 4,
        62, 54, 46, 38, 30, 22, 14, 6,
        64, 56, 48, 40, 32, 24, 16, 8,
        57, 49, 41, 33, 25, 17, 9, 1,
        59, 51, 43, 35, 27, 19, 11, 3,
        61, 53, 45, 37, 29, 21, 13, 5,
        63, 55, 47, 39, 31, 23, 15, 7,
    ]

    # 逆初始置换表
    IP_INV = [
        40, 8, 48, 16, 56, 24, 64, 32,
        39, 7, 47, 15, 55, 23, 63, 31,
        38, 6, 46, 14, 54, 22, 62, 30,
        37, 5, 45, 13, 53, 21, 61, 29,
        36, 4, 44, 12, 52, 20, 60, 28,
        35, 3, 43, 11, 51, 19, 59, 27,
        34, 2, 42, 10, 50, 18, 58, 26,
        33, 1, 41, 9, 49, 17, 57, 25,
    ]

    # 扩展置换表
    E = [
        32, 1, 2, 3, 4, 5,
        4, 5, 6, 7, 8, 9,
        8, 9, 10, 11, 12, 13,
        12, 13, 14, 15, 16, 17,
        16, 17, 18, 19, 20, 21,
        20, 21, 22, 23, 24, 25,
        24, 25, 26, 27, 28, 29,
        28, 29, 30, 31, 32, 1,
    ]

    # P-Box置换表
    P = [
        16, 7, 20, 21, 29, 12, 28, 17,
        1, 15, 23, 26, 5, 18, 31, 10,
        2, 8, 24, 14, 32, 27, 3, 9,
        19, 13, 30, 6, 22, 11, 4, 25,
    ]

    # S-Box
    SBOX = [
        # S1
        [
            [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7],
            [0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8],
            [4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0],
            [15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
        ],
        # S2
        [
            [15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10],
            [3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5],
            [0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15],
            [13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],
        ],
        # S3
        [
            [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8],
            [13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1],
            [13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7],
            [1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],
        ],
        # S4
        [
            [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15],
            [13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9],
            [10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4],
            [3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],
        ],
        # S5
        [
            [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9],
            [14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6],
            [4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14],
            [11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],
        ],
        # S6
        [
            [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11],
            [10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8],
            [9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6],
            [4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],
        ],
        # S7
        [
            [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1],
            [13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6],
            [1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2],
            [6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],
        ],
        # S8
        [
            [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7],
            [1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 2, 0, 14, 9, 11],
            [7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8],
            [2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11],
        ],
    ]

    # 置换选择1（PC-1）
    PC1 = [
        57, 49, 41, 33, 25, 17, 9,
        1, 58, 50, 42, 34, 26, 18,
        10, 2, 59, 51, 43, 35, 27,
        19, 11, 3, 60, 52, 44, 36,
        63, 55, 47, 39, 31, 23, 15,
        7, 62, 54, 46, 38, 30, 22,
        14, 6, 61, 53, 45, 37, 29,
        21, 13, 5, 28, 20, 12, 4,
    ]

    # 置换选择2（PC-2）
    PC2 = [
        14, 17, 11, 24, 1, 5,
        3, 28, 15, 6, 21, 10,
        23, 19, 12, 4, 26, 8,
        16, 7, 27, 20, 13, 2,
        41, 52, 31, 37, 47, 55,
        30, 40, 51, 45, 33, 48,
        44, 49, 39, 56, 34, 53,
        46, 42, 50, 36, 29, 32,
    ]

    # 每轮左移位数
    SHIFT = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

    def __init__(self, key: bytes):
        """
        初始化DES加密器

        参数:
            key: 8字节密钥
        """
        if len(key) != 8:
            raise ValueError("DES密钥必须是8字节")

        self.key = key
        self.round_keys = self._generate_round_keys()

    @staticmethod
    def _bytes_to_bits(data: bytes) -> list:
        """字节转换为比特列表"""
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def _bits_to_bytes(bits: list) -> bytes:
        """比特列表转换为字节"""
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            result.append(byte)
        return bytes(result)

    @staticmethod
    def _permute(data: list, table: list) -> list:
        """置换操作"""
        return [data[i - 1] for i in table]

    @staticmethod
    def _left_shift(data: list, n: int) -> list:
        """循环左移"""
        return data[n:] + data[:n]

    def _generate_round_keys(self) -> list:
        """生成16个轮密钥"""
        key_bits = self._bytes_to_bits(self.key)

        # PC-1置换
        key56 = self._permute(key_bits, self.PC1)

        # 分为左右两半
        left = key56[:28]
        right = key56[28:]

        round_keys = []
        for i in range(16):
            # 左移
            left = self._left_shift(left, self.SHIFT[i])
            right = self._left_shift(right, self.SHIFT[i])

            # PC-2置换
            combined = left + right
            round_key = self._permute(combined, self.PC2)
            round_keys.append(round_key)

        return round_keys

    def _feistel(self, right: list, round_key: list) -> list:
        """Feistel函数"""
        # 扩展置换
        expanded = self._permute(right, self.E)

        # 与轮密钥异或
        xored = [a ^ b for a, b in zip(expanded, round_key)]

        # S-Box替换
        sbox_output = []
        for i in range(8):
            block = xored[i * 6:(i + 1) * 6]
            row = (block[0] << 1) | block[5]
            col = (block[1] << 3) | (block[2] << 2) | (block[3] << 1) | block[4]
            val = self.SBOX[i][row][col]
            for j in range(3, -1, -1):
                sbox_output.append((val >> j) & 1)

        # P-Box置换
        return self._permute(sbox_output, self.P)

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """
        加密单个块（8字节）

        参数:
            plaintext: 8字节明文

        返回:
            8字节密文
        """
        if len(plaintext) != 8:
            raise ValueError("明文块必须是8字节")

        # 初始置换
        bits = self._bytes_to_bits(plaintext)
        bits = self._permute(bits, self.IP)

        # 分为左右两半
        left = bits[:32]
        right = bits[32:]

        # 16轮Feistel网络
        for i in range(16):
            new_right = [a ^ b for a, b in zip(left, self._feistel(right, self.round_keys[i]))]
            left = right
            right = new_right

        # 合并（注意：最后一轮不交换）
        combined = right + left

        # 逆初始置换
        result = self._permute(combined, self.IP_INV)

        return self._bits_to_bytes(result)

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """
        解密单个块（8字节）

        参数:
            ciphertext: 8字节密文

        返回:
            8字节明文
        """
        if len(ciphertext) != 8:
            raise ValueError("密文块必须是8字节")

        # 初始置换
        bits = self._bytes_to_bits(ciphertext)
        bits = self._permute(bits, self.IP)

        # 分为左右两半
        left = bits[:32]
        right = bits[32:]

        # 16轮Feistel网络（使用逆序轮密钥）
        for i in range(15, -1, -1):
            new_right = [a ^ b for a, b in zip(left, self._feistel(right, self.round_keys[i]))]
            left = right
            right = new_right

        # 合并
        combined = right + left

        # 逆初始置换
        result = self._permute(combined, self.IP_INV)

        return self._bits_to_bytes(result)

    def encrypt(self, plaintext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> Tuple[bytes, bytes]:
        """
        DES加密

        参数:
            plaintext: 明文
            mode: 加密模式（'ecb', 'cbc', 'ctr'）
            iv: CBC模式的初始化向量
            nonce: CTR模式的随机数

        返回:
            (密文, IV或nonce)
        """
        if mode == 'ecb':
            ecb = ECB(8)  # DES块大小为8字节
            return ecb.encrypt(plaintext, self.encrypt_block), b''
        elif mode == 'cbc':
            cbc = CBC(iv, 8)
            return cbc.encrypt(plaintext, self.encrypt_block)
        elif mode == 'ctr':
            ctr = CTR(nonce, 8)
            return ctr.encrypt(plaintext, self.encrypt_block)
        else:
            raise ValueError(f"不支持的模式: {mode}")

    def decrypt(self, ciphertext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> bytes:
        """
        DES解密

        参数:
            ciphertext: 密文
            mode: 加密模式（'ecb', 'cbc', 'ctr'）
            iv: CBC模式的初始化向量
            nonce: CTR模式的随机数

        返回:
            明文
        """
        if mode == 'ecb':
            ecb = ECB(8)
            return ecb.decrypt(ciphertext, self.decrypt_block)
        elif mode == 'cbc':
            cbc = CBC(iv, 8)
            return cbc.decrypt(ciphertext, self.decrypt_block, iv)
        elif mode == 'ctr':
            ctr = CTR(nonce, 8)
            return ctr.decrypt(ciphertext, self.encrypt_block, nonce)
        else:
            raise ValueError(f"不支持的模式: {mode}")


def demo():
    """DES加密演示"""
    print("=== DES 对称加密演示 ===\n")

    key = os.urandom(8)
    des = DES(key)

    plaintext = b"Hello DES!"
    print(f"明文: {plaintext}")
    print(f"密钥: {key.hex()}")
    print()

    # CBC模式
    ciphertext, iv = des.encrypt(plaintext, 'cbc')
    decrypted = des.decrypt(ciphertext, 'cbc', iv)
    print(f"CBC模式:")
    print(f"  IV: {iv.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")


if __name__ == '__main__':
    demo()
