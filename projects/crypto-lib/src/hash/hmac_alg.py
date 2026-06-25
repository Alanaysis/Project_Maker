"""
HMAC (Hash-based Message Authentication Code) 实现

HMAC是一种基于哈希函数的消息认证码，可以验证消息的完整性和真实性。

算法流程：
1. 如果密钥长度大于哈希块大小，先对密钥进行哈希
2. 如果密钥长度小于哈希块大小，在末尾补零
3. 计算 ipad = 密钥 XOR 0x36（重复到块大小）
4. 计算 opad = 密钥 XOR 0x5C（重复到块大小）
5. HMAC = H(opad || H(ipad || message))

支持的哈希函数：MD5、SHA-1、SHA-256
"""

from typing import Union, Callable
from .md5 import MD5
from .sha1 import SHA1
from .sha256 import SHA256


class HMAC:
    """HMAC消息认证码实现类"""

    # 哈希函数配置
    HASH_CONFIGS = {
        'md5': {
            'hash_func': MD5,
            'block_size': 64,
            'digest_size': 16,
        },
        'sha1': {
            'hash_func': SHA1,
            'block_size': 64,
            'digest_size': 20,
        },
        'sha256': {
            'hash_func': SHA256,
            'block_size': 64,
            'digest_size': 32,
        },
    }

    def __init__(self, key: Union[str, bytes], algorithm: str = 'sha256'):
        """
        初始化HMAC

        参数:
            key: 密钥（字符串或字节）
            algorithm: 哈希算法名称（'md5', 'sha1', 'sha256'）
        """
        if algorithm not in self.HASH_CONFIGS:
            raise ValueError(f"不支持的算法: {algorithm}，支持: {list(self.HASH_CONFIGS.keys())}")

        self._algorithm = algorithm
        self._config = self.HASH_CONFIGS[algorithm]

        if isinstance(key, str):
            key = key.encode('utf-8')

        block_size = self._config['block_size']

        # 如果密钥长度大于块大小，先哈希
        if len(key) > block_size:
            key = self._config['hash_func'].hash(key).encode('latin-1')
            key = bytes.fromhex(key.decode('ascii'))

        # 如果密钥长度小于块大小，补零
        if len(key) < block_size:
            key = key + b'\x00' * (block_size - len(key))

        # 计算 ipad 和 opad
        self._ipad = bytes(k ^ 0x36 for k in key)
        self._opad = bytes(k ^ 0x5C for k in key)

    def update(self, data: Union[str, bytes]) -> 'HMAC':
        """
        更新HMAC计算

        参数:
            data: 要认证的数据（字符串或字节）

        返回:
            self，支持链式调用
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._data = data
        return self

    def digest(self) -> bytes:
        """
        计算并返回HMAC值

        返回:
            HMAC值（字节）
        """
        hash_func = self._config['hash_func']

        # 内层哈希：H(ipad || message)
        inner = hash_func()
        inner.update(self._ipad + self._data)
        inner_hash = inner.digest()

        # 外层哈希：H(opad || inner_hash)
        outer = hash_func()
        outer.update(self._opad + inner_hash)

        return outer.digest()

    def hexdigest(self) -> str:
        """
        计算并返回HMAC值的十六进制表示

        返回:
            十六进制字符串
        """
        return self.digest().hex()

    @staticmethod
    def compute(key: Union[str, bytes], data: Union[str, bytes],
                algorithm: str = 'sha256') -> str:
        """
        一次性计算HMAC值

        参数:
            key: 密钥
            data: 数据
            algorithm: 哈希算法

        返回:
            十六进制字符串
        """
        return HMAC(key, algorithm).update(data).hexdigest()

    @staticmethod
    def verify(key: Union[str, bytes], data: Union[str, bytes],
               expected_mac: str, algorithm: str = 'sha256') -> bool:
        """
        验证HMAC值

        参数:
            key: 密钥
            data: 数据
            expected_mac: 期望的HMAC值（十六进制）
            algorithm: 哈希算法

        返回:
            验证是否通过
        """
        computed_mac = HMAC.compute(key, data, algorithm)

        # 常量时间比较，防止时序攻击
        if len(computed_mac) != len(expected_mac):
            return False

        result = 0
        for x, y in zip(computed_mac.encode(), expected_mac.encode()):
            result |= x ^ y

        return result == 0


def demo():
    """HMAC算法演示"""
    print("=== HMAC 消息认证码演示 ===\n")

    key = "my_secret_key"
    message = "Hello, World!"

    print(f"密钥: '{key}'")
    print(f"消息: '{message}'")
    print()

    # 不同哈希算法的HMAC
    for algo in ['md5', 'sha1', 'sha256']:
        mac = HMAC.compute(key, message, algo)
        print(f"HMAC-{algo.upper()}: {mac}")

    print()

    # 验证演示
    print("--- HMAC验证演示 ---")
    mac = HMAC.compute(key, message, 'sha256')
    print(f"计算的HMAC: {mac}")
    print(f"验证正确消息: {HMAC.verify(key, message, mac, 'sha256')}")
    print(f"验证错误消息: {HMAC.verify(key, 'wrong message', mac, 'sha256')}")
    print(f"验证错误密钥: {HMAC.verify('wrong_key', message, mac, 'sha256')}")


if __name__ == '__main__':
    demo()
