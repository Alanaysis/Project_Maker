"""
SHA-1哈希算法实现

SHA-1 (Secure Hash Algorithm 1) 产生160位（20字节）的散列值。

算法流程：
1. 填充消息到512位的倍数
2. 初始化五个32位的链接变量
3. 处理每个512位的消息分组（80轮运算）
4. 输出160位散列值

注意：SHA-1已被证明存在碰撞攻击，不建议用于安全场景。
"""

import struct
from typing import Union


class SHA1:
    """SHA-1哈希算法实现类"""

    # 初始化常量
    INIT_H0 = 0x67452301
    INIT_H1 = 0xEFCDAB89
    INIT_H2 = 0x98BADCFE
    INIT_H3 = 0x10325476
    INIT_H4 = 0xC3D2E1F0

    # 轮常量
    K0 = 0x5A827999  # 0 <= t <= 19
    K1 = 0x6ED9EBA1  # 20 <= t <= 39
    K2 = 0x8F1BBCDC  # 40 <= t <= 59
    K3 = 0xCA62C1D6  # 60 <= t <= 79

    def __init__(self):
        """初始化SHA-1哈希器"""
        self._reset()

    def _reset(self):
        """重置内部状态"""
        self._h0 = self.INIT_H0
        self._h1 = self.INIT_H1
        self._h2 = self.INIT_H2
        self._h3 = self.INIT_H3
        self._h4 = self.INIT_H4
        self._message = bytearray()
        self._length = 0

    @staticmethod
    def _left_rotate(n: int, b: int) -> int:
        """循环左移"""
        return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF

    @staticmethod
    def _pad_message(message: bytes) -> bytes:
        """
        消息填充（大端序）

        填充规则：
        1. 在消息末尾添加一个'1'位
        2. 添加'0'位直到消息长度 ≡ 448 (mod 512)
        3. 添加原始消息长度的64位大端表示
        """
        message = bytearray(message)
        original_length = len(message) * 8

        # 添加'1'位
        message.append(0x80)

        # 添加'0'位直到长度 ≡ 448 (mod 512)
        while len(message) % 64 != 56:
            message.append(0x00)

        # 添加原始长度（64位大端）
        message.extend(struct.pack('>Q', original_length))

        return bytes(message)

    def _process_block(self, block: bytes):
        """
        处理一个512位（64字节）的消息块

        参数:
            block: 64字节的消息块
        """
        # 将块分解为16个32位大端整数
        W = list(struct.unpack('>16I', block))

        # 扩展为80个字
        for t in range(16, 80):
            W.append(self._left_rotate(W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1))

        a, b, c, d, e = self._h0, self._h1, self._h2, self._h3, self._h4

        for t in range(80):
            if t < 20:
                # 第一轮：Ch(e, f, g) = (e & f) ^ (~e & g)
                f = (b & c) | (~b & d) & 0xFFFFFFFF
                k = self.K0
            elif t < 40:
                # 第二轮：Parity(b, c, d) = b ^ c ^ d
                f = b ^ c ^ d
                k = self.K1
            elif t < 60:
                # 第三轮：Maj(b, c, d) = (b & c) | (b & d) | (c & d)
                f = (b & c) | (b & d) | (c & d)
                k = self.K2
            else:
                # 第四轮：Parity(b, c, d) = b ^ c ^ d
                f = b ^ c ^ d
                k = self.K3

            temp = (self._left_rotate(a, 5) + f + e + k + W[t]) & 0xFFFFFFFF
            e = d
            d = c
            c = self._left_rotate(b, 30)
            b = a
            a = temp

        self._h0 = (self._h0 + a) & 0xFFFFFFFF
        self._h1 = (self._h1 + b) & 0xFFFFFFFF
        self._h2 = (self._h2 + c) & 0xFFFFFFFF
        self._h3 = (self._h3 + d) & 0xFFFFFFFF
        self._h4 = (self._h4 + e) & 0xFFFFFFFF

    def update(self, data: Union[str, bytes]) -> 'SHA1':
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
        计算并返回SHA-1散列值

        返回:
            20字节的SHA-1散列值
        """
        # 保存当前状态
        saved_h = (self._h0, self._h1, self._h2, self._h3, self._h4)
        saved_message = bytearray(self._message)

        # 填充并处理剩余消息
        padded = self._pad_message(bytes(self._message))
        for i in range(0, len(padded), 64):
            self._process_block(padded[i:i+64])

        # 组装结果
        result = struct.pack('>5I', self._h0, self._h1, self._h2, self._h3, self._h4)

        # 恢复状态
        self._h0, self._h1, self._h2, self._h3, self._h4 = saved_h
        self._message = saved_message

        return result

    def hexdigest(self) -> str:
        """
        计算并返回SHA-1散列值的十六进制表示

        返回:
            40字符的十六进制字符串
        """
        return self.digest().hex()

    @staticmethod
    def hash(data: Union[str, bytes]) -> str:
        """
        一次性计算SHA-1散列值

        参数:
            data: 要哈希的数据

        返回:
            40字符的十六进制字符串
        """
        return SHA1().update(data).hexdigest()


def demo():
    """SHA-1算法演示"""
    print("=== SHA-1 哈希算法演示 ===\n")

    test_cases = [
        "",
        "abc",
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnop",
        "Hello, World!",
        "密码学库测试",
    ]

    for text in test_cases:
        sha1_hash = SHA1.hash(text)
        print(f"输入: '{text}'")
        print(f"SHA1: {sha1_hash}")
        print()


if __name__ == '__main__':
    demo()
