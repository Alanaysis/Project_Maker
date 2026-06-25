"""
数字签名实现

数字签名用于验证消息的完整性和来源。

支持的签名算法：
1. RSA签名
2. ECDSA（椭圆曲线数字签名算法）

签名流程：
1. 对消息进行哈希
2. 使用私钥对哈希值进行签名
3. 验证者使用公钥验证签名

注意：此实现仅用于学习目的。
"""

import hashlib
import random
from typing import Tuple, Optional
from .rsa import RSA
from .ecdh import ECDH, EllipticCurve, SECP256K1


class RSASignature:
    """RSA数字签名"""

    def __init__(self, key_size: int = 2048):
        """
        初始化RSA签名

        参数:
            key_size: 密钥大小
        """
        self.rsa = RSA(key_size)
        self.public_key = None
        self.private_key = None

    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """生成密钥对"""
        self.public_key, self.private_key = self.rsa.generate_keys()
        return self.public_key, self.private_key

    def sign(self, message: bytes) -> bytes:
        """
        签名

        参数:
            message: 消息

        返回:
            签名
        """
        return self.rsa.sign(message, self.private_key)

    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        验证签名

        参数:
            message: 消息
            signature: 签名

        返回:
            签名是否有效
        """
        return self.rsa.verify(message, signature, self.public_key)


class ECDSASignature:
    """ECDSA椭圆曲线数字签名"""

    def __init__(self, curve: EllipticCurve = None):
        """
        初始化ECDSA

        参数:
            curve: 椭圆曲线
        """
        self.curve = curve or SECP256K1
        self.private_key = None
        self.public_key = None

    def generate_keys(self) -> Tuple[int, Tuple[int, int]]:
        """生成密钥对"""
        self.private_key = random.randrange(1, self.curve.n)
        self.public_key = self.curve.point_multiply(self.private_key, self.curve.G)
        return self.private_key, self.public_key

    def _hash_message(self, message: bytes) -> int:
        """对消息进行哈希"""
        hash_value = hashlib.sha256(message).digest()
        return int.from_bytes(hash_value, 'big')

    def sign(self, message: bytes) -> Tuple[int, int]:
        """
        ECDSA签名

        参数:
            message: 消息

        返回:
            (r, s) 签名对
        """
        if self.private_key is None:
            raise ValueError("请先生成密钥对")

        n = self.curve.n
        z = self._hash_message(message)

        while True:
            # 生成随机数k
            k = random.randrange(1, n)

            # 计算点 (x, y) = kG
            point = self.curve.point_multiply(k, self.curve.G)
            if point is None:
                continue

            r = point[0] % n
            if r == 0:
                continue

            # 计算s = k^(-1)(z + r*d) mod n
            k_inv = pow(k, -1, n)
            s = (k_inv * (z + r * self.private_key)) % n
            if s == 0:
                continue

            return r, s

    def verify(self, message: bytes, signature: Tuple[int, int]) -> bool:
        """
        验证ECDSA签名

        参数:
            message: 消息
            signature: (r, s) 签名对

        返回:
            签名是否有效
        """
        if self.public_key is None:
            raise ValueError("请先生成密钥对")

        r, s = signature
        n = self.curve.n

        # 检查r和s的范围
        if not (1 <= r < n and 1 <= s < n):
            return False

        z = self._hash_message(message)

        # 计算w = s^(-1) mod n
        w = pow(s, -1, n)

        # 计算u1 = z*w mod n, u2 = r*w mod n
        u1 = (z * w) % n
        u2 = (r * w) % n

        # 计算点 (x, y) = u1*G + u2*Q
        point1 = self.curve.point_multiply(u1, self.curve.G)
        point2 = self.curve.point_multiply(u2, self.public_key)
        point = self.curve.point_add(point1, point2)

        if point is None:
            return False

        # 验证r == x mod n
        return r == point[0] % n


class DigitalSignature:
    """数字签名统一接口"""

    @staticmethod
    def rsa_sign(message: bytes, key_size: int = 2048) -> Tuple[bytes, Tuple[int, int]]:
        """
        RSA签名

        参数:
            message: 消息
            key_size: 密钥大小

        返回:
            (签名, 公钥)
        """
        signer = RSASignature(key_size)
        public_key, _ = signer.generate_keys()
        signature = signer.sign(message)
        return signature, public_key

    @staticmethod
    def rsa_verify(message: bytes, signature: bytes,
                   public_key: Tuple[int, int], key_size: int = 2048) -> bool:
        """
        验证RSA签名

        参数:
            message: 消息
            signature: 签名
            public_key: 公钥
            key_size: 密钥大小

        返回:
            签名是否有效
        """
        signer = RSASignature(key_size)
        signer.public_key = public_key
        return signer.verify(message, signature)

    @staticmethod
    def ecdsa_sign(message: bytes) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        ECDSA签名

        参数:
            message: 消息

        返回:
            (签名(r,s), 公钥)
        """
        signer = ECDSASignature()
        _, public_key = signer.generate_keys()
        signature = signer.sign(message)
        return signature, public_key

    @staticmethod
    def ecdsa_verify(message: bytes, signature: Tuple[int, int],
                     public_key: Tuple[int, int]) -> bool:
        """
        验证ECDSA签名

        参数:
            message: 消息
            signature: 签名(r,s)
            public_key: 公钥

        返回:
            签名是否有效
        """
        signer = ECDSASignature()
        signer.public_key = public_key
        # 需要设置曲线以正确验证
        signer.curve = SECP256K1
        return signer.verify(message, signature)


def demo():
    """数字签名演示"""
    print("=== 数字签名演示 ===\n")

    # RSA签名
    print("--- RSA数字签名 ---")
    message = b"Important document to sign"

    signer = RSASignature(512)
    public_key, private_key = signer.generate_keys()

    signature = signer.sign(message)
    print(f"消息: {message}")
    print(f"签名: {signature.hex()[:32]}...")

    is_valid = signer.verify(message, signature)
    print(f"验证原始消息: {is_valid}")

    is_valid = signer.verify(b"Tampered message", signature)
    print(f"验证篡改消息: {is_valid}")
    print()

    # ECDSA签名
    print("--- ECDSA数字签名 ---")
    message = b"ECDSA signed message"

    ecdsa = ECDSASignature()
    public_key, private_key = ecdsa.generate_keys()

    r, s = ecdsa.sign(message)
    print(f"消息: {message}")
    print(f"签名 r: {hex(r)[:32]}...")
    print(f"签名 s: {hex(s)[:32]}...")

    is_valid = ecdsa.verify(message, (r, s))
    print(f"验证原始消息: {is_valid}")

    is_valid = ecdsa.verify(b"Tampered message", (r, s))
    print(f"验证篡改消息: {is_valid}")


if __name__ == '__main__':
    demo()
