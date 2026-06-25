"""
Base64编码实现

Base64是一种基于64个可打印字符来表示二进制数据的编码方式。

编码表：A-Z, a-z, 0-9, +, /

编码流程：
1. 将每3个字节（24位）分为4组（每组6位）
2. 将每6位映射到Base64字符
3. 如果字节数不是3的倍数，用'='填充

应用场景：
- 电子邮件附件
- URL编码
- 数据传输
"""

from typing import Union


class Base64Codec:
    """Base64编解码器"""

    # Base64字符表
    CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    @classmethod
    def encode(cls, data: Union[str, bytes]) -> str:
        """
        Base64编码

        参数:
            data: 要编码的数据（字符串或字节）

        返回:
            Base64编码字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        result = []
        padding = len(data) % 3

        # 处理完整的3字节组
        for i in range(0, len(data) - padding, 3):
            # 读取3个字节
            b1 = data[i]
            b2 = data[i + 1]
            b3 = data[i + 2]

            # 转换为4个6位值
            result.append(cls.CHARSET[(b1 >> 2) & 0x3F])
            result.append(cls.CHARSET[((b1 << 4) | (b2 >> 4)) & 0x3F])
            result.append(cls.CHARSET[((b2 << 2) | (b3 >> 6)) & 0x3F])
            result.append(cls.CHARSET[b3 & 0x3F])

        # 处理剩余字节
        if padding == 1:
            b1 = data[-1]
            result.append(cls.CHARSET[(b1 >> 2) & 0x3F])
            result.append(cls.CHARSET[(b1 << 4) & 0x3F])
            result.append('=')
            result.append('=')
        elif padding == 2:
            b1 = data[-2]
            b2 = data[-1]
            result.append(cls.CHARSET[(b1 >> 2) & 0x3F])
            result.append(cls.CHARSET[((b1 << 4) | (b2 >> 4)) & 0x3F])
            result.append(cls.CHARSET[(b2 << 2) & 0x3F])
            result.append('=')

        return ''.join(result)

    @classmethod
    def decode(cls, encoded: str) -> bytes:
        """
        Base64解码

        参数:
            encoded: Base64编码字符串

        返回:
            解码后的字节
        """
        # 移除空白字符
        encoded = encoded.strip()

        # 验证长度
        if len(encoded) % 4 != 0:
            raise ValueError("无效的Base64编码长度")

        # 构建反向查找表
        charset_map = {c: i for i, c in enumerate(cls.CHARSET)}

        result = bytearray()
        padding = encoded.count('=')

        # 移除填充
        encoded = encoded.rstrip('=')

        # 处理完整的4字符组
        for i in range(0, len(encoded), 4):
            # 获取4个6位值
            group = encoded[i:i+4]
            group_len = len(group)
            values = []
            for c in group:
                if c not in charset_map:
                    raise ValueError(f"无效的Base64字符: {c}")
                values.append(charset_map[c])

            # 补充缺失的值
            while len(values) < 4:
                values.append(0)

            # 转换为3个字节
            result.append(((values[0] << 2) | (values[1] >> 4)) & 0xFF)

            if group_len >= 3:
                result.append(((values[1] << 4) | (values[2] >> 2)) & 0xFF)

            if group_len >= 4:
                result.append(((values[2] << 6) | values[3]) & 0xFF)

        return bytes(result)

    @staticmethod
    def url_encode(data: Union[str, bytes]) -> str:
        """
        URL安全的Base64编码

        将 + 替换为 -，/ 替换为 _，移除填充 =

        参数:
            data: 要编码的数据

        返回:
            URL安全的Base64字符串
        """
        encoded = Base64Codec.encode(data)
        return encoded.replace('+', '-').replace('/', '_').rstrip('=')

    @staticmethod
    def url_decode(encoded: str) -> bytes:
        """
        URL安全的Base64解码

        参数:
            encoded: URL安全的Base64字符串

        返回:
            解码后的字节
        """
        # 恢复标准Base64
        encoded = encoded.replace('-', '+').replace('_', '/')

        # 补充填充
        padding = 4 - (len(encoded) % 4)
        if padding != 4:
            encoded += '=' * padding

        return Base64Codec.decode(encoded)


def demo():
    """Base64编码演示"""
    print("=== Base64 编解码演示 ===\n")

    test_cases = [
        "Hello, World!",
        "Base64编码测试",
        b"\x00\x01\x02\x03\x04\x05",
        "AB",
        "ABC",
        "ABCD",
    ]

    for data in test_cases:
        encoded = Base64Codec.encode(data)
        decoded = Base64Codec.decode(encoded)

        print(f"原始数据: {data}")
        print(f"Base64编码: {encoded}")
        print(f"解码结果: {decoded}")
        print()

    # URL安全编码演示
    print("--- URL安全Base64 ---")
    data = "Hello+World/Test=Value"
    encoded = Base64Codec.url_encode(data)
    decoded = Base64Codec.url_decode(encoded)
    print(f"原始数据: {data}")
    print(f"URL安全编码: {encoded}")
    print(f"解码结果: {decoded}")


if __name__ == '__main__':
    demo()
