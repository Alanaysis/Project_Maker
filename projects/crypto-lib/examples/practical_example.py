"""
实际应用示例

演示密码存储、数据加密和数字签名的实际应用场景。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import PasswordManager, DataEncryptor, SignatureUtil
from src.encoding import Base64Codec, HexCodec


def main():
    print("=" * 60)
    print("实际应用场景示例")
    print("=" * 60)

    # 1. 密码存储
    print("\n1. 安全密码存储")
    print("-" * 40)

    pm = PasswordManager(iterations=100000)

    # 模拟用户注册
    print("用户注册:")
    password = "MySecurePassword123!"
    stored = pm.store_password(password)
    print(f"  密码: {password}")
    print(f"  存储哈希: {stored['hash'][:32]}...")
    print(f"  盐值: {stored['salt'][:32]}...")
    print(f"  算法: {stored['algorithm']}")
    print(f"  迭代次数: {stored['iterations']}")

    # 模拟用户登录
    print("\n用户登录:")
    print(f"  输入正确密码: {pm.check_password(password, stored)}")
    print(f"  输入错误密码: {pm.check_password('WrongPassword', stored)}")

    # 2. 数据加密
    print("\n2. 数据加密")
    print("-" * 40)

    # 敏感数据加密
    encryptor = DataEncryptor('aes', 256, 'cbc')

    sensitive_data = "信用卡号: 4111-1111-1111-1111"
    print(f"敏感数据: {sensitive_data}")

    encrypted = encryptor.encrypt_string(sensitive_data)
    print(f"加密后: {encrypted[:48]}...")

    decrypted = encryptor.decrypt_string(encrypted)
    print(f"解密后: {decrypted}")

    # 3. 数字签名
    print("\n3. 数字签名验证")
    print("-" * 40)

    # 文件签名
    sig = SignatureUtil('ecdsa')

    # 创建测试文件
    test_file = "/tmp/test_document.txt"
    with open(test_file, 'w') as f:
        f.write("This is an important document.\n")
        f.write("It needs to be signed for verification.\n")

    # 签名文件
    signature_info = sig.sign_file(test_file)
    print(f"文件已签名")
    print(f"签名算法: {signature_info['algorithm']}")
    print(f"消息哈希: {signature_info['message_hash'][:32]}...")

    # 验证文件
    is_valid = sig.verify_file(test_file, signature_info)
    print(f"验证文件: {is_valid}")

    # 篡改文件
    with open(test_file, 'a') as f:
        f.write("This line was added by an attacker!\n")

    is_valid = sig.verify_file(test_file, signature_info)
    print(f"验证篡改文件: {is_valid}")

    # 清理
    os.remove(test_file)

    # 4. 编码工具
    print("\n4. 编码工具")
    print("-" * 40)

    data = "Hello, Crypto!"
    print(f"原始数据: {data}")

    # Base64编码
    b64 = Base64Codec.encode(data)
    print(f"Base64: {b64}")

    # Hex编码
    hex_encoded = HexCodec.encode(data)
    print(f"Hex: {hex_encoded}")

    # 格式化Hex
    formatted = HexCodec.format_hex(data.encode(), ':', 1)
    print(f"格式化Hex: {formatted}")


if __name__ == '__main__':
    main()
