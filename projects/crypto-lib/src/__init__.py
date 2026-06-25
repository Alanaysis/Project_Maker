"""
密码学库 (Crypto Library)

一个用Python实现的密码学学习库，支持哈希算法、对称加密、非对称加密和编码工具。
"""

__version__ = "1.0.0"
__author__ = "Crypto Learner"

from .hash import md5, sha1, sha256, hmac_alg
from .symmetric import aes, des, modes
from .asymmetric import rsa, ecdh, signature
from .encoding import base64_codec, hex_codec
from .utils import password, data_encrypt, digital_signature_util

__all__ = [
    "md5", "sha1", "sha256", "hmac_alg",
    "aes", "des", "modes",
    "rsa", "ecdh", "signature",
    "base64_codec", "hex_codec",
    "password", "data_encrypt", "digital_signature_util",
]
