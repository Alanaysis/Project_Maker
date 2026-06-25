"""
编码测试

测试Base64和Hex编码的正确性。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.encoding import Base64Codec, HexCodec


class TestBase64(unittest.TestCase):
    """Base64测试"""

    def test_encode_decode(self):
        """测试编码解码"""
        data = b"Hello, World!"
        encoded = Base64Codec.encode(data)
        decoded = Base64Codec.decode(encoded)
        self.assertEqual(decoded, data)

    def test_empty(self):
        """测试空数据"""
        self.assertEqual(Base64Codec.encode(b""), "")
        self.assertEqual(Base64Codec.decode(""), b"")

    def test_padding(self):
        """测试填充"""
        # 1字节 -> 2个填充
        self.assertEqual(Base64Codec.encode(b"A"), "QQ==")
        # 2字节 -> 1个填充
        self.assertEqual(Base64Codec.encode(b"AB"), "QUI=")
        # 3字节 -> 无填充
        self.assertEqual(Base64Codec.encode(b"ABC"), "QUJD")

    def test_string_input(self):
        """测试字符串输入"""
        data = "Hello"
        encoded = Base64Codec.encode(data)
        decoded = Base64Codec.decode(encoded)
        self.assertEqual(decoded, data.encode('utf-8'))

    def test_url_safe(self):
        """测试URL安全编码"""
        data = b"Hello+World/Test"
        encoded = Base64Codec.url_encode(data)
        decoded = Base64Codec.url_decode(encoded)
        self.assertEqual(decoded, data)
        self.assertNotIn('+', encoded)
        self.assertNotIn('/', encoded)


class TestHex(unittest.TestCase):
    """Hex测试"""

    def test_encode_decode(self):
        """测试编码解码"""
        data = b"Hello"
        encoded = HexCodec.encode(data)
        decoded = HexCodec.decode(encoded)
        self.assertEqual(decoded, data)

    def test_empty(self):
        """测试空数据"""
        self.assertEqual(HexCodec.encode(b""), "")
        self.assertEqual(HexCodec.decode(""), b"")

    def test_uppercase(self):
        """测试大写"""
        data = b"Hello"
        self.assertEqual(HexCodec.encode(data, uppercase=True), "48656C6C6F")
        self.assertEqual(HexCodec.encode(data, uppercase=False), "48656c6c6f")

    def test_format(self):
        """测试格式化"""
        data = b"\x01\x02\x03\x04"
        self.assertEqual(HexCodec.format_hex(data, ':'), "01:02:03:04")
        self.assertEqual(HexCodec.format_hex(data, ' ', 2), "0102 0304")

    def test_int_conversion(self):
        """测试整数转换"""
        self.assertEqual(HexCodec.to_int("ff"), 255)
        self.assertEqual(HexCodec.from_int(255), "ff")


if __name__ == '__main__':
    unittest.main()
