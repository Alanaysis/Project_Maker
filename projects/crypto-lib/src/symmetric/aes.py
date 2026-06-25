"""
AES (Advanced Encryption Standard) 对称加密算法实现

AES是一种分组密码，分组大小为128位（16字节），密钥长度可以是128、192或256位。

算法流程：
1. 密钥扩展：从原始密钥生成轮密钥
2. 初始轮：AddRoundKey
3. 主轮（重复N-1次）：
   - SubBytes：字节替换
   - ShiftRows：行移位
   - MixColumns：列混合
   - AddRoundKey：轮密钥加
4. 最终轮（无MixColumns）：
   - SubBytes
   - ShiftRows
   - AddRoundKey

AES-128: 10轮
AES-192: 12轮
AES-256: 14轮
"""

import os
from typing import Tuple
from .modes import ECB, CBC, CTR


class AES:
    """AES加密算法实现类"""

    # S-Box（替换盒）
    SBOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
    ]

    # 逆S-Box
    INV_SBOX = [
        0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
        0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
        0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
        0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
        0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
        0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
        0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
        0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
        0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
        0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
        0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
        0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
        0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
        0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
        0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
        0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
    ]

    # 轮常量
    RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

    def __init__(self, key: bytes):
        """
        初始化AES加密器

        参数:
            key: 密钥（16、24或32字节，对应AES-128、192、256）
        """
        if len(key) not in (16, 24, 32):
            raise ValueError("密钥长度必须是16、24或32字节")

        self.key = key
        self.key_size = len(key)
        self.num_rounds = {16: 10, 24: 12, 32: 14}[self.key_size]
        self.round_keys = self._key_expansion()

    @staticmethod
    def _xtime(a: int) -> int:
        """GF(2^8)上的乘法：乘以2"""
        return ((a << 1) ^ 0x11b) & 0xff if a & 0x80 else (a << 1) & 0xff

    def _mix_single_column(self, col: list) -> list:
        """混合单列"""
        t = col[0] ^ col[1] ^ col[2] ^ col[3]
        u = col[0]
        col[0] ^= t ^ self._xtime(col[0] ^ col[1])
        col[1] ^= t ^ self._xtime(col[1] ^ col[2])
        col[2] ^= t ^ self._xtime(col[2] ^ col[3])
        col[3] ^= t ^ self._xtime(col[3] ^ u)
        return col

    def _inv_mix_single_column(self, col: list) -> list:
        """逆混合单列"""
        u = self._xtime(self._xtime(col[0] ^ col[2]))
        v = self._xtime(self._xtime(col[1] ^ col[3]))
        col[0] ^= u
        col[1] ^= v
        col[2] ^= u
        col[3] ^= v
        return self._mix_single_column(col)

    def _sub_bytes(self, state: list) -> list:
        """字节替换"""
        return [self.SBOX[b] for b in state]

    def _inv_sub_bytes(self, state: list) -> list:
        """逆字节替换"""
        return [self.INV_SBOX[b] for b in state]

    @staticmethod
    def _shift_rows(state: list) -> list:
        """行移位"""
        s = list(state)
        # 第2行左移1位
        s[1], s[5], s[9], s[13] = s[5], s[9], s[13], s[1]
        # 第3行左移2位
        s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
        # 第4行左移3位
        s[3], s[7], s[11], s[15] = s[15], s[3], s[7], s[11]
        return s

    @staticmethod
    def _inv_shift_rows(state: list) -> list:
        """逆行移位"""
        s = list(state)
        # 第2行右移1位
        s[1], s[5], s[9], s[13] = s[13], s[1], s[5], s[9]
        # 第3行右移2位
        s[2], s[6], s[10], s[14] = s[10], s[14], s[2], s[6]
        # 第4行右移3位
        s[3], s[7], s[11], s[15] = s[7], s[11], s[15], s[3]
        return s

    def _mix_columns(self, state: list) -> list:
        """列混合"""
        s = list(state)
        for i in range(4):
            col = [s[i], s[i+4], s[i+8], s[i+12]]
            col = self._mix_single_column(col)
            s[i], s[i+4], s[i+8], s[i+12] = col
        return s

    def _inv_mix_columns(self, state: list) -> list:
        """逆列混合"""
        s = list(state)
        for i in range(4):
            col = [s[i], s[i+4], s[i+8], s[i+12]]
            col = self._inv_mix_single_column(col)
            s[i], s[i+4], s[i+8], s[i+12] = col
        return s

    @staticmethod
    def _add_round_key(state: list, round_key: list) -> list:
        """轮密钥加"""
        return [s ^ k for s, k in zip(state, round_key)]

    def _key_expansion(self) -> list:
        """
        密钥扩展

        从原始密钥生成轮密钥
        """
        # 将密钥转换为字列表
        key_words = []
        for i in range(0, self.key_size, 4):
            key_words.append(list(self.key[i:i+4]))

        # 扩展密钥
        total_words = 4 * (self.num_rounds + 1)
        while len(key_words) < total_words:
            i = len(key_words)
            temp = list(key_words[-1])

            if i % (self.key_size // 4) == 0:
                # RotWord
                temp = temp[1:] + temp[:1]
                # SubWord
                temp = [self.SBOX[b] for b in temp]
                # XOR Rcon
                temp[0] ^= self.RCON[i // (self.key_size // 4) - 1]
            elif self.key_size == 32 and i % 8 == 4:
                # AES-256的额外SubWord
                temp = [self.SBOX[b] for b in temp]

            key_words.append([a ^ b for a, b in zip(key_words[i - self.key_size // 4], temp)])

        # 转换为状态格式
        round_keys = []
        for i in range(0, total_words, 4):
            rk = []
            for j in range(4):
                rk.extend(key_words[i + j])
            round_keys.append(rk)

        return round_keys

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """
        加密单个块（16字节）

        参数:
            plaintext: 16字节明文

        返回:
            16字节密文
        """
        if len(plaintext) != 16:
            raise ValueError("明文块必须是16字节")

        state = list(plaintext)

        # 初始轮密钥加
        state = self._add_round_key(state, self.round_keys[0])

        # 主轮
        for round_num in range(1, self.num_rounds):
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._mix_columns(state)
            state = self._add_round_key(state, self.round_keys[round_num])

        # 最终轮（无MixColumns）
        state = self._sub_bytes(state)
        state = self._shift_rows(state)
        state = self._add_round_key(state, self.round_keys[self.num_rounds])

        return bytes(state)

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """
        解密单个块（16字节）

        参数:
            ciphertext: 16字节密文

        返回:
            16字节明文
        """
        if len(ciphertext) != 16:
            raise ValueError("密文块必须是16字节")

        state = list(ciphertext)

        # 初始轮密钥加
        state = self._add_round_key(state, self.round_keys[self.num_rounds])

        # 主轮（逆序）
        for round_num in range(self.num_rounds - 1, 0, -1):
            state = self._inv_shift_rows(state)
            state = self._inv_sub_bytes(state)
            state = self._add_round_key(state, self.round_keys[round_num])
            state = self._inv_mix_columns(state)

        # 最终轮
        state = self._inv_shift_rows(state)
        state = self._inv_sub_bytes(state)
        state = self._add_round_key(state, self.round_keys[0])

        return bytes(state)

    def encrypt(self, plaintext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> Tuple[bytes, bytes]:
        """
        AES加密

        参数:
            plaintext: 明文
            mode: 加密模式（'ecb', 'cbc', 'ctr'）
            iv: CBC模式的初始化向量
            nonce: CTR模式的随机数

        返回:
            (密文, IV或nonce)
        """
        if mode == 'ecb':
            ecb = ECB()
            return ecb.encrypt(plaintext, self.encrypt_block), b''
        elif mode == 'cbc':
            cbc = CBC(iv)
            return cbc.encrypt(plaintext, self.encrypt_block)
        elif mode == 'ctr':
            ctr = CTR(nonce)
            return ctr.encrypt(plaintext, self.encrypt_block)
        else:
            raise ValueError(f"不支持的模式: {mode}")

    def decrypt(self, ciphertext: bytes, mode: str = 'cbc',
                iv: bytes = None, nonce: bytes = None) -> bytes:
        """
        AES解密

        参数:
            ciphertext: 密文
            mode: 加密模式（'ecb', 'cbc', 'ctr'）
            iv: CBC模式的初始化向量
            nonce: CTR模式的随机数

        返回:
            明文
        """
        if mode == 'ecb':
            ecb = ECB()
            return ecb.decrypt(ciphertext, self.decrypt_block)
        elif mode == 'cbc':
            cbc = CBC(iv)
            return cbc.decrypt(ciphertext, self.decrypt_block, iv)
        elif mode == 'ctr':
            ctr = CTR(nonce)
            return ctr.decrypt(ciphertext, self.encrypt_block, nonce)
        else:
            raise ValueError(f"不支持的模式: {mode}")


def demo():
    """AES加密演示"""
    print("=== AES 对称加密演示 ===\n")

    # AES-128
    key = os.urandom(16)
    aes = AES(key)

    plaintext = b"Hello, AES encryption! This is a test message."
    print(f"明文: {plaintext}")
    print(f"密钥: {key.hex()}")
    print()

    # CBC模式
    ciphertext, iv = aes.encrypt(plaintext, 'cbc')
    decrypted = aes.decrypt(ciphertext, 'cbc', iv)
    print(f"CBC模式:")
    print(f"  IV: {iv.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")
    print()

    # CTR模式
    ciphertext, nonce = aes.encrypt(plaintext, 'ctr')
    decrypted = aes.decrypt(ciphertext, 'ctr', nonce)
    print(f"CTR模式:")
    print(f"  Nonce: {nonce.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")
    print()

    # AES-256
    key256 = os.urandom(32)
    aes256 = AES(key256)
    ciphertext, iv = aes256.encrypt(plaintext, 'cbc')
    decrypted = aes256.decrypt(ciphertext, 'cbc', iv)
    print(f"AES-256 CBC模式:")
    print(f"  密钥: {key256.hex()}")
    print(f"  密文: {ciphertext.hex()}")
    print(f"  解密: {decrypted}")


if __name__ == '__main__':
    demo()
