"""
密码存储工具

安全的密码存储方案：
1. 使用随机盐值
2. 使用PBKDF2进行密钥派生
3. 使用HMAC进行哈希
4. 支持多种哈希算法

安全建议：
- 不要使用MD5或SHA-1进行密码哈希
- 使用足够长的随机盐值
- 使用足够多的迭代次数
"""

import os
import hashlib
import hmac
from typing import Tuple, Optional


class PasswordManager:
    """密码管理器"""

    def __init__(self, algorithm: str = 'sha256', iterations: int = 100000):
        """
        初始化密码管理器

        参数:
            algorithm: 哈希算法（'sha256', 'sha512'）
            iterations: PBKDF2迭代次数
        """
        self.algorithm = algorithm
        self.iterations = iterations

    @staticmethod
    def generate_salt(length: int = 32) -> bytes:
        """
        生成随机盐值

        参数:
            length: 盐值长度（字节）

        返回:
            随机盐值
        """
        return os.urandom(length)

    def hash_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        哈希密码

        参数:
            password: 密码
            salt: 盐值（如果为None则自动生成）

        返回:
            (哈希值, 盐值)
        """
        if salt is None:
            salt = self.generate_salt()

        # 使用PBKDF2进行密钥派生
        hash_value = hashlib.pbkdf2_hmac(
            self.algorithm,
            password.encode('utf-8'),
            salt,
            self.iterations
        )

        return hash_value, salt

    def verify_password(self, password: str, hash_value: bytes,
                        salt: bytes) -> bool:
        """
        验证密码

        参数:
            password: 密码
            hash_value: 存储的哈希值
            salt: 盐值

        返回:
            密码是否正确
        """
        # 计算密码哈希
        computed_hash, _ = self.hash_password(password, salt)

        # 使用常量时间比较，防止时序攻击
        return hmac.compare_digest(computed_hash, hash_value)

    def store_password(self, password: str) -> dict:
        """
        存储密码（返回可序列化的字典）

        参数:
            password: 密码

        返回:
            包含哈希值、盐值和参数的字典
        """
        hash_value, salt = self.hash_password(password)

        return {
            'hash': hash_value.hex(),
            'salt': salt.hex(),
            'algorithm': self.algorithm,
            'iterations': self.iterations,
        }

    def check_password(self, password: str, stored: dict) -> bool:
        """
        检查密码是否匹配存储的值

        参数:
            password: 密码
            stored: 存储的密码字典

        返回:
            密码是否匹配
        """
        hash_value = bytes.fromhex(stored['hash'])
        salt = bytes.fromhex(stored['salt'])
        algorithm = stored['algorithm']
        iterations = stored['iterations']

        # 使用存储的参数计算哈希
        computed_hash = hashlib.pbkdf2_hmac(
            algorithm,
            password.encode('utf-8'),
            salt,
            iterations
        )

        return hmac.compare_digest(computed_hash, hash_value)


def demo():
    """密码存储演示"""
    print("=== 密码存储演示 ===\n")

    pm = PasswordManager()

    # 存储密码
    password = "MySecurePassword123!"
    stored = pm.store_password(password)

    print(f"密码: {password}")
    print(f"存储格式:")
    for key, value in stored.items():
        if isinstance(value, str) and len(value) > 32:
            print(f"  {key}: {value[:32]}...")
        else:
            print(f"  {key}: {value}")
    print()

    # 验证密码
    print("--- 密码验证 ---")
    print(f"正确密码验证: {pm.check_password(password, stored)}")
    print(f"错误密码验证: {pm.check_password('WrongPassword', stored)}")
    print()

    # 直接哈希验证
    print("--- 直接哈希验证 ---")
    hash_value, salt = pm.hash_password(password)
    print(f"哈希值: {hash_value.hex()[:32]}...")
    print(f"盐值: {salt.hex()[:32]}...")
    print(f"验证正确密码: {pm.verify_password(password, hash_value, salt)}")
    print(f"验证错误密码: {pm.verify_password('Wrong', hash_value, salt)}")


if __name__ == '__main__':
    demo()
