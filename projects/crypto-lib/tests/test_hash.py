"""
哈希算法测试

测试MD5、SHA-1、SHA-256和HMAC的正确性。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.hash import MD5, SHA1, SHA256, HMAC


class TestMD5(unittest.TestCase):
    """MD5测试"""

    def test_empty_string(self):
        """测试空字符串"""
        self.assertEqual(MD5.hash(""), "d41d8cd98f00b204e9800998ecf8427e")

    def test_abc(self):
        """测试'abc'"""
        self.assertEqual(MD5.hash("abc"), "900150983cd24fb0d6963f7d28e17f72")

    def test_message_digest(self):
        """测试'message digest'"""
        self.assertEqual(MD5.hash("message digest"), "f96b697d7cb7938d525a2f31aaf161d0")

    def test_update(self):
        """测试分块更新"""
        hasher = MD5()
        hasher.update("Hello, ")
        hasher.update("World!")
        self.assertEqual(hasher.hexdigest(), MD5.hash("Hello, World!"))

    def test_chinese(self):
        """测试中文"""
        result = MD5.hash("密码学")
        self.assertEqual(len(result), 32)


class TestSHA1(unittest.TestCase):
    """SHA-1测试"""

    def test_empty_string(self):
        """测试空字符串"""
        self.assertEqual(SHA1.hash(""), "da39a3ee5e6b4b0d3255bfef95601890afd80709")

    def test_abc(self):
        """测试'abc'"""
        self.assertEqual(SHA1.hash("abc"), "a9993e364706816aba3e25717850c26c9cd0d89d")

    def test_update(self):
        """测试分块更新"""
        hasher = SHA1()
        hasher.update("Hello, ")
        hasher.update("World!")
        self.assertEqual(hasher.hexdigest(), SHA1.hash("Hello, World!"))


class TestSHA256(unittest.TestCase):
    """SHA-256测试"""

    def test_empty_string(self):
        """测试空字符串"""
        self.assertEqual(
            SHA256.hash(""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_abc(self):
        """测试'abc'"""
        self.assertEqual(
            SHA256.hash("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

    def test_update(self):
        """测试分块更新"""
        hasher = SHA256()
        hasher.update("Hello, ")
        hasher.update("World!")
        self.assertEqual(hasher.hexdigest(), SHA256.hash("Hello, World!"))

    def test_consistency(self):
        """测试一致性"""
        data = "test data"
        self.assertEqual(SHA256.hash(data), SHA256.hash(data))


class TestHMAC(unittest.TestCase):
    """HMAC测试"""

    def test_hmac_sha256(self):
        """测试HMAC-SHA256"""
        key = "secret"
        data = "Hello"
        mac = HMAC.compute(key, data, 'sha256')
        self.assertEqual(len(mac), 64)  # 32字节 = 64十六进制字符

    def test_verify(self):
        """测试验证"""
        key = "secret"
        data = "Hello"
        mac = HMAC.compute(key, data, 'sha256')
        self.assertTrue(HMAC.verify(key, data, mac, 'sha256'))

    def test_verify_wrong_data(self):
        """测试错误数据验证"""
        key = "secret"
        data = "Hello"
        mac = HMAC.compute(key, data, 'sha256')
        self.assertFalse(HMAC.verify(key, "Wrong", mac, 'sha256'))

    def test_verify_wrong_key(self):
        """测试错误密钥验证"""
        key = "secret"
        data = "Hello"
        mac = HMAC.compute(key, data, 'sha256')
        self.assertFalse(HMAC.verify("wrong", data, mac, 'sha256'))

    def test_different_algorithms(self):
        """测试不同算法"""
        key = "secret"
        data = "Hello"
        mac_md5 = HMAC.compute(key, data, 'md5')
        mac_sha1 = HMAC.compute(key, data, 'sha1')
        mac_sha256 = HMAC.compute(key, data, 'sha256')
        self.assertEqual(len(mac_md5), 32)  # 16字节
        self.assertEqual(len(mac_sha1), 40)  # 20字节
        self.assertEqual(len(mac_sha256), 64)  # 32字节


if __name__ == '__main__':
    unittest.main()
