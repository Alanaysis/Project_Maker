"""
SHA-256哈希算法实现

SHA-256 是 SHA-2 家族的一员，产生256位（32字节）的散列值。

算法流程：
1. 填充消息到512位的倍数
2. 初始化八个32位的链接变量
3. 处理每个512位的消息分组（64轮运算）
4. 输出256位散列值

SHA-256目前仍然是安全的，广泛用于数字签名、证书等领域。
"""

import struct
from typing import Union


class SHA256:
    """SHA-256哈希算法实现类"""

    # 初始化常量（前8个素数的平方根的小数部分前32位）
    INIT_H = [
        0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
        0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
    ]

    # 轮常量（前64个素数的立方根的小数部分前32位）
    K = [
        0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
        0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
        0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
        0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
        0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC,
        0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
        0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7,
        0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
        0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
        0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
        0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3,
        0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
        0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5,
        0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
        0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
        0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2
    ]

    def __init__(self):
        """初始化SHA-256哈希器"""
        self._reset()

    def _reset(self):
        """重置内部状态"""
        self._h = list(self.INIT_H)
        self._message = bytearray()
        self._length = 0

    @staticmethod
    def _right_rotate(n: int, b: int) -> int:
        """循环右移"""
        return ((n >> b) | (n << (32 - b))) & 0xFFFFFFFF

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

        # 扩展为64个字
        for t in range(16, 64):
            s0 = (self._right_rotate(W[t-15], 7) ^
                  self._right_rotate(W[t-15], 18) ^
                  (W[t-15] >> 3))
            s1 = (self._right_rotate(W[t-2], 17) ^
                  self._right_rotate(W[t-2], 19) ^
                  (W[t-2] >> 10))
            W.append((W[t-16] + s0 + W[t-7] + s1) & 0xFFFFFFFF)

        a, b, c, d, e, f, g, h = self._h

        for t in range(64):
            S1 = (self._right_rotate(e, 6) ^
                  self._right_rotate(e, 11) ^
                  self._right_rotate(e, 25))
            ch = (e & f) ^ (~e & g) & 0xFFFFFFFF
            temp1 = (h + S1 + ch + self.K[t] + W[t]) & 0xFFFFFFFF
            S0 = (self._right_rotate(a, 2) ^
                  self._right_rotate(a, 13) ^
                  self._right_rotate(a, 22))
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        self._h[0] = (self._h[0] + a) & 0xFFFFFFFF
        self._h[1] = (self._h[1] + b) & 0xFFFFFFFF
        self._h[2] = (self._h[2] + c) & 0xFFFFFFFF
        self._h[3] = (self._h[3] + d) & 0xFFFFFFFF
        self._h[4] = (self._h[4] + e) & 0xFFFFFFFF
        self._h[5] = (self._h[5] + f) & 0xFFFFFFFF
        self._h[6] = (self._h[6] + g) & 0xFFFFFFFF
        self._h[7] = (self._h[7] + h) & 0xFFFFFFFF

    def update(self, data: Union[str, bytes]) -> 'SHA256':
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
        计算并返回SHA-256散列值

        返回:
            32字节的SHA-256散列值
        """
        # 保存当前状态
        saved_h = list(self._h)
        saved_message = bytearray(self._message)

        # 填充并处理剩余消息
        padded = self._pad_message(bytes(self._message))
        for i in range(0, len(padded), 64):
            self._process_block(padded[i:i+64])

        # 组装结果
        result = struct.pack('>8I', *self._h)

        # 恢复状态
        self._h = saved_h
        self._message = saved_message

        return result

    def hexdigest(self) -> str:
        """
        计算并返回SHA-256散列值的十六进制表示

        返回:
            64字符的十六进制字符串
        """
        return self.digest().hex()

    @staticmethod
    def hash(data: Union[str, bytes]) -> str:
        """
        一次性计算SHA-256散列值

        参数:
            data: 要哈希的数据

        返回:
            64字符的十六进制字符串
        """
        return SHA256().update(data).hexdigest()


def demo():
    """SHA-256算法演示"""
    print("=== SHA-256 哈希算法演示 ===\n")

    test_cases = [
        "",
        "abc",
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnop",
        "Hello, World!",
        "密码学库测试",
    ]

    for text in test_cases:
        sha256_hash = SHA256.hash(text)
        print(f"输入: '{text}'")
        print(f"SHA256: {sha256_hash}")
        print()


if __name__ == '__main__':
    demo()
