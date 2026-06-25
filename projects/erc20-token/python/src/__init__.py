"""
ERC20 Token Implementation in Python

A complete implementation of the ERC20 token standard with extensions:
- Mint (铸造)
- Burn (销毁)
- Pause (暂停)

Author: AI Assistant
License: MIT
"""

from .erc20 import ERC20Token
from .exceptions import (
    ERC20Error,
    InsufficientBalanceError,
    InsufficientAllowanceError,
    ZeroAddressError,
    MintOverflowError,
    BurnExceedsBalanceError,
    ContractPausedError,
    UnauthorizedError,
)
from .events import TransferEvent, ApprovalEvent

__version__ = "1.0.0"
__all__ = [
    "ERC20Token",
    "ERC20Error",
    "InsufficientBalanceError",
    "InsufficientAllowanceError",
    "ZeroAddressError",
    "MintOverflowError",
    "BurnExceedsBalanceError",
    "ContractPausedError",
    "UnauthorizedError",
    "TransferEvent",
    "ApprovalEvent",
]
