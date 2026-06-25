"""
对称加密测试

测试AES和DES加密的正确性。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.symmetric import AES, DES


class TestAES(unittest.TestCase):
    """AES测试"""

    def test_aes128_cbc(self):
        """测试AES-128 CBC模式"""
        key = os.urandom(16)
        aes = AES(key)
        plaintext = b"Hello, AES encryption test!"

        ciphertext, iv = aes.encrypt(plaintext, 'cbc')
        decrypted = aes.decrypt(ciphertext, 'cbc', iv)

        self.assertEqual(decrypted, plaintext)

    def test_aes256_cbc(self):
        """测试AES-256 CBC模式"""
        key = os.urandom(32)
        aes = AES(key)
        plaintext = b"AES-256 encryption test"

        ciphertext, iv = aes.encrypt(plaintext, 'cbc')
        decrypted = aes.decrypt(ciphertext, 'cbc', iv)

        self.assertEqual(decrypted, plaintext)

    def test_aes_ctr(self):
        """测试AES CTR模式"""
        key = os.urandom(16)
        aes = AES(key)
        plaintext = b"CTR mode test"

        ciphertext, nonce = aes.encrypt(plaintext, 'ctr')
        decrypted = aes.decrypt(ciphertext, 'ctr', nonce=nonce)

        self.assertEqual(decrypted, plaintext)

    def test_aes_ecb(self):
        """测试AES ECB模式"""
        key = os.urandom(16)
        aes = AES(key)
        plaintext = b"ECB mode test data!!"  # 必须是16字节倍数

        ciphertext, _ = aes.encrypt(plaintext, 'ecb')
        decrypted = aes.decrypt(ciphertext, 'ecb')

        self.assertEqual(decrypted, plaintext)

    def test_invalid_key_size(self):
        """测试无效密钥大小"""
        with self.assertRaises(ValueError):
            AES(b"short")

    def test_block_encrypt_decrypt(self):
        """测试块加密解密"""
        key = os.urandom(16)
        aes = AES(key)
        block = os.urandom(16)

        encrypted = aes.encrypt_block(block)
        decrypted = aes.decrypt_block(encrypted)

        self.assertEqual(decrypted, block)


class TestDES(unittest.TestCase):
    """DES测试"""

    def test_des_cbc(self):
        """测试DES CBC模式"""
        key = os.urandom(8)
        des = DES(key)
        plaintext = b"DES test!"

        ciphertext, iv = des.encrypt(plaintext, 'cbc')
        decrypted = des.decrypt(ciphertext, 'cbc', iv)

        self.assertEqual(decrypted, plaintext)

    def test_des_ctr(self):
        """测试DES CTR模式"""
        key = os.urandom(8)
        des = DES(key)
        plaintext = b"CTR mode"

        ciphertext, nonce = des.encrypt(plaintext, 'ctr')
        decrypted = des.decrypt(ciphertext, 'ctr', nonce=nonce)

        self.assertEqual(decrypted, plaintext)

    def test_invalid_key_size(self):
        """测试无效密钥大小"""
        with self.assertRaises(ValueError):
            DES(b"short")

    def test_block_encrypt_decrypt(self):
        """测试块加密解密"""
        key = os.urandom(8)
        des = DES(key)
        block = os.urandom(8)

        encrypted = des.encrypt_block(block)
        decrypted = des.decrypt_block(encrypted)

        self.assertEqual(decrypted, block)


if __name__ == '__main__':
    unittest.main()
