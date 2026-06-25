"""
非对称加密使用示例

演示RSA、ECDH和数字签名的使用方法。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.asymmetric import RSA, ECDH, DigitalSignature


def main():
    print("=" * 60)
    print("非对称加密使用示例")
    print("=" * 60)

    # 1. RSA加密
    print("\n1. RSA 加密")
    print("-" * 40)

    rsa = RSA(512)  # 使用较小密钥以便演示
    public_key, private_key = rsa.generate_keys()

    message = b"Hello, RSA encryption!"
    print(f"消息: {message}")
    print(f"公钥 e: {public_key[0]}")
    print(f"公钥 n: {hex(public_key[1])[:32]}...")

    ciphertext = rsa.encrypt(message)
    print(f"密文: {ciphertext.hex()[:32]}...")

    decrypted = rsa.decrypt(ciphertext)
    print(f"解密: {decrypted}")

    # 2. ECDH密钥交换
    print("\n2. ECDH 密钥交换")
    print("-" * 40)

    alice = ECDH()
    bob = ECDH()

    alice_private, alice_public = alice.generate_keypair()
    bob_private, bob_public = bob.generate_keypair()

    print(f"Alice公钥: ({hex(alice_public[0])[:16]}...)")
    print(f"Bob公钥: ({hex(bob_public[0])[:16]}...)")

    alice_shared = alice.compute_shared_secret(alice_private, bob_public)
    bob_shared = bob.compute_shared_secret(bob_private, alice_public)

    print(f"\nAlice共享密钥: {alice_shared.hex()[:32]}...")
    print(f"Bob共享密钥: {bob_shared.hex()[:32]}...")
    print(f"密钥一致: {alice_shared == bob_shared}")

    # 3. 数字签名
    print("\n3. 数字签名")
    print("-" * 40)

    # RSA签名
    print("\nRSA签名:")
    message = b"Important document"
    sig, pub_key = DigitalSignature.rsa_sign(message, 512)
    print(f"消息: {message}")
    print(f"签名: {sig.hex()[:32]}...")

    is_valid = DigitalSignature.rsa_verify(message, sig, pub_key, 512)
    print(f"验证原始消息: {is_valid}")

    is_valid = DigitalSignature.rsa_verify(b"Tampered", sig, pub_key, 512)
    print(f"验证篡改消息: {is_valid}")

    # ECDSA签名
    print("\nECDSA签名:")
    sig, pub_key = DigitalSignature.ecdsa_sign(message)
    print(f"消息: {message}")
    print(f"签名 r: {hex(sig[0])[:32]}...")
    print(f"签名 s: {hex(sig[1])[:32]}...")

    is_valid = DigitalSignature.ecdsa_verify(message, sig, pub_key)
    print(f"验证原始消息: {is_valid}")

    is_valid = DigitalSignature.ecdsa_verify(b"Tampered", sig, pub_key)
    print(f"验证篡改消息: {is_valid}")


if __name__ == '__main__':
    main()
