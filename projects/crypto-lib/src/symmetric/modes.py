"""
分组密码工作模式实现

实现三种常用的分组密码工作模式：
- ECB (Electronic Codebook)：电子密码本模式
- CBC (Cipher Block Chaining)：密码块链接模式
- CTR (Counter)：计数器模式

每种模式的安全性分析：
- ECB：不推荐，相同明文块产生相同密文块
- CBC：推荐，需要随机IV，串行处理
- CTR：推荐，可并行处理，需要唯一计数器
"""

import os
from typing import Callable, Tuple


class BlockCipherMode:
    """分组密码工作模式基类"""

    def __init__(self, block_size: int = 16):
        """
        初始化

        参数:
            block_size: 分组大小（字节）
        """
        self.block_size = block_size

    def _pad(self, data: bytes) -> bytes:
        """
        PKCS7填充

        参数:
            data: 待填充数据

        返回:
            填充后的数据
        """
        padding_len = self.block_size - (len(data) % self.block_size)
        return data + bytes([padding_len] * padding_len)

    def _unpad(self, data: bytes) -> bytes:
        """
        PKCS7去填充

        参数:
            data: 填充的数据

        返回:
            去填充后的数据
        """
        padding_len = data[-1]
        if padding_len > self.block_size or padding_len == 0:
            raise ValueError("无效的填充")
        if data[-padding_len:] != bytes([padding_len] * padding_len):
            raise ValueError("无效的填充")
        return data[:-padding_len]

    @staticmethod
    def _xor_blocks(a: bytes, b: bytes) -> bytes:
        """两个块异或"""
        return bytes(x ^ y for x, y in zip(a, b))


class ECB(BlockCipherMode):
    """
    ECB (Electronic Codebook) 电子密码本模式

    特点：
    - 每个块独立加密
    - 相同明文块产生相同密文块（不安全）
    - 可并行处理
    - 不需要IV

    加密：C_i = E(P_i)
    解密：P_i = D(C_i)
    """

    def encrypt(self, plaintext: bytes, encrypt_func: Callable) -> bytes:
        """
        ECB模式加密

        参数:
            plaintext: 明文
            encrypt_func: 块加密函数

        返回:
            密文
        """
        padded = self._pad(plaintext)
        ciphertext = b''

        for i in range(0, len(padded), self.block_size):
            block = padded[i:i + self.block_size]
            ciphertext += encrypt_func(block)

        return ciphertext

    def decrypt(self, ciphertext: bytes, decrypt_func: Callable) -> bytes:
        """
        ECB模式解密

        参数:
            ciphertext: 密文
            decrypt_func: 块解密函数

        返回:
            明文
        """
        plaintext = b''

        for i in range(0, len(ciphertext), self.block_size):
            block = ciphertext[i:i + self.block_size]
            plaintext += decrypt_func(block)

        return self._unpad(plaintext)


class CBC(BlockCipherMode):
    """
    CBC (Cipher Block Chaining) 密码块链接模式

    特点：
    - 每个明文块在加密前与前一个密文块异或
    - 需要随机IV（初始化向量）
    - 相同明文产生不同密文
    - 串行处理（不能并行）

    加密：C_i = E(P_i XOR C_{i-1}), C_0 = IV
    解密：P_i = D(C_i) XOR C_{i-1}, C_0 = IV
    """

    def __init__(self, iv: bytes = None, block_size: int = 16):
        """
        初始化CBC模式

        参数:
            iv: 初始化向量（如果为None则自动生成）
            block_size: 分组大小
        """
        super().__init__(block_size)
        self.iv = iv if iv else os.urandom(block_size)

    def encrypt(self, plaintext: bytes, encrypt_func: Callable) -> Tuple[bytes, bytes]:
        """
        CBC模式加密

        参数:
            plaintext: 明文
            encrypt_func: 块加密函数

        返回:
            (密文, IV)
        """
        padded = self._pad(plaintext)
        ciphertext = b''
        prev_block = self.iv

        for i in range(0, len(padded), self.block_size):
            block = padded[i:i + self.block_size]
            # 明文块与前一个密文块异或
            xored = self._xor_blocks(block, prev_block)
            # 加密
            encrypted = encrypt_func(xored)
            ciphertext += encrypted
            prev_block = encrypted

        return ciphertext, self.iv

    def decrypt(self, ciphertext: bytes, decrypt_func: Callable,
                iv: bytes = None) -> bytes:
        """
        CBC模式解密

        参数:
            ciphertext: 密文
            decrypt_func: 块解密函数
            iv: 初始化向量（如果为None则使用加密时的IV）

        返回:
            明文
        """
        if iv is None:
            iv = self.iv

        plaintext = b''
        prev_block = iv

        for i in range(0, len(ciphertext), self.block_size):
            block = ciphertext[i:i + self.block_size]
            # 解密
            decrypted = decrypt_func(block)
            # 与前一个密文块异或
            plaintext += self._xor_blocks(decrypted, prev_block)
            prev_block = block

        return self._unpad(plaintext)


