"""
数字签名工具

提供简单易用的数字签名接口，支持：
1. RSA签名
2. ECDSA签名
3. 文件签名
4. 消息验证

使用示例：
    sig = SignatureUtil()
    signature = sig.sign_message(b"important message")
    is_valid = sig.verify_message(b"important message", signature)
"""

import hashlib
from typing import Tuple, Union
from ..asymmetric.signature import RSASignature, ECDSASignature


class SignatureUtil:
    """数字签名工具"""

    def __init__(self, algorithm: str = 'ecdsa'):
        """
        初始化签名工具

        参数:
            algorithm: 签名算法（'rsa', 'ecdsa'）
        """
        self.algorithm = algorithm

        if algorithm == 'rsa':
            self._signer = RSASignature(2048)
        elif algorithm == 'ecdsa':
            self._signer = ECDSASignature()
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

        # 生成密钥对
        self._signer.generate_keys()

    def sign_message(self, message: Union[str, bytes]) -> dict:
        """
        签名消息

        参数:
            message: 消息

        返回:
            签名信息字典
        """
        if isinstance(message, str):
            message = message.encode('utf-8')

        signature = self._signer.sign(message)

        # 计算消息哈希
        message_hash = hashlib.sha256(message).hexdigest()

        if self.algorithm == 'rsa':
            return {
                'algorithm': 'rsa',
                'signature': signature.hex(),
                'message_hash': message_hash,
                'public_key': {
                    'e': self._signer.public_key[0],
                    'n': hex(self._signer.public_key[1]),
                },
            }
        else:  # ECDSA
            r, s = signature
            return {
                'algorithm': 'ecdsa',
                'signature': {
                    'r': hex(r),
                    's': hex(s),
                },
                'message_hash': message_hash,
                'public_key': {
                    'x': hex(self._signer.public_key[0]),
                    'y': hex(self._signer.public_key[1]),
                },
            }

    def verify_message(self, message: Union[str, bytes],
                       signature_info: dict) -> bool:
        """
        验证消息签名

        参数:
            message: 消息
            signature_info: sign_message()返回的字典

        返回:
            签名是否有效
        """
        if isinstance(message, str):
            message = message.encode('utf-8')

        # 验证消息哈希
        message_hash = hashlib.sha256(message).hexdigest()
        if message_hash != signature_info['message_hash']:
            return False

        if signature_info['algorithm'] == 'rsa':
            signature = bytes.fromhex(signature_info['signature'])
            pk = signature_info['public_key']
            public_key = (pk['e'], int(pk['n'], 16))
            return self._signer.verify(message, signature, public_key)
        else:  # ECDSA
            sig = signature_info['signature']
            signature = (int(sig['r'], 16), int(sig['s'], 16))
            pk = signature_info['public_key']
            public_key = (int(pk['x'], 16), int(pk['y'], 16))
            self._signer.public_key = public_key
            return self._signer.verify(message, signature)

    def sign_file(self, filepath: str) -> dict:
        """
        签名文件

        参数:
            filepath: 文件路径

        返回:
            签名信息字典
        """
        with open(filepath, 'rb') as f:
            data = f.read()

        return self.sign_message(data)

    def verify_file(self, filepath: str, signature_info: dict) -> bool:
        """
        验证文件签名

        参数:
            filepath: 文件路径
            signature_info: 签名信息

        返回:
            签名是否有效
        """
        with open(filepath, 'rb') as f:
            data = f.read()

        return self.verify_message(data, signature_info)


def demo():
    """数字签名工具演示"""
    print("=== 数字签名工具演示 ===\n")

    # ECDSA签名
    print("--- ECDSA签名 ---")
    sig = SignatureUtil('ecdsa')

    message = b"Important document content"
    print(f"消息: {message}")

    signature_info = sig.sign_message(message)
    print(f"签名算法: {signature_info['algorithm']}")
    print(f"消息哈希: {signature_info['message_hash'][:32]}...")
    print(f"签名 r: {signature_info['signature']['r'][:32]}...")
    print(f"签名 s: {signature_info['signature']['s'][:32]}...")

    is_valid = sig.verify_message(message, signature_info)
    print(f"验证原始消息: {is_valid}")

    is_valid = sig.verify_message(b"Tampered message", signature_info)
    print(f"验证篡改消息: {is_valid}")
    print()

    # RSA签名
    print("--- RSA签名 ---")
    rsa_sig = SignatureUtil('rsa')

    message = b"RSA signed message"
    print(f"消息: {message}")

    signature_info = rsa_sig.sign_message(message)
    print(f"签名算法: {signature_info['algorithm']}")
    print(f"签名: {signature_info['signature'][:32]}...")

    is_valid = rsa_sig.verify_message(message, signature_info)
    print(f"验证原始消息: {is_valid}")

    is_valid = rsa_sig.verify_message(b"Wrong message", signature_info)
    print(f"验证错误消息: {is_valid}")


if __name__ == '__main__':
    demo()
