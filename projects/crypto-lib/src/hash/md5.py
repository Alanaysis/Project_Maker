"""
MD5哈希算法实现

MD5 (Message-Digest Algorithm 5) 是一种广泛使用的密码散列函数，
产生128位（16字节）的散列值。

算法流程：
1. 填充消息到512位的倍数
2. 初始化四个32位的链接变量
3. 处理每个512位的消息分组
4. 输出128位散列值

注意：MD5已被证明存在碰撞漏洞，不建议用于安全场景。
"""

import struct
from typing import Union


class MD5:
    """MD5哈希算法实现类"""

    # 初始化常量
    INIT_A = 0x67452301
    INIT_B = 0xEFCDAB89
    INIT_C = 0x98BADCFE
    INIT_D = 0x10325476

    # 每轮使用的常量（正弦函数值）
    T = [int(4294967296 * abs(__import__('math').sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

    # 每轮的位移量
    S = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
        5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20, 5,  9, 14, 20,
        4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21
    ]

    # 消息分组索引
    M = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
        1, 6, 11, 0, 5, 10, 15, 4, 9, 14, 3, 8, 13, 2, 7, 12,
        5, 8, 11, 14, 1, 4, 7, 10, 13, 0, 3, 6, 9, 12, 15, 2,
        0, 7, 14, 5, 12, 3, 10, 1, 8, 15, 6, 13, 4, 11, 2, 9
    ]

    def __init__(self):
        """初始化MD5哈希器"""
        self._reset()

    def _reset(self):
        """重置内部状态"""
        self._a = self.INIT_A
        self._b = self.INIT_B
        self._c = self.INIT_C
        self._d = self.INIT_D
        self._message = bytearray()
        self._length = 0

    @staticmethod
    def _left_rotate(x: int, n: int) -> int:
        """循环左移"""
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    @staticmethod
    def _pad_message(message: bytes) -> bytes:
        """
        消息填充

        填充规则：
        1. 在消息末尾添加一个'1'位
        2. 添加'0'位直到消息长度 ≡ 448 (mod 512)
        3. 添加原始消息长度的64位小端表示
        """
        message = bytearray(message)
        original_length = len(message) * 8

        # 添加'1'位
        message.append(0x80)

        # 添加'0'位直到长度 ≡ 448 (mod 512)
        while len(message) % 64 != 56:
            message.append(0x00)

        # 添加原始长度（64位小端）
        message.extend(struct.pack('<Q', original_length))

        return bytes(message)

    def _process_block(self, block: bytes):
        """
        处理一个512位（64字节）的消息块

        参数:
            block: 64字节的消息块
        """
        # 将块分解为16个32位小端整数
        M = list(struct.unpack('<16I', block))

        a, b, c, d = self._a, self._b, self._c, self._d

        for i in range(64):
            if i < 16:
                # 第一轮：F(b, c, d) = (b & c) | (~b & d)
                f = (b & c) | (~b & d) & 0xFFFFFFFF
            elif i < 32:
                # 第二轮：G(b, c, d) = (b & d) | (c & ~d)
                f = (b & d) | (c & ~d) & 0xFFFFFFFF
            elif i < 48:
                # 第三轮：H(b, c, d) = b ^ c ^ d
                f = b ^ c ^ d
            else:
                # 第四轮：I(b, c, d) = c ^ (b | ~d)
                f = c ^ (b | ~d) & 0xFFFFFFFF

            f = f & 0xFFFFFFFF
            temp = d
            d = c
            c = b
            b = (b + self._left_rotate((a + f + self.T[i] + M[self.M[i]]) & 0xFFFFFFFF, self.S[i])) & 0xFFFFFFFF
            a = temp

        self._a = (self._a + a) & 0xFFFFFFFF
        self._b = (self._b + b) & 0xFFFFFFFF
        self._c = (self._c + c) & 0xFFFFFFFF
        self._d = (self._d + d) & 0xFFFFFFFF

    def update(self, data: Union[str, bytes]) -> 'MD5':
        """
        更新哈希计算

        参数:
            data: 要哈希的数据（字符串或字节）

        返回:
            self，支持链式调用
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        self._message.extend(data)
        self._length += len(data)

        # 处理完整的64字节块
        while len(self._message) >= 64:
            self._process_block(bytes(self._message[:64]))
            self._message = self._message[64:]

        return self

    def digest(self) -> bytes:
        """
        计算并返回MD5散列值

        返回:
            16字节的MD5散列值
        """
        # 保存当前状态
        saved_a, saved_b = self._a, self._b
        saved_c, saved_d = self._c, self._d
        saved_message = bytearray(self._message)

        # 填充并处理剩余消息
        padded = self._pad_message(bytes(self._message))
        for i in range(0, len(padded), 64):
            self._process_block(padded[i:i+64])

        # 组装结果
        result = struct.pack('<4I', self._a, self._b, self._c, self._d)

        # 恢复状态（允许再次调用）
        self._a, self._b = saved_a, saved_b
        self._c, self._d = saved_c, saved_d
        self._message = saved_message

        return result

    def hexdigest(self) -> str:
        """
        计算并返回MD5散列值的十六进制表示

        返回:
            32字符的十六进制字符串
        """
        return self.digest().hex()

    @staticmethod
    def hash(data: Union[str, bytes]) -> str:
        """
        一次性计算MD5散列值

        参数:
            data: 要哈希的数据

        返回:
            32字符的十六进制字符串
        """
        return MD5().update(data).hexdigest()


def demo():
    """MD5算法演示"""
    print("=== MD5 哈希算法演示 ===\n")

    test_cases = [
        "",
        "a",
        "abc",
        "message digest",
        "abcdefghijklmnopqrstuvwxyz",
        "Hello, World!",
        "密码学库测试",
    ]

    for text in test_cases:
        md5_hash = MD5.hash(text)
        print(f"输入: '{text}'")
        print(f"MD5:  {md5_hash}")
        print()

    # 分块更新演示
    print("--- 分块更新演示 ---")
    hasher = MD5()
    hasher.update("Hello, ")
    hasher.update("World!")
    print(f"分块计算 'Hello, ' + 'World!': {hasher.hexdigest()}")
    print(f"一次性计算 'Hello, World!':     {MD5.hash('Hello, World!')}")


if __name__ == '__main__':
    demo()
