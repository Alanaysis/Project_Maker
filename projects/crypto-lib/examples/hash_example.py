"""
哈希算法使用示例

演示MD5、SHA-1、SHA-256和HMAC的使用方法。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hash import MD5, SHA1, SHA256, HMAC


def main():
    print("=" * 60)
    print("哈希算法使用示例")
    print("=" * 60)

    # 1. MD5哈希
    print("\n1. MD5 哈希算法")
    print("-" * 40)
    message = "Hello, World!"
    md5_hash = MD5.hash(message)
    print(f"消息: {message}")
    print(f"MD5: {md5_hash}")

    # 分块更新
    hasher = MD5()
    hasher.update("Hello, ")
    hasher.update("World!")
    print(f"分块计算: {hasher.hexdigest()}")

    # 2. SHA-1哈希
    print("\n2. SHA-1 哈希算法")
    print("-" * 40)
    sha1_hash = SHA1.hash(message)
    print(f"消息: {message}")
    print(f"SHA-1: {sha1_hash}")

    # 3. SHA-256哈希
    print("\n3. SHA-256 哈希算法")
    print("-" * 40)
    sha256_hash = SHA256.hash(message)
    print(f"消息: {message}")
    print(f"SHA-256: {sha256_hash}")

    # 4. HMAC消息认证
    print("\n4. HMAC 消息认证码")
    print("-" * 40)
    key = "my_secret_key"
    print(f"密钥: {key}")
    print(f"消息: {message}")

    hmac_md5 = HMAC.compute(key, message, 'md5')
    hmac_sha1 = HMAC.compute(key, message, 'sha1')
    hmac_sha256 = HMAC.compute(key, message, 'sha256')

    print(f"HMAC-MD5: {hmac_md5}")
    print(f"HMAC-SHA1: {hmac_sha1}")
    print(f"HMAC-SHA256: {hmac_sha256}")

    # 验证HMAC
    print("\n--- HMAC验证 ---")
    print(f"验证正确: {HMAC.verify(key, message, hmac_sha256, 'sha256')}")
    print(f"验证错误: {HMAC.verify(key, 'wrong', hmac_sha256, 'sha256')}")


if __name__ == '__main__':
    main()
