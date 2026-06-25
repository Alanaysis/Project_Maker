"""
非对称加密测试

测试RSA、ECDH和数字签名的正确性。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.asymmetric import RSA, ECDH, DigitalSignature


class TestRSA(unittest.TestCase):
    """RSA测试"""

    def test_key_generation(self):
        """测试密钥生成"""
        rsa = RSA(512)
        public_key, private_key = rsa.generate_keys()

        self.assertEqual(len(public_key), 2)
        self.assertEqual(len(private_key), 2)
        self.assertEqual(public_key[1], private_key[1])  # n相同

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        rsa = RSA(512)
        rsa.generate_keys()

        message = b"Hello, RSA!"
        ciphertext = rsa.encrypt(message)
        decrypted = rsa.decrypt(ciphertext)

        self.assertEqual(decrypted, message)

    def test_sign_verify(self):
        """测试签名验证"""
        rsa = RSA(512)
        rsa.generate_keys()

        message = b"Sign this message"
        signature = rsa.sign(message)

        self.assertTrue(rsa.verify(message, signature))
        self.assertFalse(rsa.verify(b"Wrong message", signature))


class TestECDH(unittest.TestCase):
    """ECDH测试"""

    def test_key_exchange(self):
        """测试密钥交换"""
        alice = ECDH()
        bob = ECDH()

        alice_private, alice_public = alice.generate_keypair()
        bob_private, bob_public = bob.generate_keypair()

        alice_shared = alice.compute_shared_secret(alice_private, bob_public)
        bob_shared = bob.compute_shared_secret(bob_private, alice_public)

        self.assertEqual(alice_shared, bob_shared)

    def test_different_keys(self):
        """测试不同密钥"""
        ecdh1 = ECDH()
        ecdh2 = ECDH()

        priv1, pub1 = ecdh1.generate_keypair()
        priv2, pub2 = ecdh2.generate_keypair()

        # 不同的私钥应该产生不同的公钥
        self.assertNotEqual(priv1, priv2)


class TestDigitalSignature(unittest.TestCase):
    """数字签名测试"""

    def test_rsa_signature(self):
        """测试RSA签名"""
        message = b"Test message"
        signature, public_key = DigitalSignature.rsa_sign(message, 512)

        self.assertTrue(DigitalSignature.rsa_verify(message, signature, public_key, 512))
        self.assertFalse(DigitalSignature.rsa_verify(b"Wrong", signature, public_key, 512))

    def test_ecdsa_signature(self):
        """测试ECDSA签名"""
        message = b"Test message"
        signature, public_key = DigitalSignature.ecdsa_sign(message)

        self.assertTrue(DigitalSignature.ecdsa_verify(message, signature, public_key))
        self.assertFalse(DigitalSignature.ecdsa_verify(b"Wrong", signature, public_key))


if __name__ == '__main__':
    unittest.main()
