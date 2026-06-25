"""
Hex编码实现

Hex（十六进制）编码将二进制数据转换为十六进制字符串表示。

编码规则：
- 每个字节转换为2个十六进制字符
- 使用字符集：0-9, a-f（或A-F）

应用场景：
- 哈希值显示
- 内存地址表示
- 颜色代码
"""

from typing import Union


class HexCodec:
    """Hex编解码器"""

    @staticmethod
    def encode(data: Union[str, bytes], uppercase: bool = False) -> str:
        """
        Hex编码

        参数:
            data: 要编码的数据（字符串或字节）
            uppercase: 是否使用大写字母

        返回:
            Hex编码字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        if uppercase:
            return data.hex().upper()
        return data.hex()

    @staticmethod
    def decode(hex_str: str) -> bytes:
        """
        Hex解码

        参数:
            hex_str: Hex编码字符串

        返回:
            解码后的字节
        """
        # 移除空白和前缀
        hex_str = hex_str.strip().replace(' ', '')
        if hex_str.startswith('0x') or hex_str.startswith('0X'):
            hex_str = hex_str[2:]

        # 验证长度
        if len(hex_str) % 2 != 0:
            hex_str = '0' + hex_str

        # 验证字符
        valid_chars = set('0123456789abcdefABCDEF')
        for c in hex_str:
            if c not in valid_chars:
                raise ValueError(f"无效的Hex字符: {c}")

        return bytes.fromhex(hex_str)

    @staticmethod
    def format_hex(data: bytes, separator: str = ' ',
                   group_size: int = 1, uppercase: bool = False) -> str:
        """
        格式化Hex输出

        参数:
            data: 要格式化的数据
            separator: 分隔符
            group_size: 每组字节数
            uppercase: 是否使用大写

        返回:
            格式化的Hex字符串
        """
        hex_str = data.hex().upper() if uppercase else data.hex()

        # 按组分隔
        groups = []
        for i in range(0, len(hex_str), group_size * 2):
            groups.append(hex_str[i:i + group_size * 2])

        return separator.join(groups)

    @staticmethod
    def to_int(hex_str: str) -> int:
        """
        Hex转换为整数

        参数:
            hex_str: Hex字符串

        返回:
            整数
        """
        hex_str = hex_str.strip()
        if hex_str.startswith('0x') or hex_str.startswith('0X'):
            hex_str = hex_str[2:]
        return int(hex_str, 16)

    @staticmethod
    def from_int(value: int, byte_length: int = None) -> str:
        """
        整数转换为Hex

        参数:
            value: 整数
            byte_length: 字节长度（用于填充）

        返回:
            Hex字符串
        """
        if byte_length is None:
            byte_length = (value.bit_length() + 7) // 8

        return value.to_bytes(byte_length, 'big').hex()


def demo():
    """Hex编码演示"""
    print("=== Hex 编解码演示 ===\n")

    # 基本编码解码
    test_cases = [
        "Hello, World!",
        b"\x00\x01\x02\x03\x04\x05",
        "Hex编码测试",
        b"\xff\xfe\xfd",
    ]

    for data in test_cases:
        encoded = HexCodec.encode(data)
        decoded = HexCodec.decode(encoded)

        print(f"原始数据: {data}")
        print(f"Hex编码: {encoded}")
        print(f"解码结果: {decoded}")
        print()

    # 格式化输出
    print("--- 格式化Hex输出 ---")
    data = b"\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64"
    print(f"原始数据: {data}")
    print(f"默认格式: {HexCodec.format_hex(data)}")
    print(f"冒号分隔: {HexCodec.format_hex(data, ':')}")
    print(f"2字节分组: {HexCodec.format_hex(data, ' ', 2)}")
    print(f"大写: {HexCodec.format_hex(data, uppercase=True)}")

    # 整数转换
    print("\n--- 整数转换 ---")
    value = 1234567890
    hex_str = HexCodec.from_int(value)
    print(f"整数 {value} -> Hex: {hex_str}")
    print(f"Hex {hex_str} -> 整数: {HexCodec.to_int(hex_str)}")


if __name__ == '__main__':
    demo()
