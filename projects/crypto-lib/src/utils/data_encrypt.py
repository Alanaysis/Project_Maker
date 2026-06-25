"""
数据加密工具

提供简单易用的数据加密接口，支持：
1. AES加密
2. DES加密
3. 多种加密模式（ECB、CBC、CTR）
4. 自动处理填充

使用示例：
    encryptor = DataEncryptor()
    encrypted = encryptor.encrypt(b"secret data")
    decrypted = encryptor.decrypt(encrypted)
"""

import os
import json
from typing import Tuple, Union
from ..symmetric.aes import AES
from ..symmetric.des import DES
from ..encoding.base64_codec import Base64Codec


class DataEncryptor:
    """数据加密器"""

    def __init__(self, algorithm: str = 'aes', key_size: int = 256,
                 mode: str = 'cbc'):
        """
        初始化数据加密器

        参数:
            algorithm: 加密算法（'aes', 'des'）
            key_size: 密钥大小（AES: 128/192/256, DES: 64）
            mode: 加密模式（'ecb', 'cbc', 'ctr'）
        """
        self.algorithm = algorithm
        self.key_size = key_size
        self.mode = mode

        # 生成密钥
        if algorithm == 'aes':
            key_bytes = key_size // 8
            self.key = os.urandom(key_bytes)
            self._cipher = AES(self.key)
        elif algorithm == 'des':
            self.key = os.urandom(8)
            self._cipher = DES(self.key)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

    def encrypt(self, plaintext: Union[str, bytes]) -> dict:
        """
        加密数据

        参数:
            plaintext: 明文数据

        返回:
            包含密文和参数的字典
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        ciphertext, iv_or_nonce = self._cipher.encrypt(plaintext, self.mode)

        result = {
            'ciphertext': ciphertext.hex(),
            'algorithm': self.algorithm,
            'key_size': self.key_size,
            'mode': self.mode,
            'key': self.key.hex(),
        }

        if iv_or_nonce:
            result['iv'] = iv_or_nonce.hex()

        return result

    def decrypt(self, encrypted: dict) -> bytes:
        """
        解密数据

        参数:
            encrypted: encrypt()返回的字典

        返回:
            解密后的数据
        """
        ciphertext = bytes.fromhex(encrypted['ciphertext'])
        iv = bytes.fromhex(encrypted['iv']) if 'iv' in encrypted else None

        # 如果密钥不同，需要重新初始化
        key = bytes.fromhex(encrypted['key'])
        if key != self.key:
            if encrypted['algorithm'] == 'aes':
                self._cipher = AES(key)
            else:
                self._cipher = DES(key)

        return self._cipher.decrypt(ciphertext, encrypted['mode'], iv)

    def encrypt_string(self, text: str) -> str:
        """
        加密字符串（返回Base64编码）

        参数:
            text: 明文字符串

        返回:
            Base64编码的密文
        """
        encrypted = self.encrypt(text)
        json_str = json.dumps(encrypted)
        return Base64Codec.url_encode(json_str)

    def decrypt_string(self, encoded: str) -> str:
        """
        解密字符串

        参数:
            encoded: Base64编码的密文

        返回:
            解密后的字符串
        """
        json_str = Base64Codec.url_decode(encoded).decode('utf-8')
        encrypted = json.loads(json_str)
        return self.decrypt(encrypted).decode('utf-8')


def demo():
    """数据加密演示"""
    print("=== 数据加密演示 ===\n")

    # AES加密
    print("--- AES加密 ---")
    encryptor = DataEncryptor('aes', 256, 'cbc')

    data = b"Hello, this is secret data!"
    print(f"原始数据: {data}")

    encrypted = encryptor.encrypt(data)
    print(f"加密结果:")
    for key, value in encrypted.items():
        if isinstance(value, str) and len(value) > 32:
            print(f"  {key}: {value[:32]}...")
        else:
            print(f"  {key}: {value}")

    decrypted = encryptor.decrypt(encrypted)
    print(f"解密结果: {decrypted}")
    print()

    # 字符串加密
    print("--- 字符串加密 ---")
    text = "这是一段需要加密的文本"
    print(f"原始文本: {text}")

    encoded = encryptor.encrypt_string(text)
    print(f"加密后: {encoded[:64]}...")

    decoded = encryptor.decrypt_string(encoded)
    print(f"解密后: {decoded}")
    print()

    # DES加密
    print("--- DES加密 ---")
    des_encryptor = DataEncryptor('des', 64, 'cbc')

    data = b"DES encryption test"
    print(f"原始数据: {data}")

    encrypted = des_encryptor.encrypt(data)
    decrypted = des_encryptor.decrypt(encrypted)
    print(f"解密结果: {decrypted}")


if __name__ == '__main__':
    demo()
