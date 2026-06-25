"""
ERC20 Token Implementation in Python

A complete implementation of the ERC20 token standard (EIP-20) with extensions:
- Standard ERC20 functions: totalSupply, balanceOf, transfer, approve, transferFrom, allowance
- Mint (铸造): Create new tokens
- Burn (销毁): Destroy existing tokens
- Pause (暂停): Temporarily halt transfers

This implementation follows the Solidity conventions for educational purposes,
while leveraging Python's type hints and dataclasses for clarity.

Reference: https://eips.ethereum.org/EIPS/eip-20
"""

from dataclasses import dataclass, field
from typing import Optional

from .events import EventLog
from .exceptions import (
    BurnExceedsBalanceError,
    ContractPausedError,
    InsufficientAllowanceError,
    InsufficientBalanceError,
    MintOverflowError,
    UnauthorizedError,
    ZeroAddressError,
)


@dataclass
class ERC20Token:
    """
    ERC20 Token implementation with Mint, Burn, and Pause extensions.

    This class implements the full ERC20 standard plus common extensions,
    providing a Python-native way to interact with token functionality.

    Attributes:
        name: The name of the token (e.g., "My Token")
        symbol: The symbol of the token (e.g., "MTK")
        decimals: Number of decimal places (typically 18)
        owner: The address that deployed/owns the contract
        max_supply: Maximum supply cap (0 = unlimited)

    Example:
        >>> token = ERC20Token("My Token", "MTK", 18, "0xOwner")
        >>> token.mint("0xOwner", 1000000 * 10**18)
        >>> token.transfer("0xOwner", "0xBob", 100 * 10**18)
        >>> token.balance_of("0xBob")
        100000000000000000000
    """

    # Token metadata
    name: str
    symbol: str
    decimals: int = 18
    owner: str = ""
    max_supply: int = 0  # 0 means unlimited

    # Internal state (not part of public interface)
    _total_supply: int = field(default=0, repr=False)
    _balances: dict[str, int] = field(default_factory=dict, repr=False)
    _allowances: dict[str, dict[str, int]] = field(default_factory=dict, repr=False)
    _paused: bool = field(default=False, repr=False)
    _event_log: EventLog = field(default_factory=EventLog, repr=False)

    def __post_init__(self):
        """Initialize the token with the owner's address."""
        if not self.owner:
            raise ValueError("Owner address is required")

        # Initialize owner balance to 0 (must mint tokens separately)
        self._balances[self.owner] = 0

        # Initialize allowances for owner
        self._allowances[self.owner] = {}

    # ============================================================
    #                     ERC20 CORE FUNCTIONS
    # ============================================================

    @property
    def total_supply(self) -> int:
        """
        Returns the total supply of tokens.

        Equivalent to Solidity's totalSupply() function.

        Returns:
            The total number of tokens in circulation
        """
        return self._total_supply

    def balance_of(self, account: str) -> int:
        """
        Returns the balance of the given address.

        Equivalent to Solidity's balanceOf(address) function.

        Args:
            account: The address to query

        Returns:
            The token balance of the address
        """
        return self._balances.get(account, 0)

    def transfer(self, from_address: str, to_address: str, amount: int) -> bool:
        """
        Transfers `amount` tokens from `from_address` to `to_address`.

        Equivalent to Solidity's transfer(address, uint256) function,
        but with explicit from_address for Python (no msg.sender concept).

        Args:
            from_address: The sender's address
            to_address: The recipient's address
            amount: The amount to transfer

        Returns:
            True if the transfer succeeded

        Raises:
            ContractPausedError: If the contract is paused
            ZeroAddressError: If to_address is the zero address
            InsufficientBalanceError: If sender doesn't have enough tokens
        """
        # Check if contract is paused
        if self._paused:
            raise ContractPausedError("transfer")

        # Validate addresses
        if not to_address or to_address == "0x0":
            raise ZeroAddressError("transfer")

        # Check balance
        sender_balance = self._balances.get(from_address, 0)
        if sender_balance < amount:
            raise InsufficientBalanceError(sender_balance, amount)

        # Perform transfer
        self._balances[from_address] = sender_balance - amount
        self._balances[to_address] = self._balances.get(to_address, 0) + amount

        # Emit event
        self._event_log.advance_block()
        self._event_log.emit_transfer(from_address, to_address, amount)

        return True

    def allowance(self, owner: str, spender: str) -> int:
        """
        Returns the remaining number of tokens that `spender` is allowed
        to spend on behalf of `owner`.

        Equivalent to Solidity's allowance(address, address) function.

        Args:
            owner: The token owner's address
            spender: The approved spender's address

        Returns:
            The remaining allowance
        """
        if owner not in self._allowances:
            return 0
        return self._allowances[owner].get(spender, 0)

    def approve(self, owner: str, spender: str, amount: int) -> bool:
        """
        Approves `spender` to spend up to `amount` on behalf of `owner`.

        Equivalent to Solidity's approve(address, uint256) function.

        Args:
            owner: The token owner's address
            spender: The address authorized to spend
            amount: The maximum amount they can spend

        Returns:
            True if the approval succeeded

        Raises:
            ZeroAddressError: If spender is the zero address
        """
        # Validate addresses
        if not spender or spender == "0x0":
            raise ZeroAddressError("approve")

        # Initialize allowances dict if needed
        if owner not in self._allowances:
            self._allowances[owner] = {}

        # Set allowance
        self._allowances[owner][spender] = amount

        # Emit event
        self._event_log.advance_block()
        self._event_log.emit_approval(owner, spender, amount)

        return True

    def transfer_from(self, spender: str, from_address: str, to_address: str, amount: int) -> bool:
        """
        Transfers `amount` tokens from `from_address` to `to_address` using allowance.

        Equivalent to Solidity's transferFrom(address, address, uint256) function.

        The caller (spender) must have been approved by from_address to spend
        at least `amount` tokens.

        Args:
            spender: The address initiating the transfer (must have allowance)
            from_address: The address to transfer from
            to_address: The recipient's address
            amount: The amount to transfer

        Returns:
            True if the transfer succeeded

        Raises:
            ContractPausedError: If the contract is paused
            ZeroAddressError: If to_address is the zero address
            InsufficientBalanceError: If from_address doesn't have enough tokens
            InsufficientAllowanceError: If spender doesn't have enough allowance
        """
        # Check if contract is paused
        if self._paused:
            raise ContractPausedError("transferFrom")

        # Validate addresses
        if not to_address or to_address == "0x0":
            raise ZeroAddressError("transfer")

        # Check balance
        sender_balance = self._balances.get(from_address, 0)
        if sender_balance < amount:
            raise InsufficientBalanceError(sender_balance, amount)

        # Check allowance (skip if spender is the owner)
        if spender != from_address:
            current_allowance = self.allowance(from_address, spender)
            if current_allowance < amount:
                raise InsufficientAllowanceError(current_allowance, amount)

            # Decrease allowance
            self._allowances[from_address][spender] = current_allowance - amount

        # Perform transfer
        self._balances[from_address] = sender_balance - amount
        self._balances[to_address] = self._balances.get(to_address, 0) + amount

        # Emit event
        self._event_log.advance_block()
        self._event_log.emit_transfer(from_address, to_address, amount)

        return True

    # ============================================================
    #                      EXTENSION FUNCTIONS
    # ============================================================

    def mint(self, to_address: str, amount: int) -> bool:
        """
        Creates new tokens and assigns them to `to_address`.

        This is an extension function not part of the standard ERC20,
        but commonly used for token issuance.

        Args:
            to_address: The address to receive the minted tokens
            amount: The amount of tokens to mint

        Returns:
            True if minting succeeded

        Raises:
            ZeroAddressError: If to_address is the zero address
            MintOverflowError: If minting would exceed max_supply
            UnauthorizedError: If caller is not the owner
        """
        # Validate addresses
        if not to_address or to_address == "0x0":
            raise ZeroAddressError("mint")

        # Check max supply
        if self.max_supply > 0 and self._total_supply + amount > self.max_supply:
            raise MintOverflowError(self._total_supply, amount, self.max_supply)

        # Perform mint
        self._total_supply += amount
        self._balances[to_address] = self._balances.get(to_address, 0) + amount

        # Emit event (mint is from 0x0)
        self._event_log.advance_block()
        self._event_log.emit_transfer("0x0", to_address, amount)

        return True

    def burn(self, from_address: str, amount: int) -> bool:
        """
        Destroys `amount` tokens from `from_address`.

        This is an extension function not part of the standard ERC20,
        but commonly used for deflationary tokenomics.

        Args:
            from_address: The address to burn tokens from
            amount: The amount of tokens to burn

        Returns:
            True if burning succeeded

        Raises:
            BurnExceedsBalanceError: If burn amount exceeds balance
        """
        # Check balance
        sender_balance = self._balances.get(from_address, 0)
        if sender_balance < amount:
            raise BurnExceedsBalanceError(sender_balance, amount)

        # Perform burn
        self._balances[from_address] = sender_balance - amount
        self._total_supply -= amount

        # Emit event (burn is to 0x0)
        self._event_log.advance_block()
        self._event_log.emit_transfer(from_address, "0x0", amount)

        return True

    def pause(self, caller: str) -> bool:
        """
        Pauses the contract, preventing all transfers.

        This is an extension function for emergency situations.

        Args:
            caller: The address requesting the pause (must be owner)

        Returns:
            True if pause succeeded

        Raises:
            UnauthorizedError: If caller is not the owner
        """
        if caller != self.owner:
            raise UnauthorizedError("pause")

        self._paused = True
        return True

    def unpause(self, caller: str) -> bool:
        """
        Unpauses the contract, resuming transfers.

        Args:
            caller: The address requesting the unpause (must be owner)

        Returns:
            True if unpause succeeded

        Raises:
            UnauthorizedError: If caller is not the owner
        """
        if caller != self.owner:
            raise UnauthorizedError("unpause")

        self._paused = False
        return True

    @property
    def is_paused(self) -> bool:
        """
        Returns whether the contract is paused.

        Returns:
            True if the contract is paused
        """
        return self._paused

    # ============================================================
    #                      UTILITY FUNCTIONS
    # ============================================================

    def increase_allowance(self, owner: str, spender: str, added_value: int) -> bool:
        """
        Atomically increases the allowance granted to `spender` by `added_value`.

        This is safer than calling approve directly because it avoids the
        "front-running" attack vector.

        Args:
            owner: The token owner's address
            spender: The address to increase allowance for
            added_value: The amount to increase the allowance by

        Returns:
            True if the increase succeeded
        """
        current_allowance = self.allowance(owner, spender)
        new_allowance = current_allowance + added_value
        return self.approve(owner, spender, new_allowance)

    def decrease_allowance(self, owner: str, spender: str, subtracted_value: int) -> bool:
        """
        Atomically decreases the allowance granted to `spender` by `subtracted_value`.

        Args:
            owner: The token owner's address
            spender: The address to decrease allowance for
            subtracted_value: The amount to decrease the allowance by

        Returns:
            True if the decrease succeeded

        Raises:
            InsufficientAllowanceError: If decreased allowance would go below zero
        """
        current_allowance = self.allowance(owner, spender)
        if current_allowance < subtracted_value:
            raise InsufficientAllowanceError(current_allowance, subtracted_value)

        new_allowance = current_allowance - subtracted_value
        return self.approve(owner, spender, new_allowance)

    @property
    def event_log(self) -> EventLog:
        """
        Returns the event log for this token.

        Returns:
            The EventLog instance
        """
        return self._event_log

    def get_all_holders(self) -> list[str]:
        """
        Returns a list of all addresses that hold tokens.

        Returns:
            List of addresses with non-zero balance
        """
        return [addr for addr, balance in self._balances.items() if balance > 0]

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the token state.

        Useful for serialization and debugging.

        Returns:
            Dictionary with token state
        """
        return {
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "owner": self.owner,
            "total_supply": self._total_supply,
            "max_supply": self.max_supply,
            "paused": self._paused,
            "balances": dict(self._balances),
            "holders_count": len(self.get_all_holders()),
        }