class CTR(BlockCipherMode):
    """
    CTR (Counter) 计数器模式

    特点：
    - 将分组密码变为流密码
    - 可并行处理
    - 不需要填充
    - 需要唯一计数器（nonce + counter）

    加密：C_i = P_i XOR E(Nonce || Counter_i)
    解密：P_i = C_i XOR E(Nonce || Counter_i)
    """

    def __init__(self, nonce: bytes = None, block_size: int = 16):
        """
        初始化CTR模式

        参数:
            nonce: 随机数（如果为None则自动生成）
            block_size: 分组大小
        """
        super().__init__(block_size)
        self.nonce = nonce if nonce else os.urandom(block_size // 2)
        self.counter = 0

    def _generate_counter_block(self) -> bytes:
        """生成计数器块"""
        # nonce + counter（大端序）
        counter_bytes = self.counter.to_bytes(self.block_size // 2, 'big')
        block = self.nonce + counter_bytes
        self.counter += 1
        return block

    def encrypt(self, plaintext: bytes, encrypt_func: Callable) -> Tuple[bytes, bytes]:
        """
        CTR模式加密

        参数:
            plaintext: 明文
            encrypt_func: 块加密函数

        返回:
            (密文, nonce)
        """
        ciphertext = b''

        for i in range(0, len(plaintext), self.block_size):
            block = plaintext[i:i + self.block_size]
            # 生成密钥流
            counter_block = self._generate_counter_block()
            keystream = encrypt_func(counter_block)
            # 异或
            ciphertext += self._xor_blocks(block, keystream[:len(block)])

        return ciphertext, self.nonce

    def decrypt(self, ciphertext: bytes, decrypt_func: Callable,
                nonce: bytes = None) -> bytes:
        """
        CTR模式解密（与加密相同）

        参数:
            ciphertext: 密文
            decrypt_func: 块加密函数（CTR模式解密使用加密函数）
            nonce: 随机数

        返回:
            明文
        """
        if nonce is not None:
            self.nonce = nonce
            self.counter = 0

        # CTR模式解密与加密相同
        return self.encrypt(ciphertext, decrypt_func)[0]


def demo():
    """分组模式演示"""
    print("=== 分组密码工作模式演示 ===\n")

    # 简单的块加密函数（XOR，仅用于演示）
    def simple_encrypt(block: bytes) -> bytes:
        """简单的XOR加密（仅用于演示）"""
        key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10'
        return bytes(a ^ b for a, b in zip(block, key))

    def simple_decrypt(block: bytes) -> bytes:
        """简单的XOR解密（仅用于演示）"""
        return simple_encrypt(block)  # XOR的自反性

    plaintext = b"Hello, Crypto World!"
    print(f"明文: {plaintext}")
    print()

    # ECB模式
    ecb = ECB()
    ecb_ciphertext = ecb.encrypt(plaintext, simple_encrypt)
    ecb_decrypted = ecb.decrypt(ecb_ciphertext, simple_decrypt)
    print(f"ECB密文: {ecb_ciphertext.hex()}")
    print(f"ECB解密: {ecb_decrypted}")
    print()

    # CBC模式
    cbc = CBC()
    cbc_ciphertext, iv = cbc.encrypt(plaintext, simple_encrypt)
    cbc_decrypted = cbc.decrypt(cbc_ciphertext, simple_decrypt, iv)
    print(f"CBC IV: {iv.hex()}")
    print(f"CBC密文: {cbc_ciphertext.hex()}")
    print(f"CBC解密: {cbc_decrypted}")
    print()

    # CTR模式
    ctr = CTR()
    ctr_ciphertext, nonce = ctr.encrypt(plaintext, simple_encrypt)
    ctr_decrypted = ctr.decrypt(ctr_ciphertext, simple_encrypt, nonce)
    print(f"CTR Nonce: {nonce.hex()}")
    print(f"CTR密文: {ctr_ciphertext.hex()}")
    print(f"CTR解密: {ctr_decrypted}")


if __name__ == '__main__':
    demo()
