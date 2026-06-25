"""
对称加密使用示例

演示AES和DES加密的使用方法，包括不同的加密模式。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.symmetric import AES, DES


def main():
    print("=" * 60)
    print("对称加密使用示例")
    print("=" * 60)

    # 1. AES加密
    print("\n1. AES 加密")
    print("-" * 40)

    # AES-128
    key128 = os.urandom(16)
    aes128 = AES(key128)
    plaintext = b"Hello, AES encryption!"

    print(f"明文: {plaintext}")
    print(f"AES-128 密钥: {key128.hex()}")

    # CBC模式
    ciphertext, iv = aes128.encrypt(plaintext, 'cbc')
    decrypted = aes128.decrypt(ciphertext, 'cbc', iv)
    print(f"\nCBC模式:")
    print(f"  IV: {iv.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")

    # CTR模式
    ciphertext, nonce = aes128.encrypt(plaintext, 'ctr')
    decrypted = aes128.decrypt(ciphertext, 'ctr', nonce=nonce)
    print(f"\nCTR模式:")
    print(f"  Nonce: {nonce.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")

    # AES-256
    key256 = os.urandom(32)
    aes256 = AES(key256)
    ciphertext, iv = aes256.encrypt(plaintext, 'cbc')
    decrypted = aes256.decrypt(ciphertext, 'cbc', iv)
    print(f"\nAES-256 CBC模式:")
    print(f"  密钥: {key256.hex()}")
    print(f"  密文: {ciphertext.hex()[:32]}...")
    print(f"  解密: {decrypted}")

    # 2. DES加密
    print("\n2. DES 加密")
    print("-" * 40)

    key = os.urandom(8)
    des = DES(key)
    plaintext = b"Hello, DES!"

    print(f"明文: {plaintext}")
    print(f"DES 密钥: {key.hex()}")

    ciphertext, iv = des.encrypt(plaintext, 'cbc')
    decrypted = des.decrypt(ciphertext, 'cbc', iv)
    print(f"\nCBC模式:")
    print(f"  IV: {iv.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")

    # 3. 分组模式对比
    print("\n3. 分组模式对比")
    print("-" * 40)

    key = os.urandom(16)
    aes = AES(key)
    plaintext = b"Block cipher mode comparison test data!"

    for mode in ['ecb', 'cbc', 'ctr']:
        ciphertext, iv = aes.encrypt(plaintext, mode)
        decrypted = aes.decrypt(ciphertext, mode, iv)
        print(f"\n{mode.upper()}模式:")
        print(f"  密文长度: {len(ciphertext)} 字节")
        print(f"  解密正确: {decrypted == plaintext}")


if __name__ == '__main__':
    main()
