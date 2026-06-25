"""
RSA非对称加密算法实现

RSA是最常用的非对称加密算法，基于大数分解的困难性。

算法流程：
1. 密钥生成：
   - 选择两个大素数p, q
   - 计算n = p × q
   - 计算φ(n) = (p-1)(q-1)
   - 选择e，满足gcd(e, φ(n)) = 1
   - 计算d = e^(-1) mod φ(n)
   - 公钥：(e, n)
   - 私钥：(d, n)

2. 加密：c = m^e mod n
3. 解密：m = c^d mod n

注意：此实现仅用于学习目的，不建议用于生产环境。
"""

import random
import math
from typing import Tuple, Optional


class RSA:
    """RSA非对称加密算法实现类"""

    def __init__(self, key_size: int = 2048):
        """
        初始化RSA

        参数:
            key_size: 密钥大小（位）
        """
        self.key_size = key_size
        self.public_key = None
        self.private_key = None

    @staticmethod
    def _is_prime_miller_rabin(n: int, k: int = 20) -> bool:
        """
        Miller-Rabin素性测试

        参数:
            n: 待测试的数
            k: 测试轮数

        返回:
            是否可能是素数
        """
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False

        # 将n-1表示为2^r × d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2

        # 进行k轮测试
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)

            if x == 1 or x == n - 1:
                continue

            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False

        return True

    @staticmethod
    def _generate_prime(bits: int) -> int:
        """
        生成指定位数的素数

        参数:
            bits: 素数的位数

        返回:
            素数
        """
        while True:
            # 生成随机数
            n = random.getrandbits(bits)
            # 设置最高位和最低位
            n |= (1 << (bits - 1)) | 1

            # 测试素性
            if RSA._is_prime_miller_rabin(n):
                return n

    @staticmethod
    def _mod_inverse(e: int, phi: int) -> int:
        """
        计算模逆：d = e^(-1) mod phi

        使用扩展欧几里得算法

        参数:
            e: 公钥指数
            phi: 欧拉函数值

        返回:
            私钥指数d
        """
        if math.gcd(e, phi) != 1:
            raise ValueError("e和phi不互质")

        # 扩展欧几里得算法
        old_r, r = e, phi
        old_s, s = 1, 0

        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s

        return old_s % phi

    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        生成RSA密钥对

        返回:
            ((e, n), (d, n)) - (公钥, 私钥)
        """
        # 生成两个大素数
        half_bits = self.key_size // 2
        p = self._generate_prime(half_bits)
        q = self._generate_prime(half_bits)

        # 确保p != q
        while p == q:
            q = self._generate_prime(half_bits)

        # 计算n和phi
        n = p * q
        phi = (p - 1) * (q - 1)

        # 选择e（通常使用65537）
        e = 65537
        while math.gcd(e, phi) != 1:
            e += 2

        # 计算d
        d = self._mod_inverse(e, phi)

        self.public_key = (e, n)
        self.private_key = (d, n)

        return self.public_key, self.private_key

    def encrypt(self, plaintext: bytes, public_key: Tuple[int, int] = None) -> bytes:
        """
        RSA加密

        参数:
            plaintext: 明文（字节）
            public_key: 公钥（如果为None则使用自己的公钥）

        返回:
            密文（字节）
        """
        if public_key is None:
            public_key = self.public_key

        if public_key is None:
            raise ValueError("请先生成密钥对")

        e, n = public_key

        # 将明文转换为整数
        m = int.from_bytes(plaintext, 'big')

        if m >= n:
            raise ValueError("明文太长")

        # 加密：c = m^e mod n
        c = pow(m, e, n)

        # 将密文转换为字节
        byte_length = (n.bit_length() + 7) // 8
        return c.to_bytes(byte_length, 'big')

    def decrypt(self, ciphertext: bytes, private_key: Tuple[int, int] = None) -> bytes:
        """
        RSA解密

        参数:
            ciphertext: 密文（字节）
            private_key: 私钥（如果为None则使用自己的私钥）

        返回:
            明文（字节）
        """
        if private_key is None:
            private_key = self.private_key

        if private_key is None:
            raise ValueError("请先生成密钥对")

        d, n = private_key

        # 将密文转换为整数
        c = int.from_bytes(ciphertext, 'big')

        # 解密：m = c^d mod n
        m = pow(c, d, n)

        # 将明文转换为字节
        byte_length = (m.bit_length() + 7) // 8
        return m.to_bytes(byte_length, 'big')

    def sign(self, message: bytes, private_key: Tuple[int, int] = None) -> bytes:
        """
        RSA签名

        参数:
            message: 消息（字节）
            private_key: 私钥

        返回:
            签名（字节）
        """
        if private_key is None:
            private_key = self.private_key

        if private_key is None:
            raise ValueError("请先生成密钥对")

        d, n = private_key

        # 对消息进行哈希（简化处理）
        import hashlib
        hash_value = hashlib.sha256(message).digest()
        h = int.from_bytes(hash_value, 'big')

        # 签名：s = h^d mod n
        s = pow(h, d, n)

        byte_length = (n.bit_length() + 7) // 8
        return s.to_bytes(byte_length, 'big')

    def verify(self, message: bytes, signature: bytes,
               public_key: Tuple[int, int] = None) -> bool:
        """
        验证RSA签名

        参数:
            message: 消息（字节）
            signature: 签名（字节）
            public_key: 公钥

        返回:
            签名是否有效
        """
        if public_key is None:
            public_key = self.public_key

        if public_key is None:
            raise ValueError("请先生成密钥对")

        e, n = public_key

        # 计算消息哈希
        import hashlib
        hash_value = hashlib.sha256(message).digest()
        h = int.from_bytes(hash_value, 'big')

        # 验证签名：h' = s^e mod n
        s = int.from_bytes(signature, 'big')
        h_prime = pow(s, e, n)

        return h == h_prime


def demo():
    """RSA加密演示"""
    print("=== RSA 非对称加密演示 ===\n")

    # 使用较小的密钥大小以便演示
    rsa = RSA(512)

    # 生成密钥对
    print("生成RSA密钥对...")
    public_key, private_key = rsa.generate_keys()
    print(f"公钥 (e, n): ({public_key[0]}, {hex(public_key[1])}...)")
    print(f"私钥 (d, n): ({hex(private_key[0])}..., {hex(private_key[1])}...)")
    print()

    # 加密解密
    message = b"Hello, RSA!"
    print(f"原始消息: {message}")

    ciphertext = rsa.encrypt(message)
    print(f"密文: {ciphertext.hex()[:64]}...")

    decrypted = rsa.decrypt(ciphertext)
    print(f"解密: {decrypted}")
    print()

    # 数字签名
    print("--- 数字签名演示 ---")
    message = b"This is a signed message"
    signature = rsa.sign(message)
    print(f"消息: {message}")
    print(f"签名: {signature.hex()[:64]}...")

    # 验证签名
    is_valid = rsa.verify(message, signature)
    print(f"验证签名: {is_valid}")

    # 验证篡改的消息
    is_valid = rsa.verify(b"Tampered message", signature)
    print(f"验证篡改消息: {is_valid}")


if __name__ == '__main__':
    demo()
