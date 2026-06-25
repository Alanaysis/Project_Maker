"""
ECDH (Elliptic Curve Diffie-Hellman) 密钥交换实现

ECDH是一种基于椭圆曲线的密钥交换协议，允许双方在不安全的通道上协商共享密钥。

算法流程：
1. 双方选择相同的椭圆曲线和基点G
2. Alice生成私钥a，计算公钥A = aG
3. Bob生成私钥b，计算公钥B = bG
4. 共享密钥：S = aB = bA = abG

支持的曲线：
- secp256k1（比特币使用）
- P-256（NIST标准）

注意：此实现仅用于学习目的。
"""

import random
from typing import Tuple, Optional


class EllipticCurve:
    """椭圆曲线类"""

    def __init__(self, p: int, a: int, b: int, G: Tuple[int, int], n: int):
        """
        初始化椭圆曲线

        参数:
            p: 素数模数
            a: 曲线参数a
            b: 曲线参数b
            G: 基点 (x, y)
            n: 基点的阶
        """
        self.p = p
        self.a = a
        self.b = b
        self.G = G
        self.n = n

    def point_add(self, P: Optional[Tuple[int, int]],
                  Q: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """
        椭圆曲线点加法

        参数:
            P: 点P (x, y) 或 None（无穷远点）
            Q: 点Q (x, y) 或 None（无穷远点）

        返回:
            P + Q
        """
        if P is None:
            return Q
        if Q is None:
            return P

        x1, y1 = P
        x2, y2 = Q

        if x1 == x2 and y1 != y2:
            return None  # 无穷远点

        if x1 == x2:
            # 点加倍
            lam = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, self.p) % self.p
        else:
            # 点加法
            lam = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p

        x3 = (lam * lam - x1 - x2) % self.p
        y3 = (lam * (x1 - x3) - y1) % self.p

        return (x3, y3)

    def point_multiply(self, k: int, P: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        椭圆曲线点乘法（标量乘法）

        使用double-and-add算法

        参数:
            k: 标量
            P: 点

        返回:
            kP
        """
        if k == 0:
            return None

        if k < 0:
            k = -k
            P = (P[0], (-P[1]) % self.p)

        result = None
        addend = P

        while k:
            if k & 1:
                result = self.point_add(result, addend)
            addend = self.point_add(addend, addend)
            k >>= 1

        return result


# secp256k1曲线（比特币使用）
SECP256K1 = EllipticCurve(
    p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    a=0,
    b=7,
    G=(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
       0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8),
    n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)

# P-256曲线（NIST标准）
P256 = EllipticCurve(
    p=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF,
    a=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC,
    b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    G=(0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
       0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5),
    n=0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
)


class ECDH:
    """ECDH密钥交换实现类"""

    def __init__(self, curve: EllipticCurve = None):
        """
        初始化ECDH

        参数:
            curve: 椭圆曲线（默认使用secp256k1）
        """
        self.curve = curve or SECP256K1
        self.private_key = None
        self.public_key = None

    def generate_keypair(self) -> Tuple[int, Tuple[int, int]]:
        """
        生成密钥对

        返回:
            (私钥, 公钥)
        """
        # 生成私钥（随机数）
        self.private_key = random.randrange(1, self.curve.n)

        # 计算公钥
        self.public_key = self.curve.point_multiply(self.private_key, self.curve.G)

        return self.private_key, self.public_key

    def compute_shared_secret(self, private_key: int,
                              other_public_key: Tuple[int, int]) -> bytes:
        """
        计算共享密钥

        参数:
            private_key: 自己的私钥
            other_public_key: 对方的公钥

        返回:
            共享密钥（字节）
        """
        # 计算共享点
        shared_point = self.curve.point_multiply(private_key, other_public_key)

        if shared_point is None:
            raise ValueError("共享点是无穷远点")

        # 提取x坐标作为共享密钥
        x = shared_point[0]
        byte_length = (self.curve.p.bit_length() + 7) // 8
        return x.to_bytes(byte_length, 'big')


def demo():
    """ECDH密钥交换演示"""
    print("=== ECDH 密钥交换演示 ===\n")

    # Alice的ECDH
    alice_ecdh = ECDH()
    alice_private, alice_public = alice_ecdh.generate_keypair()

    # Bob的ECDH
    bob_ecdh = ECDH()
    bob_private, bob_public = bob_ecdh.generate_keypair()

    print(f"Alice私钥: {hex(alice_private)[:16]}...")
    print(f"Alice公钥: ({hex(alice_public[0])[:16]}..., {hex(alice_public[1])[:16]}...)")
    print()
    print(f"Bob私钥: {hex(bob_private)[:16]}...")
    print(f"Bob公钥: ({hex(bob_public[0])[:16]}..., {hex(bob_public[1])[:16]}...)")
    print()

    # 计算共享密钥
    alice_shared = alice_ecdh.compute_shared_secret(alice_private, bob_public)
    bob_shared = bob_ecdh.compute_shared_secret(bob_private, alice_public)

    print(f"Alice计算的共享密钥: {alice_shared.hex()[:32]}...")
    print(f"Bob计算的共享密钥:   {bob_shared.hex()[:32]}...")
    print(f"共享密钥一致: {alice_shared == bob_shared}")


if __name__ == '__main__':
    demo()
