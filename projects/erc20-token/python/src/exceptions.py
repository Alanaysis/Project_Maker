"""
Custom exceptions for ERC20 token operations.

These exceptions provide clear error messages for common ERC20 failures,
mirroring Solidity's require() revert messages.
"""


class ERC20Error(Exception):
    """Base exception for all ERC20 errors."""
    pass


class ZeroAddressError(ERC20Error):
    """Raised when a zero address is provided where it's not allowed."""

    def __init__(self, operation: str = ""):
        message = f"ERC20: {operation} to the zero address" if operation else "ERC20: zero address not allowed"
        super().__init__(message)


class InsufficientBalanceError(ERC20Error):
    """Raised when trying to transfer more tokens than available."""

    def __init__(self, balance: int, required: int):
        self.balance = balance
        self.required = required
        super().__init__(f"ERC20: insufficient balance (have {balance}, need {required})")


class InsufficientAllowanceError(ERC20Error):
    """Raised when trying to transferFrom without enough allowance."""

    def __init__(self, allowance: int, required: int):
        self.allowance = allowance
        self.required = required
        super().__init__(f"ERC20: insufficient allowance (have {allowance}, need {required})")


class MintOverflowError(ERC20Error):
    """Raised when minting would cause total supply overflow."""

    def __init__(self, current_supply: int, mint_amount: int, max_supply: int):
        self.current_supply = current_supply
        self.mint_amount = mint_amount
        self.max_supply = max_supply
        super().__init__(
            f"ERC20: mint would overflow total supply "
            f"(current: {current_supply}, mint: {mint_amount}, max: {max_supply})"
        )


class BurnExceedsBalanceError(ERC20Error):
    """Raised when trying to burn more tokens than available."""

    def __init__(self, balance: int, burn_amount: int):
        self.balance = balance
        self.burn_amount = burn_amount
        super().__init__(f"ERC20: burn amount exceeds balance (have {balance}, burn: {burn_amount})")


class ContractPausedError(ERC20Error):
    """Raised when trying to perform operations on a paused contract."""

    def __init__(self, operation: str = ""):
        message = f"ERC20: contract is paused, cannot {operation}" if operation else "ERC20: contract is paused"
        super().__init__(message)


class UnauthorizedError(ERC20Error):
    """Raised when a non-owner tries to perform owner-only operations."""

    def __init__(self, operation: str = ""):
        message = f"ERC20: unauthorized to {operation}" if operation else "ERC20: unauthorized"
        super().__init__(message)
